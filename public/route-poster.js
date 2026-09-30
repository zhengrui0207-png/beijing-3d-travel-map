import {formatDistance} from './route-core.mjs';

export function wrapLines(ctx,text,width){
  const result=[];let line='';
  for(const char of String(text||'')){
    if(char==='\n'){result.push(line);line='';continue;}
    if(line&&ctx.measureText(line+char).width>width){result.push(line);line=char;}else line+=char;
  }
  if(line)result.push(line);return result;
}
export function makeRoutePoster({map,points,metrics,places,title,day,color,actualRoutes=null,guideCues={}}){
  const out=document.createElement('canvas');out.width=1080;
  let ctx=out.getContext('2d');
  const font=(size,weight=400)=>`${weight} ${size}px "PingFang SC","Microsoft YaHei",sans-serif`;
  ctx.font=font(29);
  const rows=metrics.stops.map((id,i)=>{
    const p=places[id];
    const text=p.highlights?.join(' · ')||p.description||'我的地标';
    const lines=wrapLines(ctx,text,810);
    ctx.font=font(38,600);const names=wrapLines(ctx,p.name,810);ctx.font=font(29);
    return {p,i,lines,names,h:80+(p.metro1?42:0)+names.length*46+lines.length*42+(i<metrics.legs.length?66:20)};
  });
  const actual=actualRoutes?.length===metrics.legs.length&&metrics.legs.length>0, distance=actual?actualRoutes.reduce((n,r)=>n+r.distance,0):metrics.total;
  const listY=1615,total=rows.reduce((n,r)=>n+r.h,0);
  out.height=Math.max(1920,listY+Math.max(total,170)+328);
  ctx=out.getContext('2d');
  ctx.fillStyle='#fffdf3';ctx.fillRect(0,0,out.width,out.height);
  const text=(s,x,y,size=28,color='#344e44',weight=400)=>{ctx.font=font(size,weight);ctx.fillStyle=color;ctx.textAlign='left';ctx.fillText(s,x,y);};
  text('BEIJING  /  立体旅行图鉴',54,54,22,'#7c8170',600);
  text('北京',48,170,108,'#be2925',900);
  text('一日漫游',294,164,66,'#263b35',800);
  ctx.fillStyle='#f7d45b';ctx.fillRect(54,202,972,60);
  ctx.font=font(34,800);const titleLines=wrapLines(ctx,title,940);
  text(titleLines[0],72,245,34,'#29352a',800);
  text(`${day}  ·  ${metrics.stops.length} 站  ·  ${actual?'实际路程':'直线合计'} ${formatDistance(distance)}`,60,305,26,'#536a5a',600);
  const area={x:30,y:340,w:1020,h:1147.5};
  ctx.save();ctx.beginPath();ctx.roundRect(area.x,area.y,area.w,area.h,24);ctx.clip();
  ctx.drawImage(map,area.x,area.y,area.w,area.h);
  const pts=points.map(p=>({x:area.x+p.x*area.w,y:area.y+p.y*area.h}));
  if(actual){for(const route of actualRoutes)for(const path of route.paths){ctx.beginPath();path.forEach((p,i)=>i?ctx.lineTo(area.x+p.x*area.w,area.y+p.y*area.h):ctx.moveTo(area.x+p.x*area.w,area.y+p.y*area.h));ctx.strokeStyle='white';ctx.lineWidth=11;ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=5;ctx.stroke();}}
  if(!actual&&pts.length>1){ctx.lineJoin='round';ctx.lineCap='round';ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.strokeStyle='white';ctx.lineWidth=12;ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=6;ctx.stroke();}
  // Offset coincident pins with leader lines; geographic route vertices stay unchanged.
  const occupied=[];const labels=[];
  pts.forEach((anchor,i)=>{
    let p={...anchor};
    for(let k=0;k<150&&occupied.some(q=>Math.hypot(p.x-q.x,p.y-q.y)<46);k++){
      const r=30+8*Math.sqrt(k);p={x:Math.max(area.x+28,Math.min(area.x+area.w-28,anchor.x+Math.cos(k*2.4)*r)),y:Math.max(area.y+28,Math.min(area.y+area.h-28,anchor.y+Math.sin(k*2.4)*r))};
    }
    occupied.push(p);ctx.beginPath();ctx.moveTo(anchor.x,anchor.y);ctx.lineTo(p.x,p.y);ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();
    ctx.beginPath();ctx.arc(p.x,p.y,23,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.strokeStyle='white';ctx.lineWidth=4;ctx.stroke();
    ctx.fillStyle='white';ctx.font=font(24,600);ctx.textAlign='center';ctx.fillText(String(i+1),p.x,p.y+8);
  });
  // Red framed place labels, packed independently from the geographic anchors.
  const overlaps=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
  pts.forEach((anchor,i)=>{
    const id=metrics.stops[i],name=places[id].name;ctx.font=font(28,800);
    const lines=wrapLines(ctx,name,280),nameWidth=Math.max(...lines.map(s=>ctx.measureText(s).width))+28,nameHeight=lines.length*34+16;
    ctx.font=font(22,700);
    const cues=guideCues[id]?wrapLines(ctx,guideCues[id],280):[];
    const cueWidth=cues.length?Math.max(...cues.map(s=>ctx.measureText(s).width))+28:0;
    const w=Math.min(310,Math.max(nameWidth,cueWidth)),h=nameHeight+(cues.length?cues.length*28+10:0);
    const candidates=[];
    for(const off of [40,85,130,180,240])for(const side of [1,-1])for(const dy of [-h/2,-h-20,25])candidates.push({x:Math.max(area.x+10,Math.min(area.x+area.w-w-10,anchor.x+side*off-(side<0?w:0))),y:Math.max(area.y+10,Math.min(area.y+area.h-h-10,anchor.y+dy)),w,h});
    const box=candidates.find(b=>!labels.some(q=>overlaps(b,q))&&!occupied.some(q=>overlaps(b,{x:q.x-26,y:q.y-26,w:52,h:52})))||candidates[0];labels.push(box);
    ctx.beginPath();ctx.moveTo(anchor.x,anchor.y);ctx.lineTo(box.x+w/2,box.y+h/2);ctx.strokeStyle='#cb342d';ctx.lineWidth=2;ctx.stroke();
    ctx.beginPath();ctx.roundRect(box.x,box.y,w,h,9);ctx.fillStyle='#fffdf5';ctx.fill();ctx.strokeStyle='#cb342d';ctx.lineWidth=4;ctx.stroke();
    lines.forEach((s,j)=>text(s,box.x+14,box.y+34+j*34,28,'#292e26',800));
    if(cues.length){ctx.fillStyle='#f8db65';ctx.fillRect(box.x+3,box.y+nameHeight,w-6,h-nameHeight-4);cues.forEach((s,j)=>text(s,box.x+14,box.y+nameHeight+24+j*28,22,'#4e351f',700));}
  });
  // Show each leg on the map as well as in the itinerary. Values are never invented.
  for(let i=0;i<pts.length-1;i++){
    const a=pts[i],b=pts[i+1],msg=actual?`${formatDistance(actualRoutes[i].distance)} · ${Math.ceil(actualRoutes[i].duration/60)}分钟`:`直线 ${formatDistance(metrics.legs[i].meters)}`;
    ctx.font=font(22,700);const w=ctx.measureText(msg).width+22,h=36;
    let box=null;
    for(const f of [.5,.3,.7])for(const off of [0,45,-45,90,-90]){const q={x:Math.max(area.x+8,Math.min(area.x+area.w-w-8,a.x+(b.x-a.x)*f-w/2+off)),y:Math.max(area.y+8,Math.min(area.y+area.h-h-8,a.y+(b.y-a.y)*f+22)),w,h};if(!box&&!labels.some(r=>overlaps(q,r)))box=q;}
    if(box){labels.push(box);ctx.beginPath();ctx.roundRect(box.x,box.y,w,h,5);ctx.fillStyle='#fff2b7';ctx.fill();text(msg,box.x+11,box.y+26,22,'#623e21',700);}
  }
  ctx.restore();
  text(actual?'沿红线出发 · 百度实际出行方案':'沿红线出发 · 景点间直线示意',60,1530,24,'#697b70');
  text('这一程，值得慢慢看',60,1595,39,'#293e31',800);
  let y=listY+35;
  for(const {p,i,lines,names,h} of rows){
    ctx.beginPath();ctx.arc(86,y+19,25,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.fillStyle='white';ctx.font=font(25,600);ctx.textAlign='center';ctx.fillText(String(i+1).padStart(2,'0'),86,y+28);
    names.forEach((s,j)=>text(s,140,y+30+j*46,38,'#28473e',600));
    let cy=y+names.length*46+21;
    if(p.duration)text(`建议停留 ${p.duration}`,140,cy,25,color);else text('我的地标 · 自由安排',140,cy,25,color);
    cy+=43;if(p.metro1){text(`1号线 · ${p.metro1.station}站 · 出站后步行`,140,cy,25,color);cy+=42;}lines.forEach((s,j)=>text(s,140,cy+j*42,29,'#62746a'));
    if(i<metrics.legs.length){const ly=y+h-22;text(`↓  下一站 · ${actual?`${formatDistance(actualRoutes[i].distance)} / ${Math.ceil(actualRoutes[i].duration/60)}分钟`:`直线 ${formatDistance(metrics.legs[i].meters)}`}`,140,ly,25,color);ctx.beginPath();ctx.moveTo(140,ly+18);ctx.lineTo(1020,ly+18);ctx.strokeStyle='#d8ded3';ctx.lineWidth=1;ctx.stroke();}
    y+=h;
  }
  if(!rows.length)text('还没有选择景点，先收藏一个想去的地方吧。',60,y+45,30);
  const fy=out.height-258;
  text('把想去的地方，连成今天的北京。',60,fy,30,'#28473e',600);
  text(actual?'方案为查询时预计值；出行请核对入口、班次和预约。':'直线距离不是步行里程；出行请核对入口、道路和预约。',60,fy+48,24,'#697b70');
  text('停留时间为建议，不含排队与交通。',60,fy+84,24,'#697b70');
  text(actual?'出行 © 百度地图 · 底图 © OSM · 屋顶 TRNKL / CC BY 4.0':'© OpenStreetMap contributors · 屋顶 TRNKL / CC BY 4.0',60,fy+123,19,'#7f8b80');
  text('建筑轮廓：Overture Maps / ODbL · Qian Shi et al. (2023) / CC BY 4.0',60,fy+151,19,'#7f8b80');
  text('East Asian Buildings · doi.org/10.5281/zenodo.8174931 · 高度与部分屋顶为推定',60,fy+179,19,'#7f8b80');
  text('琼华岛地形：Mapzen Terrain Tiles / SRTM courtesy USGS · 经平滑与基础整平',60,fy+207,19,'#7f8b80');
  return out;
}
