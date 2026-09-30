import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const manifest=read('public/assets/route-landmarks/manifest.json');
test('Tiananmen detail uses versioned embedded assets, correct model height and usable view identifiers',()=>{
 const s=manifest.assets.find(s=>s.id==='tiananmen');assert(s);assert(!manifest.retainedExisting.includes('tiananmen'));
 assert.equal(s.height,.347);assert.equal(s.license,'CC BY-SA 3.0');assert(!Array.isArray(s.additionalViews));assert(s.additionalViews.portals);
 const counts=[];
 for(const level of ['preview','detail']){
  const url=new URL(s.lods[level],root),bytes=fs.readFileSync(new URL(url.pathname,'file://'));
  assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,12),url.searchParams.get('v'));
  const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
  assert.equal(gltf.meshes.length,21);assert(gltf.images.every(i=>i.bufferView!==undefined));assert.equal(gltf.images.length,2);
  assert(!gltf.cameras);assert(gltf.extensionsRequired.includes('KHR_draco_mesh_compression'));
  counts.push(gltf.meshes.flatMap(m=>m.primitives).reduce((sum,p)=>sum+gltf.accessors[p.indices].count/3,0));
 }
 assert(counts[0]<counts[1]/2);
});
test('boundary walls are exported as solid materials instead of generic window facades',()=>{
 const path='public/assets/urban/city-shell.glb',bytes=fs.readFileSync(new URL(path,root));
 const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
 const walls=gltf.nodes.filter(n=>n.name?.includes('solid_'));assert(walls.length>0);
 assert(walls.every(n=>n.extras.layer==='buildings_urban_heritage'));
 const m=read('public/assets/urban/manifest.json');assert.equal(m.boundaryWallMaterialCorrection.count,16);assert.equal(m.tiles.length,144);
});
