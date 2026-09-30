import json,pathlib,urllib.request,concurrent.futures
root=pathlib.Path(__file__).resolve().parents[1]/'data/landmark-references'
def run(pair):
 pid,i=pair
 try:
  r=json.loads((root/(pid+'-candidates.json')).read_text())[i]
  req=urllib.request.Request(r['url'],headers={'User-Agent':'BeijingAtlas/1.0 reference research'})
  with urllib.request.urlopen(req,timeout=25) as f:body=f.read()
  (root/(pid+'-'+str(i)+'.jpg')).write_bytes(body);print(pid,i,len(body),flush=True)
 except Exception as e:print(pid,i,type(e).__name__,getattr(e,'code',''),flush=True)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,[('bell',0),('drum',2),('national',0),('zhongshan',0),('zhongshan',2),('wangfujing',2),('guomao',0),('cctv',0),('cctv',2),('yonghe',3),('wudaoying',1),('guozijian',2),('gongwang',3)]))
