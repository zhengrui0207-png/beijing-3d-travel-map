import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';

// Footprints and tagged roof shapes from OSM; generic trim is illustrative.
export class UrbanArchitecture {
  constructor({scene,city,camera,stage,invalidate}) {
    Object.assign(this,{scene,city,camera,stage,invalidate});
    this.draco=new DRACOLoader().setDecoderPath('public/vendor/examples/jsm/libs/draco/gltf/').setWorkerLimit(1);
    this.loader=new GLTFLoader().setDRACOLoader(this.draco);this.root=new THREE.Group();scene.add(this.root);
    this.root.name='Urban district detail';this.enabled=true;this.height=1;this.loading=0;this.revision=0;this.tiles=[];
    this.frustum=new THREE.Frustum();this.matrix=new THREE.Matrix4();this.lastUpdate=-Infinity;
  }
  async init(){
    try {
      const r=await fetch('public/assets/urban/manifest.json',{cache:'no-store'});if(!r.ok)throw Error(r.status);
      this.manifest=await r.json();const {scene:shell}=await this.loader.loadAsync(this.assetURL(this.manifest.shell));
      // Replace only the ordinary-building meshes, after the new asset succeeds.
      const old=[];this.city.traverse(o=>{if(['buildings_low','buildings_tall'].includes(o.userData.layer))old.push(o);});
      for(const o of old){o.removeFromParent();o.geometry.dispose();}
      shell.traverse(o=>{if(o.isMesh){o.material=o.material.clone();o.castShadow=true;o.receiveShadow=true;}});
      this.city.add(shell);this.shell=shell;
      await this.loadInfill();
      this.tiles=[...this.manifest.tiles,...(this.infillDetailManifest?.tiles||[])].map(s=>({...s,root:null,pending:false,lastSeen:0,errorAt:-Infinity,box:new THREE.Box3(new THREE.Vector3(s.bounds[0],0,-s.bounds[3]),new THREE.Vector3(s.bounds[2],s.height,-s.bounds[1]))}));
      this.normalizeGround();if(new URLSearchParams(location.search).has('qa'))console.info('Urban architecture ready',JSON.stringify({buildings:this.manifest.stats.buildings,infill:this.fillManifest?.stats.accepted||0,infillMeshes:this.fillManifest?.meshes||0,shellMeshes:shell.children.length,tiles:this.tiles.length,infillDetailTiles:this.infillDetailManifest?.tiles.length||0}));this.invalidate();
    }catch(e){console.warn('Urban architectural layer unavailable; original city retained',e);}
  }
  async loadInfill(){
    try{
      const response=await fetch('public/assets/urban-fill/manifest.json',{cache:'no-store'});if(!response.ok)throw Error(response.status);
      const manifest=await response.json();const {scene:fill}=await this.loader.loadAsync(`${manifest.url}?v=${encodeURIComponent(manifest.revision)}`);
      fill.traverse(o=>{if(o.isMesh){o.material=o.material.clone();o.castShadow=true;o.receiveShadow=true;}});
      this.city.add(fill);this.fill=fill;this.fillManifest=manifest;
      try{
        const details=await fetch('public/assets/urban-fill/detail/manifest.json',{cache:'no-store'});
        if(!details.ok)throw Error(details.status);
        this.infillDetailManifest=await details.json();
      }catch(error){console.warn('Infill roof detail unavailable; footprint shells retained',error);}
    }catch(error){console.warn('Additional building footprints unavailable; OSM buildings retained',error);}
  }
  assetURL(path,revision){return `${path}?v=${encodeURIComponent(revision||this.manifest.revision||'1')}`;}
  normalizeGround(){
    const surface={parks:.0085,water:.009,paths:.0105,roads_local:.0099,roads_major:.010};
    const landmarkFloors=new Map();
    this.city.traverse(o=>{if(o.isMesh&&o.userData.layer?.startsWith('landmark_')){
      o.geometry.computeBoundingBox();const l=o.userData.layer;
      landmarkFloors.set(l,Math.min(landmarkFloors.get(l)??Infinity,o.geometry.boundingBox.min.y));
    }});
    this.city.traverse(o=>{
      if(!o.isMesh)return;const layer=o.userData.layer;
      if(layer in surface){o.geometry.computeBoundingBox();o.geometry.translate(0,surface[layer]-o.geometry.boundingBox.max.y,0);}
      else if(layer==='palace_buildings'||layer==='palace_roofs'){o.geometry.translate(0,-.064,0);o.userData.groundHeight=.011;}
      else if(layer==='trees'||layer==='tree_trunks')o.geometry.translate(0,-.017,0);
      else if(landmarkFloors.has(layer)){o.geometry.translate(0,.011-landmarkFloors.get(layer),0);o.userData.groundHeight=.011;}
    });
    this.city.userData.groundNormalized=true;
  }
  setEnabled(on){this.enabled=on;this.root.visible=on;this.invalidate();}
  setHeight(h){this.height=h;this.root.scale.y=h;this.root.position.y=.011*(1-h);this.invalidate();}
  async request(tile){
    if(tile.pending||tile.root)return;tile.pending=true;this.loading++;
    try{
      const {scene:root}=await this.loader.loadAsync(this.assetURL(tile.url,tile.revision));
      root.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
      this.reconstruction?.replace(root);this.landform?.liftBuildings(root);root.visible=false;this.root.add(root);tile.root=root;this.revision++;
    }catch(e){tile.errorAt=performance.now();console.warn('District detail unavailable',tile.id,e);}
    finally{tile.pending=false;this.loading--;this.invalidate();}
  }
  release(tile){
    this.landform?.release(tile.root);
    const resources=new Set();tile.root.traverse(o=>{if(o.isMesh){resources.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material])resources.add(m);}});
    tile.root.removeFromParent();resources.forEach(r=>r.dispose());tile.root=null;this.revision++;
  }
  update(time){
    if(time-this.lastUpdate<180)return false;this.lastUpdate=time;
    this.frustum.setFromProjectionMatrix(this.matrix.multiplyMatrices(this.camera.projectionMatrix,this.camera.matrixWorldInverse));
    const ppu=this.stage.clientHeight*this.camera.zoom/(this.camera.top-this.camera.bottom);
    this.near=this.enabled&&ppu>65;let changed=false;
    for(const tile of this.tiles){
      tile.box.max.y=tile.height*this.height+.011+(this.landform?.maxOffset||0);
      const threshold=tile.minPpu||65;
      const visible=this.enabled&&ppu>threshold*(tile.root?.visible ? .86 : 1)&&this.frustum.intersectsBox(tile.box);
      if(visible){tile.lastSeen=time;if(!tile.root&&!tile.pending&&this.loading<2&&time-tile.errorAt>30000)this.request(tile);}
      if(tile.root){if(tile.root.visible!==visible){tile.root.visible=visible;changed=true;}if(!visible&&time-tile.lastSeen>20000){this.release(tile);changed=true;}}
    }
    if(changed&&new URLSearchParams(location.search).has('qa'))console.info('Urban district LOD',JSON.stringify({ppu:Math.round(ppu),resident:this.tiles.filter(t=>t.root).length,visible:this.tiles.filter(t=>t.root?.visible).length,infillVisible:this.tiles.filter(t=>t.root?.visible&&t.id.startsWith('infill-')).length,loading:this.loading}));
    return changed;
  }
}
