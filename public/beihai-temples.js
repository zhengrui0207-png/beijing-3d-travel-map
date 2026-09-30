import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';

// Remove only triangles in the replacement footprints, including concave annex outlines. New assets must load first.
function inRing(x,y,ring){
 let inside=false;
 for(let i=0,j=ring.length-1;i<ring.length;j=i++){
  const [ax,ay]=ring[i],[bx,by]=ring[j];
  if((ay>y)!==(by>y)&&x<(bx-ax)*(y-ay)/(by-ay)+ax)inside=!inside;
 }return inside;
}
function nearRing(x,y,ring,tolerance){
 return ring.some(([ax,ay],i)=>{const [bx,by]=ring[(i+1)%ring.length],dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-ax-t*dx,y-ay-t*dy)<=tolerance;});
}
function withinFootprint(x,y,s){
 const [x0,y0,x1,y1]=s.bounds,tolerance=s.role==='annex'?.002:.012;
 if(x<x0-tolerance||x>x1+tolerance||y<y0-tolerance||y>y1+tolerance)return false;
 if(!s.rings?.length)return true;
 return(inRing(x,y,s.rings[0])||nearRing(x,y,s.rings[0],tolerance))&&!s.rings.slice(1).some(r=>inRing(x,y,r));
}
export function removeTempleShells(root,buildings){
 let removed=0;
 root.traverse(o=>{
  if(!o.isMesh||o.userData.templeReplacement||o.userData.templeFiltered||!o.userData.layer?.startsWith('buildings')||o.userData.layer==='buildings_urban_paving')return;
  const g=o.geometry;g.computeBoundingBox();const b=g.boundingBox;
  const masks=buildings.filter(({bounds:[x0,y0,x1,y1]})=>b.max.x>x0-.012&&b.min.x<x1+.012&&-b.min.z>y0-.012&&-b.max.z<y1+.012);
  if(!masks.length)return;
  const p=g.attributes.position,index=g.index,count=index?index.count:p.count,kept=[];
  for(let i=0;i<count;i+=3){
   const a=index?index.getX(i):i,c=index?index.getX(i+1):i+1,d=index?index.getX(i+2):i+2;
   const x=(p.getX(a)+p.getX(c)+p.getX(d))/3,y=-(p.getZ(a)+p.getZ(c)+p.getZ(d))/3;
   if(masks.some(s=>withinFootprint(x,y,s))){removed++;continue;}
   kept.push(a,c,d);
  }
  // GLTFLoader exposes individual primitives with one material; retain original attributes.
  if(kept.length<count){g.setIndex(kept);g.clearGroups();g.setDrawRange(0,kept.length);}
  o.userData.templeFiltered=true;
 });return removed;
}
export class BeihaiTemples{
 constructor({city}){this.city=city;}
 async init(){
  try{
   const r=await fetch('public/assets/beihai-temples/manifest.json',{cache:'no-store'});if(!r.ok)throw Error(r.status);const spec=await r.json();
   const draco=new DRACOLoader().setDecoderPath('public/vendor/examples/jsm/libs/draco/gltf/').setWorkerLimit(1);
   let model;try{({scene:model}=await new GLTFLoader().setDRACOLoader(draco).loadAsync(`${spec.url}?v=${spec.revision}`));}finally{draco.dispose();}
   model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
   this.spec=spec;const removed=removeTempleShells(this.city,spec.buildings);this.city.add(model);this.root=model;
   if(new URLSearchParams(location.search).has('qa'))console.info('Beihai temples ready',JSON.stringify({buildings:spec.buildings.length,triangles:spec.triangles,removedShellTriangles:removed,bytes:spec.bytes}));
  }catch(e){console.warn('Beihai temple reconstruction unavailable; original shells retained',e);}
 }
 replace(root){if(this.spec)return removeTempleShells(root,this.spec.buildings);return 0;}
}
