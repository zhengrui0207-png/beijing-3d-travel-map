import {footprintContains} from './landmark-footprint.js';
import * as THREE from 'three';
import {FACADE_PROFILES} from './facade-profiles.js?v=atlas-foliage1';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

// An illustrated travel atlas over the unchanged OSM geometry. All distances
// and map coordinates remain geographic; only surface treatment is stylised.
export class CartographicStyle {
  constructor({scene,city,invalidate,groundOffset=()=>0,landmarkMasks=[],landscapeUrl='public/assets/cartographic/landscape.json'}){Object.assign(this,{scene,city,invalidate,groundOffset,landmarkMasks,landscapeUrl});this.root=new THREE.Group();this.root.name='Atlas illustrative planting';scene.add(this.root);this.parts=[];this.height=1;}
  material(mesh,kind){
    const m=mesh.material,previous=m.onBeforeCompile,key=m.customProgramCacheKey();
    const profile=FACADE_PROFILES[mesh.userData.facadeProfile]||FACADE_PROFILES.generic;
    const num=n=>Number(n).toFixed(4),vec=a=>`vec${a.length}(${a.map(num).join(',')})`;
    const [left,bottom,right,top]=profile.opening;
    m.onBeforeCompile=(s,r)=>{
      previous.call(m,s,r);
      if(kind==='roof'&&this.roofSurface){s.uniforms.atlasRoofSurface={value:this.roofSurface};s.fragmentShader='uniform sampler2D atlasRoofSurface;\n'+s.fragmentShader;}
      s.vertexShader='varying vec3 atlasP;varying vec3 atlasN;varying vec2 atlasUV;\n'+s.vertexShader;
      s.vertexShader=s.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\natlasUV=uv;atlasP=(modelMatrix*vec4(transformed,1.)).xyz;atlasN=normalize(mat3(modelMatrix)*normal);');
      s.fragmentShader='varying vec3 atlasP;varying vec3 atlasN;varying vec2 atlasUV;\n'+s.fragmentShader;
      let paint='';
      if(kind==='facade'||kind==='tagged-facade')paint=`
        vec2 domeDelta=(atlasP.xz-vec2(-26.855027,12.978075))/vec2(1.125621,0.783415);if(dot(domeDelta,domeDelta)<1.02)discard;
        vec2 cell=atlasUV, f=fract(cell), aa=max(fwidth(cell),vec2(.003));
        vec2 opening=smoothstep(${vec([left,bottom])},${vec([left,bottom])}+aa,f)*(1.-smoothstep(${vec([right,top])},${vec([right,top])}+aa,f));
        float visible=1.-smoothstep(.3,1.1,max(aa.x,aa.y));
        float variation=.5+.5*sin(atlasP.x*.73+atlasP.z*.97);
        vec3 plaster=${kind==='tagged-facade'?'diffuseColor.rgb':`${vec(profile.wall)}*(.94+.06*variation)`};
        float atlasPane=opening.x*opening.y;
        vec2 outer=smoothstep(${vec([left-.03,bottom-.03])},${vec([left-.03,bottom-.03])}+aa,f)*(1.-smoothstep(${vec([right+.03,top+.03])},${vec([right+.03,top+.03])}+aa,f));
        float atlasFrame=max(0.,outer.x*outer.y-atlasPane);
        float mullion=(1.-smoothstep(.010,.010+aa.x,abs(f.x-.5)))*atlasPane;
        float transom=(1.-smoothstep(.009,.009+aa.y,abs(f.y-${num(bottom+(top-bottom)*.7)})))*atlasPane;
        atlasFrame=max(atlasFrame,max(mullion,transom));
        float atlasGlass=atlasPane*(1.-atlasFrame)*visible;
        diffuseColor.rgb=mix(plaster,${vec(profile.glass)},atlasGlass*.96);
        diffuseColor.rgb=mix(diffuseColor.rgb,${vec(profile.frame)},atlasFrame*visible);
        float sill=(1.-smoothstep(.015,.045,abs(f.y-(${num(bottom-.04)}))))*step(${num(left-.04)},f.x)*step(f.x,${num(right+.04)})*visible;
        diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.68,.67,.59),sill*${num(profile.sill)});
        float atlasRelief=(atlasFrame*.0005-atlasPane*.0008+sill*.0007)*visible;
      `;
      if(kind==='roof')paint=`
        vec2 domeDelta=(atlasP.xz-vec2(-26.855027,12.978075))/vec2(1.125621,0.783415);if(dot(domeDelta,domeDelta)<1.02)discard;
        float slope=1.-smoothstep(.85,.99,abs(atlasN.y));
        vec2 fall=length(atlasN.xz)>.01?normalize(atlasN.xz):vec2(1.,0.);
        vec2 ridge=vec2(-fall.y,fall.x);
        vec2 tiles=vec2(dot(atlasP.xz,ridge)*500.,dot(atlasP.xz,fall)*285.);
        float vis=1.-smoothstep(.25,.9,max(fwidth(tiles.x),fwidth(tiles.y)));
        vec2 tileCell=fract(tiles),tileAA=max(fwidth(tiles),vec2(.002));
        float joint=1.-smoothstep(.04,.04+tileAA.y,tileCell.y);
        float roll=.5+.5*cos(tiles.x*6.2831853);
        ${this.roofSurface?`vec3 roofTex=texture2D(atlasRoofSurface,atlasP.xz*12.5).rgb;float roofGrain=clamp(dot(roofTex,vec3(.2126,.7152,.0722))/.235,.65,1.45);`:'float roofGrain=1.;'}
        float flatFinish=.78*roofGrain;
        float tiledFinish=.40+.045*sin(atlasP.x*.73+atlasP.z*.97)+(roll*.055-joint*.10)*vis;
        diffuseColor.rgb*=mix(flatFinish,tiledFinish,slope);
        float atlasRelief=(roll*.00022-joint*.00008)*vis*slope+(roofGrain-1.)*.000008*(1.-slope);
      `;
      if(kind==='building')paint=`
        vec2 domeDelta=(atlasP.xz-vec2(-26.855027,12.978075))/vec2(1.125621,0.783415);if(dot(domeDelta,domeDelta)<1.02)discard;
        // Dome footprint masking is installed from cached OSM bounds below.
        float wall=1.-smoothstep(.3,.7,abs(atlasN.y));
        vec2 facade=vec2(abs(atlasN.x)>abs(atlasN.z)?atlasP.z:atlasP.x,atlasP.y);
        vec2 cell=facade*vec2(26.,30.);vec2 f=fract(cell);
        vec2 aa=max(fwidth(cell),vec2(.005));
        vec2 win=smoothstep(vec2(.16),vec2(.16)+aa,f)*(1.-smoothstep(vec2(.74),vec2(.74)+aa,f));
        float vis=1.-smoothstep(.35,1.2,max(aa.x,aa.y));
        float pane=win.x*win.y*wall*vis*step(.10,atlasP.y);
        vec3 ivory=vec3(.70,.68,.57),glass=vec3(.028,.105,.16);
        float variation=.5+.5*sin(atlasP.x*.73+atlasP.z*.97);
        vec3 body=mix(ivory,vec3(.40,.55,.62),variation*.64);
        vec3 roof=variation<.33?vec3(.085,.13,.16):variation<.67?vec3(.16,.16,.135):vec3(.20,.225,.21);
        diffuseColor.rgb=mix(mix(roof,body,wall),glass,pane*.82);
        float cornice=(1.-smoothstep(.018,.055,fract(atlasP.y*6.)))*wall*vis;
        diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.89,.87,.75),cornice*.36);
      `;
      if(kind==='water')paint=`
        float wave=sin(atlasP.x*63.+sin(atlasP.z*29.))*sin(atlasP.z*75.+atlasP.x*8.);
        float vis=1.-smoothstep(.12,.8,length(fwidth(atlasP.xz*30.)));
        diffuseColor.rgb=mix(vec3(.002,.14,.39),vec3(.005,.34,.53),.5+.5*sin(atlasP.x*.3+atlasP.z*.2));
        diffuseColor.rgb+=wave*.025*vis;
      `;
      if(kind==='park')paint=`float moss=.5+.5*sin(atlasP.x*5.2+sin(atlasP.z*4.))*sin(atlasP.z*6.1);diffuseColor.rgb=mix(vec3(.10,.28,.035),vec3(.30,.47,.065),moss*.6);`;
      s.fragmentShader=s.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\n'+paint);
      if(kind==='facade'||kind==='tagged-facade'||kind==='roof'){
        // Screen-filtered relief in the same 100 m coordinates as the geometry.
        // Adds construction-scale shading without instancing millions of frames.
        s.fragmentShader=s.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
          vec3 atlasDx=dFdx(-vViewPosition),atlasDy=dFdy(-vViewPosition);
          vec3 atlasR1=cross(atlasDy,normal),atlasR2=cross(normal,atlasDx);
          float atlasDet=dot(atlasDx,atlasR1);
          if(abs(atlasDet)>1e-16)normal=normalize(abs(atlasDet)*normal-sign(atlasDet)*(dFdx(atlasRelief)*atlasR1+dFdy(atlasRelief)*atlasR2));
        `);
      }
      if(kind==='facade'||kind==='tagged-facade')s.fragmentShader=s.fragmentShader.replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nroughnessFactor=mix(roughnessFactor,.24,atlasGlass);');
    };m.customProgramCacheKey=()=>key+'/travel-atlas-v7/'+kind+'/'+(mesh.userData.facadeProfile||'generic');m.needsUpdate=true;
  }
  async init(){
    try{this.roofSurface=await new THREE.TextureLoader().loadAsync('public/assets/urban-materials/concrete-roof-v1.png');this.roofSurface.wrapS=this.roofSurface.wrapT=THREE.RepeatWrapping;this.roofSurface.colorSpace=THREE.SRGBColorSpace;this.roofSurface.anisotropy=4;this.roofSurface.needsUpdate=true;}catch(error){console.warn('Roof surface unavailable; base roof material retained',error);}
    this.city.traverse(o=>{
      if(!o.isMesh)return;const l=o.userData.layer||'',m=o.material;
      if(l==='buildings_urban_roofs')this.material(o,'roof');
      else if(l==='buildings_urban_courtyard'){/* Keep the reconstructed historic materials. */}
      else if(l==='buildings_urban_paving'){m.color.set('#b6afa3');m.roughness=.97;}
      else if(l==='buildings_urban_tagged_facade')this.material(o,'tagged-facade');
      else if(l==='buildings_urban_walls')this.material(o,'facade');
      else if(l==='buildings_urban_heritage'){m.roughness=.9;}
      else if(l.startsWith('buildings'))this.material(o,'building');
      else if(l==='water'){m.roughness=.3;m.metalness=.05;m.envMapIntensity=.45;this.material(o,'water');}
      else if(l==='parks'||l==='urban_ground_green')this.material(o,'park');
      else if(l.startsWith('roads'))m.color.set('#59666e');
      else if(l==='paths')m.color.set('#d6c7a6');
      else if(l==='terrain')m.color.set('#b9b8ac');
      else if(l==='base')m.color.set('#a4b39b');
      else if(l==='palace_roofs'||m.name.startsWith('Roof')){m.color.set('#ec9a14');m.roughness=.6;}
      else if(l==='palace_buildings'||m.name.startsWith('Palace'))m.color.set('#bf3220');
      else if(l==='trees')m.color.set('#577b24');
    });
    try{
      const response=await fetch(this.landscapeUrl);if(!response.ok)throw Error(response.status);
      const data=await response.json();
      try{const model=await new GLTFLoader().loadAsync('public/assets/cartographic/botanical-tree.glb');this.treeAsset=model.scene;}catch(e){console.warn('Textured trees unavailable; using existing canopy',e);}
      const trees=data.trees.filter(([x,y])=>!this.landmarkMasks.some(mask=>{if(mask.polygon)return footprintContains([x,y],mask.polygon,.15);const [a,b,c,d]=mask;return x>a-.12&&x<c+.12&&y>b-.12&&y<d+.12;}));
      this.buildTrees(trees);
      // Replace the old decorative cones only after the planted tree layer succeeds.
      this.city.traverse(o=>{if(o.isMesh&&['trees','tree_trunks'].includes(o.userData.layer)){o.userData.atlasReplaced=true;o.visible=false;}});
      this.buildMarks(data.roadMarks);await this.buildDome();this.invalidate();
    }catch(e){console.warn('Illustrative landscape unavailable',e);}
  }
  buildTrees(rows){
    // One multi-lobed canopy mesh, instanced in bounded spatial tiles for culling.
    const lobes=[[0,.62,0,.70,.75,.66],[-.38,.43,.10,.48,.48,.49],[.35,.48,.12,.50,.53,.48],[.02,.49,-.35,.52,.56,.46],[.08,.85,.03,.42,.44,.4]];
    const shapes=lobes.map(([x,y,z,a,b,c])=>{const g=new THREE.IcosahedronGeometry(1,1);g.scale(a,b,c);g.translate(x,y,z);return g;});
    let crown=mergeGeometries(shapes);shapes.forEach(g=>g.dispose());crown.computeVertexNormals();
    let trunk=new THREE.CylinderGeometry(.04,.06,.6,5);trunk.translate(0,.3,0);
    let leaf=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.94});
    let bark=new THREE.MeshStandardMaterial({color:'#7b6650',roughness:1});
    let greens=['#34811c','#82a92d','#20582a','#2b7724','#b0b739','#327d2b','#609c20','#40892b'];
    const far={crown,trunk,leaf,bark,greens};this.treeLods=[];
    const foliage=this.treeAsset?.getObjectByName('Atlas_foliage'),wood=this.treeAsset?.getObjectByName('Atlas_branches');
    if(foliage&&wood){
      crown=foliage.geometry;trunk=wood.geometry;leaf=foliage.material;bark=wood.material;
      leaf.transparent=false;leaf.alphaTest=.18;leaf.alphaToCoverage=true;leaf.side=THREE.DoubleSide;leaf.roughness=.86;
      leaf.color.set('#ffffff');leaf.envMapIntensity=.5;
      if(leaf.map)leaf.map.anisotropy=4;
      greens=['#bce49a','#e6edaa','#9ace94','#b0da8f','#f6e4a0','#afd6ae','#cbe698','#c0e6a4'];
    }
    const tiles=new Map();for(const row of rows){const k=`${Math.floor(row[0]/8)},${Math.floor(row[1]/8)}`;if(!tiles.has(k))tiles.set(k,[]);tiles.get(k).push(row);}
    const dummy=new THREE.Object3D(),col=new THREE.Color();
    for(const batch of tiles.values()){
      const leaves=new THREE.InstancedMesh(crown,leaf,batch.length),stems=new THREE.InstancedMesh(trunk,bark,batch.length);
      const distant=new THREE.InstancedMesh(far.crown,far.leaf,batch.length),distantStems=new THREE.InstancedMesh(far.trunk,far.bark,batch.length);
      batch.forEach(([x,y,r,h,t],i)=>{
        dummy.position.set(x,(this.city.userData.groundNormalized?.011:.028)+this.groundOffset(x,y),-y);dummy.rotation.set(0,(x+y)*5,0);dummy.scale.set(r*.78,h*.29,r*.78);dummy.updateMatrix();leaves.setMatrixAt(i,dummy.matrix);leaves.setColorAt(i,col.set(greens[t]));stems.setMatrixAt(i,dummy.matrix);
        distant.setMatrixAt(i,dummy.matrix);distant.setColorAt(i,col.set(far.greens[t]));distantStems.setMatrixAt(i,dummy.matrix);
      });
      for(const m of [leaves,stems,distant,distantStems]){m.castShadow=true;m.receiveShadow=true;m.userData.atlasLayer='parks';m.computeBoundingSphere();this.root.add(m);this.parts.push(m);}
      leaves.visible=stems.visible=false;this.treeLods.push({near:[leaves,stems],far:[distant,distantStems]});
    }
  }
  update(camera,stage){
    const near=stage.clientHeight*camera.zoom/(camera.top-camera.bottom)>(this.treesNear?150:180);
    if(this.treesNear===near)return false;this.treesNear=near;
    for(const pair of this.treeLods||[]){for(const m of pair.near)m.visible=near&&this.parksEnabled!==false;for(const m of pair.far)m.visible=!near&&this.parksEnabled!==false;}
    this.invalidate();return true;
  }
  preparePoster(){
    const near=this.treesNear;
    for(const pair of this.treeLods||[]){for(const m of pair.near)m.visible=false;for(const m of pair.far)m.visible=this.parksEnabled!==false;}
    return ()=>{for(const pair of this.treeLods||[]){for(const m of pair.near)m.visible=!!near&&this.parksEnabled!==false;for(const m of pair.far)m.visible=!near&&this.parksEnabled!==false;}};
  }
  buildMarks(rows){
    const geo=new THREE.PlaneGeometry(1,1);geo.rotateX(-Math.PI/2);
    const mat=new THREE.MeshBasicMaterial({color:'#f5e8bb',depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1});
    const mesh=new THREE.InstancedMesh(geo,mat,rows.length),dummy=new THREE.Object3D();
    rows.forEach(([x,y,angle,len],i)=>{dummy.position.set(x,(this.city.userData.groundNormalized?.0102:.068)+this.groundOffset(x,y),-y);dummy.rotation.y=angle;dummy.scale.set(len,1,.008);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);});
    mesh.userData.atlasLayer='roads';mesh.computeBoundingSphere();this.root.add(mesh);this.parts.push(mesh);
  }
  async buildDome(){
    const spec=await fetch('public/assets/cartographic/dome.json').then(r=>r.json());
    const geometry=new THREE.SphereGeometry(1,64,24,0,Math.PI*2,0,Math.PI/2);
    const material=new THREE.MeshStandardMaterial({color:'#9bb5ba',roughness:.35,metalness:.45});
    material.onBeforeCompile=s=>{s.vertexShader='varying vec3 domeP;\n'+s.vertexShader;s.vertexShader=s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\ndomeP=position;');s.fragmentShader='varying vec3 domeP;\n'+s.fragmentShader;s.fragmentShader=s.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat glass=1.-smoothstep(.10,.14,abs(domeP.x));diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.03,.12,.17),glass*.85);float seam=pow(abs(sin(atan(domeP.z,domeP.x)*64.)),32.);diffuseColor.rgb*=1.-seam*.12;');};
    const dome=new THREE.Mesh(geometry,material);dome.position.set(spec.x,this.city.userData.groundNormalized?.011:.075,-spec.y);dome.scale.set(spec.rx,spec.height*this.height,spec.rz);dome.castShadow=true;dome.receiveShadow=true;dome.userData.atlasLayer='buildings';this.root.add(dome);this.parts.push(dome);this.dome=dome;this.domeHeight=spec.height;
  }
  setHeight(h){this.height=h;if(this.dome)this.dome.scale.y=this.domeHeight*h;}
  setLayers(layers){this.parksEnabled=layers.parks;for(const mesh of this.parts)mesh.visible=layers[mesh.userData.atlasLayer];for(const pair of this.treeLods||[]){for(const m of pair.near)m.visible=!!this.treesNear&&layers.parks;for(const m of pair.far)m.visible=!this.treesNear&&layers.parks;}}
}
