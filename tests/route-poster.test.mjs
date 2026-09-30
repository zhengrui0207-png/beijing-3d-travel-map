import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const core=await readFile(new URL('../public/route-core.mjs',import.meta.url),'utf8');
const source=(await readFile(new URL('../public/route-poster.js',import.meta.url),'utf8')).replace("'./route-core.mjs'",JSON.stringify('data:text/javascript;base64,'+Buffer.from(core).toString('base64')));
const {makeRoutePoster}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
function mockCanvas(){
 const labels=[];const ctx={font:'29px sans-serif',measureText(s){return {width:Array.from(s).length*Number(this.font.match(/(\d+)px/)[1])};},fillText(s,x,y){labels.push({s,x,y});}};
 for(const k of ['fillRect','save','restore','beginPath','roundRect','clip','drawImage','moveTo','lineTo','stroke','arc','fill'])ctx[k]=()=>{};
 return {width:0,height:0,getContext:()=>ctx,labels};
}
for(const count of [0,1,7,32])test(`portrait retains ${count} stops and all distances without vertical clipping`,()=>{
 globalThis.document={createElement:()=>mockCanvas()};
 const places=Object.fromEntries(Array.from({length:count},(_,i)=>[String(i),{name:`景点${i}`,description:i===count-1?'用户添加的很长备注'.repeat(30):'看点说明'}]));
 const stops=Object.keys(places),legs=stops.slice(1).map(()=>({meters:123}));
 const out=makeRoutePoster({map:{},points:stops.map(()=>({x:.5,y:.5})),metrics:{stops,legs,total:legs.length*123},places,title:'我的路线',day:'2026-09-14',color:'#335544'});
 assert.equal(out.width,1080);assert.ok(out.height>=1920&&out.height>out.width);
 for(const id of stops)assert.ok(out.labels.some(l=>l.s===places[id].name));
 assert.equal(out.labels.filter(l=>l.s.startsWith('↓  下一站')).length,Math.max(0,count-1));
 assert.ok(out.labels.every(l=>l.y>0&&l.y<out.height));
});
