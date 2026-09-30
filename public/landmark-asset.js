import * as THREE from 'three';

// Authored landmark models retain their own materials and are streamed on zoom.
// The host owns the loader, request budget, visible-bounds test and city coverage.
export class LandmarkAsset {
  constructor(host, spec) {
    this.host = host;
    this.spec = spec;
    this.coverage = {value: 0};
    this.refinement = {value: 0};
    this.levels = Object.fromEntries(['preview', 'detail'].map(id => [id, {
      id, url: spec.lods[id].url, root: null, bytes: 0, requested: false,
      failedAt: null, controller: null,
    }]));
    this.lastSeen = 0;
    this.lastDetailSeen = 0;
    this.wanted = false;
    this.detailWanted = false;
    this.fallbackNodes = new Set();
  }

  // Called by the host's existing material compiler only for source-ID-tagged
  // fallback nodes. Ordinary palace geometry keeps its original shader.
  maskFallback(shader) {
    shader.uniforms.externalCoverage = this.coverage;
    shader.fragmentShader = 'uniform float externalCoverage;\n' + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace('#include <clipping_planes_fragment>', `
      #include <clipping_planes_fragment>
      float externalDither = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(.06711056,.00583715))));
      if (externalDither < externalCoverage) discard;
    `);
  }

  prepare(root, level) {
    const materials = new Set(), geometries = new Set(), textures = new Set();
    const prepareMaterial = material => {
      if (materials.has(material)) return;
      materials.add(material);
      for (const value of Object.values(material)) if (value?.isTexture) {
        textures.add(value);
        value.anisotropy = Math.min(8, this.host.renderer.capabilities.getMaxAnisotropy());
      }
      // Keep the creator's PBR colors, maps, UVs, roughness and transparency.
      const originalCompile = material.onBeforeCompile;
      const originalKey = material.customProgramCacheKey();
      material.onBeforeCompile = (shader, renderer) => {
        originalCompile.call(material, shader, renderer);
        shader.uniforms.cityCoverage = this.host.coverage;
        shader.uniforms.externalCoverage = this.coverage;
        shader.uniforms.externalRefinement = this.refinement;
        shader.fragmentShader = 'uniform float cityCoverage;uniform float externalCoverage;uniform float externalRefinement;\n' + shader.fragmentShader;
        shader.fragmentShader = shader.fragmentShader.replace('#include <clipping_planes_fragment>', `
          #include <clipping_planes_fragment>
          float assetDither = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(.06711056,.00583715))));
          if (assetDither >= cityCoverage || assetDither >= externalCoverage) discard;
          ${level === 'detail' ? 'if (assetDither >= externalRefinement) discard;' : 'if (assetDither < externalRefinement) discard;'}
        `);
      };
      material.customProgramCacheKey = () => `${originalKey}/licensed-landmark/${level}/1`;
      material.needsUpdate = true;
    };
    root.name = `licensed-landmark/${this.spec.id}/${level}`;
    root.traverse(mesh => {
      if (!mesh.isMesh) return;
      geometries.add(mesh.geometry);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData.detailLayer = 'always';
      const meshMaterials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      meshMaterials.forEach(prepareMaterial);
      // An alpha-cut roof needs the same silhouette in its shadow. Multi-material
      // meshes are split during conversion before this adapter is activated.
      const m = meshMaterials[0];
      mesh.customDepthMaterial = new THREE.MeshDepthMaterial({
        depthPacking: THREE.RGBADepthPacking, map: m.map, alphaMap: m.alphaMap,
        alphaTest: m.alphaTest, side: m.side,
      });
      prepareMaterial(mesh.customDepthMaterial);
    });
    let bytes = 0;
    for (const geometry of geometries) {
      for (const a of Object.values(geometry.attributes)) bytes += a.array.byteLength;
      bytes += geometry.index?.array.byteLength || 0;
    }
    for (const t of textures) bytes += (t.image?.width || 0) * (t.image?.height || 0) * 4 * 4 / 3;
    root.userData.ownedResources = {materials, geometries, textures};
    root.visible = false;
    this.host.root.add(root);
    return Math.ceil(bytes);
  }

