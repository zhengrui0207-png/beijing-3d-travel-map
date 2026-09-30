"""Prepare the reviewable photo manifest and free Tripo dry runs. Never generates."""
import base64
import html
import json
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/route-landmarks'
OUT.mkdir(parents=True, exist_ok=True)
rows = json.loads((ROOT / 'data/landmark-references/selected.json').read_text())
plans = []
for row in rows:
    command = ['npx', 'tripo-cli@latest', 'make', row['input'], '--model', 'tripo-v3.1',
               '-p', 'face_limit=50000', '-p', 'texture_quality=detailed',
               '-p', 'texture=true', '-p', 'pbr=true',
               '-p', 'negative_prompt=people, pedestrians, vehicles, floating fragments',
               '--name', 'beijing-' + row['id'], '-o', 'public/assets/route-landmarks']
    result = subprocess.run(command + ['--dry-run', '--json'], cwd=ROOT,
                            capture_output=True, text=True, timeout=90)
    plan = json.loads(result.stdout)
    assert result.returncode == 0 and plan['valid'], (row['id'], result.stderr, plan)
    plans.append({'id': row['id'], 'command': command, 'dryRun': plan})
    print(row['id'], 'validated', flush=True)
(OUT / 'dry-run-plans.json').write_text(json.dumps(plans, ensure_ascii=False, indent=2))

e = html.escape
cards = []
for i, row in enumerate(rows, 1):
    encoded = base64.b64encode((ROOT / row['input']).read_bytes()).decode()
    cards.append(f'''<article><img src="data:image/jpeg;base64,{encoded}" alt="{e(row['name'])}实景参考">
    <div class="body"><small>{i:02d} / 实景参考 · 待生成</small><h2>{e(row['name'])}</h2>
    <p>建模主体：{e(row['subject'])}</p><p class="credit">摄影：{e(row['author'])}<br>
    许可：{e(row['license'])} · <a href="{e(row['page'], quote=True)}" target="_blank" rel="noopener">原始来源</a></p></div></article>''')
page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>北京旅游地图 · 17 处地标实景参考</title><style>
*{box-sizing:border-box}body{margin:0;background:#f0f3ee;color:#203b36;font:16px/1.65 system-ui,-apple-system,sans-serif}main{max-width:1380px;margin:auto;padding:48px 28px}header{max-width:960px;margin-bottom:32px}small{font-size:12px;letter-spacing:1px;color:#667a70}h1{font-size:clamp(28px,4vw,48px);line-height:1.25;margin:12px 0 22px}h2{font-size:21px;margin:8px 0}p{margin:8px 0}.budget{padding:22px;background:#dce9db;border-radius:14px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}article{background:white;border:1px solid #d9e0d7;border-radius:16px;overflow:hidden}img{display:block;width:100%;height:280px;object-fit:contain;background:#e6ebe3}.body{padding:20px}.credit{font-size:12px;color:#65746a;overflow-wrap:anywhere}a{color:#256e58}footer{margin-top:32px;color:#65746a}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){main{padding:28px 16px}.grid{grid-template-columns:1fr}img{height:290px}}
</style><main><header><small>BEIJING ATLAS / PHOTO TO 3D</small><h1>让旅游线路上的地标<br>有真实建筑的样子</h1><p>17 处新增地标的实景参考清单。故宫继续沿用现有精细模型。这里展示的是参考照片，尚未生成 3D 成品。</p><div class="budget"><strong>计划：17 个模型 × 约 40 积分 = 约 680 Tripo 积分</strong><p>Tripo v3.1 · 每个最多 50,000 三角面 · 高清 PBR 纹理 · GLB 输出<br>随后通过 Blender MCP 整理比例、制作 LOD、渲染检查并接入当前 3D 地图。</p></div><p>公园和街巷采用代表性建筑或街景片段。照片不可见的背面会由模型推断，并非测绘级还原；照片中的人物和车辆不作为建模目标。部分照片为历史影像，不代表当前所有店铺及广告外观。</p></header><section class="grid">''' + ''.join(cards) + '''</section><footer>保留原图作者、来源与许可。基于 CC BY-SA 素材形成的改编资产须保留相应署名与相同方式共享信息。生成失败或取消的任务按平台规则退还积分。</footer></main></html>'''
(OUT / 'reference-gallery.html').write_text(page)

lines = ['# 北京旅游地图：实景图生成 3D 计划', '',
         '状态：参考图和参数已准备，尚未提交付费生成。', '',
         '- 模型：CLI `tripo-v3.1` → API `v3.1-20260211`。',
         '- 参数：face_limit=50000，texture_quality=detailed，texture=true，pbr=true。',
         '- negative_prompt：people, pedestrians, vehicles, floating fragments。',
         '- 每次预计 40 积分（图片生成含纹理 30 + 高清纹理 10）；17 次约 680 积分。',
         '- 失败或取消的任务按平台规则退还积分；不自动追加付费重生成。',
         '- 公园/街区模型是代表性建筑或街景片段，不是完整景区测绘模型。',
         '- 故宫保留现有资产。', '', '## 按顺序调用的 API', '']
for i, (row, plan) in enumerate(zip(rows, plans), 1):
    lines += [f"{i}. POST `/v3/generation/image-to-model` — {row['name']} / {row['subject']}，输入 `{row['input']}`，以上参数，约 40 积分。"]
lines += ['', '## 交付文件与接入', '',
          '- 每个模型：`public/assets/route-landmarks/tripo-out/beijing-<id>-<task8>/model.glb`，以及生成预览与任务元数据。',
          '- Blender 场景和渲染：`output/route-landmarks/`；地图轻量 GLB、LOD 和署名信息：`public/assets/route-landmarks/`。',
          '- 由 Blender MCP 执行导入、比例/材质检查、LOD 处理及渲染；通过质量检查后接入当前地图。',
          '- 所有作者、许可、来源见 `data/landmark-references/selected.json`。',
          '- 免费参数验证结果见 `output/route-landmarks/dry-run-plans.json`。', '', '## 待确认后执行的命令', '']
for plan in plans:
    lines += ['```sh', shlex.join(plan['command'] + ['--yes']), '```', '']
(OUT / 'generation-plan.md').write_text('\n'.join(lines))
print('Gallery and plan saved. No paid generation submitted.', flush=True)
