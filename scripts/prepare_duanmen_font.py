from pathlib import Path
from fontTools.ttLib import TTCollection
from fontTools import subset
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'data/duanmen-plaque.ttf'
text='端門'
fonts=TTCollection('/System/Library/Fonts/Supplemental/Songti.ttc').fonts
f=next(f for f in fonts if all(ord(ch) in f.getBestCmap() for ch in text));s=subset.Subsetter();s.populate(text=text);s.subset(f);f.save(out)
print(out)
