import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const root=new URL('../',import.meta.url), read=p=>JSON.parse(fs.readFileSync(new URL(p,root)));const m=read('public/assets/route-landmarks/manifest.json'),s=m.assets.find(x=>x.id==='imperial-vault'),plan=read('data/imperial-vault-plan.json');
test('vault retains geographic anchor and masks only its source footprint',()=>{
 assert.deepEqual([s.x,s.y],plan.center);const r=read('data/urban/records.json').records;
 const source=r.find(x=>x.osmId===43921121);assert.ok(source.rings[0].every(([x,y])=>x>s.bounds[0]&&x<s.bounds[2]&&y>s.bounds[1]&&y<s.bounds[3]));
 for(const id of [43921117,43921122,43921123]){const q=r.find(x=>x.osmId===id);assert.ok(q.bounds[2]<s.bounds[0]||q.bounds[0]>s.bounds[2]||q.bounds[3]<s.bounds[1]||q.bounds[1]>s.bounds[3]);}
 assert.ok(m.assets.find(x=>x.id==='tiantan').relatedModels.some(x=>x.id===s.id));
});
test('both compressed assets contain finite metre-scale geometry and distinct Chinese plaque meshes',()=>{
 let sizes=[];
 for(const url of Object.values(s.lods)){
 const b=fs.readFileSync(new URL(url.split('?')[0],root));assert.equal(b.readUInt32LE(8),b.length);assert.equal(b.subarray(0,4).toString(),'glTF');const doc=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));assert.ok(doc.extensionsRequired.includes('KHR_draco_mesh_compression'));assert.ok(!doc.cameras);
 for(const c of '皇穹宇'){const node=doc.nodes.find(x=>x.name.includes('plaque '+c));assert.ok(node);const mesh=doc.meshes[node.mesh];assert.ok(doc.accessors[mesh.primitives[0].indices].count>100);}
 for(const a of doc.accessors)if(a.type==='VEC3'&&a.min){assert.ok(a.min.concat(a.max).every(Number.isFinite));}
 assert.ok(doc.images.every(x=>x.bufferView!==undefined));sizes.push(b.length);
 }
 assert.ok(sizes[1]>sizes[0]);
 const audit=read('output/imperial-vault/detail.json');assert.ok(Math.abs(audit.bounds[1][2]*100-19.5)<.001);assert.equal(audit.roofTiers,1);
});
