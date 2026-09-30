import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const plan=read('data/art-plan.json'),spec=read('public/assets/route-landmarks/manifest.json').assets.find(x=>x.id==='art');
test('art museum replaces its mapped footprint and preserves the neighbouring museum annex',()=>{
 assert(spec);assert.deepEqual([spec.x,spec.y],plan.center);assert(Math.abs(spec.rotation*Math.PI/180-plan.angle)<1e-12);assert.deepEqual(spec.maskPolygon,plan.maskPolygon);assert.deepEqual(spec.sourceOsmIds,[131710744]);assert.equal(spec.height,.35);assert.match(spec.method,/推定/);assert.equal(plan.heightSource,'photo-inferred, not measured');assert(spec.detailView.y<spec.y);assert(spec.detailView.offset[2]>0);
});
test('museum LOD files and actual aperture-ray audit match the current exported mesh',()=>{
 for(const level of ['preview','detail']){
  const meta=read(`output/art-detail/art-${level}.json`),bytes=fs.readFileSync(new URL('../'+spec.lods[level].split('?')[0],import.meta.url));
  const hash=crypto.createHash('sha256').update(bytes).digest('hex').slice(0,12);assert.equal(meta.revision,hash);assert(spec.lods[level].endsWith('v='+hash));assert.equal(bytes.length,meta.bytes);
  const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));for(const part of ['roof','reveal','glass','frame','frieze'])assert(doc.meshes.some(x=>x.name.includes(part)));
  assert.equal(doc.meshes.length,meta.meshes);assert(Math.abs(meta.boundsLocal[1][2]-.35)<1e-6);
  const audit=read('output/art-detail/geometry-validation.json').find(v=>v.level===level);assert.equal(audit.revision,hash);assert.equal(audit.windowRays,meta.windows.length);assert(audit.windowRays>300);assert.deepEqual(audit.errors,[]);
  assert(meta.roofs.filter(r=>r.skirt).length>=4);
 }
 assert(read('output/art-detail/art-detail.json').triangles>read('output/art-detail/art-preview.json').triangles*3);
});
