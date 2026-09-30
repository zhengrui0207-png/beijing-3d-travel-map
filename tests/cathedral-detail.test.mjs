import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const plan=read('data/cathedral-plan.json'),spec=read('public/assets/route-landmarks/manifest.json').assets.find(x=>x.id==='cathedral');
test('East Church keeps mapped west-facing footprint and limits replacement to its actual building',()=>{
 assert(spec);assert.deepEqual([spec.x,spec.y],plan.center);assert(Math.abs(spec.rotation*Math.PI/180-plan.angle)<1e-12);assert.deepEqual(spec.maskPolygon,plan.maskPolygon);assert.deepEqual(spec.sourceOsmIds,[85902975]);
 // Local south is the facade; after rotation it must face geographic west.
 assert(Math.sin(spec.rotation*Math.PI/180)<-.99);assert(spec.detailView.x<spec.x-.29);assert(Math.abs(spec.detailView.y-spec.y)<.02);assert(spec.detailView.offset[0]<0);
 assert.match(spec.method,/推定/);assert.equal(spec.height,.30);assert.equal(plan.heightSource,'photo-inferred, not measured');
});
test('both cathedral LODs contain geometry for domes, actual reveals, doors, glass and roof',()=>{
 for(const level of ['preview','detail']){
  const meta=read(`output/cathedral-detail/cathedral-${level}.json`),bytes=fs.readFileSync(new URL('../'+spec.lods[level].split('?')[0],import.meta.url));
  const hash=crypto.createHash('sha256').update(bytes).digest('hex').slice(0,12);assert.equal(meta.revision,hash);assert(spec.lods[level].endsWith('v='+hash));assert.equal(bytes.length,meta.bytes);
  const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));for(const part of ['dome','reveal','door','glass','roof'])assert(doc.meshes.some(x=>x.name.includes(part)));
  assert.equal(doc.meshes.length,meta.meshes);assert(Math.abs(meta.boundsLocal[1][2]-.30)<1e-6);
 }
 assert(read('output/cathedral-detail/cathedral-detail.json').triangles>read('output/cathedral-detail/cathedral-preview.json').triangles*2);
});
test('actual mesh rays confirm all cathedral apertures are recessed and central tower is tallest',()=>{
 const audit=read('output/cathedral-detail/geometry-validation.json');assert.equal(audit.length,2);
 for(const r of audit){assert.equal(r.assetRevision,read(`output/cathedral-detail/cathedral-${r.level}.json`).revision);assert.equal(r.openingRays,63);assert.equal(r.doors,3);assert.deepEqual(r.errors,[]);assert(r.depthRange[0]>.0015);assert(r.depthRange[1]<.0051);assert(r.towerHeights[1]>r.towerHeights[0]);assert(r.towerHeights[1]>r.towerHeights[2]);}
});
