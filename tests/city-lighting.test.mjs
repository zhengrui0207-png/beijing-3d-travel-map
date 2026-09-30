import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import * as THREE from '../public/vendor/build/three.module.js';
const source=readFileSync(new URL('../public/city-lighting.js',import.meta.url),'utf8').replace(/^import .*;$/mg,'').replaceAll('export function','function');
const {fitCityShadow,cityOcclusion}=new Function('THREE',source+';return {fitCityShadow,cityOcclusion};')(THREE);
const direction=new THREE.Vector3(-65,80,40);
function cameraAt(offset,zoom,aspect=16/9,target=new THREE.Vector3()) {const c=new THREE.OrthographicCamera(-63*aspect,63*aspect,63,-63,.1,1000);c.position.copy(target).add(new THREE.Vector3(...offset));c.lookAt(target);c.zoom=zoom;c.updateProjectionMatrix();c.updateMatrixWorld();return c;}
function lightFor(target,fit){const c=new THREE.OrthographicCamera(fit.left,fit.right,fit.top,fit.bottom,fit.near,fit.far);c.position.copy(fit.lightPosition||target.clone().add(direction));c.lookAt(target);c.updateProjectionMatrix();c.updateMatrixWorld();return c;}
test('sun covers oblique ground and rooftop receivers at city, route and landmark scales',()=>{
 for(const offset of [[6,80,185],[120,90,110],[0,220,.01],[.22,.52,.82]])for(const zoom of [1,5,12,90,250])for(const aspect of [16/9,9/16]){
  const target=new THREE.Vector3(-20,.035,-5),camera=cameraAt(offset,zoom,aspect,target),fit=fitCityShadow(camera,target,direction),light=lightFor(target,fit);
  assert.ok(fit.near>0&&fit.far>fit.near);assert.ok(Object.values(fit).filter(v=>typeof v==='number').every(Number.isFinite));
  for(const p of fit.receivers){const q=p.clone().project(light);assert.ok(Math.abs(q.x)<=1.00001&&Math.abs(q.y)<=1.00001&&Math.abs(q.z)<=1.00001,JSON.stringify({offset,zoom,aspect,q}));}
 }
});
test('former zoom-only square misses distant streets while fitted frustum includes them',()=>{
 const target=new THREE.Vector3(),camera=cameraAt([6,80,185],12),fit=fitCityShadow(camera,target,direction),span=130/camera.zoom,old=lightFor(target,{left:-span,right:span,bottom:-span,top:span,near:1,far:260});
 assert.ok(fit.receivers.some(p=>{const q=p.clone().project(old);return Math.abs(q.x)>1||Math.abs(q.y)>1;}));
 assert.ok(fitCityShadow(cameraAt([6,80,185],250),target,direction).far-fitCityShadow(cameraAt([6,80,185],250),target,direction).near<10);
});
test('city contact shading persists at macro scale and blends continuously into near detail',()=>{
 let previous=cityOcclusion(0);
 for(let p=0;p<=1000;p++) {const s=cityOcclusion(p);assert.ok(s.intensity>=.46&&s.intensity<=.7);assert.ok(s.radius>=.1&&s.radius<=.24);assert.ok(Math.abs(s.intensity-previous.intensity)<.004);previous=s;}
 assert.deepEqual(cityOcclusion(0),cityOcclusion(20));assert.deepEqual(cityOcclusion(130),cityOcclusion(1000));
});
