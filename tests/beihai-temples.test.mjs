import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as THREE from '../public/vendor/build/three.module.js';
const source=(await readFile(new URL('../public/beihai-temples.js',import.meta.url),'utf8')).replace(/^import .*;$/mg,'');
const {removeTempleShells}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const manifest=JSON.parse(await readFile(new URL('../public/assets/beihai-temples/manifest.json',import.meta.url)));
test('replacement removes only the original hall shell, preserves neighbours, paving and replacement model',()=>{
 const root=new THREE.Group(),[a,b,c,d]=manifest.buildings[0].bounds,x=(a+c)/2,y=(b+d)/2;
 const geom=()=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([x,.02,-y,x+.001,.02,-y,x,.03,-y,0,0,0,1,0,0,0,1,0],3));g.setIndex([0,1,2,3,4,5]);return g;};
 const shell=new THREE.Mesh(geom());shell.userData.layer='buildings_urban_walls';root.add(shell);
 const paving=new THREE.Mesh(geom());paving.userData.layer='buildings_urban_paving';root.add(paving);
 const replacement=new THREE.Mesh(geom());replacement.userData.layer='buildings_urban_courtyard';replacement.userData.templeReplacement=true;root.add(replacement);
 assert.equal(removeTempleShells(root,manifest.buildings),1);assert.deepEqual([...shell.geometry.index.array],[3,4,5]);assert.equal(paving.geometry.index.count,6);assert.equal(replacement.geometry.index.count,6);assert.equal(removeTempleShells(root,manifest.buildings),0);
});
test('seven halls and four annexes have distinct footprints and embedded model bytes',async()=>{
 assert.equal(new Set(manifest.buildings.map(b=>b.id)).size,11);assert.deepEqual(new Set(manifest.buildings.filter(b=>!b.role).map(b=>b.name)),new Set(['法轮殿','正觉殿','普安殿','圣果殿','宗镜殿']));
 const raw=await readFile(new URL('../'+manifest.url,import.meta.url));assert.equal(raw.length,manifest.bytes);const doc=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));assert.ok(doc.extensionsRequired.includes('KHR_draco_mesh_compression'));assert.ok(doc.images.every(i=>i.bufferView!==undefined));
 const ids=new Set(doc.nodes.map(n=>n.extras?.osmId).filter(Boolean));assert.equal(ids.size,11);assert.ok(doc.nodes.filter(n=>n.mesh!==undefined).every(n=>n.extras.templeReplacement&&n.extras.groundHeight>.011));
});

test('concave replacement preserves a neighbouring object inside the L-shaped courtyard void',()=>{
 const root=new THREE.Group(),g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute([.5,0,-.5,.51,0,-.5,.5,1,-.5, 1.5,0,-1.5,1.51,0,-1.5,1.5,1,-1.5],3));
 const shell=new THREE.Mesh(g);shell.userData.layer='buildings_urban_walls';root.add(shell);
 const spec={bounds:[0,0,2,2],role:'annex',rings:[[[0,0],[2,0],[2,1],[1,1],[1,2],[0,2]]]};
 assert.equal(removeTempleShells(root,[spec]),1);assert.deepEqual([...g.index.array],[3,4,5]);
});
