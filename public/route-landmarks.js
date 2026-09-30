import {replacementMaskGLSL} from './landmark-footprint.js';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';

// Photo-derived representative landmarks. Models use the city's 100 m units.
export class RouteLandmarks {
  constructor({scene, camera, renderer, stage, city, invalidate,groundOffset=()=>0}) {
    Object.assign(this, {scene, camera, renderer, stage, city, invalidate,groundOffset});
    this.draco=new DRACOLoader().setDecoderPath('public/vendor/examples/jsm/libs/draco/gltf/').setWorkerLimit(1);
    this.loader = new GLTFLoader().setDRACOLoader(this.draco);
    this.root = new THREE.Group(); this.root.name = 'Photo referenced tourism landmarks'; scene.add(this.root);
    this.entries = []; this.loading = 0; this.enabled = true; this.height = 1; this.revision = 0;
    this.frustum = new THREE.Frustum(); this.matrix = new THREE.Matrix4();
  }
  async init() {
    try {
      const response = await fetch('public/assets/route-landmarks/manifest.json', {cache:'no-store'});
      if (!response.ok) return;
      const manifest = await response.json();
      this.entries = manifest.assets.map(spec => ({spec, preview:null, detail:null, jobs:{}, pending:new Set(), errors:{}, near:false, lastSeen:0}));
      this.installMasks();
    } catch (error) { console.warn('Tourism landmark manifest unavailable', error); }
  }
  get(id) { return this.entries.find(entry => entry.spec.id === id); }
  setEnabled(enabled) {this.enabled = enabled; this.root.visible = enabled; this.invalidate();}
  setHeight(height) {this.height = height; this.root.scale.y = height;for(const e of this.entries)for(const level of ['preview','detail'])if(e[level])e[level].position.y=((e.spec.groundHeight??.018)+this.groundOffset(e.spec.x,e.spec.y))/height; this.invalidate();}
  installMasks() {
    if (!this.entries.length) return;
    this.maskBounds = {value:this.entries.map(({spec}) => new THREE.Vector4(...spec.bounds))};
    this.maskActive = {value:this.entries.map(() => 0)};
    const polygons=this.entries.map((e,i)=>({spec:e.spec,index:i})).filter(e=>e.spec.maskPolygon||e.spec.maskPolygons);
    const helpers=polygons.map(e=>replacementMaskGLSL(e.spec,`tourPolygon${e.index}`)).join("\n");
    const polygonSkip=polygons.map(e=>`i==${e.index}`).join("||")||"false";
    const polygonClips=polygons.map(e=>`if(tourActive[${e.index}]>.5&&tourPolygon${e.index}(vec2(tourWorld.x,-tourWorld.z)))discard;`).join("\n");
    this.city.traverse(mesh => {
      if (!mesh.isMesh || !/^(buildings|landmark)/.test(mesh.userData.layer || '')) return;
      const layer = mesh.userData.layer || '';
      if(layer==='buildings_urban_paving')return;
      const replacement = this.entries.findIndex(e => layer === `landmark_${e.spec.id}`);
      const patch = material => {
        const before = material.onBeforeCompile, key = material.customProgramCacheKey();
        material.onBeforeCompile = (shader, renderer) => {
          before.call(material, shader, renderer);
          shader.uniforms.tourBounds = this.maskBounds; shader.uniforms.tourActive = this.maskActive;
          shader.vertexShader = 'varying vec3 tourWorld;\n' + shader.vertexShader;
          shader.vertexShader = shader.vertexShader.replace('#include <project_vertex>', '#include <project_vertex>\ntourWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
          shader.fragmentShader = `varying vec3 tourWorld;uniform vec4 tourBounds[${this.entries.length}];uniform float tourActive[${this.entries.length}];\n` + helpers + shader.fragmentShader;
          const clipping = replacement >= 0 ? `if(tourActive[${replacement}]>.5)discard;` : `
            for(int i=0;i<${this.entries.length};i++) {
              if(${polygonSkip})continue;
              vec2 tp=vec2(tourWorld.x,-tourWorld.z);vec4 tb=tourBounds[i];
              if(tourActive[i]>.5&&tp.x>tb.x&&tp.x<tb.z&&tp.y>tb.y&&tp.y<tb.w)discard;
            }${polygonClips}`;
          shader.fragmentShader = shader.fragmentShader.replace('#include <clipping_planes_fragment>', '#include <clipping_planes_fragment>\n'+clipping);
        };
        material.customProgramCacheKey = () => `${key}/tour-mask/${this.entries.length}/${replacement}/${helpers}`;
        material.needsUpdate = true;
      };
      (Array.isArray(mesh.material)?mesh.material:[mesh.material]).forEach(patch);
      if (mesh.customDepthMaterial) patch(mesh.customDepthMaterial);
    });
    // Bridge geometry replaces the flat road beneath its arch only after loading.
    const bridges=this.entries.map((e,i)=>({spec:e.spec,index:i})).filter(e=>e.spec.roadReplacement);
    this.city.traverse(mesh=>{
      if(!mesh.isMesh||!['roads_local','roads_major','paths'].includes(mesh.userData.layer))return;
      const patch=material=>{
        const before=material.onBeforeCompile,key=material.customProgramCacheKey();
        material.onBeforeCompile=(shader,renderer)=>{
          before.call(material,shader,renderer);shader.uniforms.bridgeActive=this.maskActive;
          shader.vertexShader='varying vec3 bridgeWorld;\n'+shader.vertexShader;
          shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nbridgeWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
          shader.fragmentShader=`varying vec3 bridgeWorld;uniform float bridgeActive[${this.entries.length}];\n`+shader.fragmentShader;
          const clips=bridges.map(({spec,index})=>{
            const {axis,halfLength,halfWidth}=spec.roadReplacement;
            return `{vec2 d=vec2(bridgeWorld.x,-bridgeWorld.z)-vec2(${spec.x},${spec.y});vec2 axis=vec2(${axis[0]},${axis[1]});if(bridgeActive[${index}]>.5&&abs(dot(d,axis))<${halfLength}&&abs(dot(d,vec2(axis.y,-axis.x)))<${halfWidth})discard;}`;
          }).join('\n');
          shader.fragmentShader=shader.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\n'+clips);
        };
        material.customProgramCacheKey=()=>`${key}/bridge-road/${JSON.stringify(bridges)}`;material.needsUpdate=true;
      };
      (Array.isArray(mesh.material)?mesh.material:[mesh.material]).forEach(patch);
      if(mesh.customDepthMaterial)patch(mesh.customDepthMaterial);
    });
  }
  installPalaceMasks(root) {
    const replacements=this.entries.map((e,i)=>({spec:e.spec,index:i})).filter(e=>e.spec.palaceReplacement);
    if(!replacements.length)return;
    const patched=new Set();
    root.traverse(mesh=>{
      if(!mesh.isMesh||/Courtyard|Garden|Water|Terrace_Paving|Foliage|Tree_Bark/.test(mesh.material.name))return;
      for(const material of [mesh.material,mesh.customDepthMaterial]){
        if(!material||patched.has(material))continue;patched.add(material);
        const before=material.onBeforeCompile,key=material.customProgramCacheKey();
        material.onBeforeCompile=(shader,renderer)=>{
          before.call(material,shader,renderer);
          shader.uniforms.palaceReplacementActive=this.maskActive;
          shader.vertexShader='varying vec3 replacementWorld;\n'+shader.vertexShader;
          shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nreplacementWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
          shader.fragmentShader=`varying vec3 replacementWorld;uniform float palaceReplacementActive[${this.entries.length}];\n`+shader.fragmentShader;
          const clips=replacements.map(({spec,index})=>{const [x0,y0,x1,y1]=spec.bounds;return `if(palaceReplacementActive[${index}]>.5&&replacementWorld.x>${x0}&&replacementWorld.x<${x1}&&-replacementWorld.z>${y0}&&-replacementWorld.z<${y1})discard;`;}).join('\n');
          shader.fragmentShader=shader.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\n'+clips);
        };
        material.customProgramCacheKey=()=>`${key}/palace-replacement/${JSON.stringify(replacements)}`;material.needsUpdate=true;
      }
    });
  }
  async request(entry, level) {
    if (entry.pending.has(level)) return entry.jobs[level];
    if (entry[level] || performance.now() - (entry.errors[level] || -Infinity) < 30000) return;
    entry.pending.add(level); this.loading++;
    entry.jobs[level] = (async () => {
    try {
      const {scene:root} = await this.loader.loadAsync(entry.spec.lods[level]);
      root.name = `tourism/${entry.spec.id}/${level}`;
      root.position.set(entry.spec.x, ((entry.spec.groundHeight??.018)+this.groundOffset(entry.spec.x,entry.spec.y))/this.height, -entry.spec.y);
      root.rotation.y=THREE.MathUtils.degToRad(entry.spec.rotation || 0);
      root.traverse(mesh => {
        if (!mesh.isMesh) return;
        mesh.castShadow = true; mesh.receiveShadow = true;
        for (const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]) {
          for (const value of Object.values(material)) if (value?.isTexture) value.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
          material.envMapIntensity = .7;
        }
      });
      root.visible = false; this.root.add(root); entry[level] = root; this.revision++;
      if(new URLSearchParams(location.search).has('qa')){
        let triangles=0,meshes=0;root.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;}});
        const box=new THREE.Box3().setFromObject(root);
        console.info('Landmark loaded',JSON.stringify({id:entry.spec.id,level,meshes,triangles,bounds:[box.min.toArray(),box.max.toArray()]}));
      }
    } catch (error) {entry.errors[level] = performance.now(); console.warn('Tourism model unavailable',entry.spec.id,level,error);}
    finally {entry.pending.delete(level); this.loading--; this.invalidate();}
    })();
    return entry.jobs[level];
  }
  async preparePoster(ids) {
    this.exporting = true;
    for (const id of ids) {const entry=this.get(id);if(entry)await this.request(entry,'preview');}
    for (let i=0;i<this.entries.length;i++) {
      const entry=this.entries[i];
      if(entry.preview)entry.preview.visible=this.enabled&&!['national','bell','drum','wudaoying','yandai'].includes(entry.spec.id);
      if(entry.detail)entry.detail.visible=false;
      this.maskActive.value[i]=this.enabled&&entry.preview&&!['national','bell','drum','wudaoying','yandai'].includes(entry.spec.id)?1:0;
    }
    return () => {this.exporting=false;this.update(performance.now());this.invalidate();};
  }
  release(entry) {
    const root = entry.detail; if (!root) return;
    root.removeFromParent(); const resources = new Set(), images = new Set();
    root.traverse(mesh => {
      if (!mesh.isMesh) return; resources.add(mesh.geometry);
      for (const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]) {
        resources.add(material);
        for (const value of Object.values(material)) if (value?.isTexture) {resources.add(value); images.add(value.image);}
      }
    });
    for (const resource of resources) resource.dispose(); for (const image of images) image?.close?.();
    entry.detail = null; this.revision++;
    if(new URLSearchParams(location.search).has('qa'))console.info('Landmark detail released',entry.spec.id);
  }
  update(time) {
    if (!this.entries.length || this.exporting) return false;
    this.frustum.setFromProjectionMatrix(this.matrix.multiplyMatrices(this.camera.projectionMatrix,this.camera.matrixWorldInverse));
    const pixelsPerUnit = this.stage.clientHeight*this.camera.zoom/(this.camera.top-this.camera.bottom);
    let changed = false;
    for (let i=0;i<this.entries.length;i++) {
      const entry=this.entries[i], s=entry.spec;
      const visible=this.enabled&&this.frustum.intersectsSphere(new THREE.Sphere(new THREE.Vector3(s.x,s.height*this.height/2,-s.y),Math.max(s.span,s.height*this.height)));
      entry.near=visible&&pixelsPerUnit*Math.max(s.span,s.height*this.height)>(entry.near?110:150);
      if (visible && !entry.preview && this.loading<2) this.request(entry,'preview');
      if (entry.near) {
        entry.lastSeen=time;
        if(entry.preview&&!entry.detail&&this.loading<2)this.request(entry,'detail');
      }
      if(!entry.near&&entry.detail&&time-entry.lastSeen>25000)this.release(entry);
      const usePhoto=!['national','bell','drum','wudaoying','yandai'].includes(entry.spec.id)||entry.near;
      for(const level of ['preview','detail'])if(entry[level]){
        const want=visible&&usePhoto&&(level==='detail'?entry.near:!(entry.near&&entry.detail));
        if(entry[level].visible!==want){entry[level].visible=want;changed=true;}
      }
      // Keep the museum's clean geographic mass at city scale; its photo mesh contains foreground scenery.
      const covered=this.enabled&&entry.preview&&usePhoto?1:0;
      if(this.maskActive.value[i]!==covered){this.maskActive.value[i]=covered;changed=true;}
    }
    if(changed)this.revision++;
    return changed;
  }
  get near() {return this.entries.some(e=>e.near&&e.detail);}
  get state() {return this.entries.map(e=>({id:e.spec.id,preview:!!e.preview,detail:!!e.detail,loading:[...e.pending],errors:Object.keys(e.errors)}));}
}
