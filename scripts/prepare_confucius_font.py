"""Prepare a user-provided CJK font for local Blender rebuilding; never bundle the font."""
import argparse
from pathlib import Path
from fontTools.ttLib import TTFont,TTCollection
p=argparse.ArgumentParser();p.add_argument('font',type=Path);a=p.parse_args()
fonts=TTCollection(str(a.font)).fonts if a.font.suffix.lower()=='.ttc' else [TTFont(str(a.font))]
for f in fonts:
 if all(ord(c)in f.getBestCmap()for c in '大成殿萬世師表'):
  out=Path(__file__).resolve().parents[1]/'output/confucius-detail/working-font.ttf';out.parent.mkdir(parents=True,exist_ok=True);f.save(out);print('Prepared working font; excluded from distribution.');break
else:raise SystemExit('Font lacks required CJK characters')
