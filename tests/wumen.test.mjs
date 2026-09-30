import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));const plan=read('data/wumen-plan.json'),manifest=read('public/assets/route-landmarks/manifest.json'),spec=manifest.assets.find(s=>s.id==='wumen');
test('Wumen LODs preserve the geographic anchor and documented proportions',()=>{
 assert.deepEqual([spec.x,spec.y],plan.center);assert.equal(spec.parentPlace,'forbidden');assert(spec.palaceReplacement);const audits=[];
 for(const level of ['preview','detail']){
  const u=new URL(spec.lods[level],root),bytes=fs.readFileSync(new URL(u.pathname,'file://'));assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,12),u.searchParams.get('v'));const g=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());assert(g.extensionsRequired.includes('KHR_draco_mesh_compression'));assert(!g.cameras);assert(g.nodes.some(n=>n.name.includes('plaque')));
  const audit=read(`output/wumen-detail/${level}.json`);assert.equal(audit.platformHeight,12);assert.deepEqual(audit.mainHallDimensions,[60.05,25]);assert.equal(audit.cornerPavilions,4);assert(audit.bounds[1][2]>.355&&audit.bounds[1][2]<.358);assert(audit.bytes<12e6);audits.push(audit);
 }
 assert(audits[0].triangles<audits[1].triangles/3);assert.deepEqual(audits[0].bounds,audits[1].bounds);
 const rows=read('data/palace-layout.json').records.filter(r=>r.owner==='午门'),[x0,y0,x1,y1]=spec.bounds;
 assert.equal(rows.length,plan.sourceParts.length);for(const r of rows)assert(r.boundary.every(([x,y])=>x>x0&&x<x1&&y>y0&&y<y1));
});
test('streamed palace replacement preserves LOD fade, masks both visible and shadow geometry, and leaves courtyard intact',()=>{
 const source=fs.readFileSync(new URL('public/route-landmarks.js',root),'utf8').replace(/^import .*;$/gm,'').replace('export class RouteLandmarks','class RouteLandmarks')+'\nthis.R=RouteLandmarks';const context={};vm.createContext(context);vm.runInContext(source,context);const manager=Object.create(context.R.prototype);manager.entries=manifest.assets.map(spec=>({spec}));manager.maskActive={value:manager.entries.map(()=>0)};
 const mat=name=>({name,onBeforeCompile:s=>{s.fragmentShader+='\n// retained LOD fade';},customProgramCacheKey:()=>name});const material=mat('Vermilion'),depth=mat('depth'),ground=mat('Courtyard_Stone');const original=ground.onBeforeCompile;
 manager.installPalaceMasks({traverse:f=>[ {isMesh:true,material,customDepthMaterial:depth},{isMesh:true,material:ground} ].forEach(f)});
 assert.equal(ground.onBeforeCompile,original);
 for(const m of [material,depth]){const s={uniforms:{},vertexShader:'#include <project_vertex>',fragmentShader:'#include <clipping_planes_fragment>'};m.onBeforeCompile(s);assert(s.fragmentShader.includes('retained LOD fade'));assert(s.fragmentShader.includes('discard;'));assert(s.vertexShader.includes('modelMatrix'));assert.equal(s.uniforms.palaceReplacementActive,manager.maskActive);assert(s.fragmentShader.includes('palaceReplacementActive['+manifest.assets.indexOf(spec)+']>.5'));}
});
