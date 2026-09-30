from pathlib import Path
from fontTools.ttLib import TTCollection
from fontTools import subset
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'data/tiananmen-banner.ttf'
text='中华人民共和国万岁世界人民大团结万岁'
fonts=TTCollection('/System/Library/Fonts/Supplemental/Songti.ttc').fonts
f=next(f for f in fonts if all(ord(ch) in f.getBestCmap() for ch in text));s=subset.Subsetter();s.populate(text=text);s.subset(f);f.save(out)
print(out)
