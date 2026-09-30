"""Separate the old Taihe upper roof into named fallback nodes, staging only.

Run with Blender --background --disable-autoexec --python this_file.py.
Reuses the existing builder definitions without executing its output pipeline.
No public asset, live manifest or native scene is replaced by this script.
"""
import ast
import hashlib
import json
import math
import pathlib
import random
import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / '.dream-loop/sketchfab/staging'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = 638449354
source_path = ROOT / 'scripts/build_palace.py'
source = source_path.read_text()
parsed = ast.parse(source)
layout = json.loads((ROOT / 'data/palace-layout.json').read_text())
manifest_path = ROOT / 'public/assets/palace/manifest.json'
live = json.loads(manifest_path.read_text())
affected = ['central-medium.glb', 'central-high.glb', 'roof-tiles-3-5.glb']
paths = [manifest_path, source_path] + [ROOT / 'public/assets/palace' / p for p in affected]
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
colors = next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'COLORS' for t in n.targets))
materials = {}
for name, (color, roughness) in colors.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = roughness
    m.diffuse_color = (*color, 1)
    m['uv_units'] = 'metres'
    m['appearance'] = 'artist-authored reconstruction'
    materials[name] = m

ns = {'bpy': bpy, 'math': math, 'random': random, 'Vector': Vector, 'MATERIALS': materials}
definitions = [n for n in parsed.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'prepare']
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(source_path), 'exec'), ns)
Batch = ns['Batch']
original_part = ns['build_part']
original_create = Batch.create

def split_part(batch, record, high):
    if record['id'] == SOURCE_ID:
        if not hasattr(batch, 'fallback'):
            batch.fallback = Batch()
        original_part(batch.fallback, record, high)
    else:
        original_part(batch, record, high)

def split_create(batch, zone, lod):
    objects = original_create(batch, zone, lod)
    if hasattr(batch, 'fallback'):
        fallback = original_create(batch.fallback, zone, lod)
        for obj in fallback:
            obj.name = f'taihe-roof-fallback/{lod}/{obj.data.materials[0].name}'
            obj['externalFallback'] = 'taihe-roof'
            obj['sourceRecordId'] = SOURCE_ID
        objects.extend(fallback)
    return objects

Batch.create = split_create
ns['build_part'] = split_part
data = dict(layout)
data['zones'] = {'central': layout['zones']['central']}
staged = {'zones': []}
ns.update(data=data, OUT=OUT, manifest=staged)
body = source[source.index('all_high=[]'):source.index('# Micro roof overlays:')]
exec(compile(body, str(source_path), 'exec'), ns)

audit = json.loads((ROOT / '.dream-loop/sketchfab/integration-audit.json').read_text())
chunk = next(c for c in audit['taiheMicroChunks'] if c['id'] == 'roof-tiles-3-5')
records = [r for r in layout['records'] if r['id'] in chunk['sourceRecordIds']]
assert {SOURCE_ID, 638449349, 8854351}.issubset({r['id'] for r in records})
batch = Batch()
batch.tiles_only = True
batch.fallback = Batch()
batch.fallback.tiles_only = True
for record in records:
    shape = record['tags'].get('roof:shape')
    height, bottom, rise = ns['part_elevations'](record)
    top = height + .011
    if shape:
        base = max(bottom, top - rise)
    else:
        shape = 'gabled' if record['w'] > 2 * record['d'] else 'hipped'
        rise = min(.07, max(.016, record['d'] * .32))
        base = top
    ns['build_roof'](batch.fallback if record['id'] == SOURCE_ID else batch, record, base, rise, shape, True)
objects = batch.create(chunk['id'], 'micro')
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:
    obj.select_set(True)
out = OUT / chunk['url']
bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', use_selection=True, export_extras=True, export_yup=True, export_apply=True, export_cameras=False, export_lights=False)
triangle_count = lambda obs: sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs)
staged['microTiles'] = [{**chunk, 'bytes': out.stat().st_size, 'triangles': triangle_count(objects), 'drawCalls': len(objects)}]
old_central = next(z for z in live['zones'] if z['id'] == 'central')
new_central = staged['zones'][0]
checks = []
for level in ['medium', 'high']:
    before = old_central['lods'][level]['triangles']
    after = new_central['lods'][level]['triangles']
    assert before == after, (level, before, after)
    checks.append({'asset': f'central-{level}.glb', 'trianglesBefore': before, 'trianglesAfter': after})
assert chunk['triangles'] == staged['microTiles'][0]['triangles']
checks.append({'asset': chunk['url'], 'trianglesBefore': chunk['triangles'], 'trianglesAfter': staged['microTiles'][0]['triangles']})
for path in paths:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == hashes[str(path.relative_to(ROOT))]
staged.update(sourceRecordId=SOURCE_ID, fallbackTag={'externalFallback': 'taihe-roof'}, sourceHashesSHA256=hashes, validation=checks, publicFilesUnchanged=True, activated=False)
(OUT / 'replacement-staging.json').write_text(json.dumps(staged, ensure_ascii=False, indent=2))
print('STAGED', json.dumps(checks), flush=True)
