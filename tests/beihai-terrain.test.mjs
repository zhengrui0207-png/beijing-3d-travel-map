import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as THREE from '../public/vendor/build/three.module.js';
const src=(await readFile(new URL('../public/beihai-terrain.js',import.meta.url),'utf8')).replace(/^import .*;$/mg,'');
const {BeihaiTerrain}=await import('data:text/javascript;base64,'+Buffer.from(src).toString('base64'));
const field=JSON.parse(await readFile(new URL('../public/assets/beihai-terrain/heightfield.json',import.meta.url)));
const terrain=()=>{const t=new BeihaiTerrain({city:new THREE.Group()});t.field=field;return t;};
test('island contains the tower, leaves lake and other landmarks unchanged',()=>{
 const t=terrain();assert.equal(t.contains(-27.32041668157,10.48766128666),true);assert.equal(t.offset(0,0),0);assert.equal(t.offset(-28,13),0);
 const h=t.offset(-27.32041668157,10.48766128666,true);assert.ok(h>.2&&h<.3);assert.ok(Math.abs(h+.011-field.towerGroundHeight)<1e-10);
 assert.equal(field.pads.length,59);assert.ok(field.grid.flat().every(v=>Number.isFinite(v)&&v>=0));
});
test('building base stays at the same ground elevation through height changes and tile reload',()=>{
 const t=terrain(),x=-27.32041668157,y=10.48766128666,h=t.offset(x,y,true);
 const root=new THREE.Group(),g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([x,.011,-y,x,.111,-y,x+.001,.011,-y],3));
 const mesh=new THREE.Mesh(g);mesh.userData.layer='buildings';root.add(mesh);t.liftBuildings(root);
 const base=g.attributes.position.getY(0);assert.ok(Math.abs(base-(h+.011))<1e-6);
 t.setHeight(2);assert.ok(Math.abs(g.attributes.position.getY(0)*2-(h+.022))<1e-6);assert.ok(Math.abs((g.attributes.position.getY(1)-g.attributes.position.getY(0))*2-.2)<1e-6);
 t.setHeight(1);assert.ok(Math.abs(g.attributes.position.getY(0)-base)<1e-6);t.liftBuildings(root);assert.equal(t.lifted.length,1);
 t.release(root);assert.equal(t.lifted.length,0);
});
test('modelled stairs preserve source counts, monotonic elevations and explicit source conflicts',async()=>{
 const stairs=field.stairs;assert.equal(stairs.length,5);
 const byId=new Map(stairs.map(s=>[s.osmId,s]));assert.equal(byId.get(78058972).count,37);assert.equal(byId.get(227116618).count,55);assert.equal(byId.get(227116615).count,72);
 assert.equal(byId.get(227116615).osmStepCount,70);assert.match(byId.get(227116615).countSource,/gygl.beijing.gov.cn/);assert.ok(byId.get(227116615).sourceConflict);
 for(const s of stairs){assert.equal(s.treadTopHeights.length,s.count);assert.ok(s.topOffset>s.bottomOffset);assert.ok(s.widthMetresEstimated>0);assert.ok(Math.abs(s.treadTopHeights.at(-1)-(.0127+s.topOffset))<1e-10);assert.ok(s.treadTopHeights.every((h,i)=>i===0||h>s.treadTopHeights[i-1]));}
 const data=await readFile(new URL('../public/assets/beihai-terrain/terrain.glb',import.meta.url));const doc=JSON.parse(data.subarray(20,20+data.readUInt32LE(12)));
 const tread=doc.nodes.find(n=>n.extras?.layer==='architecture_beihai_steps_treads');assert.ok(tread);const primitive=doc.meshes[tread.mesh].primitives[0];assert.equal(doc.accessors[primitive.indices].count/6,stairs.reduce((n,s)=>n+s.count,0));
});
test('tower terrace heights are level, ordered and retained after building height scaling',()=>{
 const t=terrain();assert.equal(field.terraces.length,2);const [upper,lower]=field.terraces;assert.ok(upper.heightOffset>lower.heightOffset);
 assert.equal(upper.osmId,584742928);assert.equal(lower.osmId,584742932);
 for(const [x,y,h]of[[-27.3,10.50,upper.heightOffset],[-27.30,10.63,lower.heightOffset],[-27.45,10.50,lower.heightOffset]]){assert.equal(t.offset(x,y),h);t.setHeight(2);assert.equal(t.offset(x,y),h);}
 assert.ok(field.courtyard.areaSquareMetres>200&&field.courtyard.areaSquareMetres<500);
});
