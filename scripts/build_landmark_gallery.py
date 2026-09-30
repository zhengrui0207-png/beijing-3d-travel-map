import html
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/route-landmarks'
assets=json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())['assets']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Songti.ttc',27)
sheet=Image.new('RGB',(2400,((len(assets)+3)//4)*540),'#eef1eb');draw=ImageDraw.Draw(sheet)
cards=[]
for i,a in enumerate(assets):
    name=a['id']+'-blender.png';image=Image.open(OUT/name).convert('RGB');image.thumbnail((600,500))
    x=(i%4)*600;y=(i//4)*540;sheet.paste(image,(x,y));draw.text((x+20,y+504),a['name'],font=font,fill='#29483b')
    e=html.escape
    cards.append(f'<article><a href="../../?detail={a["id"]}"><img loading="lazy" src="{name}" alt="{e(a["name"])} Blender 渲染"></a><div><small>{e(a["methodLabel"])}</small><h2>{e(a["name"])}</h2><p>{e(a["subject"])}</p><a class="open" href="../../?detail={a["id"]}">进入地图 · 查看 3D ↗</a><details><summary>来源与模型说明</summary><p>{e(a["method"])}</p><p>摄影：{e(a["author"])} · {e(a["license"])}</p><a href="{e(a["source"],quote=True)}" target="_blank" rel="noreferrer">原图来源 ↗</a></details></div></article>')
sheet.save(OUT/'北京旅游地标_渲染总览.jpg',quality=92)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>北京旅游地图 · 3D 地标成果</title><style>
*{box-sizing:border-box}body{margin:0;background:#f1f4ee;color:#254035;font:16px/1.7 system-ui,-apple-system,sans-serif}main{max-width:1440px;margin:auto;padding:48px 28px}header{max-width:950px;margin-bottom:35px}h1{font-size:clamp(32px,4vw,50px);line-height:1.2;margin:12px 0 24px}h2{font-size:23px;margin:4px 0}p{margin:6px 0}small{font-size:12px;color:#65766a;letter-spacing:.6px}a{color:#2a6950}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}article{background:#fff;border:1px solid #dce2d8;border-radius:14px;overflow:hidden}article img{width:100%;display:block}article>div{padding:20px}details{font-size:12px;color:#637067;margin-top:18px}summary{cursor:pointer}details p{margin:12px 0}.open{display:inline-block;margin-top:12px}.facts{background:#dfeada;padding:20px;border-radius:12px;margin:20px 0}header>a{margin-right:20px}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){.grid{grid-template-columns:1fr}main{padding:28px 16px}}
</style><main><header><small>BEIJING ATLAS / BLENDER MCP</small><h1>把线路上的地标<br>带进 3D 地图</h1><p>新增 17 处景点模型，全部经 Blender MCP 整理、导出与渲染。四条主题路线中的 18 个景点均有 3D 表达，故宫与天安门保留原模型。</p><div class="facts"><strong>15 处图片转 3D + 2 处照片参考建模</strong><p>实际使用 640 Tripo 积分；34 个轻量 / 高清 GLB；近景按需加载，高清版按需加载。</p></div><p>天安门图片被平台审核拒绝，因此沿用现有模型；王府井生成只提取到护栏，未采用该结果，改用 Blender 钟楼街景示意，该次生成仍计费 40 积分。未追加付费重生成。</p><p>这些模型以实景照片为参考，背面、遮挡处和尺寸存在推断，部分街巷仍保留照片中的游客及背景痕迹，不能视为完整景区的测绘还原。</p><a href="../../">打开旅游地图 ↗</a><a href="reference-gallery.html">实景参考清单</a><a href="credits-ledger.json">逐项积分记录</a></header><section class="grid">'''+''.join(cards)+'</section></main></html>'
(OUT/'model-gallery.html').write_text(page)
print('Gallery and model render overview saved.')
