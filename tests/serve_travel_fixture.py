"""Explicit localhost-only UI fixture. No Baidu calls, keys, or production state."""
import sys,pathlib,json,time,urllib.parse
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import server,travel_api
class Fixture(server.Handler):
 def do_GET(self):
  if self.path.startswith('/api/travel/status'):return self.send_json({'configured':True,'token':'fixture-only'})
  if self.path=='/':
   html=(server.ROOT/'index.html').read_text().replace('一日北京 · 3D 旅行地图','测试夹具 · 非真实百度结果').replace('<body>','<body><div style="position:fixed;top:0;left:38%;z-index:9999;background:#ffecad;padding:5px">接口测试夹具 · 非真实百度结果</div>')
   body=html.encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
  super().do_GET()
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  if self.path.endswith('/route'):
   a,b=body['from'],body['to'];x,y=a['lon']+.006,a['lat']+.001;u,v=b['lon']+.006,b['lat']+.001
   path=f'{x},{y};{u},{y};{u},{v}'
   walking={'type':5,'distance':240,'duration':180,'instruction':'步行至上车站（测试）','instructions':'步行至上车站（测试）','path':path}
   rail={'type':3,'distance':2400,'duration':420,'instructions':'乘坐地铁（测试）','path':path,'vehicle':{'type':1,'name':'地铁1号线（测试）','start_name':'王府井站','end_name':'建国门站','direction_text':'往环球度假区方向','stop_num':3}}
   steps=[walking] if body['mode']=='walking' else [[walking],[rail],[{**walking,'instructions':'下车后步行到景点（测试）'}]]
   route=travel_api.normalize_route({'distance':900 if body['mode']=='walking' else 2880,'duration':800 if body['mode']=='walking' else 780,'steps':steps},body['mode'])
   return self.send_json({'routes':[route],'fetchedAt':int(time.time()),'provider':'fixture'})
  if self.path.endswith('/search'):return self.send_json({'places':[{'name':'测试酒店（仅用于验收）','uid':'fixtureHotel','address':'测试数据，不是真实商户','lon':116.406,'lat':39.921,'coordType':'gcj02'},{'name':'范围外测试','uid':'fixtureOutside','address':'范围外','lon':116.8,'lat':40.2,'coordType':'gcj02'}]})
  return self.send_json({'error':'Fixture does not accept credentials'},403)
print('UI TEST FIXTURE http://127.0.0.1:5199 (not live Baidu data)',flush=True)
server.Server(('127.0.0.1',5199),Fixture).serve_forever()
