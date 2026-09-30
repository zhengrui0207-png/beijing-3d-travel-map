#!/usr/bin/env python3
"""Package an existing complete atlas checkout; excludes keys, caches and generation jobs."""
import argparse,hashlib,io,json,pathlib,tarfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('destination',type=pathlib.Path);p.add_argument('--repo');p.add_argument('--tag',default='assets-2026-09-30');a=p.parse_args();src=a.source.resolve();a.destination.mkdir(parents=True,exist_ok=True)
 runtime=[p for p in(src/'public/assets').rglob('*')if p.is_file()and p.suffix.lower()in['.glb','.png','.jpg','.jpeg','.webp']and not any(x in p.parts for x in['tripo-out'])]
 data=[]
 for rel in['data/urban','data/urban-ground','data/terrain','data/tiles','data/osm_beijing.json','data/geometry.json']:
  root=src/rel
  data.extend([root]if root.is_file()else[p for p in root.rglob('*')if p.is_file()and p.suffix.lower()in['.json','.osm']])
 manifest={'repository':a.repo,'tag':a.tag,'bundles':[]}
 for name,files,optional in[('beijing-models.tar.gz',runtime,False),('beijing-geodata.tar.gz',data,True)]:
  target=a.destination/name;rows=[]
  with tarfile.open(target,'w:gz',compresslevel=3)as tar:
   for f in sorted(set(files)):
    rel=f.relative_to(src).as_posix();info=tar.gettarinfo(str(f),arcname=rel);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
    if rel=='data/urban/infill-detail/index.json':
     content=f.read_text().replace(str(src),'.').encode();info.size=len(content)
     tar.addfile(info,io.BytesIO(content));rows.append({'path':rel,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
    else:
     with f.open('rb')as stream:tar.addfile(info,stream)
     rows.append({'path':rel,'bytes':f.stat().st_size,'sha256':digest(f)})
  manifest['bundles'].append({'name':name,'optional':optional,'bytes':target.stat().st_size,'sha256':digest(target),'files':rows})
  print(name,len(rows),'files',target.stat().st_size,flush=True)
 (ROOT/'assets-release.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
