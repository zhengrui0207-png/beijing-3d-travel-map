// GCJ-02 is retained for provider data; inverse coordinates are only for OSM alignment.
export function wgsToGcj(lon,lat){
 const pi=Math.PI,x=lon-105,y=lat-35;
 let a=-100+2*x+3*y+.2*y*y+.1*x*y+.2*Math.sqrt(Math.abs(x));
 let b=300+x+2*y+.1*x*x+.1*x*y+.1*Math.sqrt(Math.abs(x));
 a+=(20*Math.sin(6*x*pi)+20*Math.sin(2*x*pi))*2/3+(20*Math.sin(y*pi)+40*Math.sin(y/3*pi))*2/3+(160*Math.sin(y/12*pi)+320*Math.sin(y*pi/30))*2/3;
 b+=(20*Math.sin(6*x*pi)+20*Math.sin(2*x*pi))*2/3+(20*Math.sin(x*pi)+40*Math.sin(x/3*pi))*2/3+(150*Math.sin(x/12*pi)+300*Math.sin(x/30*pi))*2/3;
 const rad=lat*pi/180,m=1-.00669342162296594323*Math.sin(rad)**2;
 return [lon+b*180/(6378245/Math.sqrt(m)*Math.cos(rad)*pi),lat+a*180/((6378245*(1-.00669342162296594323))/(m*Math.sqrt(m))*pi)];
}
export function gcjToWgs(lon,lat){let x=lon,y=lat;for(let i=0;i<5;i++){const [a,b]=wgsToGcj(x,y);x+=lon-a;y+=lat-b;}return {lon:x,lat:y};}
export function minutes(seconds){return `${Math.max(1,Math.ceil(seconds/60))} 分钟`;}
export function routeScore(r,preference='fastest'){
 return r.duration+(preference==='less-walking'?(r.walkingDistance??r.distance)*.8:0)+(preference==='few-transfers'?r.transfers*900:0);
}
export function chooseRoute(routes,preference){return [...routes].sort((a,b)=>routeScore(a,preference)-routeScore(b,preference))[0];}
export function navigationUrl(from,to,mode){
 const params=new URLSearchParams({origin:`latlng:${from.lat},${from.lon}|name:${from.name}`,destination:`latlng:${to.lat},${to.lon}|name:${to.name}`,mode:mode==='walking'?'walking':'transit',region:'北京',coord_type:'wgs84',output:'html',src:'webapp.beijingatlas.daytrip'});
 return 'https://api.map.baidu.com/direction?'+params;
}
// Exact directed Held–Karp search with a fixed starting point, at most 8 stops.
export function optimizeOrder(ids,matrix,preference='fastest',keepLast=true){
 if(ids.length>8||ids.length<2)throw Error('顺序建议支持2至8个景点。');
 const n=ids.length,all=(1<<n)-1,states=new Map([['1:0',{cost:0,order:[0]}]]);
 for(let mask=1;mask<=all;mask++)for(let last=0;last<n;last++){
   const state=states.get(`${mask}:${last}`);if(!state)continue;
   for(let next=1;next<n;next++){
     if(mask&(1<<next)||keepLast&&next===n-1&&(mask|(1<<next))!==all)continue;
     const edge=matrix[`${ids[last]}|${ids[next]}`];if(!edge)continue;
     const nextMask=mask|(1<<next),key=`${nextMask}:${next}`,cost=state.cost+routeScore(edge,preference);
     if(!states.has(key)||cost<states.get(key).cost)states.set(key,{cost,order:[...state.order,next]});
   }
 }
 const best=[...states.entries()].filter(([k])=>k.startsWith(all+':')).map(([,v])=>v).sort((a,b)=>a.cost-b.cost)[0];
 return best?best.order.map(i=>ids[i]):null;
}
export function visitMinutes(place){
 const text=place.duration||'';const nums=text.match(/\d+(?:\.\d+)?/g)?.map(Number);
 if(!nums)return 60;
 return Math.round((nums.reduce((a,b)=>a+b,0)/nums.length)*(text.includes('小时')?60:1));
}
