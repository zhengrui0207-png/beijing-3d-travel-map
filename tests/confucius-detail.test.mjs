import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const plan=read('data/confucius-plan.json'),spec=read('public/assets/route-landmarks/manifest.json').assets.find(x=>x.id==='confucius');
test('Dacheng Hall anchors to its own footprint without masking the temple gates',()=>{
 assert(spec);assert.deepEqual([spec.x,spec.y],plan.center);assert(Math.abs(spec.rotation*Math.PI/180-plan.angle)<1e-12);assert.deepEqual(spec.maskPolygon,plan.maskPolygon);assert.deepEqual(spec.sourceOsmIds,[227782229]);assert.match(spec.method,/推定/);assert.match(spec.method,/33米/);assert(spec.detailView.y<spec.y);
});
test('Dacheng Hall LODs match the actual door-clearance audit and have distinct detail budgets',()=>{
 for(const level of ['preview','detail']){
  const meta=read(`output/confucius-detail/confucius-${level}.json`),bytes=fs.readFileSync(new URL('../'+spec.lods[level].split('?')[0],import.meta.url));
  const hash=crypto.createHash('sha256').update(bytes).digest('hex').slice(0,12);assert.equal(meta.revision,hash);assert(spec.lods[level].endsWith('v='+hash));assert.equal(bytes.length,meta.bytes);
  const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));for(const part of ['roof','stone','gold','blue'])assert(doc.meshes.some(x=>x.name.includes(part)));
  const audit=read('output/confucius-detail/geometry-validation.json').find(v=>v.level===level);assert.equal(audit.revision,hash);assert.equal(audit.doorRays.length,6);assert.deepEqual(audit.errors,[]);assert.equal(audit.meshCount,doc.meshes.length);assert.equal(audit.boundsLocal[0][2],0);assert.equal(spec.height,audit.boundsLocal[1][2]);
 }
 assert(read('output/confucius-detail/confucius-detail.json').triangles>read('output/confucius-detail/confucius-preview.json').triangles*3);
});
