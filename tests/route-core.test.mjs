import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {distanceMeters,formatDistance,routeMetrics,moveStop,cleanStops,readPlans,localDay,validDay,toModelPosition,fromModelPosition,insideMap,customPlace,readCustomPlaces} from '../public/route-core.mjs';
const data=JSON.parse(readFileSync(new URL('../public/assets/tourism.json',import.meta.url)));
const places=Object.fromEntries(data.places.map(p=>[p.id,p]));
test('geographic distance: coincident, equator and symmetry',()=>{
  const a={lat:0,lon:0},b={lat:0,lon:1};
  assert.equal(distanceMeters(a,a),0);
  assert.ok(Math.abs(distanceMeters(a,b)-111195.0802)<.01);
  assert.equal(distanceMeters(a,b),distanceMeters(b,a));
  assert.ok(Math.abs(distanceMeters(a,{lat:0,lon:180})-20015114.442)<.01);
  assert.equal(formatDistance(873.6),'874 米');
  assert.equal(formatDistance(1201),'1.20 公里');
});
test('map picking inverses the same projection as modeled OSM coordinates',()=>{
  for(const p of data.places){const xy=toModelPosition(p.lon,p.lat);assert.ok(Math.abs(xy.x-p.x)<1e-8);assert.ok(Math.abs(xy.y-p.y)<1e-8);const ll=fromModelPosition(xy.x,xy.y);assert.ok(Math.abs(ll.lon-p.lon)<1e-10);assert.ok(Math.abs(ll.lat-p.lat)<1e-10);}
  assert.ok(insideMap(116.4,39.92));assert.ok(!insideMap(116.6,39.92));assert.ok(!insideMap(NaN,39.92));assert.ok(!insideMap('116.4',39.92));
});
test('custom landmarks are validated, persisted with routes and restored before route validation',()=>{
  const record={id:'user-test-1',name:'<b>集合点</b> & 茶',lon:116.4,lat:39.92,note:'自己的备注'};
  const p=customPlace(record);assert.ok(p);assert.equal(p.name,record.name);assert.equal(p.description,record.note);
  assert.equal(customPlace({...record,lat:50}),null);assert.equal(customPlace({...record,name:'   '}),null);
  assert.equal(customPlace({...record,id:'forbidden'}),null);assert.equal(customPlace({...record,id:'user-<script>'}),null);
  const raw=JSON.stringify({version:1,days:{'2026-09-09':['forbidden',record.id]},customPlaces:[record,record,{...record,id:'user-invalid',lon:null}]});
  const custom=readCustomPlaces(raw);assert.equal(custom.length,1);
  const all={...places,...Object.fromEntries(custom.map(p=>[p.id,p]))};
  const restored=readPlans(raw,all)['2026-09-09'];assert.deepEqual(restored,['forbidden','user-test-1']);
  assert.equal(routeMetrics(restored,all).legs.length,1);assert.ok(routeMetrics(restored,all).total>500);
  assert.deepEqual(readCustomPlaces('bad json'),[]);assert.deepEqual(readCustomPlaces(JSON.stringify({version:1,days:{}})),[]);
});
test('empty and one stop have no legs; reorder recomputes adjacent distances',()=>{
  assert.deepEqual(routeMetrics([],places),{stops:[],legs:[],total:0});
  assert.equal(routeMetrics(['forbidden'],places).legs.length,0);
  const original=['tiananmen','forbidden','beihai'];
  const reordered=moveStop(original,'beihai',-1);
  assert.deepEqual(original,['tiananmen','forbidden','beihai']);
  assert.deepEqual(reordered,['tiananmen','beihai','forbidden']);
  assert.notEqual(routeMetrics(original,places).total,routeMetrics(reordered,places).total);
  assert.deepEqual(moveStop(original,'tiananmen',-1),original);
  assert.deepEqual(moveStop(original,'missing',1),original);
});
test('all curated routes have complete unique points inside modeled Beijing',()=>{
  assert.equal(data.places.length,32);assert.equal(new Set(data.places.map(p=>p.id)).size,32);
  for(const p of data.places){assert.ok(p.lat>=39.865&&p.lat<=39.965,p.name);assert.ok(p.lon>=116.345&&p.lon<=116.485,p.name);}
  for(const t of data.tours){const m=routeMetrics(t.stops,places);assert.equal(m.stops.length,t.stops.length);assert.equal(m.legs.length,t.stops.length-1);assert.ok(m.total>1000);assert.ok(m.total<15000);assert.equal(m.total,m.legs.reduce((n,l)=>n+l.meters,0));}
  // Tian'anmen → Palace representative points: about 1 km northbound.
  const leg=distanceMeters(places.tiananmen,places.forbidden);assert.ok(leg>990&&leg<1030);
});
test('storage validates date keys and removes stale or duplicated ids',()=>{
  assert.deepEqual(cleanStops(['forbidden','x','forbidden',null,'beihai'],places),['forbidden','beihai']);
  assert.deepEqual(readPlans('{bad json',places),{});
  assert.deepEqual(readPlans(JSON.stringify({version:1,days:{'2026-09-09':['forbidden','forbidden','removed'],'2026-09-10':['beihai'],'2026-02-31':['cctv'],'__proto__':['cctv']}}),places),{'2026-09-09':['forbidden'],'2026-09-10':['beihai']});
  assert.ok(validDay('2024-02-29'));assert.ok(!validDay('2026-02-29'));assert.ok(!validDay('09-09-2026'));
  assert.equal(localDay(new Date(2026,8,9,0,1)),'2026-09-09');
});
