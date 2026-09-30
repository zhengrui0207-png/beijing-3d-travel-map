import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const plans=read('data/axis-courts.json'),m=read('public/assets/route-landmarks/manifest.json');
test('four courtyard LOD pairs preserve source anchors and embed only authored architectural meshes',()=>{
 let sourceParts=0,gates=0;
 for(const p of plans){
  const s=m.assets.find(s=>s.id===p.id);assert(s);assert.deepEqual([s.x,s.y],p.center);assert(Math.abs(s.rotation-p.angle*180/Math.PI)<1e-8);assert.equal(s.parentPlace,'forbidden');assert(s.detailView);
  const audits=[];
  for(const level of ['preview','detail']){
   const u=new URL(s.lods[level],root),bytes=fs.readFileSync(new URL(u.pathname,'file://'));assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,12),u.searchParams.get('v'));
   const g=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());assert(g.extensionsRequired.includes('KHR_draco_mesh_compression'));assert(!g.cameras);assert(!g.images);
   assert(g.nodes.some(n=>n.name.includes('grayRoof')));assert(g.nodes.some(n=>n.name.endsWith('roof')||n.name.includes('roof.')));
   const a=read(`output/axis-courts/${p.id}-${level}.json`);assert.equal(a.gateCount,p.gates.length);assert(a.bounds[1][2]<.131&&a.bounds[1][2]>.125);audits.push(a);
  }
  assert(audits[0].triangles<audits[1].triangles/2);assert(audits[0].bounds.flat().every((v,i)=>Math.abs(v-audits[1].bounds.flat()[i])<1e-7));sourceParts+=p.sourceParts.length;gates+=p.gates.length;
 }
 assert.equal(sourceParts,35);assert.equal(gates,6);assert.equal(read('public/assets/urban/manifest.json').tiles.length,144);
});
test('source parts fit replacement masks without masking Duanmen itself',()=>{
 const records=read('data/urban/records.json').records;const d=m.assets.find(s=>s.id==='duanmen');
 for(const p of plans){const [a,b,c,e]=p.bounds;
  assert(!(d.x>a&&d.x<c&&d.y>b&&d.y<e));
  const parts=records.filter(r=>p.sourceParts.includes(r.osmId));assert.equal(parts.length,p.sourceParts.length);
  for(const r of parts)assert(r.rings.flat().every(([x,y])=>x>a&&x<c&&y>b&&y<e));
 }
 assert(d.contextView);assert(d.relatedModels.some(l=>l.id==='axis-nw'));
});
