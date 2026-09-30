"""Server-only Baidu WebAPI adapter. Coordinates entering this API are WGS84."""
import ipaddress, json, math, os, pathlib, re, threading, time, urllib.parse, urllib.request
CONFIG = pathlib.Path.home()/'.config/beijing-atlas/baidu.json'
CACHE = {}; LOCK = threading.Lock(); UPSTREAM = threading.BoundedSemaphore(2)
class TravelError(Exception):
    def __init__(self,message,code='PROVIDER_ERROR',status=502):
        super().__init__(message);self.code=code;self.status=status

def provider_opener():
    # A changing proxy exit can invalidate a server AK's IP whitelist. Keep Baidu
    # on the server's direct route unless a deployment explicitly needs a proxy.
    if os.environ.get('BAIDU_USE_SYSTEM_PROXY') == '1':
        return urllib.request.build_opener()
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))

def diagnostics():
    result={'configured':bool(key()),'connected':False,
            'transport':'system-proxy' if os.environ.get('BAIDU_USE_SYSTEM_PROXY')=='1' else 'direct'}
    try:
        query('/place/v2/search',{'query':'天安门','region':'北京','output':'json','page_size':1})
        result.update(connected=True,message='百度地点检索验证成功。')
    except TravelError as e:
        result.update(code=e.code,message=str(e))
    if result.get('code')=='IP_WHITELIST':
        # This is a network diagnostic service, not a guarantee that policy-based
        # routing uses the same exit for every destination. Never send the AK.
        try:
            with provider_opener().open('https://myip.ipip.net',timeout=5) as response:
                text=response.read(2048).decode('utf-8')
            match=re.search(r'当前 IP[：:]\s*([0-9.]+)',text)
            if match:
                address=ipaddress.ip_address(match[1])
                if address.is_global:result['publicIpHint']=str(address)
        except Exception:pass
    return result

def key():
    if os.environ.get('BAIDU_MAP_AK'): return os.environ['BAIDU_MAP_AK'].strip()
    try:return json.loads(CONFIG.read_text()).get('ak','').strip()
    except (OSError,ValueError):return ''

