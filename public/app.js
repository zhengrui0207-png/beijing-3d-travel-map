import {Travel} from './travel.js?v=20261001-hosted1';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {PalaceLOD} from './palace-lod.js?v=20260930-wumen1';
import {LandmarkRenderer} from './landmark-renderer.js?v=city-depth1';
import {RouteLandmarks} from './route-landmarks.js?v=20260930-echo1';
import {makeRoutePoster} from './route-poster.js?v=atlas4';
import {CartographicStyle} from './cartographic-style.js?v=atlas4';
import {BeihaiTemples} from './beihai-temples.js?v=2';
import {BeihaiTerrain} from './beihai-terrain.js?v=terraces1';
import {UrbanArchitecture} from './urban-architecture.js?v=infill-detail2';
import {UrbanGround} from './urban-ground.js?v=1';
import {installDaylight} from './daylight.js';
import {fitCityShadow} from './city-lighting.js';
import {formatDistance, routeMetrics, cleanStops, moveStop, localDay, validDay, readPlans, fromModelPosition, insideMap, customPlace, readCustomPlaces} from './route-core.mjs';

const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const stage = $('#stage'), canvas = $('#map'), overlay = $('#route-overlay');
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const STORAGE = 'beijing-day-trips-v1';
const ANCHOR_HEIGHT=.011;
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
let needsRedraw = true, city, meta, data, places = {}, plans = {}, day = localDay();
let draft = [], preview = 'history', tourId = 'history', selected = null, currentTab = 'recommend';
let travel;
let islandTerrain, urban, atlasStyle, palace, routeLandmarks, enhancedRenderer, height = 1, view = '3d', flight = null, labels = [], metrics = {stops:[], legs:[], total:0};
let category = '全部', showNames = true, undo = null, ready = false;
let picking=false, inspecting=false, inspectionFocus=null;
const layers = {buildings:true,roads:true,parks:true,water:true};
const renderer = new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.8));
renderer.shadowMap.enabled = true; renderer.shadowMap.autoUpdate=false; renderer.shadowMap.needsUpdate=true; renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.05;
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xc8dfdf);
const camera = new THREE.OrthographicCamera(-110,110,65,-65,.1,1000); camera.position.set(80,155,150);
const controls = new OrbitControls(camera, canvas);
Object.assign(controls,{enableDamping:true,dampingFactor:.085,minZoom:.25,maxZoom:720,maxPolarAngle:Math.PI*.475,minPolarAngle:.02,screenSpacePanning:true});
controls.target.set(0,0,0); controls.addEventListener('change',()=>{needsRedraw=true;enhancedRenderer?.moving();if(!flight&&inspectionFocus&&Math.hypot(controls.target.x-inspectionFocus.x,controls.target.z-inspectionFocus.z)>inspectionFocus.radius){const info=$('#tour-model-info');if(info)info.hidden=true;}}); controls.addEventListener('start',()=>flight=null);
installDaylight(renderer,scene);
scene.add(new THREE.HemisphereLight(0xf4faff,0x869367,.30));
const daylightOffset=new THREE.Vector3(-65,80,40);
const sun = new THREE.DirectionalLight(0xfff6e8,2.8);sun.position.copy(daylightOffset);sun.castShadow=true;sun.shadow.mapSize.set(4096,4096);
Object.assign(sun.shadow.camera,{left:-92,right:92,top:92,bottom:-92,near:1,far:260});
sun.shadow.bias=-.0003;sun.shadow.normalBias=.004;sun.shadow.radius=12;sun.shadow.blurSamples=12;sun.shadow.intensity=.85;scene.add(sun);scene.add(sun.target);
const fill=new THREE.DirectionalLight(0xd6eaff,.20);fill.position.set(60,70,-90);scene.add(fill);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(2000,2000),new THREE.MeshStandardMaterial({color:0xc8dfdf,roughness:1}));
ground.rotation.x=-Math.PI/2;ground.position.y=-1.9;ground.receiveShadow=true;scene.add(ground);
const isBuilding = layer => /^(buildings|palace|landmark)/.test(layer);
function applyLayers(){urban?.setEnabled(layers.buildings);atlasStyle?.setLayers(layers);routeLandmarks?.setEnabled(layers.buildings);palace?.setEnabled(layers.buildings);palace?.setLayers(layers);if(!city)return;city.traverse(o=>{if(!o.isMesh)return;if(o.userData.atlasReplaced){o.visible=false;return;}const l=o.userData.layer||'';o.visible=l==='urban_ground_green'?layers.parks:l==='urban_ground_sidewalk'?layers.roads:isBuilding(l)?layers.buildings:/^(roads|paths)/.test(l)?layers.roads:/^(parks|trees|tree_trunks)/.test(l)?layers.parks:l==='water'?layers.water:true;});needsRedraw=true;}
function scaleBuildings(){islandTerrain?.setHeight(height);urban?.setHeight(height);atlasStyle?.setHeight(height);routeLandmarks?.setHeight(height);palace?.setHeight(height);if(city)city.traverse(o=>{if(o.isMesh&&isBuilding(o.userData.layer||'')){o.scale.y=height;o.position.y=(o.userData.groundHeight||0)*(1-height);}});needsRedraw=true;}
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);enhancedRenderer?.resize(w,h);camera.left=-63*w/h;camera.right=63*w/h;camera.top=63;camera.bottom=-63;camera.updateProjectionMatrix();needsRedraw=true;}
enhancedRenderer=new LandmarkRenderer(renderer,scene,camera);
new ResizeObserver(resize).observe(stage);resize();
window.addEventListener('resize',()=>{if(ready&&!inspecting&&!$('.workspace').classList.contains('landmark-focus')){resize();fitPoints(metrics.stops);}});
function fly(target, position, zoom){
  needsRedraw=true;
  if(reduced){controls.target.copy(target);camera.position.copy(position);camera.zoom=zoom;camera.updateProjectionMatrix();controls.update();return;}
  flight={samples:[],previous:0,start:performance.now(),fromTarget:controls.target.clone(),toTarget:target,fromPosition:camera.position.clone(),toPosition:position,fromZoom:camera.zoom,toZoom:zoom};
}
function fitPoints(ids, all=false){
  if($('.workspace').classList.contains('landmark-focus')){$('.workspace').classList.remove('landmark-focus');resize();}
  if($('#tour-model-info'))$('#tour-model-info').hidden=true;
  if(!data)return;
  const points=ids.map(id=>places[id]).filter(Boolean);
  let minX=-62,maxX=62,minZ=-57,maxZ=57;
  if(points.length&&!all){minX=Math.min(...points.map(p=>p.x));maxX=Math.max(...points.map(p=>p.x));minZ=Math.min(...points.map(p=>-p.y));maxZ=Math.max(...points.map(p=>-p.y));}
  const target=new THREE.Vector3((minX+maxX)/2,0,(minZ+maxZ)/2);
  const offset=view==='top'?new THREE.Vector3(0,220,.01):new THREE.Vector3(6,80,185);
  const testCamera=camera.clone();testCamera.position.copy(target).add(offset);testCamera.zoom=1;testCamera.lookAt(target);testCamera.updateMatrixWorld();testCamera.updateProjectionMatrix();
  const margin=all?3:points.length===1?7:3;
  const corners=[];
  for(const x of [minX-margin,maxX+margin])for(const z of [minZ-margin,maxZ+margin])corners.push(new THREE.Vector3(x,0,z).project(testCamera));
  const sx=Math.max(...corners.map(p=>p.x))-Math.min(...corners.map(p=>p.x));
  const sy=Math.max(...corners.map(p=>p.y))-Math.min(...corners.map(p=>p.y));
  // Reserve breathing room for the HUD, route names and distance badges.
  const fitZoom=Math.min(1.58/Math.max(sx,.01),1.48/Math.max(sy,.01),12);
  fly(target,target.clone().add(offset),Math.max(.25,fitZoom));
}
function fitRoute(){inspecting=false;selected=null;renderPlaceInfo();fitPoints(metrics.stops);updatePinState();}
function setView(value){view=value;$$('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);b.setAttribute('aria-pressed',String(b.dataset.view===view));});fitRoute();}
function zoom(f){flight=null;camera.zoom=THREE.MathUtils.clamp(camera.zoom*f,.25,controls.maxZoom);camera.updateProjectionMatrix();needsRedraw=true;}
function inspectPalace(level='palace'){
  inspecting=true;selected=null;renderPlaceInfo();updatePinState();
  const p=places.forbidden, target=new THREE.Vector3(p.x,0,-p.y);
  if(level!=='palace'){target.set(-20.65043,level==='roof'?.32:.05,-.99698);}
  const offset=level==='roof'?new THREE.Vector3(55,110,160):new THREE.Vector3(6,80,185);
  fly(target,target.clone().add(offset),level==='roof'?145:level==='hall'?70:12);
}
function inspectLandmark(id,modelView='overview'){
  const entry=routeLandmarks?.get(id);if(!entry)return;
  $('.workspace').classList.add('landmark-focus');resize();
  const spec=entry.spec;inspecting=false;selected=null;renderPlaceInfo();updatePinState();
  const focus=modelView==='detail'?spec.detailView:modelView==='context'?spec.contextView:spec.additionalViews?.[modelView];
  const views=[...Object.entries(spec.additionalViews||{}).map(([key,value])=>[key,value.label]),...(spec.contextView?[['context','查看建筑群']]:[]),...(spec.detailView?[['overview','查看建筑全貌'],['detail',spec.detailView.label||'走近建筑细节']]:[])].filter(([view])=>view!==modelView);
  const info=$('#tour-model-info');info.hidden=false;info.innerHTML=`<strong>${esc(spec.name)} · ${esc(focus?.label||spec.subject)}</strong><span>${esc(focus?.methodLabel||spec.methodLabel||'实景参考 3D')} · 拖动旋转查看</span>${views.map(([view,label])=>`<button data-landmark="${id}" data-model-view="${view}">${label}</button> · `).join('')}${(spec.relatedModels||[]).filter(link=>routeLandmarks.get(link.id)).map(link=>`<button data-landmark="${esc(link.id)}">${esc(link.label)}</button> · `).join('')}<button data-model-back="${esc(spec.parentPlace||id)}">返回景点介绍</button>`;
  const target=new THREE.Vector3(focus?.x??spec.x,(focus?.height??spec.height*.4)*height+(islandTerrain?.offset(focus?.x??spec.x,focus?.y??spec.y,true)||0),-(focus?.y??spec.y));
  const span=focus?.span??Math.max(spec.span,spec.height*height, .35);
  inspectionFocus={x:target.x,z:target.z,radius:span*.8};
  const aspect=stage.clientWidth/stage.clientHeight;
  const zoom=Math.min(focus?.zoomLimit??(modelView==='detail'?controls.maxZoom:180),Math.max(8,Math.min(90,90*aspect)/span));
  const offset=focus?.offset||spec.viewOffset;
  fly(target,target.clone().add(offset?new THREE.Vector3(...offset):new THREE.Vector3(id==='cctv'?-100:['wudaoying','yandai'].includes(id)?0:55,id==='cctv'?150:100,160)),zoom);
}
function fitSunToCamera(viewCamera,focus){
  const fit=fitCityShadow(viewCamera,focus,daylightOffset,sun.shadow.mapSize.x);
  sun.position.copy(fit.lightPosition);sun.target.position.copy(focus);sun.target.updateMatrixWorld();
  const {left,right,bottom,top,near,far}=fit;Object.assign(sun.shadow.camera,{left,right,bottom,top,near,far});sun.shadow.camera.updateProjectionMatrix();
  sun.shadow.normalBias=Math.min(.004,.00015+fit.texel*.25);
  sun.shadow.bias=-.00003/(far-near);
  sun.userData.worldTexel=fit.texel;
  sun.userData.shadowFit=fit;
  return fit;
}
function updateSun(){
  const moving=performance.now()-enhancedRenderer.lastMotion<240;
  const focus=controls.target;
  const shadowKey=[...focus.toArray().map(n=>n.toFixed(4)),...camera.position.toArray().map(n=>n.toFixed(4)),camera.zoom.toFixed(4),camera.left,camera.right,height,urban?.revision,routeLandmarks?.revision,layers.buildings,layers.parks,palace?.coverage.value,palace?.state.zones.map(z=>z.blend).join(','),palace?.external.map(a=>`${a.coverage.value}:${a.refinement.value}`).join(','),moving].join('/');
  if(sun.userData.shadowKey===shadowKey)return;sun.userData.shadowKey=shadowKey;renderer.shadowMap.needsUpdate=true;
  const fit=fitSunToCamera(camera,focus);
  sun.shadow.radius=(moving?-1:1)*Math.min(35,Math.max(2,.005/fit.texel));
}
function activeTour(){return data?.tours.find(t=>t.id===preview);}
function activeTitle(){return activeTour()?.name || '我的一日行程';}
function routeColor(){return '#cf3027';}
// Short editorial captions complement the full attraction guides. No opening
// hours, prices or booking promises are embedded in these persistent labels.
const guideCues={tiananmen:'从中轴线出发',forbidden:'沿中轴逛宫殿',jingshan:'登高俯瞰故宫',beihai:'湖畔漫步 · 看白塔',gongwang:'看王府与花园',shichahai:'湖畔散步',yandai:'逛胡同小店',drum:'登楼看老北京',bell:'钟鼓楼间慢行',nanluo:'走进胡同街巷',yonghe:'赏古建与彩绘',ditan:'古坛与秋色',zhongshan:'社稷坛旁慢行',tiantan:'看祈年殿',wangfujing:'逛街与觅食',guozijian:'走进古代学府',wudaoying:'胡同小店慢慢逛',national:'读懂历史与文物',guomao:'看北京城市天际线',cctv:'看当代建筑'};
function save(){
  plans[day]=[...draft];
  try{localStorage.setItem(STORAGE,JSON.stringify({version:1,days:plans,customPlaces:data.places.filter(p=>p.custom).map(({id,name,lon,lat,note,baiduUid})=>({id,name,lon,lat,note,baiduUid}))}));$('#save-state').textContent='已保存到当前浏览器 · 按日期分别记录';}
  catch{$('#save-state').textContent='浏览器存储不可用，请及时保存线路图';toast('行程暂存在页面内，请保存线路图留存');}
}
function setDraft(ids, message){
  undo={day,stops:[...draft],message};draft=cleanStops(ids,places);preview=null;save();syncRoute();renderPanels();renderPlaceInfo();if(message)toast(message);
}
function togglePlace(id){
  if(!places[id])return;
  const exists=draft.includes(id);setDraft(exists?draft.filter(x=>x!==id):[...draft,id],`${places[id].name}${exists?'已移出':'已加入'}当天行程`);
}
function undoDraft(){if(!undo||undo.day!==day)return;draft=[...undo.stops];undo=null;preview=null;save();syncRoute();renderPanels();renderPlaceInfo();toast('已撤销上一步行程修改');}
function showTab(tab){
  if(tab!=='recommend'&&ready)setImmersive(false);
  currentTab=tab;
  $$('[data-tab]').forEach(b=>{const on=b.dataset.tab===tab;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;});
  ['recommend','places','plan'].forEach(t=>$('#panel-'+t).hidden=t!==tab);
  if(tab==='plan'){preview=null;syncRoute();renderPlan();fitPoints(draft);}
  $('#route-panel').classList.toggle('open',tab==='plan');
  needsRedraw=true;
}
function setDay(value){
  if(!validDay(value)){$('#trip-date').value=day;return;}
  day=value;$('#trip-date').value=day;draft=cleanStops(plans[day],places);undo=null;preview=null;selected=null;
  syncRoute();renderPanels();renderPlaceInfo();showTab('plan');$('#save-state').textContent=draft.length?'已读取此日期的行程':'此日期还没有行程 · 仅保存在当前浏览器';
}
function previewTour(id){
  tourId=id;preview=id;selected=null;syncRoute();renderPanels();renderPlaceInfo();fitPoints(metrics.stops);
  $('#plan-content').scrollTop=0;
}
function adoptTour(id){const tour=data.tours.find(t=>t.id===id);if(!tour)return;setDraft(tour.stops,'已采用路线，可继续增删和调整顺序');showTab('plan');$('#plan-content').scrollTop=0;}
function selectPlace(id, focus=false){
  if(!places[id])return;selected=id;renderPlaceInfo();updatePinState();needsRedraw=true;
  if(focus)fitPoints([id]);
}
function syncRoute(){
  metrics=routeMetrics(activeTour()?.stops || draft,places);
  document.documentElement.style.setProperty('--route',routeColor());
  $('#plan-count').textContent=draft.length;$('#capture').disabled=!ready;
  renderHUD();renderPlan();updatePinState();travel?.setStops(metrics.stops.map(id=>places[id]));needsRedraw=true;
}
function renderHUD(){
  const t=activeTour();
  $('#route-hud').innerHTML=`<div class="hud-kicker"><i></i>${t?'BEIJING / 立体旅行图鉴':`${esc(day)} · 自选行程`}</div><h2>${esc(activeTitle())}</h2><p>${metrics.stops.length?`${metrics.stops.length} 个景点 <span> · </span> 直线串联示意  <strong>${formatDistance(metrics.total)}</strong>`:'点击地图上的景点，开始安排今天'}</p>`;
  $('#mobile-leg-count').textContent=`${metrics.legs.length} 段距离`;
}
const motifs={metro:'M16 7h32v31H16zM16 22h32M23 7v15M41 7v15M23 31h1M40 31h1M22 38l-7 9M42 38l7 9M20 44h24',axis:'M31 4v41M19 12h24M14 19h34M17 28h28M11 39h40M23 8l8-5 8 5M20 23l11-6 11 6',walk:'M8 39 22 31 17 20 33 14 45 24 55 10M9 41c14 11 31-3 48-1',autumn:'M32 47V21M32 36 18 26M32 29 45 16M32 38c-19-1-25-13-16-22 1 10 14 6 16 22M33 31c0-17 9-23 18-22 0 15-5 20-18 22'};
function renderTours(){
  $('#atlas-tour-strip').innerHTML=data.tours.map((t,i)=>`<button data-tour="${t.id}" class="${preview===t.id?'active':''}" aria-pressed="${preview===t.id}"><small>0${i+1}</small>${esc(t.short||t.name)}</button>`).join('');
  $('#tour-list').innerHTML=data.tours.map(t=>{const m=routeMetrics(t.stops,places);return `<button class="tour-card ${tourId===t.id?'active':''}" style="--tour:${t.color}" data-tour="${t.id}" aria-label="预览${esc(t.name)}" aria-pressed="${preview===t.id}"><span class="tour-eyebrow">${t.en}</span><h2>${t.name}</h2><svg class="tour-motif" viewBox="0 0 64 52" aria-hidden="true"><path d="${motifs[t.motif]}"/></svg><div class="tour-meta"><span>${t.stops.length} 站</span><span>直线 ${formatDistance(m.total)}</span></div><span class="view-indicator">${preview===t.id?'正在地图上':'查看 ↗'}</span></button>`;}).join('');
  const t=data.tours.find(t=>t.id===tourId);
  const m=routeMetrics(t.stops,places);
  $('#tour-detail').style.setProperty('--route',t.color);
  $('#tour-detail').innerHTML=`<div class="tour-detail-head"><h3>${t.short}</h3><span>${t.duration}</span></div><p class="tour-description">${t.description}</p><div class="tour-note">${t.season}<br>点击主题路线，在地图和路线详情中查看各站。</div>`;
}
function stopList(m, editable){
  return `<ol class="route-stops">${m.stops.map((id,i)=>{const p=places[id],actual=i?travel?.forLeg(i-1):null;return `${i?`<li class="leg-row" aria-label="${esc(m.legs[i-1].from.name)}至${esc(p.name)}${actual?'实际':'直线'}距离${formatDistance(actual?.distance??m.legs[i-1].meters)}"><span>↓ ${actual?'实际':'直线'}</span><strong>${formatDistance(actual?.distance??m.legs[i-1].meters)}${actual?` · ${Math.ceil(actual.duration/60)}分钟`:''}</strong></li>`:''}<li class="stop-row ${id===selected?'active':''}" data-stop="${id}"><span class="stop-num">${i+1}</span><button class="stop-title" data-focus="${id}" aria-label="在地图查看${esc(p.name)}">${esc(p.name)}${p.metro1?`<small class="metro-access">1号线 · ${esc(p.metro1.station)}站</small>`:(editable?`<small>${p.category}</small>`:'')}</button>${editable?`<div class="stop-controls"><button data-move="${id}" data-delta="-1" ${i===0?'disabled':''} aria-label="上移${esc(p.name)}">↑</button><button data-move="${id}" data-delta="1" ${i===m.stops.length-1?'disabled':''} aria-label="下移${esc(p.name)}">↓</button><button data-remove="${id}" aria-label="从行程移除${esc(p.name)}">×</button></div>`:''}</li>`;}).join('')}</ol>`;
}
function renderCatalog(){
  $('#categories').innerHTML=data.categories.map(c=>`<button data-category="${c}" class="${category===c?'active':''}" aria-pressed="${category===c}">${c}</button>`).join('');
  const matches=data.places.filter(p=>category==='全部'||p.category===category);
  $('#catalog-count').textContent=`${matches.length} 个景点`;
  $('#place-list').innerHTML=matches.map(p=>`<div class="place-row"><button class="place-open" data-focus="${p.id}" aria-label="在地图查看${esc(p.name)}">${esc(p.name)}<small>${p.category}${draft.includes(p.id)?` · 行程第 ${draft.indexOf(p.id)+1} 站`:''}</small></button><button class="place-add ${draft.includes(p.id)?'added':''}" data-toggle="${p.id}" aria-label="${draft.includes(p.id)?'移除':'添加'}${esc(p.name)}${draft.includes(p.id)?'':'到当天行程'}" aria-pressed="${draft.includes(p.id)}">${draft.includes(p.id)?'✓':'+'}</button></div>`).join('')||'<p class="no-results">没有找到相关景点<br>试试其他名称，或切换到「全部」</p>';
}
function renderPlan(){
  const t=activeTour();
  $('#route-mode').textContent=t?'推荐预览':'我的线路';
  $('#route-panel-title').textContent=activeTitle();
  const mine=routeMetrics(draft,places);
  $('#my-plan-summary').innerHTML=`<div class="my-plan-intro"><div class="eyebrow">${esc(day)}</div><h2>${draft.length?`${draft.length} 个想去的地方`:'从一个想去的地方开始'}</h2><p>${draft.length?`直线合计 ${formatDistance(mine.total)}。在路线详情中调整顺序或移除景点，地图会同步更新。`:'选取已有景点，或手动标记自己的小店、住处和集合点。'}</p><div class="my-plan-mini">${draft.slice(0,5).map(id=>`<span>${esc(places[id].name)}</span>`).join('')}${draft.length>5?`<span>另 ${draft.length-5} 站</span>`:''}</div><button class="primary-button" data-goto="places"><span>继续选择景点</span><span>＋</span></button><button class="secondary-button" data-show-route>查看我的线路与距离 ↗</button></div>`;
  if(t){
    const m=routeMetrics(t.stops,places);
    $('#plan-content').innerHTML=`<div class="plan-summary"><div><strong>${m.stops.length}<small>站</small></strong><span>线路上的景点</span></div><div><strong>${formatDistance(m.total)}</strong><span>相邻地标直线合计</span></div></div>${t.metro?`<div class="metro-route-note"><strong>地铁下车站 · 从西向东</strong><p>${esc(t.metro)}</p><small>仅列游览下车站；出站后步行，地图连线不是轨道。</small></div>`:''}${stopList(m,false)}<button class="primary-button route-adopt" data-adopt="${t.id}"><span>采用这条路线</span><span>加入当天 →</span></button><div class="tour-note"><strong>${t.season}</strong><br>${t.note}<br><a href="${t.source}" target="_blank" rel="noreferrer">参考：${t.sourceName} ↗</a></div>`;
    return;
  }
  const m=routeMetrics(draft,places);
  const undoHTML=undo&&undo.day===day?`<div class="undo-bar"><span>${esc(undo.message||'行程已更新')}</span><button data-undo>撤销</button></div>`:'';
  if(!draft.length){$('#plan-content').innerHTML=`${undoHTML}<div class="empty-plan"><svg viewBox="0 0 80 80" aria-hidden="true"><path d="m9 59 15-18 24 11 22-32" stroke-dasharray="3 4"/><circle cx="9" cy="59" r="4"/><circle cx="24" cy="41" r="4"/><circle cx="48" cy="52" r="4"/><path d="M70 9c-6 0-10 5-10 10s10 16 10 16 10-11 10-16-4-10-10-10z"/></svg><h2>从一个想去的地方开始</h2><p>在地图上点选景点加入行程，<br>或直接采用一条推荐路线。</p><button class="primary-button" data-goto="places">挑选当天景点 →</button><button class="text-button" data-goto="recommend">看看推荐路线</button></div>`;return;}
  $('#plan-content').innerHTML=`${undoHTML}<div class="plan-summary"><div><strong>${draft.length}<small>站</small></strong><span>按下方顺序游览</span></div><div><strong>${formatDistance(m.total)}</strong><span>相邻景点直线合计</span></div></div><div class="plan-actions"><button data-fit>↗ 在地图查看整条路线</button><button data-clear>清空行程</button></div>${stopList(m,true)}<div class="plan-bottom-actions"><button class="secondary-button" data-goto="places">＋ 继续加景点</button><button class="secondary-button" data-copy>复制行程</button></div><p class="plan-prompt">用 ↑ ↓ 调整先后顺序，距离会随之更新。${draft.length===1?'再加一个景点，即可生成第一段连线。':'行程较长时，可结合公共交通安排跨片区出行。'}</p>`;
}
function renderPanels(){renderTours();renderCatalog();renderPlan();}
function renderPlaceInfo(){
  const panel=$('#place-info');panel.hidden=!selected;if(!selected)return;
  const p=places[selected], added=draft.includes(selected);
  panel.innerHTML=`<button class="close" aria-label="关闭景点详情">×</button><div class="eyebrow">${p.category}${added?` / 当天第 ${draft.indexOf(selected)+1} 站`:''}</div><h2>${esc(p.name)}</h2><p>${esc(p.description)}</p>${p.metro1?`<div class="metro-route-note"><strong>1号线 · ${esc(p.metro1.station)}站</strong><p>${esc(p.metro1.note)}</p></div>`:''}${p.duration?`<div class="visit-duration">建议停留 ${esc(p.duration)}<small>不含排队与交通</small></div>`:''}${p.highlights?.length?`<h3>重点看什么</h3><ul class="place-highlights">${p.highlights.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:''}${p.walk?`<h3>怎么逛</h3><p>${esc(p.walk)}</p>`:''}${p.guideSource?`<a class="guide-source" href="${esc(p.guideSource.url)}" target="_blank" rel="noreferrer">参考：${esc(p.guideSource.label)} ↗</a>`:''}${p.tip?`<p class="place-tip">${esc(p.tip)}</p>`:''}<button class="primary-button" data-toggle="${p.id}" aria-pressed="${added}"><span>${added?'已在当天行程 · 点击移除':'加入当天行程'}</span><span>${added?'✓':'＋'}</span></button>${routeLandmarks?.get(p.id)?`<button class="secondary-button" data-landmark="${p.id}">查看 3D 建筑 · ${esc(routeLandmarks.get(p.id).spec.subject)} ↗</button><small class="model-origin">${esc(routeLandmarks.get(p.id).spec.methodLabel)} · 代表性模型，非测绘还原<br><a href="${esc(routeLandmarks.get(p.id).spec.source)}" target="_blank" rel="noreferrer">照片来源与署名 ↗</a></small>`:''}${p.id==='forbidden'?'<button class="secondary-button" data-inspect="hall">走近太和殿 · 查看建筑细节 ↗</button>':''}<div class="coordinate"><span>${p.lat.toFixed(4)}° N / ${p.lon.toFixed(4)}° E</span><a href="${p.source}" target="_blank" rel="noreferrer">地图点位 ↗</a></div>`;
  panel.querySelector('.close').onclick=()=>{selected=null;renderPlaceInfo();updatePinState();needsRedraw=true;};
}
function updatePinState(){
  $$('[data-stop]').forEach(el=>el.classList.toggle('active',el.dataset.stop===selected));
  for(const {p,el} of labels){const index=metrics.stops.indexOf(p.id);el.classList.toggle('route-pin',index>=0);el.classList.toggle('selected',p.id===selected);el.setAttribute('aria-pressed',String(draft.includes(p.id)));el.querySelector('.pin-dot').textContent=index>=0?index+1:'';el.setAttribute('aria-label',`${index>=0?`路线第${index+1}站，`:''}查看${p.name}${draft.includes(p.id)?'，已加入当天行程':''}`);}
}

function registerPin(p){
  const b=document.createElement('button');b.className='map-pin'+(p.custom?' custom-pin':'');b.dataset.place=p.id;
  const dot=document.createElement('span');dot.className='pin-dot';
  const name=document.createElement('span');name.className='pin-name';name.textContent=p.name;
  if(guideCues[p.id]){const cue=document.createElement('small');cue.className='pin-cue';cue.textContent=guideCues[p.id];name.append(cue);}
  b.append(dot,name);b.onclick=()=>selectPlace(p.id);$('#labels').appendChild(b);labels.push({p,el:b});
}
function openCustomPlace(){
  if(!ready){toast('地图加载完成后即可添加地标');return;}
  $('#route-panel').classList.remove('open');$('#custom-place-form').reset();$('#custom-error').textContent='';
  $('#custom-position-hint').textContent='在地图上点选，或直接填写下方经纬度（WGS84）。';
  $('#custom-place-dialog').showModal();$('#custom-name').focus();
}
function startPicking(){
  pickPointers.clear();pickDown=null;
  $('#custom-place-dialog').close();selected=null;renderPlaceInfo();updatePinState();flight=null;
  picking=true;stage.classList.add('picking');$('#pick-banner').hidden=false;$('#layers').hidden=true;$('#settings-toggle').setAttribute('aria-expanded','false');needsRedraw=true;canvas.focus();
}
function finishPicking(){
  pickPointers.clear();pickDown=null;
  picking=false;stage.classList.remove('picking');$('#pick-banner').hidden=true;
  $('#custom-place-dialog').showModal();needsRedraw=true;
}
function saveCustomPlace(e){
  e.preventDefault();
  const p=customPlace({id:`user-${crypto.randomUUID()}`,name:$('#custom-name').value,lon:Number($('#custom-lon').value),lat:Number($('#custom-lat').value),note:$('#custom-note').value});
  if(!p){$('#custom-error').textContent='请填写地标名称，并选择当前地图范围内的位置。';return;}
  data.places.push(p);places[p.id]=p;if(!data.categories.includes('我的地标'))data.categories.push('我的地标');registerPin(p);
  $('#custom-place-dialog').close();setDraft([...draft,p.id],`已添加「${p.name}」并加入当天路线`);
  showTab('plan');fitPoints(draft);needsRedraw=true;
}

let screenPins=[], screenLegs=[];
const projected=new THREE.Vector3();
const intersects=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
function project(p){projected.set(p.x,ANCHOR_HEIGHT,-p.y).project(camera);return {x:(projected.x*.5+.5)*stage.clientWidth,y:(-.5*projected.y+.5)*stage.clientHeight,z:projected.z};}
function rectOf(element){const r=element.getBoundingClientRect(),s=stage.getBoundingClientRect();return {left:r.left-s.left-5,right:r.right-s.left+5,top:r.top-s.top-5,bottom:r.bottom-s.top+5};}
function updateOverlay(){
  const w=stage.clientWidth,h=stage.clientHeight;
  overlay.setAttribute('viewBox',`0 0 ${w} ${h}`);
  const points=new Map(data.places.map(p=>[p.id,project(p)]));
  const occupied=[rectOf($('#route-hud')),rectOf($('.map-tools')),rectOf($('#atlas-tour-strip'))];
  if(!$('#palace-inspector').hidden)occupied.push(rectOf($('#palace-inspector')));
  if(!$('#place-info').hidden)occupied.push(rectOf($('#place-info')));
  const inFrame=r=>r.left>4&&r.right<w-4&&r.top>3&&r.bottom<h-7;
  const pinPoints=new Map(points),pinLeaders=[],placed=[];
  // Separate nearby numbered buttons in screen space, with a leader back to the
  // unchanged geographic anchor. This keeps short legs selectable on a phone.
  for(const id of metrics.stops){
    const anchor=points.get(id);let pt={...anchor};
    if(placed.some(p=>Math.hypot(p.x-pt.x,p.y-pt.y)<29)){
      let found=false;
      for(const radius of [29,42,58,74]){
        for(const angle of [Math.PI,0,-Math.PI/2,Math.PI/2,-Math.PI/4,Math.PI*.75]){
          const candidate={x:anchor.x+Math.cos(angle)*radius,y:anchor.y+Math.sin(angle)*radius,z:anchor.z};
          if(candidate.x>16&&candidate.x<w-16&&candidate.y>16&&candidate.y<h-16&&!placed.some(p=>Math.hypot(p.x-candidate.x,p.y-candidate.y)<29)){pt=candidate;found=true;break;}
        }if(found)break;
      }
    }
    pinPoints.set(id,pt);placed.push(pt);
    occupied.push({left:pt.x-16,right:pt.x+16,top:pt.y-16,bottom:pt.y+16});
    if(pt.x!==anchor.x||pt.y!==anchor.y)pinLeaders.push(`<path d="M${anchor.x},${anchor.y}L${pt.x},${pt.y}" stroke="${routeColor()}" stroke-width="1" stroke-dasharray="2 2"/><circle cx="${anchor.x}" cy="${anchor.y}" r="2.5" fill="${routeColor()}" stroke="white" stroke-width="1"/>`);
  }
  const sorted=[...labels].sort((a,b)=>{
    const priority=p=>p.id===selected?-100:metrics.stops.includes(p.id)?metrics.stops.indexOf(p.id)-50:0;
    return priority(a.p)-priority(b.p);
  });
  screenPins=[];screenLegs=[];
  for(const {p,el} of sorted){
    const pt=pinPoints.get(p.id), index=metrics.stops.indexOf(p.id), onRoute=index>=0;
    const visible=pt.z>-1&&pt.z<1&&pt.x>8&&pt.x<w-8&&pt.y>10&&pt.y<h-16;
    el.hidden=!visible;if(!visible)continue;
    el.style.left=pt.x+'px';el.style.top=pt.y+'px';el.style.zIndex=p.id===selected?50:onRoute?20:1;
    const name=el.querySelector('.pin-name');
    const hasCue=onRoute&&!!guideCues[p.id]&&w>=600;
    el.classList.toggle('with-cue',hasCue);
    // Measure once per responsive/style state; approximate character widths clip
    // longer captions and leave distance badges underneath their yellow footer.
    const measureKey=`${onRoute}/${hasCue}/${w<600}/${w<760}`;
    if(name.dataset.measureKey!==measureKey){
      const hidden=name.hidden;name.hidden=false;
      name._atlasSize={width:name.offsetWidth+6,height:name.offsetHeight+6};
      name.hidden=hidden;name.dataset.measureKey=measureKey;
    }
    const labelWidth=name._atlasSize.width,labelHeight=name._atlasSize.height;
    let positions=[[18,-10],[-labelWidth-18,-10],[-labelWidth/2,-labelHeight-18],[-labelWidth/2,18],[18,-36],[-labelWidth-18,19],[-labelWidth-36,-labelHeight/2],[36,-labelHeight-24],[-labelWidth-36,-labelHeight-24],[36,36],[-labelWidth-36,36],[-labelWidth/2,-labelHeight-65]];
    let chosen=null;
    if(onRoute||p.id===selected||(showNames&&(innerWidth>=760||!metrics.stops.length))){
      for(const [dx,dy] of positions){const rect={left:pt.x+dx,top:pt.y+dy,right:pt.x+dx+labelWidth,bottom:pt.y+dy+labelHeight};if(inFrame(rect)&&!occupied.some(r=>intersects(rect,r))){chosen={dx,dy,rect};break;}}
    }
    // Route numbers remain visible even when dense labels cannot fit at this zoom.
    name.hidden=!chosen;
    if(chosen){
      name.style.left=chosen.dx+12+'px';name.style.top=chosen.dy+12+'px';occupied.push(chosen.rect);
      if(onRoute){const x=Math.max(chosen.rect.left,Math.min(chosen.rect.right,pt.x)),y=Math.max(chosen.rect.top,Math.min(chosen.rect.bottom,pt.y));
        pinLeaders.push(`<path d="M${pt.x},${pt.y}L${x},${y}" stroke="white" stroke-width="3"/><path d="M${pt.x},${pt.y}L${x},${y}" stroke="${routeColor()}" stroke-width="1"/>`);}
    }
    if(onRoute||p.id===selected)occupied.push({left:pt.x-15,right:pt.x+15,top:pt.y-15,bottom:pt.y+15});
    screenPins.push({p,index,pt,anchor:points.get(p.id),label:chosen});
  }
  const paths=[],badges=[];
  for(const leg of metrics.legs){
    const a=points.get(leg.from.id),b=points.get(leg.to.id);
    if(a.z<=-1||a.z>=1||b.z<=-1||b.z>=1)continue;
    const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy),nx=-dy/(len||1),ny=dx/(len||1);
    const actual=travel?.forLeg(leg.index-1);
    if(actual?.hasPath){
      for(const segment of actual.modelPaths){const pts=segment.points.map(project);const d=pts.map((p,i)=>`${i?'L':'M'}${p.x.toFixed(2)},${p.y.toFixed(2)}`).join('');paths.push(`<path d="${d}" fill="none" stroke="white" stroke-width="8"/><path d="${d}" fill="none" stroke="${routeColor()}" stroke-width="4" ${segment.kind==='walking'&&travel.mode==='transit'?'stroke-dasharray="5 4"':''}/>`);}
    }else paths.push(`<path class="route-segment" d="M${a.x},${a.y}L${b.x},${b.y}" stroke="white" stroke-width="8"/><path class="route-segment" d="M${a.x},${a.y}L${b.x},${b.y}" stroke="${routeColor()}" stroke-width="4" stroke-dasharray="9 5"/>`);
    if(len>65&&!actual?.hasPath){const ax=a.x+dx*.68,ay=a.y+dy*.68,ux=dx/len,uy=dy/len;paths.push(`<path d="M${ax-ux*5+nx*3},${ay-uy*5+ny*3}L${ax},${ay}L${ax-ux*5-nx*3},${ay-uy*5-ny*3}" stroke="white" stroke-width="1.5" fill="none"/>`);}
    if(w<600)continue; // Small screens keep distances in the ordered route panel, not detached map badges.
    const text=`${leg.index}→${leg.index+1} · ${actual?'道路':'直线'} ${formatDistance(actual?.distance??leg.meters)}`,bw=innerWidth<760?116:132,bh=23;
    let chosen=null;
    for(const f of [.5,.38,.62,.2,.8]){
      for(const offset of [18,-18,38,-38,58,-58,80,-80,104,-104,136,-136,168,-168]){
        const x=a.x+dx*f+nx*offset,y=a.y+dy*f+ny*offset;
        const r={left:x-bw/2,right:x+bw/2,top:y-bh/2,bottom:y+bh/2};
        if(inFrame(r)&&!occupied.some(q=>intersects(r,q))){chosen={x,y,r,mx:a.x+dx*f,my:a.y+dy*f};break;}
      }if(chosen)break;
    }
    // A distance is never discarded solely because of collision: use the nearest
    // in-frame midpoint as a fallback; the ordered sidebar also lists every leg.
    if(!chosen){const mx=(a.x+b.x)/2,my=(a.y+b.y)/2;if(mx<0||mx>w||my<0||my>h)continue;const x=Math.max(bw/2+5,Math.min(w-bw/2-5,mx)),y=Math.max(bh/2+5,Math.min(h-bh/2-5,my+20));chosen={x,y,mx,my,r:{left:x-bw/2,right:x+bw/2,top:y-bh/2,bottom:y+bh/2}};}
    occupied.push(chosen.r);
    const {x,y,mx,my}=chosen;
    badges.push(`<g data-leg="${leg.index}"><path d="M${mx},${my}L${x},${y}" stroke="${routeColor()}" stroke-opacity=".48" stroke-width="1"/><rect x="${x-bw/2}" y="${y-bh/2}" width="${bw}" height="${bh}" rx="5" fill="#fff2b9" stroke="${routeColor()}" stroke-opacity=".23" stroke-width=".7"/><text class="route-distance" x="${x}" y="${y+3.5}" text-anchor="middle" style="fill:${routeColor()}">${text}</text></g>`);
    screenLegs.push({leg,a,b,...chosen});
  }
  overlay.innerHTML=paths.join('')+pinLeaders.join('')+badges.join('');
  $('#compass-needle').style.transform=`rotate(${-controls.getAzimuthalAngle()*180/Math.PI}deg)`;
  $('#map-scale').textContent=metrics.stops.length>1?`${metrics.legs.length} 段 · ${travel?.legs.some(l=>l.route?.hasPath)?'百度路线 / 未计算段为直线':'直线示意'}`:'景点代表点 · WGS84';
}
function render(t){
  requestAnimationFrame(render);if(document.hidden)return;
  if(flight){if(flight.previous)flight.samples.push(t-flight.previous);flight.previous=t;let u=Math.min(1,(t-flight.start)/850);u=u*u*(3-2*u);controls.target.lerpVectors(flight.fromTarget,flight.toTarget,u);camera.position.lerpVectors(flight.fromPosition,flight.toPosition,u);camera.zoom=THREE.MathUtils.lerp(flight.fromZoom,flight.toZoom,u);camera.updateProjectionMatrix();if(u>=1){if(new URLSearchParams(location.search).has('qa')&&flight.samples.length){const gaps=[...flight.samples].sort((a,b)=>a-b);console.info('Atlas camera transition',JSON.stringify({frames:gaps.length,medianMs:Math.round(gaps[Math.floor(gaps.length/2)]),fps:Math.round(1000/gaps[Math.floor(gaps.length/2)])}));}flight=null;}needsRedraw=true;}
  controls.update();camera.updateMatrixWorld();if(palace?.update(t))needsRedraw=true;if(routeLandmarks?.update(t))needsRedraw=true;if(urban?.update(t))needsRedraw=true;if(atlasStyle?.update(camera,stage))needsRedraw=true;
  if(enhancedRenderer.updateQuality(t))needsRedraw=true;
  if(!needsRedraw)return;needsRedraw=false;updateSun();
  enhancedRenderer.render((!!palace?.near&&palace.coverage.value===1)||!!routeLandmarks?.near||!!urban?.near);if(data)updateOverlay();
}
requestAnimationFrame(render);

let toastTimer;
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3200);}
async function copyPlan(){
  const m=routeMetrics(draft,places);
  const text=[`${day} · 北京一日行程`,...m.stops.flatMap((id,i)=>[`${i+1}. ${places[id].name}${places[id].metro1?`（1号线 · ${places[id].metro1.station}站）`:''}`,...(i<m.legs.length?[`   ↓ 直线 ${formatDistance(m.legs[i].meters)}`]:[])]),`直线合计：${formatDistance(m.total)}`,'注：景点代表点之间的直线距离，非实际步行距离。'].join('\n');
  try{await navigator.clipboard.writeText(text);toast('已复制行程与每段直线距离');}catch{const blob=new Blob([text],{type:'text/plain;charset=utf-8'});download(blob,`北京行程_${day}.txt`);toast('已保存行程文本');}
}
function download(blob,filename){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
async function capture(){
  if(!ready)return;
  const trace=step=>{if(new URLSearchParams(location.search).has('qa'))console.info('Poster export:',step);};trace('start');
  const button=$('#capture');button.disabled=true;
  try{
    await document.fonts.ready;trace('fonts ready');
    const m=routeMetrics(metrics.stops,places), color=routeColor(),title=activeTitle(),date=day;
    const routePlaces=m.stops.map(id=>places[id]);
    const center=new THREE.Vector3();
    const framingPoints=routePlaces.map(p=>new THREE.Vector3(p.x,ANCHOR_HEIGHT,-p.y));
    // Include actual building envelopes, not just their representative route points.
    for(const p of routePlaces){
      const bounds=p.id==='forbidden'?palace?.manifest?.replacementBounds:routeLandmarks?.get(p.id)?.spec.bounds;
      if(bounds)for(const x of [bounds[0],bounds[2]])for(const y of [bounds[1],bounds[3]])framingPoints.push(new THREE.Vector3(x,0,-y));
    }
    if(framingPoints.length){
      const box=new THREE.Box3().setFromPoints(framingPoints);box.getCenter(center);center.y=0;
    }
    const exportCamera=camera.clone();Object.assign(exportCamera,{left:-63*960/1080,right:63*960/1080,top:63,bottom:-63,zoom:1});
    exportCamera.position.copy(center).add(new THREE.Vector3(6,80,185));exportCamera.lookAt(center);exportCamera.updateMatrixWorld();exportCamera.updateProjectionMatrix();
    if(routePlaces.length){
      const extent=framingPoints.map(p=>p.clone().project(exportCamera)).reduce((n,p)=>Math.max(n,Math.abs(p.x),Math.abs(p.y)),0);
      exportCamera.zoom=Math.min(9,.72/Math.max(extent,.01));exportCamera.updateProjectionMatrix();
    }
    const points=routePlaces.map(p=>{const v=new THREE.Vector3(p.x,ANCHOR_HEIGHT,-p.y).project(exportCamera);return {x:v.x*.5+.5,y:-v.y*.5+.5};});
    const map=document.createElement('canvas');map.width=1440;map.height=1620;
    const size=renderer.getSize(new THREE.Vector2()),ratio=renderer.getPixelRatio();
    const restoreLandmarks=await routeLandmarks?.preparePoster(m.stops);
    const restorePalace=m.stops.includes('forbidden')?await palace?.preparePoster():null;
    const restoreTrees=atlasStyle?.preparePoster();trace('models ready');
    try{
      fitSunToCamera(exportCamera,center);renderer.shadowMap.needsUpdate=true;
      renderer.setPixelRatio(1);renderer.setSize(map.width,map.height,false);renderer.render(scene,exportCamera);
      map.getContext('2d').drawImage(canvas,0,0);trace('map rendered');
    }finally{
      restoreLandmarks?.();restorePalace?.();restoreTrees?.();sun.userData.shadowKey=null;updateSun();renderer.setPixelRatio(ratio);renderer.setSize(size.x,size.y,false);needsRedraw=true;
      enhancedRenderer.render((!!palace?.near&&palace.coverage.value===1)||!!routeLandmarks?.near||!!urban?.near);
    }
    const complete=travel?.legs.length===m.legs.length&&m.legs.length>0&&travel.legs.every(l=>l.route?.hasPath);
    const actualRoutes=complete?travel.legs.map(l=>({distance:l.route.distance,duration:l.route.duration,paths:l.route.modelPaths.map(segment=>segment.points.map(p=>{const v=new THREE.Vector3(p.x,ANCHOR_HEIGHT,-p.y).project(exportCamera);return {x:v.x*.5+.5,y:-v.y*.5+.5};}))})):null;
    const out=makeRoutePoster({map,points,metrics:m,places,title,day:date,color,actualRoutes,guideCues});
    trace('layout ready');
    const blob=await new Promise(resolve=>out.toBlob(resolve,'image/png'));if(!blob)throw Error('图片生成失败');
    let dialog=$('#poster-preview');
    if(!dialog){dialog=document.createElement('dialog');dialog.id='poster-preview';document.body.append(dialog);}
    if(dialog.dataset.url)URL.revokeObjectURL(dialog.dataset.url);
    const url=URL.createObjectURL(blob);dialog.dataset.url=url;
    dialog.innerHTML=`<div class="poster-preview-bar"><div><strong>你的北京旅行海报</strong><small>1080 × ${out.height} · PNG · 手机可长按图片保存</small></div><button aria-label="关闭海报预览">×</button></div><img src="${out.toDataURL('image/png')}" alt="${esc(title)}竖版攻略海报"><a class="poster-download" href="${url}" download="${esc(`一日北京_竖版攻略_${title}_${date}.png`)}">下载海报 PNG ↓</a>`;
    dialog.querySelector('button').onclick=()=>dialog.close();dialog.showModal();trace('preview open');
    toast('竖版海报已生成，可预览后下载');
  }catch(e){console.error(e);toast('海报保存失败，请重试');}finally{button.disabled=false;}
}

// One event delegation path keeps map, list and itinerary edits identical.
document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b||b.disabled||!data)return;
  if(b.dataset.modelBack){$('#tour-model-info').hidden=true;selectPlace(b.dataset.modelBack,true);}
  if(b.dataset.landmark)inspectLandmark(b.dataset.landmark,b.dataset.modelView);
  if(b.dataset.inspect)inspectPalace(b.dataset.inspect);
  if(b.hasAttribute('data-close-inspector')){inspecting=false;$('#palace-inspector').hidden=true;needsRedraw=true;}
  if(b.dataset.tour)previewTour(b.dataset.tour);
  if(b.dataset.adopt)adoptTour(b.dataset.adopt);
  if(b.dataset.focus)selectPlace(b.dataset.focus,true);
  if(b.dataset.toggle)togglePlace(b.dataset.toggle);
  if(b.dataset.category){category=b.dataset.category;renderCatalog();}
  if(b.dataset.goto){showTab(b.dataset.goto);$('.panel-scroll').scrollTop=0;}
  if(b.dataset.move){const id=b.dataset.move,delta=Number(b.dataset.delta);setDraft(moveStop(draft,id,delta),'已调整景点顺序');requestAnimationFrame(()=>$(`[data-move="${id}"][data-delta="${delta}"]`)?.focus());}
  if(b.dataset.remove)setDraft(draft.filter(id=>id!==b.dataset.remove),'已移除景点');
  if(b.hasAttribute('data-clear'))setDraft([],'已清空当天行程');
  if(b.hasAttribute('data-undo'))undoDraft();
  if(b.hasAttribute('data-fit'))fitRoute();
  if(b.hasAttribute('data-copy'))copyPlan();
  if(b.hasAttribute('data-new-place'))openCustomPlace();
  if(b.hasAttribute('data-show-route')){setImmersive(false);$('#route-panel').classList.add('open');$('#plan-content').scrollTop=0;}
});
$('#route-panel-close').onclick=()=>$('#route-panel').classList.remove('open');
$('#custom-place-close').onclick=()=>$('#custom-place-dialog').close();
$('#custom-pick').onclick=startPicking;$('#cancel-pick').onclick=finishPicking;
$('#custom-place-form').onsubmit=saveCustomPlace;
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&picking){e.preventDefault();finishPicking();}});
const pickRay=new THREE.Raycaster(),pickPlane=new THREE.Plane(new THREE.Vector3(0,1,0),-ANCHOR_HEIGHT),pickPoint=new THREE.Vector3();
let pickDown=null;
const pickPointers=new Set();
canvas.addEventListener('pointerdown',e=>{
  if(!picking)return;pickPointers.add(e.pointerId);
  if(pickPointers.size===1&&e.button===0)pickDown={id:e.pointerId,x:e.clientX,y:e.clientY,dragged:false};
  else if(pickDown)pickDown.dragged=true;
});
canvas.addEventListener('pointermove',e=>{if(pickDown&&Math.hypot(e.clientX-pickDown.x,e.clientY-pickDown.y)>6)pickDown.dragged=true;});
canvas.addEventListener('pointercancel',e=>{pickPointers.delete(e.pointerId);pickDown=null;});
canvas.addEventListener('pointerup',e=>{
  pickPointers.delete(e.pointerId);const down=pickDown;pickDown=null;
  if(!picking||!down||down.id!==e.pointerId||down.dragged||pickPointers.size)return;
  const r=canvas.getBoundingClientRect();camera.updateMatrixWorld();
  pickRay.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);
  if(!pickRay.ray.intersectPlane(pickPlane,pickPoint)){toast('请点击地图中的城区位置');return;}
  const position=fromModelPosition(pickPoint.x,-pickPoint.z);
  if(!insideMap(position.lon,position.lat)){toast('请在当前北京核心城区模型范围内选点');return;}
  $('#custom-lon').value=position.lon.toFixed(6);$('#custom-lat').value=position.lat.toFixed(6);
  $('#custom-position-hint').textContent='已从地图选取位置，可再次选点或修改坐标。';
  finishPicking();if(!$('#custom-name').value)$('#custom-name').focus();
});
$$('[data-tab]').forEach(b=>b.onclick=()=>data&&showTab(b.dataset.tab));
$('.planner-tabs').onkeydown=e=>{const tabs=$$('[data-tab]'),i=tabs.indexOf(document.activeElement);if(i<0)return;let next;if(e.key==='ArrowRight')next=(i+1)%3;if(e.key==='ArrowLeft')next=(i+2)%3;if(e.key==='Home')next=0;if(e.key==='End')next=2;if(next!==undefined){e.preventDefault();tabs[next].focus();showTab(tabs[next].dataset.tab);}};
$('#trip-date').value=day;$('#trip-date').onchange=e=>data&&setDay(e.target.value);$('#today').onclick=()=>data&&setDay(localDay());
$$('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));
function setImmersive(on){$('.workspace').classList.toggle('atlas-immersive',on);$('#map-mode').textContent=on?'路线与攻略':'展开地图';$('#map-mode').setAttribute('aria-pressed',String(on));resize();needsRedraw=true;}
$('#map-mode').onclick=()=>{setImmersive(!$('.workspace').classList.contains('atlas-immersive'));fitRoute();};
$('#fit-route').onclick=fitRoute;$('#reset').onclick=()=>{selected=null;renderPlaceInfo();fitPoints([],true);};
$('#zoom-in').onclick=()=>zoom(1.25);$('#zoom-out').onclick=()=>zoom(.8);
$('#settings-toggle').onclick=()=>{const panel=$('#layers');panel.hidden=!panel.hidden;$('#settings-toggle').setAttribute('aria-expanded',String(!panel.hidden));};
$$('[data-layer]').forEach(input=>input.onchange=()=>{layers[input.dataset.layer]=input.checked;applyLayers();});
$('#height').oninput=e=>{height=Number(e.target.value);$('#height-value').textContent=height.toFixed(1)+'×';scaleBuildings();};
$('#toggle-labels').onchange=e=>{showNames=e.target.checked;needsRedraw=true;};
$('#capture').onclick=capture;
$('#about-open').onclick=()=>$('#about').showModal();$('#about-close').onclick=()=>$('#about').close();
$('#about').onclick=e=>{if(e.target===$('#about')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}};
canvas.addEventListener('keydown',e=>{if(['+','='].includes(e.key)){zoom(1.2);e.preventDefault();}if(e.key==='-'){zoom(1/1.2);e.preventDefault();}if(e.key==='Home'){fitRoute();e.preventDefault();}if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){flight=null;const d=4/camera.zoom;const v=new THREE.Vector3(e.key==='ArrowLeft'?-d:e.key==='ArrowRight'?d:0,0,e.key==='ArrowUp'?-d:e.key==='ArrowDown'?d:0);controls.target.add(v);camera.position.add(v);needsRedraw=true;e.preventDefault();}});
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();toast('图形连接中断，请刷新页面重新载入');});

async function init(){try{
  travel=new Travel({update:()=>{needsRedraw=true;if(data){renderHUD();renderPlan();}},apply:ids=>{setDraft(ids,'已采用交通顺序建议，可撤销');showTab('plan');fitPoints(draft);},add:poi=>{
    let p=data.places.find(p=>p.baiduUid&&p.baiduUid===poi.baiduUid);
    if(!p){p=customPlace({id:`user-${crypto.randomUUID()}`,name:poi.name.slice(0,60),lon:poi.lon,lat:poi.lat,note:poi.address,baiduUid:poi.baiduUid});if(!p){toast('该地点不在当前三维城区范围内');return;}data.places.push(p);places[p.id]=p;if(!data.categories.includes('我的地标'))data.categories.push('我的地标');registerPin(p);}
    setDraft([...draft,p.id],`已加入「${p.name}」`);fitPoints(draft);
  }});
  [data,meta]=await Promise.all(['tourism.json','metadata.json'].map(file=>fetch('public/assets/'+file+'?v=metro-20260929').then(r=>{if(!r.ok)throw Error('地图资料未找到');return r.json();})));
  let stored=null;
  try{stored=localStorage.getItem(STORAGE);}catch{$('#save-state').textContent='浏览器存储不可用，行程仅在当前页面保留';}
  data.places.push(...readCustomPlaces(stored));if(data.places.some(p=>p.custom))data.categories.push('我的地标');
  places=Object.fromEntries(data.places.map(p=>[p.id,p]));plans=readPlans(stored,places);
  draft=cleanStops(plans[day],places);if(draft.length){preview=null;currentTab='plan';}
  for(const p of data.places)registerPin(p);
  renderPanels();syncRoute();showTab(currentTab);
  $('#about-sources').innerHTML='<p>路线内容参考：<br>'+data.tours.map(t=>`<a href="${t.source}" target="_blank" rel="noreferrer">${t.sourceName}</a>`).join('<br>')+'</p>';
  const gltf=await new GLTFLoader().loadAsync('public/assets/beijing.glb',e=>{if(e.total)$('#progress').style.width=`${10+e.loaded/e.total*85}%`;});city=gltf.scene;
  city.traverse(o=>{if(!o.isMesh)return;o.castShadow=isBuilding(o.userData.layer||'')||o.userData.layer==='trees';o.receiveShadow=true;if(o.material){o.material.roughness=Math.max(o.material.roughness,.45);o.material.envMapIntensity=.3;}});
  scene.add(city);
  urban=new UrbanArchitecture({scene,city,camera,stage,invalidate:()=>{needsRedraw=true;renderer.shadowMap.needsUpdate=true;}});await urban.init();
  islandTerrain=new BeihaiTerrain({city});await islandTerrain.init();urban.landform=islandTerrain;
  const urbanGround=new UrbanGround({city});await urbanGround.init();
  const beihaiTemples=new BeihaiTemples({city});await beihaiTemples.init();urban.reconstruction=beihaiTemples;
  palace=new PalaceLOD({scene,camera,renderer,stage,city,invalidate:()=>needsRedraw=true,status:(text,kind)=>{const el=$('#detail-state');el.textContent=text;el.dataset.state=kind;el.hidden=kind==='hidden'||(kind==='ready'&&!inspecting);$('#palace-inspector').hidden=!inspecting||kind==='hidden'||kind==='error';}});
  await palace.init();
  routeLandmarks=new RouteLandmarks({scene,camera,renderer,stage,city,groundOffset:(x,y)=>islandTerrain.offset(x,y,true),invalidate:()=>needsRedraw=true});
  await routeLandmarks.init();
  palace.onPrepared=root=>routeLandmarks.installPalaceMasks(root);
  for(const root of palace.root.children)routeLandmarks.installPalaceMasks(root);
  atlasStyle=new CartographicStyle({scene,city,groundOffset:(x,y)=>islandTerrain.offset(x,y),landscapeUrl:urban.fillManifest?.landscape,landmarkMasks:[...routeLandmarks.entries.map(e=>e.spec.plantingPolygon?{polygon:e.spec.plantingPolygon}:e.spec.maskPolygon?{polygon:e.spec.maskPolygon}:(e.spec.plantingBounds||e.spec.bounds)),...(urban.manifest?.reconstructions||[]).map(e=>e.bounds),...(urban.manifest?.pavedCourtyards||[]).map(e=>e.bounds)],invalidate:()=>{needsRedraw=true;renderer.shadowMap.needsUpdate=true;}});await atlasStyle.init();
  stage.insertAdjacentHTML('beforeend','<div id="tour-model-info" class="tour-model-info" hidden></div>');
  if(routeLandmarks.entries.length)$('#about-sources').insertAdjacentHTML('beforeend','<p>地标模型：包含实景照片生成及照片参考建模，经 Blender 整理与渲染。<a href="public/assets/route-landmarks/attributions.html" target="_blank" rel="noreferrer">模型来源、照片署名与许可</a></p>');
  scaleBuildings();applyLayers();ready=true;syncRoute();fitPoints(metrics.stops);$('#loader').classList.add('loaded');$('#progress').style.width='100%';
  window.atlas={islandTerrain,urban,anchorHeight:ANCHOR_HEIGHT,scene,camera,controls,renderer,enhancedRenderer,city,meta,places,data,selectPlace,fitRoute,inspectPalace,inspectLandmark,palace,routeLandmarks,invalidate:()=>needsRedraw=true,
    get selected(){return selected;},get height(){return height;},
    get state(){return {day,draft:[...draft],preview,tourId,currentTab,picking,customCount:data.places.filter(p=>p.custom).length,active:metrics.stops.slice(),total:metrics.total,legs:metrics.legs.map(l=>({from:l.from.id,to:l.to.id,meters:l.meters})),visibleLegs:screenLegs.length,ready,animating:!!flight};}};
  const detail=new URLSearchParams(location.search).get('detail');
  if(['palace','hall','roof'].includes(detail))inspectPalace(detail);
  else if(routeLandmarks.get(detail))inspectLandmark(detail,new URLSearchParams(location.search).get('view')||'overview');
  if(new URLSearchParams(location.search).get('qa')==='urban'&&new URLSearchParams(location.search).get('district')==='temple'){
    const target=new THREE.Vector3(-6.3,.05,36.8);fly(target,target.clone().add(new THREE.Vector3(55,100,160)),65);
  }
  if(new URLSearchParams(location.search).get('qa')==='urban'&&new URLSearchParams(location.search).get('district')==='residential'){
    const target=new THREE.Vector3(31.0,.10,28.8);fly(target,target.clone().add(new THREE.Vector3(65,90,160)),80);
  }
}catch(e){console.error(e);$('#loading-text').textContent=`加载未完成：${e.message}`;$('#loader>span').textContent='请双击「打开北京地图.command」启动，或刷新页面重试';}}
init();
