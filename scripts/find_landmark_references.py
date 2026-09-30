import urllib.request,urllib.parse,json,pathlib,concurrent.futures,re
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'data/landmark-references'
queries={'tiananmen':'Tiananmen gate front','jingshan':'Wanchun Pavilion','beihai':'Beihai white dagoba -Miaoying','gongwang':'Prince Gong Mansion','yonghe':'Yonghe temple pavilion','guozijian':'Biyong Guozijian','wudaoying':'Wudaoying Hutong','bell':'Beijing Bell Tower exterior','drum':'Beijing Drum Tower exterior','yandai':'Yandai Xiejie','shichahai':'Yinding Bridge','ditan':'Ditan altar','national':'National Museum of China exterior','zhongshan':'Altar of Land and Grain Beijing','wangfujing':'Wangfujing street','guomao':'China Zun','cctv':'CCTV Headquarters Beijing'}
def fetch(item):
 pid,q=item;params={'action':'query','format':'json','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':4,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':1000}
 url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)
 try:
  d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'BeijingAtlas/1.0 reference research'}),timeout=25));rows=[]
  for p in sorted(d.get('query',{}).get('pages',{}).values(),key=lambda p:p.get('index',0)):
   i=p['imageinfo'][0];m=i.get('extmetadata',{});rows.append({'title':p['title'],'url':i.get('thumburl',i['url']),'original':i['url'],'page':i['descriptionurl'],'license':m.get('LicenseShortName',{}).get('value',''),'licenseUrl':m.get('LicenseUrl',{}).get('value',''),'author':re.sub('<[^>]+>','',m.get('Artist',{}).get('value','')),'description':re.sub('<[^>]+>','',m.get('ImageDescription',{}).get('value',''))[:700]})
  (OUT/(pid+'-candidates.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(pid,json.dumps([r['title'] for r in rows],ensure_ascii=False),flush=True)
 except Exception as e:print(pid,type(e).__name__,getattr(e,'code',''),flush=True)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(fetch,queries.items()))
