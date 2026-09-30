import http.server,json,os,pathlib,socketserver,webbrowser,threading,sys,secrets,urllib.parse
from travel_api import TravelError,key,save_key,route,search,diagnostics
ROOT=pathlib.Path(__file__).resolve().parent
TOKEN=secrets.token_urlsafe(32)
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def send_json(self,data,status=200):
        content=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    def local(self,mutation=False):
        host=self.headers.get('Host','')
        if host not in ['127.0.0.1:5198','localhost:5198']:raise TravelError('仅允许本机访问。','FORBIDDEN',403)
        if mutation and (self.headers.get('Origin') not in [None,'http://'+host] or self.headers.get('X-Atlas-Token')!=TOKEN):raise TravelError('页面已过期，请刷新后重试。','FORBIDDEN',403)
    def do_GET(self):
        path=urllib.parse.urlparse(self.path)
        if path.path.startswith('/api/'):
            try:
                self.local()
                if path.path=='/api/travel/status':return self.send_json({'configured':bool(key()),'token':TOKEN})
                raise TravelError('接口不存在。','NOT_FOUND',404)
            except TravelError as e:return self.send_json({'error':str(e),'code':e.code},e.status)
        # Serve only public deliverables, never source/config or dotfiles.
        decoded=urllib.parse.unquote(path.path)
        parts=pathlib.PurePosixPath(decoded).parts
        if '..' in parts or any(p.startswith('.') for p in parts) or not (decoded in ['/','/index.html'] or decoded.startswith(('/public/','/output/')) or decoded.endswith(('.blend','.png'))):
            return self.send_error(404)
        return super().do_GET()
    def do_POST(self):
        try:
            self.local(True)
            length=int(self.headers.get('Content-Length',0))
            if length<=0 or length>32000:raise TravelError('请求体过大或为空。','INVALID',400)
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):raise ValueError()
            if self.path=='/api/travel/config':save_key(body.get('ak'));return self.send_json({'configured':True})
            if self.path=='/api/travel/diagnostics':return self.send_json(diagnostics())
            if self.path=='/api/travel/route':return self.send_json(route(body))
            if self.path=='/api/travel/search':return self.send_json(search(body.get('query')))
            raise TravelError('接口不存在。','NOT_FOUND',404)
        except TravelError as e:self.send_json({'error':str(e),'code':e.code},e.status)
        except (ValueError,TypeError):self.send_json({'error':'请求格式错误。','code':'INVALID'},400)
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:self.send_json({'error':'服务处理失败，请稍后重试。','code':'INTERNAL'},500)
    def log_message(self,fmt,*args):
        # Access logs omit query strings and bodies, including search queries and AKs.
        if self.path.startswith('/api/'):return
        super().log_message(fmt,*args)
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer):
    daemon_threads=True;allow_reuse_address=True
if __name__=='__main__':
    try:server=Server(('127.0.0.1',5198),Handler)
    except OSError:raise SystemExit('地图服务已启动：http://127.0.0.1:5198')
    print('北京城市立体图册: http://127.0.0.1:5198',flush=True)
    if '--open' in sys.argv:threading.Timer(.4,lambda:webbrowser.open('http://127.0.0.1:5198')).start()
    server.serve_forever()
