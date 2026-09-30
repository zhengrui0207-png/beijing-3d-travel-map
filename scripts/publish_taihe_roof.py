"""Publish inspected, locally converted CC BY roof assets and their attribution."""
import json, pathlib, shutil, struct
ROOT=pathlib.Path(__file__).resolve().parents[1]
WORK=ROOT/'.dream-loop/sketchfab'
BASE=ROOT/'public/assets/palace'
DEST=BASE/'taihe-roof'
DEST.mkdir(parents=True,exist_ok=True)
meta=json.loads((WORK/'converted/metadata.json').read_text())
stage=json.loads((WORK/'staging/replacement-staging.json').read_text())
credits=json.loads((WORK/'download-metadata.json').read_text())['asset']['extras']

def publish_glb(source,destination,level):
    data=source.read_bytes()
    magic,version,size,length,kind=struct.unpack_from('<5I',data)
    assert magic==0x46546c67 and version==2 and size==len(data) and kind==0x4e4f534a
    doc=json.loads(data[20:20+length])
    assert 'KHR_draco_mesh_compression' in doc.get('extensionsRequired',[])
    doc['asset']['extras']={**credits,'modifications':f'Uniform scale and georeferencing; {level} LOD; resized original textures; Draco quantization. See ATTRIBUTION.md.'}
    encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    encoded+=b' '*((-len(encoded))%4)
    tail=data[20+length:]
    result=struct.pack('<5I',magic,version,20+len(encoded)+len(tail),len(encoded),kind)+encoded+tail
    destination.write_bytes(result)
    return len(result)

lods={}
for level in ['preview','detail']:
    info=meta['lods'][level]
    count=publish_glb(WORK/'converted'/info['file'],DEST/f'{level}.glb',level)
    lods[level]={'url':f'taihe-roof/{level}.glb','bytes':count,'triangles':info['triangles'],'textureRGBABytesWithMipmaps':round(info['textureRGBABytesWithMipmaps']),'compression':info['compression']}
bound=meta['lods']['detail']['blenderBounds']
asset={'id':'taihe-roof','title':credits['title'],'author':'TRNKL','source':credits['source'],'license':'CC BY 4.0','licenseUrl':'https://creativecommons.org/licenses/by/4.0/','bounds':[bound[0][0],bound[0][1],bound[1][0],bound[1][1]],'lods':lods,'sourceSHA256':meta['sourceSHA256'],'uniformSourceToMapScale':meta['uniformSourceToMapScale'],'sourceToBlenderWorldMatrix':meta['sourceToBlenderWorldMatrix'],'limitations':meta['limitations']}
(DEST/'asset.json').write_text(json.dumps(asset,ensure_ascii=False,indent=2))
attribution=f'''# 太和殿上层屋顶 · 署名与修改记录

《[{credits['title']}]({credits['source']})》，作者 [TRNKL](https://sketchfab.com/123456abctongtong)，采用 [Creative Commons Attribution 4.0（CC BY 4.0）](https://creativecommons.org/licenses/by/4.0/) 许可。

原模型由用户从 Sketchfab 官方下载，核验日期2026年9月14日。原下载 SHA256：`{meta['sourceSHA256']}`。原始文件保留，不改变原许可。本项目不暗示作者为地图背书。

## 本地图的修改

- 根据主滴水瓦檐口宽度定位，进行平移、旋转和统一等比例缩放；没有单独拉伸高度或进深。转换矩阵见 asset.json。
- 将檐口宽从55.6602米映射为约59.9042米；保留源比例后的檐口深约27.833米。源模型进深比此前OSM简化屋顶窄，殿身与下层屋顶没有一并重制。
- 为衔接作者屋檐，仅将原有上层柱廊三层斗拱块下移0.23米，柱、梁、墙体及新屋顶不变。
- 近景保留3,343,228个三角面；中景减面至401,126个三角面。两级均保留作者的UV、材质和法线贴图引用。
- 近景主要屋面贴图缩为1024，其他缩为512；中景分别为512和256。图像重新编码并内嵌GLB，避免读取原始848MB包。
- 使用Draco压缩，位置20位、法线12位、UV14位量化。原始纹理和几何可从作者来源页获取。

## 作品范围与精度

署名仅对应太和殿上层屋顶。殿身、下层屋顶、台基、周边建筑及城市数据来自项目原有重建；地理数据独立署名 [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright)，ODbL 1.0。

这是作者制作的建筑模型，不是文物测绘或摄影测量数据。定位沿用地图的OSM参考及1.1米表现基面；三大殿连接台基沿用9米，和官方8.13米仍有0.87米差异，不宣称测绘级建筑还原。
'''
(DEST/'ATTRIBUTION.md').write_text(attribution)
live_path=BASE/'manifest.json'
backup=WORK/'manifest-before-external.json'
if not backup.exists():shutil.copy2(live_path,backup)
manifest=json.loads(live_path.read_text())
zone=next(z for z in manifest['zones'] if z['id']=='central')
for level in ['medium','high']:
    name=f'central-{level}-taihe-v2.glb'
    shutil.copy2(WORK/'staging'/f'central-{level}.glb',BASE/name)
    zone[level]=name;zone['lods'][level]=stage['zones'][0]['lods'][level]
micro=next(m for m in manifest['microTiles'] if m['id']=='roof-tiles-3-5')
shutil.copy2(WORK/'staging/roof-tiles-3-5.glb',BASE/'roof-tiles-3-5-taihe.glb')
micro.update(url='roof-tiles-3-5-taihe.glb',bytes=stage['microTiles'][0]['bytes'],drawCalls=2)
manifest['externalAssets']=[a for a in manifest.get('externalAssets',[])if a['id']!='taihe-roof']+[asset]
manifest['externalAssetNotes']='TRNKL CC BY4.0 upper roof replaces only source record 638449354 when loaded. Tagged original roof nodes remain a complete fallback. See taihe-roof/ATTRIBUTION.md.'
temporary=BASE/'manifest.json.tmp';temporary.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));temporary.replace(live_path)
print(json.dumps(lods,ensure_ascii=False,indent=2))
