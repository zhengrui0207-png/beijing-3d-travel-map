import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const manifest=JSON.parse(await readFile(new URL('../public/assets/urban-ground/manifest.json',import.meta.url)));
test('mapped ground asset has embedded paving texture, bounded height and source-specific layers',async()=>{
 const b=await readFile(new URL('../'+manifest.url,import.meta.url));assert.equal(b.length,manifest.bytes);assert.equal(createHash('sha256').update(b).digest('hex').slice(0,12),manifest.revision);
 const g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));assert.ok(g.extensionsRequired.includes('KHR_draco_mesh_compression'));assert.ok(g.images.length&&g.images.every(i=>i.bufferView!==undefined&&!i.uri));
 const kinds=new Set();for(const n of g.nodes.filter(n=>n.mesh!==undefined)){kinds.add(n.extras.sourceKind);assert.equal(n.extras.layer,'urban_ground_'+n.extras.sourceKind);assert.equal(n.extras.surfaceInferred,n.extras.sourceKind==='sidewalk');for(const p of g.meshes[n.mesh].primitives){const a=g.accessors[p.attributes.POSITION];assert.ok(a.min[1]>.008&&a.max[1]<.01121);}}
 assert.deepEqual(kinds,new Set(['parking','campus','residential','sidewalk','commercial','service','paved','green']));assert.equal(g.meshes.length,manifest.meshes);
});
test('below-ground polygons are excluded and mapped features retain original identifiers',()=>{
 assert.ok(manifest.sources.length>3000);assert.equal(new Set(manifest.sources.map(s=>`${s.osmType}/${s.osmId}`)).size,manifest.sources.length);
 const ids=new Set(manifest.sources.map(s=>s.osmId));for(const underground of [997931219,1075553889,1217444636,862117211])assert.equal(ids.has(underground),false);
 assert.ok(manifest.sidewalkRoadIds.length>0);assert.match(manifest.method,/inferred 1.6 m/);
});
