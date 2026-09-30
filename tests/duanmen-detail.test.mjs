import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const m=read('public/assets/route-landmarks/manifest.json');
test('Duanmen LOD assets carry embedded texture, consistent bounds, and independent compressed meshes',()=>{
 const s=m.assets.find(s=>s.id==='duanmen');assert(s);assert.equal(s.license,'CC BY-SA 4.0');
 const levels=[];
 for(const level of ['preview','detail']){
  const u=new URL(s.lods[level],root),bytes=fs.readFileSync(new URL(u.pathname,'file://'));
  assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,12),u.searchParams.get('v'));
  const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
  assert(!gltf.cameras);assert(gltf.extensionsRequired.includes('KHR_draco_mesh_compression'));
  assert.equal(gltf.images.length,1);assert(gltf.images.every(i=>i.bufferView!==undefined));
  assert(gltf.nodes.some(n=>n.name.startsWith('Duanmen plaque')));
  const a=read(`output/duanmen-detail/${level}-audit.json`);assert.equal(a.meshes,gltf.meshes.length);
  assert(Math.abs(a.boundsLocalBlender[1][2]-.35)<.002);assert.equal(a.portals,5);assert.deepEqual(a.centerOpeningMetres,[5.52,8.82]);
  levels.push(a);
 }
 assert(levels[0].triangles<levels[1].triangles/3);assert.deepEqual(levels[0].boundsLocalBlender,levels[1].boundsLocalBlender);
});
test('Duanmen replaces all twelve source parts and exposes valid related / return navigation',()=>{
 const s=m.assets.find(s=>s.id==='duanmen');const f=read('data/duanmen-footprint.json');
 assert.equal(s.x,f.center[0]);assert.equal(s.y,f.center[1]);assert(Math.abs(s.rotation-f.angle*180/Math.PI)<1e-8);
 const records=read('data/urban/records.json').records.filter(r=>r.parentOsmId===s.anchorOsmId);assert.equal(records.length,12);
 const [x0,y0,x1,y1]=s.bounds;assert(records.every(r=>r.rings.flat().every(([x,y])=>x>x0&&x<x1&&y>y0&&y<y1)));
 assert.equal(s.parentPlace,'forbidden');assert(s.additionalViews.portals);
 for(const e of m.assets)for(const link of e.relatedModels||[])assert(m.assets.some(a=>a.id===link.id));
 assert(m.assets.find(e=>e.id==='tiananmen').relatedModels.some(e=>e.id==='duanmen'));
});
