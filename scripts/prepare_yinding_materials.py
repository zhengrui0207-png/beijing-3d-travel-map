"""Prepare synthesized stone grain and a three-glyph local font for Blender.
Requires Pillow, numpy and fontTools. No reference-photo pixels are reused.
"""
from pathlib import Path
from fontTools.ttLib import TTCollection
from fontTools import subset
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(20260930);h=rng.normal(0,1,(256,256));dy,dx=np.gradient(h)
normal=np.stack([-dx*.16,-dy*.16,np.ones_like(h)],axis=2);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
Image.fromarray(((normal+1)*127.5).astype('uint8')).save(ROOT/'public/assets/yinding-detail/stone-grain-normal.png')
fonts=TTCollection('/System/Library/Fonts/Supplemental/Songti.ttc').fonts
f=next(f for f in fonts if all(ord(ch)in f.getBestCmap()for ch in '銀錠橋'));sub=subset.Subsetter();sub.populate(text='銀錠橋');sub.subset(f);f.save('/tmp/yinding-inscription.ttf')
