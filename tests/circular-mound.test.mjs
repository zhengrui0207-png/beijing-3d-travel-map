import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createHash} from 'node:crypto';import {footprintContains} from '../public/landmark-footprint.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url)));const plan=read('data/circular-mound-plan.json'),m=read('public/assets/route-landmarks/manifest.json');const spec=m.assets.find(s=>s.id==='circular-mound');
test('mound replaces its eight former generic footprints without consuming independently detailed north gates',()=>{
 assert.deepEqual([spec.x,spec.y],plan.center);assert.equal(spec.maskPolygons.length,8);assert.deepEqual(spec.sourceOsmIds.sort(),[43922668,43922669,43922697,727026433,727026437,727026439,237696578,237696579].sort());
 for(const g of plan.gates){assert.equal(spec.maskPolygons.some(p=>footprintContains(g.center,p)),!g.existing);assert.ok(footprintContains(g.center,spec.plantingPolygon,.025));}
 for(const id of ['echo-court','imperial-vault']){const s=m.assets.find(a=>a.id===id);assert.equal(footprintContains([s.x,s.y],spec.plantingPolygon),false);}
 for(const url of Object.values(spec.lods)){const b=fs.readFileSync(new URL('../'+url.split('?')[0],import.meta.url));assert.equal(b.subarray(0,4).toString(),'glTF');assert.equal(b.readUInt32LE(8),b.length);assert.ok(url.endsWith(createHash('sha256').update(b).digest('hex').slice(0,12)));}
});
test('official terrace dimensions and actual exported stair surfaces agree in both LODs',()=>{
 assert.deepEqual(plan.tiers.map(t=>t.radius*2),[54.91,39.31,23.65]);assert.deepEqual(plan.tiers.map(t=>t.pavers.reduce((a,b)=>a+b)),[1863,1134,405]);
 const checks=read('output/circular-mound/geometry-validation.json');assert.equal(checks.length,2);
 for(const c of checks){assert.equal(c.finite,true);assert.equal(c.stairSamples,108);assert.equal(c.heartStoneTop,5.178);for(const p of c.passages)assert.deepEqual(p.clear,p.osmId>=727000000?[true,true,true]:[true,false,true]);}
});
