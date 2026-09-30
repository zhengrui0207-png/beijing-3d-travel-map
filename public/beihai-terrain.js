import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
// Local, coarse SRTM interpretation. Every raised object uses the same height field.
export class BeihaiTerrain {
  constructor({city}){this.city=city;this.lifted=[];this.height=1;}
  async init(){
    try{
      const r=await fetch('public/assets/beihai-terrain/heightfield.json',{cache:'no-store'});if(!r.ok)throw Error(r.status);const field=await r.json();
      const {scene:terrain}=await new GLTFLoader().loadAsync(`public/assets/beihai-terrain/terrain.glb?v=${field.meshRevision||'1'}`);
      this.field=field;this.maxOffset=Math.max(...field.grid.flat());this.liftBuildings(this.city);
      terrain.traverse(o=>{if(o.isMesh){o.castShadow=(o.userData.layer||'').startsWith('architecture_beihai_steps');o.receiveShadow=true;}});this.city.add(terrain);this.root=terrain;
      if(new URLSearchParams(location.search).has('qa'))console.info('Beihai terrain ready',JSON.stringify({terraces:field.terraces?.length||0,stairs:field.stairs?.length||0,steps:field.stairs?.reduce((n,s)=>n+s.count,0)||0,pads:field.pads.length,raisedMeshes:this.lifted.length,towerGround:field.towerGroundHeight}));
    }catch(e){console.warn('Island terrain unavailable; flat map retained',e);}
  }
  contains(x,y){
    if(!this.field)return false;const [a,b,c,d]=this.field.bounds;if(x<a||x>c||y<b||y>d)return false;
    const ring=this.field.ring;let inside=false;
    for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [xi,yi]=ring[i],[xj,yj]=ring[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)inside=!inside;}return inside;
  }
  offset(x,y,building=false){
    if(!this.contains(x,y))return 0;
    if(building){for(const pad of this.field.pads){const [a,b,c,d]=pad.bounds;if(x>=a&&x<=c&&y>=b&&y<=d)return pad.height;}}
    // The two terraces are level surfaces; use their boundary before coarse-grid interpolation.
    for(const terrace of this.field.terraces||[]){
      let inside=false;const ring=terrace.ring;
      for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [ax,ay]=ring[i],[bx,by]=ring[j];if((ay>y)!==(by>y)&&x<(bx-ax)*(y-ay)/(by-ay)+ax)inside=!inside;}
      if(inside)return terrace.heightOffset;
    }
    const {origin,step,grid}=this.field;const fx=(x-origin[0])/step,fy=(y-origin[1])/step,ix=Math.floor(fx),iy=Math.floor(fy),u=fx-ix,v=fy-iy;
    return (grid[iy]?.[ix]||0)*(1-u)*(1-v)+(grid[iy]?.[ix+1]||0)*u*(1-v)+(grid[iy+1]?.[ix]||0)*(1-u)*v+(grid[iy+1]?.[ix+1]||0)*u*v;
  }
  liftBuildings(root){
    if(!this.field)return;
    const [a,b,c,d]=this.field.bounds;
    root.traverse(o=>{
      if(!o.isMesh||o.userData.islandLift||!(o.userData.layer?.startsWith('buildings')||o.userData.layer==='landmark_beihai'))return;
      const g=o.geometry;g.computeBoundingBox();const bb=g.boundingBox;
      if(bb.max.x<a||bb.min.x>c||-bb.min.z<b||-bb.max.z>d)return;
      const pos=g.attributes.position,indices=[],original=[],lifts=[];
      for(let i=0;i<pos.count;i++){const lift=o.userData.layer==='landmark_beihai'?this.field.towerGroundHeight-.011:this.offset(pos.getX(i),-pos.getZ(i),true);if(lift>0){indices.push(i);original.push(pos.getY(i));lifts.push(lift);pos.setY(i,pos.getY(i)+lift/this.height);}}
      if(!indices.length)return;o.userData.islandLift=true;
      this.lifted.push({object:o,indices,original,lifts});pos.needsUpdate=true;g.computeBoundingBox();g.computeBoundingSphere();
    });
  }
  setHeight(h){
    if(this.height===h)return;this.height=h;
    this.lifted=this.lifted.filter(({object})=>object.parent);
    for(const {object,indices,original,lifts} of this.lifted){const g=object.geometry,p=g.attributes.position;for(let k=0;k<indices.length;k++)p.setY(indices[k],original[k]+lifts[k]/h);p.needsUpdate=true;g.computeBoundingBox();g.computeBoundingSphere();}
  }
  release(root){const objects=new Set();root.traverse(o=>objects.add(o));this.lifted=this.lifted.filter(e=>!objects.has(e.object));}
}
