"""Reusable textured tree for the illustrated atlas, authored in live Blender."""
import bpy, math, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
rng=random.Random(1908)
scene=bpy.data.scenes.new('Atlas botanical tree')
bpy.context.window.scene=scene

def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.9
 return m,p
leaf,p=material('Atlas textured leaves',(.65,.85,.45))
im=bpy.data.images.load(str(ROOT/'public/assets/palace/foliage.png'),check_existing=True)
tex=leaf.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
leaf.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);leaf.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
# Blender 5 exports alpha for the glTF material; the web renderer uses alphaTest.
bark,_=material('Atlas branching bark',(.14,.09,.045))
verts=[];faces=[];uvs=[];branches=[]
for z,r,n in [(.51,.53,9),(.79,.51,9),(1.02,.30,7)]:
 for i in range(n):
  a=i*math.tau/n+rng.uniform(-.25,.25)
  center=Vector((math.cos(a)*r,math.sin(a)*r,z+rng.uniform(-.045,.045)))
  normal=Vector((math.cos(a)*.72,math.sin(a)*.72,.65)).normalized()
  u=Vector((-math.sin(a),math.cos(a),0));v=normal.cross(u).normalized()
  size=rng.uniform(.56,.71)
  k=len(verts)
  for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:verts.append(tuple(center+(u*dx+v*dy)*size/2))
  faces.append((k,k+1,k+2,k+3));uvs.extend([(0,0),(1,0),(1,1),(0,1)])
  branches.append((Vector((0,0,z*.55)),center,.012))
me=bpy.data.meshes.new('Textured canopy');me.from_pydata(verts,[],faces);me.update()
uv=me.uv_layers.new(name='Leaf image')
for p0 in me.polygons:
 for li in p0.loop_indices:uv.data[li].uv=uvs[li]
me.materials.append(leaf);leaves=bpy.data.objects.new('Atlas foliage',me);scene.collection.objects.link(leaves)
verts=[];faces=[]
branches.insert(0,(Vector((0,0,0)),Vector((.015,0,.84)),.045))
for a,b,r in branches:
 axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u)
 k=len(verts);N=6
 for end,rad in [(a,r),(b,r*.35)]:
  for i in range(N):verts.append(tuple(end+rad*(u*math.cos(i*math.tau/N)+v*math.sin(i*math.tau/N))))
 for i in range(N):faces.append((k+i,k+(i+1)%N,k+(i+1)%N+N,k+i+N))
me=bpy.data.meshes.new('Branch network');me.from_pydata(verts,[],faces);me.update();me.materials.append(bark)
wood=bpy.data.objects.new('Atlas branches',me);scene.collection.objects.link(wood)
for p0 in me.polygons:p0.use_smooth=True
bpy.context.view_layer.update()
for o in scene.objects:o.select_set(True)
bpy.context.view_layer.objects.active=leaves
import io_scene_gltf2
formats=[x[0]for x in io_scene_gltf2.get_format_items(None,bpy.context)]
fmt=next(x for x in formats if x.upper()=='GLB')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/cartographic/botanical-tree.glb'),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False)
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_distance=3
  area.spaces.active.region_3d.view_location=(0,0,.6)
print({'scene':scene.name,'cards':25,'objects':len(scene.objects),'output':'botanical-tree.glb'})
