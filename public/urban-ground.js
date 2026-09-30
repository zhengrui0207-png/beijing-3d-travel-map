import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
// OSM polygon classes; roadside paving widths are an illustrative inference.
export class UrbanGround {
 constructor({city}){this.city=city;}
 async init(){
  let draco;
  try{
   const r=await fetch('public/assets/urban-ground/manifest.json',{cache:'no-store'});if(!r.ok)throw Error(r.status);const spec=await r.json();
   draco=new DRACOLoader().setDecoderPath('public/vendor/examples/jsm/libs/draco/gltf/').setWorkerLimit(1);
   const {scene:root}=await new GLTFLoader().setDRACOLoader(draco).loadAsync(`${spec.url}?v=${spec.revision}`);
   root.traverse(o=>{if(o.isMesh){o.receiveShadow=true;o.castShadow=false;if(o.material.map)o.material.map.anisotropy=4;}});
   this.city.add(root);this.root=root;this.spec=spec;
   if(new URLSearchParams(location.search).has('qa'))console.info('Urban ground ready',JSON.stringify({sources:spec.sources.length,meshes:spec.meshes,triangles:spec.triangles,bytes:spec.bytes}));
  }catch(e){console.warn('Mapped urban ground unavailable; existing base retained',e);}
  finally{draco?.dispose();}
 }
}
