import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import * as THREE from '../public/vendor/build/three.module.js';
const manifest=JSON.parse(await readFile(new URL('../public/assets/urban-fill/detail/manifest.json',import.meta.url)));
const fill=JSON.parse(await readFile(new URL('../public/assets/urban-fill/manifest.json',import.meta.url)));
const exclusions=JSON.parse(await readFile(new URL('../data/urban/exclusions-circular-mound.json',import.meta.url)));
const source=(await readFile(new URL('../public/urban-architecture.js',import.meta.url),'utf8')).replace(/^import .*;$/mg,'').replace('export class','class');
const Urban=new Function('THREE','location',source+';return UrbanArchitecture;')(THREE,{search:''});
test('all infill detail tiles exist, revisions match bytes, and exported coordinates stay inside their geographic bounds',async()=>{
 let bytes=0,triangles=0;
 for(const t of manifest.tiles){
  const b=await readFile(new URL('../'+t.url,import.meta.url));assert.equal(b.readUInt32LE(0),0x46546c67);assert.equal(b.length,t.bytes);assert.equal(createHash('sha256').update(b).digest('hex').slice(0,12),t.revision);
  const doc=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));assert.ok(doc.extensionsRequired.includes('KHR_draco_mesh_compression'));assert.ok(doc.nodes.filter(n=>n.mesh!==undefined).every(n=>n.extras.inferredRoofDetail&&n.extras.groundHeight===.011));
  for(const m of doc.meshes)for(const p of m.primitives){const a=doc.accessors[p.attributes.POSITION];assert.ok(a.min[0]>=t.bounds[0]-.0001&&a.max[0]<=t.bounds[2]+.0001);assert.ok(-a.max[2]>=t.bounds[1]-.0001&&-a.min[2]<=t.bounds[3]+.0001);assert.ok(a.min[1]>=.010&&a.max[1]<=t.height+.0111);}
  bytes+=b.length;triangles+=t.triangles;
 }
 assert.equal(bytes,manifest.bytes);assert.equal(triangles,manifest.triangles);assert.equal(manifest.tiles.reduce((a,t)=>a+t.buildings,0),fill.stats.accepted);assert.equal(fill.stats.accepted+exclusions.records.length,76142);assert.equal(exclusions.records.length,4);
});
test('near roof details use their own threshold and hysteresis while city shells remain untouched',()=>{
 const camera=new THREE.OrthographicCamera(-2,2,2,-2,.1,100);camera.position.set(0,10,0);camera.up.set(0,0,-1);camera.lookAt(0,0,0);camera.updateMatrixWorld();
 const u=Object.assign(Object.create(Urban.prototype),{camera,stage:{clientHeight:400},enabled:true,height:1,lastUpdate:-Infinity,frustum:new THREE.Frustum(),matrix:new THREE.Matrix4(),loading:0,tiles:[]});
 const tile={box:new THREE.Box3(new THREE.Vector3(-1,0,-1),new THREE.Vector3(1,.1,1)),height:.1,minPpu:300,root:{visible:false},lastSeen:0};u.tiles=[tile];let released=false;u.release=()=>{released=true;tile.root=null;};
 camera.zoom=2;camera.updateProjectionMatrix();u.update(0);assert.equal(tile.root.visible,false);
 camera.zoom=3.1;camera.updateProjectionMatrix();u.update(200);assert.equal(tile.root.visible,true);
 camera.zoom=2.8;camera.updateProjectionMatrix();u.update(400);assert.equal(tile.root.visible,true);
 camera.zoom=2.5;camera.updateProjectionMatrix();u.update(600);assert.equal(tile.root.visible,false);
 u.update(21000);assert.equal(released,true);
 assert.match(u.assetURL('detail.glb','abc123'),/v=abc123$/);
});