def save_key(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}',value):
        raise TravelError('请输入有效的百度地图服务端 AK。','BAD_KEY',400)
    # Validate the requested service before persisting. Never expose the key in responses/logs.
    query('/place/v2/search',{'query':'天安门','region':'北京','city_limit':'true','page_size':1,'output':'json'},value)
    CONFIG.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(str(CONFIG),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    os.chmod(CONFIG,0o600)
    with os.fdopen(fd,'w') as f:json.dump({'ak':value},f)
    with LOCK:CACHE.clear()

def query(path,params,ak=None):
    ak=ak or key()
    if not ak:raise TravelError('尚未配置百度地图服务端 AK，请先连接出行服务。','NOT_CONFIGURED',503)
    url='https://api.map.baidu.com'+path+'?'+urllib.parse.urlencode({**params,'ak':ak})
    try:
        with UPSTREAM:
            with provider_opener().open(url,timeout=18) as r: data=json.load(r)
    except Exception:raise TravelError('百度服务暂时无法连接，请稍后重试。','NETWORK',502) from None
    status=data.get('status')
    if status!=0:
        if status==210:
            raise TravelError('百度 IP 白名单校验失败（210）。请在百度控制台为此服务端 AK 填写当前服务器的公网出口 IP；换网络或代理后需重新核对。不要填写 127.0.0.1 或内网地址。','IP_WHITELIST',502)
        if status==211:
            raise TravelError('百度 SN 签名校验失败（211）。当前服务使用 IP 白名单校验，请在控制台核对 AK 的校验方式。','SIGNATURE_REQUIRED',502)
        if status in [7,1001,1002,1003]:raise TravelError('这两个地点之间暂未找到可用方案，请调整点位或改用其他方式。','NO_ROUTE',422)
        raise TravelError(f'百度接口返回状态码 {status}，请检查 AK 的服务权限、IP 白名单及配额。','BAIDU_REJECTED',502)
    return data

def point(p):
    if not isinstance(p,dict):raise TravelError('地点格式错误。','INVALID',400)
    try: lon,lat=float(p['lon']),float(p['lat'])
    except (KeyError,ValueError,TypeError):raise TravelError('地点坐标不完整。','INVALID',400)
    if not math.isfinite(lon+lat) or not (115<=lon<=118 and 39<=lat<=42):raise TravelError('仅支持北京范围内的地点。','INVALID',400)
    return f'{lat:.6f},{lon:.6f}'

def number(n):
    try:n=float(n)
    except (TypeError,ValueError):return None
    return n if math.isfinite(n) and n>=0 else None

def clean(s):return re.sub('<[^>]*>','',str(s or ''))[:1200]
def path_points(path):
    if not isinstance(path,str):return []
    points=[]
    for item in path.split(';'):
        try:
            lng,lat=map(float,item.split(','))
            if math.isfinite(lng+lat) and 115<=lng<=118 and 39<=lat<=42:points.append([lng,lat])
        except (ValueError,TypeError):continue
    return points

def normalize_route(route,mode):
    distance,duration=number(route.get('distance')),number(route.get('duration'))
    if distance is None or duration is None:raise TravelError('百度方案缺少距离或耗时，请重试。','INCOMPLETE')
    steps=[]
    for group in route.get('steps',[]):
        # A nested step contains alternative vehicles for that leg, not extra transfers.
        step=group[0] if isinstance(group,list) and group else group
        if not isinstance(step,dict):continue
        v=step.get('vehicle') or {}; walking=mode=='walking' or str(step.get('type'))=='5'
        steps.append({'kind':'walking' if walking else ('subway' if str(v.get('type'))=='1' else 'bus'),
          'instruction':clean(step.get('instruction') or step.get('instructions')),
          'distance':number(step.get('distance')),'duration':number(step.get('duration')),
          'line':clean(v.get('name')),'direction':clean(v.get('direction_text')),
          'boarding':clean(v.get('start_name')),'alighting':clean(v.get('end_name')),
          'stops':number(v.get('stop_num')),'path':path_points(step.get('path'))})
    rides=[s for s in steps if s['kind']!='walking']
    walking=[s['distance'] for s in steps if s['kind']=='walking']
    return {'distance':distance,'duration':duration,'steps':steps,'transfers':max(0,len(rides)-1),
      'walkingDistance':sum(walking) if all(x is not None for x in walking) else None,
      'coordType':'gcj02','hasPath':any(len(s['path'])>=2 for s in steps)}

def route(body):
    mode=body.get('mode','walking')
    if mode not in ['walking','transit']:raise TravelError('不支持的出行方式。','INVALID',400)
    params={'origin':point(body.get('from')),'destination':point(body.get('to')),'coord_type':'wgs84','ret_coordtype':'gcj02','steps_info':1}
    for field,endpoint in [('origin_uid','from'),('destination_uid','to')]:
        uid=body[endpoint].get('baiduUid')
        if isinstance(uid,str) and re.fullmatch('[A-Za-z0-9_-]{1,100}',uid):params[field]=uid
    cache_key=(key(),mode,json.dumps(params,sort_keys=True))
    with LOCK:cached=CACHE.get(cache_key)
    if cached and time.time()-cached[0]<300:return cached[1]
    response=query('/directionlite/v1/'+mode,params)
    routes=[normalize_route(r,mode) for r in (response.get('result') or {}).get('routes',[])][:5]
    if not routes:raise TravelError('没有找到可用方案。','NO_ROUTE',422)
    result={'routes':routes,'provider':'百度地图','fetchedAt':int(time.time())}
    with LOCK:
        if len(CACHE)>500:CACHE.clear()
        CACHE[cache_key]=(time.time(),result)
    return result

def search(q):
    if not isinstance(q,str) or not 1<=len(q.strip())<=80:raise TravelError('请输入1至80字的地点名称。','INVALID',400)
    data=query('/place/v2/search',{'query':q.strip(),'region':'北京','city_limit':'true','page_size':10,'scope':1,'ret_coordtype':'gcj02ll','output':'json'})
    results=[]
    for r in data.get('results',[]):
        loc=r.get('location') or {}
        if number(loc.get('lng')) is None or number(loc.get('lat')) is None:continue
        results.append({'uid':str(r.get('uid',''))[:100],'name':str(r.get('name',''))[:100],
         'address':str(r.get('address',''))[:300],'lon':loc['lng'],'lat':loc['lat'],'coordType':'gcj02'})
    return {'places':results,'provider':'百度地图'}
