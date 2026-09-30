import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {LandmarkAsset} from './landmark-asset.js?v=20260914-taihe2';

// The orthographic camera zooms without moving. LOD therefore uses projected
// pixels per metre and visible bounds, not distance to the camera.
export class PalaceLOD {
  constructor({scene,camera,renderer,stage,city,invalidate,status}) {
    Object.assign(this,{scene,camera,renderer,stage,city,invalidate,status});
    this.loader=new GLTFLoader();this.base='public/assets/palace/';
    this.draco=new DRACOLoader().setDecoderPath('public/vendor/examples/jsm/libs/draco/gltf/').setWorkerLimit(2);
    this.loader.setDRACOLoader(this.draco);
    this.zones=[];this.micro=[];this.external=[];this.coverage={value:0};this.enabled=true;this.height=1;this.layers={buildings:true,parks:true,water:true,roads:true};
    this.lastTime=0;this.loading=0;this.queue=[];this.events=[];this.error='';
    this.maxBytes=192*1024*1024;this.mediumPromise=null;this.textures=null;
    this.root=new THREE.Group();this.root.name='Forbidden City • streamed details';scene.add(this.root);
  }
  async init(){
    try {
      const r=await fetch(this.base+'manifest.json',{cache:'no-store'});if(!r.ok)throw Error('manifest');
      this.manifest=await r.json();this.zones=this.manifest.zones.map(z=>({...z,mediumScene:null,highScene:null,blend:{value:0},lastSeen:0,requested:false,failedAt:0,bytes:0}));
      this.micro=(this.manifest.microTiles||[]).map(z=>({...z,high:z.url,micro:true,highScene:null,blend:{value:0},lastSeen:0,requested:false,failedAt:0,bytes:0}));
      this.external=(this.manifest.externalAssets||[]).map(spec=>new LandmarkAsset(this,spec));
      this.installCityMask();this.invalidate();
    }catch(e){this.error='地标细节暂时不可用';this.status(this.error,'error');console.warn('Palace manifest',e);}
  }
  installCityMask(){
    const bounds={value:new THREE.Vector4(...this.manifest.replacementBounds)};
    this.city.traverse(mesh=>{
      if(!mesh.isMesh||/^base$/.test(mesh.userData.layer||''))return;
      const mask=material=>{
        material.onBeforeCompile=s=>{
          s.uniforms.palaceBounds=bounds;s.uniforms.palaceCoverage=this.coverage;
          s.vertexShader='varying vec3 palaceWorld;\n'+s.vertexShader;
          s.vertexShader=s.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\npalaceWorld=(modelMatrix*vec4(transformed,1.0)).xyz;');
          s.fragmentShader='varying vec3 palaceWorld;uniform vec4 palaceBounds;uniform float palaceCoverage;\n'+s.fragmentShader;
          s.fragmentShader=s.fragmentShader.replace('#include <clipping_planes_fragment>',`#include <clipping_planes_fragment>
            vec2 p=vec2(palaceWorld.x,-palaceWorld.z);
            if(p.x>palaceBounds.x&&p.x<palaceBounds.z&&p.y>palaceBounds.y&&p.y<palaceBounds.w){
              float d=fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))));
              if(d<palaceCoverage)discard;
            }`);
        };
        material.customProgramCacheKey=()=> 'palace-city-mask-v1';material.needsUpdate=true;
      };
      mesh.material=mesh.material.clone();mask(mesh.material);
      mesh.customDepthMaterial=new THREE.MeshDepthMaterial({depthPacking:THREE.RGBADepthPacking});mask(mesh.customDepthMaterial);
    });
  }
  async loadTextures(){
    if(this.textures)return this.textures;
    const loader=new THREE.TextureLoader();
    this.textures=Promise.all(['courtyard-stone.png','glazed-ochre.png','foliage.png','marble.png'].map(file=>loader.loadAsync(this.base+file).then(t=>{
      t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=Math.min(8,this.renderer.capabilities.getMaxAnisotropy());return t;
    }))).then(([stone,roof,foliage,marble])=>{stone.repeat.set(.20,.20);roof.repeat.set(1,1);foliage.wrapS=foliage.wrapT=THREE.ClampToEdgeWrapping;marble.repeat.set(.25,.25);return {stone,roof,foliage,marble};}).catch(e=>{this.textures=null;throw e;});
    return this.textures;
  }
  prepare(root,z,level,textures){
    root.name=`palace/${z.id}/${level}`;let bytes=0;
    root.traverse(o=>{if(!o.isMesh)return;
      const external=this.external.find(a=>a.spec.id===o.userData.externalFallback);
      if(external){o.material=o.material.clone();external.fallbackNodes.add(o);}
      for(const a of Object.values(o.geometry.attributes))bytes+=a.array.byteLength;
      if(o.geometry.index)bytes+=o.geometry.index.array.byteLength;
      o.castShadow=!z.micro&&!/Courtyard|Garden|Water|Terrace_Paving/.test(o.material.name);o.receiveShadow=true;
      const m=o.material;o.userData.detailLayer=/Foliage|Garden_Green|Tree_Bark/.test(m.name)?'parks':/Water_Jade/.test(m.name)?'water':'always';o.visible=this.layers[o.userData.detailLayer]!==false;m.roughness=Math.max(.5,m.roughness);m.envMapIntensity=.9;
      if(/Roof_Glazed|Roof_Ridge/.test(m.name)){m.map=textures.roof;m.color.set('#ffffff');m.roughness=.57;m.bumpMap=textures.roof;m.bumpScale=.00008;}
      if(/^Courtyard_/.test(m.name)){m.map=textures.stone;m.color.set(({Courtyard_Stone:'#ebeee8',Courtyard_Axis:'#f0ede3',Courtyard_Cool:'#d8e2df',Courtyard_Warm:'#e3dccb'})[m.name]||'#ebeee8');m.bumpMap=textures.stone;m.bumpScale=.00025;}
      if(m.name==='Terrace_Paving'){m.map=textures.marble;m.color.set('#c2c4bd');m.roughness=.88;m.bumpMap=textures.marble;m.bumpScale=.00016;}
      if(m.name==='Foliage_Leaves'){m.map=textures.foliage;m.color.setRGB(1.2,1.2,1.1);m.side=THREE.DoubleSide;m.alphaTest=.45;m.roughness=.9;}
      if(m.name==='Limestone'){m.map=textures.marble;m.bumpMap=textures.marble;m.bumpScale=.00018;m.color.set('#eceee9');m.roughness=.91;}
      if(m.name==='Vermilion'){m.color.set('#b84128');m.roughness=.83;}
      if(m.name==='Water_Jade'){m.color.set('#168fa8');m.roughness=.22;m.metalness=.15;m.envMapIntensity=1.5;}
      if(m.name==='Garden_Green')m.color.set('#719341');
      if(m.name==='Painted_Timber')m.color.set('#325f51');
      if(m.name==='Painted_Azure')m.color.set('#376b78');
      const fade=material=>{
        material.onBeforeCompile=s=>{
          s.uniforms.palaceCoverage=this.coverage;s.uniforms.lodBlend=z.blend;
          if(/Roof_Glazed|Roof_Ridge/.test(m.name))s.fragmentShader=s.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\ndiffuseColor.rgb=mix(vec3(dot(diffuseColor.rgb,vec3(.2126,.7152,.0722))),diffuseColor.rgb,.82);');
          // Filtered tile relief remains readable before geometry is large enough
          // to sample. UV metres and roof slope choose the correct roll direction.
          if(!z.micro&&m.name==='Roof_Glazed_Ochre'&&!material.isMeshDepthMaterial){
            s.vertexShader='varying vec3 roofWorld;\n'+s.vertexShader;
            s.vertexShader=s.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nroofWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
            s.fragmentShader='varying vec3 roofWorld;\n'+s.fragmentShader;
            s.fragmentShader=s.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
              vec2 tx=dFdx(vMapUv),ty=dFdy(vMapUv);
              vec3 px=dFdx(roofWorld),py=dFdy(roofWorld);
              float uvDet=tx.x*ty.y-tx.y*ty.x;
              if(abs(uvDet)>.00000001){
                vec3 pu=(px*ty.y-py*tx.y)/uvDet,pv=(py*tx.x-px*ty.x)/uvDet;
                bool acrossU=abs(pu.y)<abs(pv.y);
                float tile=(acrossU?vMapUv.x:vMapUv.y)*2.;
                float visibility=1.-smoothstep(.24,.52,fwidth(tile));
                vec3 across=normalize(mat3(viewMatrix)*(acrossU?pu:pv));
                normal=normalize(normal+across*cos(tile*6.2831853)*.30*visibility);
                roughnessFactor=min(1.,roughnessFactor+.06*(1.-visibility));
              }`);
          }
          s.fragmentShader='uniform float palaceCoverage;uniform float lodBlend;\n'+s.fragmentShader;
          s.fragmentShader=s.fragmentShader.replace('#include <clipping_planes_fragment>',`#include <clipping_planes_fragment>
            float d=fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))));
            if(d>=palaceCoverage)discard;
            ${level==='high'?'if(d>=lodBlend)discard;':'if(d<lodBlend)discard;'}`);
          external?.maskFallback(s);
        };material.customProgramCacheKey=()=>`palace-fade-${level}-${m.name}-${external?.spec.id||'ordinary'}-v3`;material.needsUpdate=true;
      };
      fade(m);o.customDepthMaterial=new THREE.MeshDepthMaterial({depthPacking:THREE.RGBADepthPacking,map:m.map,alphaTest:m.alphaTest,side:m.side});fade(o.customDepthMaterial);
    });
    this.onPrepared?.(root);
    root.visible=false;this.root.add(root);return bytes;
  }
  async readGLB(url,signal){
    const r=await fetch(this.base+url,{signal});if(!r.ok)throw Error(`${url}: ${r.status}`);
    const buffer=await r.arrayBuffer();if(signal?.aborted)throw new DOMException('Aborted','AbortError');
    return (await this.loader.parseAsync(buffer,this.base)).scene;
  }
  ensureMedium(){
    if(this.mediumPromise)return;
    this.status('正在展开故宫建筑…','loading');
    this.mediumPromise=(async()=>{
      const textures=await this.loadTextures();
      // Bound decoding work: sequential chunks yield between each parse.
      for(const z of this.zones){
        const root=await this.readGLB(z.medium);z.mediumScene=root;this.prepare(root,z,'medium',textures);
        await new Promise(requestAnimationFrame);
      }
      this.error='';this.mediumReady=true;this.events.push({type:'medium-ready',time:performance.now()});this.invalidate();
    })().catch(e=>{
      console.warn('Palace medium',e);this.error='细节加载失败，城市地图仍可使用';this.status(this.error,'error');
      for(const z of this.zones){if(z.mediumScene)this.dispose(z.mediumScene);z.mediumScene=null;}
      this.mediumPromise=null;this.retryAfter=performance.now()+15000;
    });
  }
  async preparePoster(){
    if(!this.enabled||!this.manifest)return ()=>{};
    this.ensureMedium();await this.mediumPromise;
    if(!this.mediumReady)return ()=>{};
    const visibility=this.root.children.map(o=>[o,o.visible]);
    const uniforms=[this.coverage,...this.zones.map(z=>z.blend),...this.micro.map(z=>z.blend),...this.external.map(a=>a.coverage)].map(u=>[u,u.value]);
    this.coverage.value=1;
    for(const o of this.root.children)o.visible=false;
    for(const z of this.zones){z.blend.value=0;if(z.mediumScene)z.mediumScene.visible=true;}
    for(const a of this.external)a.coverage.value=0;
    return ()=>{for(const [o,v]of visibility)o.visible=v;for(const [u,v]of uniforms)u.value=v;this.invalidate();};
  }
  async requestHigh(z){
    z.requested=true;z.abort=new AbortController();this.loading++;
    try {
      const textures=await this.loadTextures(),root=await this.readGLB(z.high,z.abort.signal);
      if(z.abort.signal.aborted){this.dispose(root);return;}
      z.bytes=this.prepare(root,z,'high',textures);z.highScene=root;
      this.events.push({type:'high-ready',zone:z.id,time:performance.now(),bytes:z.bytes});
    }catch(e){if(e.name!=='AbortError'){z.failedAt=performance.now();console.warn('Palace detail',z.id,e);}}
    finally{z.requested=false;z.abort=null;this.loading--;this.invalidate();}
  }
  visible(bounds){
    let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
    for(const x of [bounds[0],bounds[2]])for(const n of [bounds[1],bounds[3]])for(const y of [0,.5*this.height]){
      const p=new THREE.Vector3(x,y,-n).project(this.camera);minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y);
    }
    return maxX> -1.3&&minX<1.3&&maxY> -1.3&&minY<1.3;
  }
  update(t){
    if(!this.manifest)return false;
    const dt=Math.min((t-this.lastTime)/1000,.07);this.lastTime=t;
    const ppu=this.stage.clientHeight*this.camera.zoom/(this.camera.top-this.camera.bottom);
    const onScreen=this.visible(this.manifest.replacementBounds);
    this.near=this.enabled&&onScreen&&ppu>(this.near?11:15);
    if(this.near&&!this.mediumReady&&t>(this.retryAfter||0))this.ensureMedium();
    const target=this.near&&this.mediumReady?1:0,old=this.coverage.value;
    this.coverage.value=THREE.MathUtils.clamp(old+Math.sign(target-old)*dt*2.5,0,1);
    if(Math.abs(target-old)<dt*2.5)this.coverage.value=target;
    let changing=old!==this.coverage.value;
    const queue=[];
    for(const z of this.zones){
      const visible=this.visible(z.bounds),wanted=this.near&&visible&&ppu>(z.wantHigh?56:73);
      z.wantHigh=wanted;
      if(wanted){z.lastSeen=t;if(!z.highScene&&!z.requested&&(!z.failedAt||t-z.failedAt>15000))queue.push(z);}
      else if(z.requested)z.abort?.abort();
      const dest=wanted&&z.highScene?1:0,prev=z.blend.value;
      z.blend.value=THREE.MathUtils.clamp(prev+Math.sign(dest-prev)*dt*3.4,0,1);
      if(Math.abs(dest-prev)<dt*3.4)z.blend.value=dest;
      changing||=z.blend.value!==prev;
      if(z.mediumScene)z.mediumScene.visible=this.coverage.value>0&&z.blend.value<1;
      if(z.highScene)z.highScene.visible=this.coverage.value>0&&z.blend.value>0;
    }
    const direction=this.camera.getWorldDirection(new THREE.Vector3()),focus=this.camera.position.clone().addScaledVector(direction,-this.camera.position.y/direction.y);
    queue.sort((a,b)=>{const c=z=>Math.hypot((z.bounds[0]+z.bounds[2])/2-focus.x,(z.bounds[1]+z.bounds[3])/2+focus.z);return c(a)-c(b);});
    for(const z of queue){if(this.loading>=2)break;this.requestHigh(z);}
    let bytes=this.zones.reduce((n,z)=>n+z.bytes,0);
    for(const z of [...this.zones].sort((a,b)=>a.lastSeen-b.lastSeen)){
      if(z.highScene&&!z.wantHigh&&z.blend.value===0&&(t-z.lastSeen>20000||bytes>this.maxBytes)){
        this.dispose(z.highScene);z.highScene=null;bytes-=z.bytes;z.bytes=0;this.events.push({type:'evicted',zone:z.id,time:t});
      }
    }
    for(const asset of this.external)changing=asset.update(t,dt,ppu)||changing;
    changing=this.updateMicro(t,dt,ppu)||changing;
    if(this.near&&this.loading)this.status('正在加载屋面细节…','loading');
    else if(this.near&&this.zones.some(z=>z.wantHigh&&z.failedAt&&!z.highScene))this.status('部分细节暂未载入，稍后自动重试','ready');
    else if(this.near&&this.external.some(a=>a.wanted&&a.state.levels.some(l=>l.failed)))this.status('精细屋顶暂未载入，已保留原屋顶','ready');
    else if(this.near&&this.external.some(a=>a.coverage.value===1))this.status('太和殿 · TRNKL 精细屋顶','ready');
    else if(this.near&&this.mediumReady)this.status('故宫 · 建筑细节','ready');
    else if(!this.error)this.status('','hidden');
    this.events=this.events.slice(-50);return changing;
  }
  updateMicro(t,dt,ppu){
    let changing=false;
    const eligible=this.near&&this.mediumReady&&ppu>300;
    const target=this.camera.getWorldDirection(new THREE.Vector3());
    // Intersect the camera centre with the ground to prioritize cells independently
    // of the orthographic camera's arbitrary distance behind the scene.
    const centre=this.camera.position.clone().addScaledVector(target,-this.camera.position.y/target.y);
    const cells=eligible?this.micro.filter(z=>this.visible(z.bounds)).sort((a,b)=>{
      const d=z=>Math.hypot((z.bounds[0]+z.bounds[2])/2-centre.x,(z.bounds[1]+z.bounds[3])/2+centre.z);return d(a)-d(b);
    }).slice(0,4):[];
    for(const z of this.micro){
      z.wantHigh=cells.includes(z);
      if(z.wantHigh)z.lastSeen=t;
      else if(z.requested)z.abort?.abort();
      const dest=z.wantHigh&&z.highScene?1:0,prev=z.blend.value;
      z.blend.value=THREE.MathUtils.clamp(prev+Math.sign(dest-prev)*dt*3.4,0,1);
      if(Math.abs(dest-prev)<dt*3.4)z.blend.value=dest;
      if(z.highScene)z.highScene.visible=this.coverage.value>0&&z.blend.value>0;
      changing||=z.blend.value!==prev;
    }
    for(const z of cells){if(this.loading>=2)break;if(!z.highScene&&!z.requested&&(!z.failedAt||t-z.failedAt>15000))this.requestHigh(z);}
    let bytes=this.micro.reduce((n,z)=>n+z.bytes,0);
    for(const z of this.micro){if(z.highScene&&!z.wantHigh&&z.blend.value===0&&(t-z.lastSeen>5000||bytes>48*1024*1024)){
      this.dispose(z.highScene);z.highScene=null;bytes-=z.bytes;z.bytes=0;
    }}
    return changing;
  }
  dispose(root){root.removeFromParent();root.traverse(o=>{if(!o.isMesh)return;for(const a of this.external)a.fallbackNodes.delete(o);o.geometry.dispose();o.material.dispose();o.customDepthMaterial?.dispose();});}
  setHeight(h){this.height=h;this.root.scale.y=h;this.invalidate();}
  setLayers(layers){this.layers={...layers};this.root.traverse(o=>{if(o.isMesh)o.visible=this.layers[o.userData.detailLayer]!==false;});this.invalidate();}
  setEnabled(on){this.enabled=on;this.invalidate();}
  get state(){return {external:this.external.map(a=>a.state),near:this.near,coverage:this.coverage.value,mediumReady:!!this.mediumReady,loading:this.loading,error:this.error,cachedBytes:this.zones.reduce((n,z)=>n+z.bytes,0),microBytes:this.micro.reduce((n,z)=>n+z.bytes,0),micro:this.micro.filter(z=>z.highScene||z.requested).map(z=>({id:z.id,blend:z.blend.value,wanted:z.wantHigh,requested:z.requested})),zones:this.zones.map(z=>({id:z.id,high:!!z.highScene,blend:z.blend.value,wanted:z.wantHigh,requested:z.requested})),events:this.events};}
}
