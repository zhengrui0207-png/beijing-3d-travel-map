import {formatDistance,insideMap,toModelPosition} from './route-core.mjs';
import {gcjToWgs,minutes,chooseRoute,navigationUrl,optimizeOrder,visitMinutes,routeScore} from './travel-core.mjs';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export class Travel {
 constructor(callbacks){
  this.cb=callbacks;this.stops=[];this.mode='walking';this.preference='fastest';this.legs=[];this.cache=new Map();this.epoch=0;this.configured=false;this.visits={};this.keepLast=true;this.budget=8;
  this.panel=document.querySelector('#travel-panel');this.panel.addEventListener('click',e=>this.click(e));
  this.panel.addEventListener('change',e=>this.change(e));
  document.querySelector('#baidu-search-form').onsubmit=e=>{e.preventDefault();this.search();};
  document.querySelector('#baidu-query').oninput=e=>{if(!e.target.value.trim()){this.searchController?.abort();this.searchResults=[];document.querySelector('#baidu-search-results').textContent='';}};
  document.querySelector('#baidu-search-results').onclick=e=>{const b=e.target.closest('[data-poi]');if(b){const p=this.searchResults[Number(b.dataset.poi)];this.cb.add(p);b.disabled=true;b.textContent='已加入';}};
  document.querySelector('#baidu-connect').onclick=()=>this.configure();
  this.ready=this.status();
 }
 async status(){
  try{const r=await fetch('./api/travel/status',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();this.token=data.token;this.configured=data.configured;this.readOnly=!!data.readOnly;this.statusError='';}
  catch{this.statusError='出行服务暂时不可用，请稍后刷新重试。';}
  this.render();return this.configured;
 }
 async post(path,body,signal){
  const r=await fetch('./api/travel/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Atlas-Token':this.token||''},body:JSON.stringify(body),signal});
  let data;try{data=await r.json();}catch{throw Error('出行服务返回异常，请稍后重试。');}
  if(!r.ok){const e=Error(data.error||'查询失败');e.code=data.code;throw e;}return data;
 }
 async diagnose(){
  this.diagnosticMessage='正在检测…';this.render();
  try{const d=await this.post('diagnostics',{});this.diagnosticMessage=d.connected?'百度连接已恢复，可重新加载方案。':d.message+(d.publicIpHint?` 当前检测到的公网 IP：${d.publicIpHint}（若使用代理分流，请核对百度实际出口）。`:'');}
  catch(e){this.diagnosticMessage=e.message;}this.render();
 }
 async configure(){
  await this.status();if(this.readOnly)return;let d=document.querySelector('#baidu-config');if(!d){d=document.createElement('dialog');d.id='baidu-config';document.body.append(d);}
  d.innerHTML=`<form><button type="button" class="dialog-close" aria-label="关闭百度配置">×</button><h2>连接百度出行服务</h2><p>使用百度地图开放平台的服务端 AK，开通地点检索、轻量级路线规划，采用 IP 白名单校验。此本机版不支持 SN 签名型 AK。</p><label for="baidu-ak">服务端 AK</label><input id="baidu-ak" type="password" required autocomplete="off" placeholder="密钥仅保存在本机服务端"><p>将写入用户目录 .config/beijing-atlas/baidu.json，不会写入前端或海报。</p><p><a href="https://lbsyun.baidu.com/apiconsole/key" target="_blank" rel="noreferrer">打开百度控制台申请 / 查看 AK ↗</a></p><p role="status" id="config-result"></p><button type="submit" class="primary-button">验证并连接</button></form>`;
  d.querySelector('[type=button]').onclick=()=>d.close();
  d.querySelector('form').onsubmit=async e=>{e.preventDefault();const button=d.querySelector('[type=submit]');button.disabled=true;const input=d.querySelector('input');try{await this.post('config',{ak:input.value.trim()});input.value='';this.configured=true;this.cache.clear();d.close();this.load();}catch(e){d.querySelector('#config-result').textContent=e.message;}finally{button.disabled=false;}};d.showModal();
 }
 setStops(stops){
  const key=JSON.stringify(stops.map(p=>[p.id,p.lon,p.lat]));if(key===this.stopKey)return;
  this.stopKey=key;this.stops=stops;this.load();
 }
 async load(){
  this.controller?.abort();const controller=this.controller=new AbortController(),epoch=++this.epoch;this.suggestion=null;this.optimizeMessage='';this.optimizeBusy=false;this.legs=[];this.authError='';this.cb.update();this.render();
  await this.ready;if(epoch!==this.epoch)return;
  this.legs=this.stops.slice(1).map((to,i)=>({from:this.stops[i],to,loading:this.configured}));this.render();
  if(!this.configured)return;
  for(let i=0;i<this.legs.length;i++){
   if(epoch!==this.epoch)return;const leg=this.legs[i];
   try{leg.route=await this.getRoute(leg.from,leg.to,controller.signal);}catch(e){if(e.name==='AbortError')return;leg.error=e.message;if(e.code==='IP_WHITELIST')this.authError=e.message;}
   if(epoch!==this.epoch)return;leg.loading=false;this.render();this.cb.update();
  }
 }
 async getRoute(from,to,signal){
  const key=JSON.stringify([from.id,from.lon,from.lat,to.id,to.lon,to.lat,this.mode]);let entry=this.cache.get(key);
  if(!entry||Date.now()-entry.at>300000){const response=await this.post('route',{from,to,mode:this.mode},signal);entry={at:Date.now(),...response};this.cache.set(key,entry);}
  const route=chooseRoute(entry.routes,this.preference);
  return {...route,alternatives:entry.routes,fetchedAt:entry.fetchedAt,modelPaths:route.steps.filter(s=>s.path?.length).map(s=>({kind:s.kind,points:s.path.map(([lon,lat])=>{const p=gcjToWgs(lon,lat);return toModelPosition(p.lon,p.lat);})}))};
 }
 forLeg(index){return this.legs[index]?.route;}
 render(){
  document.querySelector('#baidu-connect').hidden=this.configured||this.readOnly;
  const total=this.legs.reduce((n,l)=>n+(l.route?.duration||0),0),all=this.legs.length>0&&this.legs.every(l=>l.route),stops=this.stops;
  this.panel.innerHTML=`<div class="travel-heading"><strong>百度出行</strong>${this.readOnly?'<span>在线服务</span>':`<button data-connect>${this.configured?'已配置 · 设置':'连接服务'}</button>`}</div><div class="travel-modes"><button data-mode="walking" aria-pressed="${this.mode==='walking'}">实际步行</button><button data-mode="transit" aria-pressed="${this.mode==='transit'}">公交 / 地铁</button></div><label class="travel-label">方案偏好<select id="travel-preference"><option value="fastest">更省时间</option><option value="less-walking">少走路</option><option value="few-transfers">少换乘</option></select></label>
  ${this.authError&&!this.readOnly?`<p class="travel-error">${esc(this.authError)}</p><button data-diagnose>检测百度连接与公网 IP</button><p role="status">${esc(this.diagnosticMessage||'')}</p><a href="https://lbsyun.baidu.com/apiconsole/key" target="_blank" rel="noreferrer">打开百度控制台修改白名单 ↗</a>`:''}
  ${!this.configured?`<p class="travel-message">${esc(this.statusError||'连接服务端 AK 后，可计算实际道路距离和预计耗时。下方导航链接可直接使用。')}</p>`:''}
  ${stops.length<2?'<p class="travel-message">选择至少两个地点，按行程顺序计算交通。</p>':''}
  ${all?`<div class="travel-total"><strong>${minutes(total)}</strong><span>预计交通总耗时 · ${formatDistance(this.legs.reduce((n,l)=>n+l.route.distance,0))}</span></div>`:''}
  ${this.configured&&stops.length>1?'<button class="travel-refresh" data-refresh>重新加载当前方案</button>':''}<div class="travel-legs">${this.legs.map((l,i)=>this.legHTML(l,i)).join('')}</div>
  ${stops.length>=2?`<details class="smart-plan"><summary>智能安排行程 · 顺序建议</summary><p>固定第一站；根据百度交通耗时比较顺序，不包含开放时间校验。最多8站，最多查询56段交通。</p><label>当天可用时间 <input id="travel-budget" type="number" min="1" max="24" value="${this.budget}"> 小时</label><label><input id="travel-keep-last" type="checkbox" ${this.keepLast?'checked':''}> 保留最后一站</label><div class="visit-editor">${stops.map(p=>`<label>${esc(p.name)}<input data-visit="${esc(p.id)}" type="number" min="0" max="720" value="${this.visits[p.id]??visitMinutes(p)}">分钟</label>`).join('')}</div><button data-optimize ${!this.configured||stops.length>8||this.optimizeBusy?'disabled':''}>${this.optimizeBusy?'正在比较交通方案…':'比较顺序并给建议'}</button><p role="status">${esc(this.optimizeMessage||'游览时间取攻略建议中值，可自行修改。')}</p><div>${this.suggestionHTML()}</div></details>`:''}
  <p class="travel-disclaimer">${all?'地图实线为百度方案，虚线为步行接驳。':'未获取方案的段落仍显示直线示意。'} 公交方案含地铁与地面公交；耗时为查询时的预计值，不保证所选日期班次。园内代表点不等于入口，请在百度导航中核对通行入口。</p><a class="travel-provider" href="https://map.baidu.com" target="_blank" rel="noreferrer">出行方案 © 百度地图</a>`;
  this.panel.querySelector('#travel-preference').value=this.preference;
  if(this.smartOpen)this.panel.querySelector('.smart-plan')?.setAttribute('open','');
  const details=this.panel.querySelector('.smart-plan');if(details)details.ontoggle=()=>this.smartOpen=details.open;
 }
 legHTML(l,i){
  const r=l.route;
  return `<article class="travel-leg"><h3>${i+1}. ${esc(l.from.name)} → ${esc(l.to.name)}</h3>${l.loading?'<p role="status">正在计算道路方案…</p>':l.error?`<p class="travel-error">${esc(l.error)}</p><button data-retry>重试未完成方案</button>`:!r?'<p>尚未计算实际交通</p>':`<p class="leg-actual"><strong>${minutes(r.duration)}</strong> · ${formatDistance(r.distance)}${this.mode==='transit'?` · 换乘 ${r.transfers} 次`:''}</p>${this.mode==='transit'?`<p>步行接驳 ${r.walkingDistance===null?'距离未提供':formatDistance(r.walkingDistance)}</p>`:''}${r.alternatives.length>1?`<label>其他方案<select data-alternative="${i}">${r.alternatives.map((a,j)=>`<option value="${j}" ${a.duration===r.duration&&a.distance===r.distance?'selected':''}>${minutes(a.duration)} · ${formatDistance(a.distance)} · 换乘${a.transfers}次</option>`).join('')}</select></label>`:''}<details><summary>查看${this.mode==='walking'?'道路步骤':'步行与乘车分段'}</summary><ol>${r.steps.map(s=>`<li><strong>${s.kind==='walking'?'步行':esc(s.line||'公共交通')}</strong> ${s.duration===null?'':minutes(s.duration)}${s.distance===null?'':` · ${formatDistance(s.distance)}`}<p>${s.kind==='walking'?esc(s.instruction):`${esc(s.boarding||'上车站未提供')} 上车 → ${esc(s.alighting||'下车站未提供')} 下车${s.stops===null?'':` · ${s.stops}站`} ${esc(s.direction)}`}</p></li>`).join('')}</ol></details>${!r.hasPath?'<p>接口未提供线路形状；地图保留直线示意。</p>':''}<small>查询于 ${new Date(r.fetchedAt*1000).toLocaleTimeString('zh-CN')}</small>`}
  <a class="go-next" href="${esc(navigationUrl(l.from,l.to,this.mode))}" target="_blank" rel="noreferrer">去下一站 · ${esc(l.to.name)} ↗</a></article>`;
 }
 click(e){
  const b=e.target.closest('button');if(!b)return;
  if(b.hasAttribute('data-connect'))this.configure();
  if(b.hasAttribute('data-diagnose'))this.diagnose();
  if(b.dataset.mode&&b.dataset.mode!==this.mode){this.mode=b.dataset.mode;this.load();}
  if(b.hasAttribute('data-retry'))this.load();
  if(b.hasAttribute('data-refresh')){this.cache.clear();this.load();}
  if(b.hasAttribute('data-optimize'))this.optimize();
  if(b.hasAttribute('data-apply-order')&&this.suggestion){this.cb.apply(this.suggestion.order);}
 }
 change(e){
  const el=e.target;
  if(el.id==='travel-preference'){this.preference=el.value;this.load();}
  if(el.id==='travel-budget'){this.budget=Math.max(1,Math.min(24,Number(el.value)||8));this.suggestion=null;this.render();}
  if(el.id==='travel-keep-last'){this.keepLast=el.checked;this.suggestion=null;this.render();}
  if(el.dataset.visit){this.visits[el.dataset.visit]=Math.max(0,Math.min(720,Number(el.value)||0));this.suggestion=null;this.render();}
  if(el.dataset.alternative!==undefined){const leg=this.legs[Number(el.dataset.alternative)],r=leg.route.alternatives[Number(el.value)];leg.route={...leg.route,...r,modelPaths:r.steps.filter(s=>s.path?.length).map(s=>({kind:s.kind,points:s.path.map(([lon,lat])=>{const p=gcjToWgs(lon,lat);return toModelPosition(p.lon,p.lat);})}))};this.render();this.cb.update();}
 }
 async optimize(){
  if(this.optimizeBusy||this.stops.length>8)return;const epoch=this.epoch;this.optimizeBusy=true;this.smartOpen=true;this.optimizeMessage='正在获取有方向的交通耗时…';this.render();
  const stops=[...this.stops],ids=stops.map(p=>p.id),matrix={};let done=0;
  try{
   for(const a of stops)for(const b of stops){
    if(a.id===b.id)continue;if(epoch!==this.epoch)return;
    matrix[a.id+'|'+b.id]=await this.getRoute(a,b,this.controller.signal);
    this.optimizeMessage=`已比较 ${++done} / ${stops.length*(stops.length-1)} 段`;this.render();
   }
   if(epoch!==this.epoch)return;
   let order=optimizeOrder(ids,matrix,this.preference,this.keepLast);if(!order)throw Error('无法为全部景点找到完整可行顺序。');
   const score=arr=>arr.slice(1).reduce((n,id,i)=>n+routeScore(matrix[arr[i]+'|'+id],this.preference),0);
   if(score(order)>=score(ids)-1)order=ids;
   const duration=arr=>arr.slice(1).reduce((n,id,i)=>n+matrix[arr[i]+'|'+id].duration,0);
   const visits=stops.reduce((n,p)=>n+(this.visits[p.id]??visitMinutes(p)),0)*60;
   this.suggestion={order,before:duration(ids),after:duration(order),visits,budget:this.budget*3600};
   this.optimizeMessage=order.every((id,i)=>id===ids[i])?'当前顺序已符合所选偏好，建议保持；可结合下方时间预算调整停留。':'已按出行偏好比较顺序；采用后仍可撤销。';
  }catch(e){if(e.name!=='AbortError')this.optimizeMessage='无法完成比较：'+e.message;}
  finally{if(epoch===this.epoch){this.optimizeBusy=false;this.render();}}
 }
 suggestionHTML(){
  const s=this.suggestion;if(!s)return '';
  const over=s.after+s.visits-s.budget;
  return `<div class="order-suggestion"><strong>${s.order.map(id=>esc(this.stops.find(p=>p.id===id).name)).join(' → ')}</strong><p>交通：原 ${minutes(s.before)} → 建议 ${minutes(s.after)}；游览 ${minutes(s.visits)}。</p><p>${over>0?`超过当天预算 ${minutes(over)}，建议减少一处长时间展馆或缩短停留；本建议不会自动删除景点。`:'交通与游览在时间预算内，请另留排队、用餐和休息时间。'}</p><button data-apply-order>采用建议顺序</button></div>`;
 }
 async search(){
  const q=document.querySelector('#baidu-query').value.trim(),container=document.querySelector('#baidu-search-results');if(!q)return;
  this.searchController?.abort();const controller=this.searchController=new AbortController();container.textContent='正在搜索百度地图…';
  await this.ready;if(!this.configured){container.textContent=this.readOnly?'地点检索暂时不可用，请稍后重试。':'请先点击「连接百度」配置服务端 AK。';return;}
  try{
   const response=await this.post('search',{query:q},controller.signal);if(controller.signal.aborted)return;
   this.searchResults=response.places.map(p=>({...p,...gcjToWgs(p.lon,p.lat),baiduUid:p.uid}));
   container.innerHTML=this.searchResults.map((p,i)=>`<article><strong>${esc(p.name)}</strong><p>${esc(p.address)}</p><button data-poi="${i}" ${insideMap(p.lon,p.lat)?'':'disabled'}>${insideMap(p.lon,p.lat)?'＋ 加入我的行程':'超出当前3D城区范围'}</button></article>`).join('')||'<p>未找到地点，试试更完整的名称或所在街区。</p>';
  }catch(e){if(e.name!=='AbortError'){container.textContent=e.message;if(e.code==='IP_WHITELIST'){this.authError=e.message;this.render();}}}
 }
}
