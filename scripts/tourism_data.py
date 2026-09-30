"""Curated visitor stops, anchored to the same cached OSM dataset as the city."""
import json, pathlib, math
ROOT = pathlib.Path(__file__).resolve().parents[1]
candidates = json.loads((ROOT/'data/tourism-candidates.json').read_text())
meta = json.loads((ROOT/'public/assets/metadata.json').read_text())
existing = {p['id']: p for p in meta['landmarks']}
places = []
def add(id, name, category, description, osm=None, original=None, coords=None, tip=''):
    if original:
        p = existing[original]
        lon, lat = p['lon'], p['lat']
        source = f"https://www.openstreetmap.org/{p.get('osm_type','way')}/{p.get('osm_id','') }" if p.get('osm_id') else 'https://www.openstreetmap.org/#map=16/39.9164/116.3908'
    elif coords:
        lon, lat = coords
        source = f'https://www.openstreetmap.org/{osm[0]}/{osm[1]}'
    else:
        p = next(p for p in candidates if p['type'] == osm[0] and p['id'] == str(osm[1]))
        lon, lat = p['lon'], p['lat']
        source = f'https://www.openstreetmap.org/{osm[0]}/{osm[1]}'
    places.append(dict(id=id, name=name, category=category, description=description, tip=tip,
        lon=lon, lat=lat, x=(lon-116.415)*111320*math.cos(math.radians(39.915))/100,
        y=(lat-39.915)*111320/100, source=source))
