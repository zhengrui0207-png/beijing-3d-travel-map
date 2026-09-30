import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {footprintContains,polygonMaskGLSL} from '../public/landmark-footprint.js';
const p=JSON.parse(fs.readFileSync(new URL('../data/tiantan-corridor-plan.json',import.meta.url)));
test('concave corridor mask retains neighbouring courtyards and covers its own walls',()=>{
 for(const point of p.maskPolygon)assert.ok(footprintContains(point,p.maskPolygon));
 for(let i=1;i<p.axis.length;i++)assert.ok(footprintContains(p.axis[i].map((v,j)=>(v+p.axis[i-1][j])/2),p.maskPolygon));
 for(const point of [[-6.0077,-36.0170],[-5.4611,-35.7301],[-5.5195,-36.0011]])assert.equal(footprintContains(point,p.maskPolygon),false);
 const code=polygonMaskGLSL(p.maskPolygon,'corridor');assert.ok(!code.includes('--'));assert.match(code,/bool corridor/);
});
test('72 bays, sourced dimensions, 2 actual GLBs and precise masks are integrated',()=>{
 assert.equal(p.bayCounts.reduce((a,b)=>a+b),72);assert.equal(p.officialWidthMetres,5);
 const manifest=JSON.parse(fs.readFileSync(new URL('../public/assets/route-landmarks/manifest.json',import.meta.url)));
 const s=manifest.assets.find(a=>a.id==='tiantan-corridor');assert.deepEqual(s.maskPolygon,p.maskPolygon);assert.equal(s.parentPlace,'tiantan');
 for(const url of Object.values(s.lods)){const data=fs.readFileSync(new URL('../'+url.split('?')[0],import.meta.url));assert.equal(data.subarray(0,4).toString(),'glTF');assert.equal(data.readUInt32LE(8),data.length);}
 assert.ok(manifest.assets.find(a=>a.id==='tiantan').relatedModels.some(a=>a.id===s.id));
});
