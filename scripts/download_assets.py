#!/usr/bin/env python3
"""Fetch and verify the model/data release without credentials or third-party modules."""
import argparse,hashlib,json,pathlib,re,shutil,subprocess,tarfile,tempfile,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]

def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def repository(manifest,override):
 name=override or manifest.get('repository')
 if not name:
  remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()
  match=re.fullmatch(r'(?:https://github.com/|git@github.com:)([\w.-]+/[\w.-]+?)(?:\.git)?',remote)
  name=match[1]if match else None
 if not name or not re.fullmatch(r'[\w.-]+/[\w.-]+',name):raise ValueError('Cannot determine repository; pass --repo OWNER/NAME')
 return name

def install(bundle,archive):
 if digest(archive)!=bundle['sha256']:raise ValueError('Archive checksum mismatch: '+bundle['name'])
 expected={x['path']:x for x in bundle['files']}
 # Extract only manifest-listed regular files, never links, devices or traversal.
 with tempfile.TemporaryDirectory(prefix='atlas-extract-')as tmp:
  stage=pathlib.Path(tmp);seen=set()
  with tarfile.open(archive,'r:gz')as tar:
   for member in tar:
    if not member.isfile()or member.name not in expected:raise ValueError('Unexpected archive member: '+member.name)
    path=pathlib.PurePosixPath(member.name)
    if path.is_absolute()or '..'in path.parts or member.name in seen:raise ValueError('Unsafe or duplicate archive member')
    spec=expected[member.name]
    if member.size!=spec['bytes']:raise ValueError('File size mismatch: '+member.name)
    target=stage/path;target.parent.mkdir(parents=True,exist_ok=True)
    with tar.extractfile(member)as inp,target.open('wb')as out:shutil.copyfileobj(inp,out)
    if digest(target)!=spec['sha256']:raise ValueError('File checksum mismatch: '+member.name)
    seen.add(member.name)
  if seen!=set(expected):raise ValueError('Incomplete archive')
  for name in sorted(seen):
   target=ROOT/name
   if not target.resolve().is_relative_to(ROOT):raise ValueError('Destination escapes project root')
   target.parent.mkdir(parents=True,exist_ok=True)
   # Move through a same-directory temporary file for an atomic final rename.
   with tempfile.NamedTemporaryFile(dir=target.parent,delete=False)as out:
    with(stage/name).open('rb')as inp:shutil.copyfileobj(inp,out)
    staged=pathlib.Path(out.name)
   staged.replace(target)

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo');p.add_argument('--with-data',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--local-dir',type=pathlib.Path);a=p.parse_args()
 manifest=json.loads((ROOT/'assets-release.json').read_text())
 for b in manifest['bundles']:
  if b.get('optional')and not a.with_data:continue
  files=b['files'];present=all((ROOT/f['path']).is_file()and(ROOT/f['path']).stat().st_size==f['bytes']for f in files)
  if present and(not a.verify or all(digest(ROOT/f['path'])==f['sha256']for f in files)):
   print('已就绪：',b['name']);continue
  if a.local_dir:archive=a.local_dir/b['name'];install(b,archive)
  else:
   repo=repository(manifest,a.repo);url=f'https://github.com/{repo}/releases/download/{manifest["tag"]}/{b["name"]}'
   with tempfile.TemporaryDirectory(prefix='atlas-download-')as tmp:
    archive=pathlib.Path(tmp)/b['name'];print(f'正在下载 {b["name"]}（{b["bytes"]/1024/1024:.1f} MiB）',flush=True)
    req=urllib.request.Request(url,headers={'User-Agent':'Beijing3DTravelMap/1.0'})
    with urllib.request.urlopen(req,timeout=120)as inp,archive.open('wb')as out:shutil.copyfileobj(inp,out)
    install(b,archive)
  print('已校验并安装：',b['name'])
if __name__=='__main__':main()