add('tiananmen','天安门','古建园林','沿长安街看城楼，从这里向北展开中轴线的一天。', original='tiananmen',tip='城楼与广场的参观安排请分别查看官方预约信息。')
add('forbidden','故宫','古建园林','把时间留给宫殿、院落与红墙，从南向北慢慢看。', original='forbidden',tip='提前查看官方预约；午门进入，神武门方向离开后可接景山。')
add('jingshan','景山公园','公园湖泊','登高看故宫屋顶与中轴线，也适合在园中慢行。',osm=('way',29201967))
add('beihai','北海公园','公园湖泊','白塔、湖面与皇家园林，适合作为古城路线的湖畔一站。',original='beihai')
add('gongwang','恭王府','古建园林','走进王府院落与花园，再接什刹海附近的胡同。',osm=('way',26514871),tip='进入府邸前查看官方预约与开放安排。')
add('yonghe','雍和宫','古建园林','从古建与院落出发，串起国子监、五道营一带。',osm=('way',24825312))
add('guozijian','国子监','古建园林','在太学旧址与街边古树之间，读一段北京文脉。',osm=('way',30784273))
add('confucius','孔庙','古建园林','与国子监相邻，可以把两处院落安排在同一段行程。',osm=('way',24825402))
add('wudaoying','五道营胡同','胡同漫步','窄巷里的小店与咖啡，适合放慢步调逛一逛。',osm=('way',30662318))
add('beiluo','北锣鼓巷','胡同漫步','从胡同生活切入老城，可衔接钟鼓楼一带。',osm=('way',30784359))
add('nanluo','南锣鼓巷','胡同漫步','主巷与两侧支巷相连，适合按自己的节奏探索。',osm=('way',4922662))
add('bell','钟楼','古建园林','在钟鼓楼之间的开阔空间，感受老城的日常。',osm=('way',425993664))
add('drum','鼓楼','古建园林','中轴线北段的醒目地标，向南可接烟袋斜街。',osm=('way',267371087))
add('yandai','烟袋斜街','胡同漫步','沿斜街穿行，走向什刹海的水岸与巷口。',osm=('way',42676210))
add('shichahai','什刹海','公园湖泊','湖畔散步，看水面、街巷与岸边的老北京。',osm=('node',5196349279))
add('ditan','地坛公园','公园湖泊','古坛与树荫相伴，深秋可留意园内的银杏。',osm=('way',24825400),tip='赏秋看叶色与天气，路线不代表实时红叶或银杏状态。')
add('tiantan','天坛','古建园林','以祈年殿为地图锚点，在开阔园林中感受礼制建筑。',original='tiantan',tip='标注位于祈年殿附近，并非公园入口。')
add('qianmen','前门·正阳门','古建园林','看中轴南段的城门，再往大栅栏的街巷里走。',osm=('way',25109960),coords=(116.3915261,39.8991846286))
add('dashilan','大栅栏','胡同漫步','老字号与商业街巷汇在一起，可与前门连成一段。',osm=('node',4454758090))
add('dongjiao','东交民巷','胡同漫步','沿街看近代建筑外观，适合与前门一带组合。',osm=('way',24804550))
add('national','中国国家博物馆','艺术展馆','为馆藏与展览单独留出充裕时间。',osm=('relation',8607825),coords=(116.3956607588,39.9037097235),tip='展览、预约和开放时间以博物馆官方信息为准。')
add('zhongshan','中山公园','公园湖泊','故宫西南侧的一片园林，可以在中轴路线中留一段安静时光。',osm=('relation',9054321),coords=(116.3886139206,39.9093003426))
add('wangfujing','王府井大街','现代都市','在步行街逛店、休息，再去附近的美术馆或教堂。',osm=('way',33612197))
add('cathedral','王府井天主堂','古建园林','在街边广场看教堂立面，适合建筑主题散步。',osm=('way',85902975))
add('art','中国美术馆','艺术展馆','给艺术展览留一站，再沿老城街区慢行。',osm=('way',131710744),tip='具体展览和入馆要求请查看馆方最新信息。')
add('huguosi','护国寺街','胡同漫步','把老城小吃与街巷漫步，放进行程的中途休息。',osm=('way',30748909))
add('taoranting','陶然亭公园','公园湖泊','到城南看亭台、水面与园林，适合留一段完整的散步时间。',osm=('way',30784976))
add('ritan','日坛公园','公园湖泊','CBD 西侧的古坛绿地，让城市建筑路线多一点树荫。',osm=('way',24476204))
add('tuanjiehu','团结湖公园','公园湖泊','在东部城区的湖边稍作停留，可与三里屯组合。',osm=('way',233218915))
add('sanlitun','三里屯','现代都市','逛街、咖啡与现代建筑，适合作为东部城区的一站。',osm=('node',5174023921))
add('cctv','央视大楼','现代都市','从公共区域欣赏倾斜双塔与悬挑连环的外观。',original='cctv',tip='路线以建筑外观观赏为主，不代表可以进入办公区域。')
add('guomao','国贸·中国尊','现代都市','在国贸一带看北京天际线，感受与老城不同的尺度。',original='guomao',tip='标注为建筑位置，路线以周边公共区域观赏为主。')
tours = [
 dict(id='history', name='北京历史文化线',short='历史文化',en='THE IMPERIAL AXIS',color='#9d533e', motif='axis',duration='建议留出一整天',season='四季皆宜',
      description='从中轴宫城走到皇家园林。红墙之后，是山顶视野与湖畔的留白。',stops=['tiananmen','forbidden','jingshan','beihai','gongwang'],
      note='故宫需提前查看预约，建议按午门入、神武门出的方向参观。地图连线连接景点代表点，进出园门另行规划。',source='https://www.dpm.org.cn/Visit.html',sourceName='故宫博物院参观指南'),
 dict(id='citywalk',name='北京 Citywalk 线',short='Citywalk',en='HUTONGS & LAKES',color='#317989',motif='walk',duration='适合半天至一天',season='胡同 · 小店 · 湖边',
      description='从雍和宫附近钻进胡同，经过钟鼓楼，最后在什刹海水边歇一歇。',stops=['yonghe','guozijian','wudaoying','bell','drum','yandai','shichahai'],
      note='给小店、咖啡和支巷留点空白。路线参考北京旅游网的胡同漫步推荐，按地图景点重新编排。',source='https://www.visitbeijing.com.cn/article/4QCq4eBXC0I?device=amp',sourceName='北京旅游网 · 胡同 Citywalk'),
 dict(id='autumn',name='北京赏秋线',short='秋日漫游',en='GOLDEN BEIJING',color='#b77923',motif='autumn',duration='建议留出一整天',season='深秋参考 · 叶色随天气变化',
      description='银杏、古建、山顶与湖面，把北京的秋天串成一段慢行记忆。',stops=['ditan','yonghe','guozijian','jingshan','beihai'],
      note='以地坛银杏和古建园林为主题编排；跨片区可结合公共交通。赏秋受天气影响，请临行确认当季叶色。',source='https://www.beijing.gov.cn/renwen/rwzyd/xltj/202510/t20251028_4241972.html',sourceName='首都之窗 · 古建赏秋线路（2025）')
]
tours.append(json.loads((ROOT/'data/metro-tour.json').read_text()))
result = dict(places=places,tours=tours,categories=['全部','古建园林','胡同漫步','公园湖泊','艺术展馆','现代都市'],
    attribution='© OpenStreetMap contributors',coordinateSystem='WGS84',distanceMethod='Haversine / Earth radius 6371008.8 m',
    note='景点为代表点，并非入口。距离为相邻代表点之间的地表直线距离，不是步行或驾车里程。')
guides=json.loads((ROOT/'data/place-guides.json').read_text())
for place in places:
    place.update(guides.get(place['id'],{}))
result['guideNote']='建议时长与游览顺序为编辑建议，不含排队和交通；开放、预约与展览以官方当日信息为准。'
(ROOT/'public/assets/tourism.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(f'Created {len(places)} places and {len(tours)} routes')