  async request(level, t) {
    if (level.requested || level.root || (level.failedAt !== null && t - level.failedAt < 15000)) return;
    const controller = new AbortController();
    level.controller = controller;
    level.requested = true;
    this.host.loading++;
    let root;
    try {
      root = await this.host.readGLB(level.url, controller.signal);
      if (controller.signal.aborted) {
        this.releaseRoot(root);
        return;
      }
      level.bytes = this.prepare(root, level.id);
      level.root = root;
      level.failedAt = null;
    } catch (error) {
      if (root && !level.root) this.releaseRoot(root);
      if (error.name !== 'AbortError') {
        level.failedAt = performance.now();
        console.warn('Landmark asset load failed', this.spec.id, level.id, error);
      }
    } finally {
      level.requested = false;
      level.controller = null;
      this.host.loading--;
      this.host.invalidate();
    }
  }

  update(t, dt, ppu) {
    const visible = this.host.near && this.host.mediumReady && this.host.visible(this.spec.bounds);
    this.wanted = visible && ppu > (this.wanted ? 135 : 180);
    this.detailWanted = this.wanted && ppu > (this.detailWanted ? 480 : 580);
    if (this.wanted) this.lastSeen = t;
    if (this.detailWanted) this.lastDetailSeen = t;
    const preview = this.levels.preview, detail = this.levels.detail;
    if (!this.wanted) preview.controller?.abort();
    if (!this.detailWanted) detail.controller?.abort();
    if (this.wanted && this.host.loading < 2) this.request(preview, t);
    if (this.detailWanted && preview.root && this.host.loading < 2) this.request(detail, t);
    const fade = (uniform, destination) => {
      const previous = uniform.value, step = dt * 2.5;
      uniform.value = Math.abs(destination - previous) <= step ? destination : previous + Math.sign(destination - previous) * step;
      return previous !== uniform.value;
    };
    // Never hide a fallback until the replacement has finished parsing.
    let changed = fade(this.coverage, this.wanted && preview.root ? 1 : 0);
    changed = fade(this.refinement, this.detailWanted && detail.root ? 1 : 0) || changed;
    if (preview.root) preview.root.visible = this.host.coverage.value > 0 && this.coverage.value > 0 && this.refinement.value < 1;
    if (detail.root) detail.root.visible = this.host.coverage.value > 0 && this.coverage.value > 0 && this.refinement.value > 0;
    for (const mesh of this.fallbackNodes) mesh.visible = this.coverage.value < 1;
    if (!this.detailWanted && this.refinement.value === 0 && t - this.lastDetailSeen > 5000) this.release(detail);
    if (!this.wanted && this.coverage.value === 0 && t - this.lastSeen > 20000) this.release(preview);
    return changed;
  }

  releaseRoot(root) {
    root.removeFromParent();
    const resources = root.userData.ownedResources || {materials: new Set(), geometries: new Set(), textures: new Set()};
    if (!root.userData.ownedResources) root.traverse(mesh => {
      if (!mesh.isMesh) return;
      resources.geometries.add(mesh.geometry);
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        resources.materials.add(m);
        for (const value of Object.values(m)) if (value?.isTexture) resources.textures.add(value);
      }
    });
    for (const resource of [...resources.materials, ...resources.geometries, ...resources.textures]) resource.dispose();
    const images = new Set([...resources.textures].map(t => t.image).filter(Boolean));
    for (const bitmap of images) bitmap.close?.();
  }

  release(level) {
    if (level.root) this.releaseRoot(level.root);
    level.root = null;
    level.bytes = 0;
  }

  get state() {
    return {id: this.spec.id, coverage: this.coverage.value, refinement: this.refinement.value,
      bytes: this.levels.preview.bytes + this.levels.detail.bytes,
      levels: Object.values(this.levels).map(l => ({id: l.id, ready: !!l.root, loading: l.requested, failed: l.failedAt !== null}))};
  }
}
