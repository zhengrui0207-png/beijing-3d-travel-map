import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {footprintContains,replacementMaskGLSL} from '../public/landmark-footprint.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url)));
const plan=read('data/echo-court-plan.json'),manifest=read('public/assets/route-landmarks/manifest.json');
const spec=manifest.assets.find(a=>a.id==='echo-court');
test('disjoint court replacement covers all three source parts without removing the independent main hall or northern gate',()=>{
 assert.equal(spec.maskPolygons.length,3);
 for(const part of plan.parts){for(const pt of [...part.mask,part.center])assert.ok(spec.maskPolygons.some(poly=>footprintContains(pt,poly)));}
 const vault=manifest.assets.find(a=>a.id==='imperial-vault');
 for(const pt of [[vault.x,vault.y],[-6.93,-41.48],plan.center])assert.equal(spec.maskPolygons.some(poly=>footprintContains(pt,poly)),false);
 assert.ok(footprintContains([vault.x,vault.y],spec.plantingPolygon));
 const shader=replacementMaskGLSL(spec,'court');assert.match(shader,/courtPart0\(p\)\|\|courtPart1\(p\)\|\|courtPart2\(p\)/);
 assert.ok(!shader.includes('--'));
});
test('court LOD assets are embedded, independently versioned, source aligned and linked from the main hall',()=>{
 for(const level of ['preview','detail']){const bytes=fs.readFileSync(new URL('../'+spec.lods[level].split('?')[0],import.meta.url));assert.equal(bytes.subarray(0,4).toString(),'glTF');assert.equal(bytes.readUInt32LE(8),bytes.length);const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));assert.ok(!gltf.buffers.some(b=>b.uri));assert.ok(gltf.meshes.length>=12);}
 assert.deepEqual([spec.x,spec.y],plan.center);assert.equal(plan.wallHeightMetres,3.72);assert.equal(plan.wallThicknessMetres,.9);
 assert.ok(plan.pavingJoints.length>1000);assert.ok(Math.abs(plan.mappedDiameterMetres-plan.documentedDiameterMetres)>5);
 assert.ok(manifest.assets.find(a=>a.id==='imperial-vault').relatedModels.some(a=>a.id===spec.id));
});
