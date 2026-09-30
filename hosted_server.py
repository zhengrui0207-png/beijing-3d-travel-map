"""Read-only public travel API; static files are served by Nginx."""
import http.server,json,os,secrets,socketserver,urllib.parse
from travel_api import TravelError,key,route,search
TOKEN=secrets.token_urlsafe(32)
ORIGIN=os.environ.get('ATLAS_PUBLIC_ORIGIN','https://airesumejob.xyz')
HOST=urllib.parse.urlsplit(ORIGIN).netloc
class Handler(http.server.BaseHTTPRequestHandler):
    def send_json(self,data,status=200):
        content=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status)
        for k,v in [('Content-Type','application/json; charset=utf-8'),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Content-Length',str(len(content)))]:self.send_header(k,v)
        self.end_headers();self.wfile.write(content)
    def check_request(self,mutation=False):
        if self.headers.get('Host')!=HOST:raise TravelError('请求域名无效。','FORBIDDEN',403)
        if self.headers.get('Origin') not in (None,ORIGIN):raise TravelError('请求来源无效。','FORBIDDEN',403)
        if mutation and (self.headers.get('Origin')!=ORIGIN or self.headers.get('X-Atlas-Token')!=TOKEN):raise TravelError('请刷新地图后重试。','FORBIDDEN',403)
    def do_GET(self):
        try:
            self.check_request()
            if self.path!='/api/travel/status':raise TravelError('接口不存在。','NOT_FOUND',404)
            self.send_json({'configured':bool(key()),'token':TOKEN,'readOnly':True})
        except TravelError as e:self.send_json({'error':str(e),'code':e.code},e.status)
    def do_POST(self):
        try:
            self.check_request(True)
            if self.path not in ('/api/travel/route','/api/travel/search'):raise TravelError('线上版本不支持修改服务配置。','FORBIDDEN',403)
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=32000:raise ValueError()
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError()
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):raise ValueError()
            self.send_json(route(body) if self.path.endswith('/route') else search(body.get('query')))
        except TravelError as e:self.send_json({'error':str(e),'code':e.code},e.status)
        except (ValueError,TypeError):self.send_json({'error':'请求格式错误。','code':'INVALID'},400)
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:self.send_json({'error':'出行服务暂时不可用。','code':'INTERNAL'},500)
    def log_message(self,*args):pass
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer):
    daemon_threads=True;allow_reuse_address=True
if __name__=='__main__':Server(('127.0.0.1',int(os.environ.get('ATLAS_PORT','5199'))),Handler).serve_forever()
