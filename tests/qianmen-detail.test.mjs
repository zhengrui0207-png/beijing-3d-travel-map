import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const plan=read('data/qianmen-plan.json'),manifest=read('public/assets/route-landmarks/manifest.json');
test('Qianmen pair keeps separate geographic anchors and replaces only its two old footprints',()=>{
 for(const p of plan.assets){const a=manifest.assets.find(a=>a.id===p.id);assert(a);assert.equal(a.x,p.center[0]);assert.equal(a.y,p.center[1]);assert.equal(a.rotation,p.angle);assert.deepEqual(a.sourceOsmIds,[p.osmId]);assert.deepEqual(a.maskPolygon,p.maskPolygon);assert.equal(a.height,p.dimensions[2]/100);assert(a.relatedModels.some(q=>q.id===(p.id==='qianmen'?'qianmen-arrow':'qianmen')));}
 assert.equal(manifest.assets.find(a=>a.id==='qianmen-arrow').parentPlace,'qianmen');assert(plan.assets[0].center[1]>plan.assets[1].center[1]);
});
test('both Qianmen LODs exist with byte revisions, corrected heights and distinct roof meshes',()=>{
 for(const p of plan.assets)for(const level of['preview','detail']){
  const a=manifest.assets.find(a=>a.id===p.id),audit=read(`output/qianmen-detail/${p.id}-${level}.json`),bytes=fs.readFileSync(new URL('../'+a.lods[level].split('?')[0],import.meta.url)),hash=crypto.createHash('sha256').update(bytes).digest('hex').slice(0,12);
  assert.equal(hash,audit.revision);assert(a.lods[level].endsWith('v='+hash));assert.equal(audit.bytes,bytes.length);assert(Math.abs(audit.boundsLocal[1][2]*100-p.dimensions[2])<.001);
  const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));for(const key of['roof','tile','reveal'])assert(doc.meshes.some(m=>m.name.includes(key)));assert.equal(doc.meshes.length,audit.meshes);
  if(p.id==='qianmen-arrow'){assert.equal(audit.windowRecesses.length,95);assert(audit.windowRecesses.every(w=>w.recess>=.7));}
 }
});
test('mesh ray audit verifies genuine passage openings and all arrow window recesses in both LODs',()=>{
 const report=read('output/qianmen-detail/geometry-validation.json');assert.equal(report.length,4);
 for(const row of report){assert.deepEqual(row.errors,[]);assert.equal(row.throughPortalRays,9);assert.equal(row.solidFlankRays,2);assert.equal(row.stairRays.length,2);assert(row.stairRays.every(p=>p&&p[2]>.05&&p[2]<.10));assert.equal(row.assetRevision,read(`output/qianmen-detail/${row.id}-${row.level}.json`).revision);if(row.id==='qianmen-arrow')assert.equal(row.windowRays,95);}
});
