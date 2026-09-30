import importlib.util,pathlib,unittest,io,json
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('travel_api',ROOT/'travel_api.py');api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
class AdapterTests(unittest.TestCase):
 def test_210_is_actionable_and_does_not_echo_key(self):
  with patch.object(api,'provider_opener') as opener:
   opener.return_value.open.return_value.__enter__.return_value=io.StringIO(json.dumps({'status':210,'message':'APP IP校验失败'}))
   with self.assertRaises(api.TravelError)as error:api.query('/place/v2/search',{},'private-key-do-not-echo')
   self.assertEqual(error.exception.code,'IP_WHITELIST');self.assertIn('公网出口 IP',str(error.exception));self.assertNotIn('private-key',str(error.exception))
 def test_direct_transport_does_not_inherit_proxy(self):
  with patch.dict(api.os.environ,{},clear=True),patch.object(api.urllib.request,'build_opener')as build,patch.object(api.urllib.request,'ProxyHandler')as proxy:
   api.provider_opener();proxy.assert_called_once_with({});build.assert_called_once_with(proxy.return_value)
 def test_explicit_proxy_override(self):
  with patch.dict(api.os.environ,{'BAIDU_USE_SYSTEM_PROXY':'1'}),patch.object(api.urllib.request,'build_opener')as build:
   api.provider_opener();build.assert_called_once_with()
 def test_diagnostic_distinguishes_saved_key_from_working_service(self):
  with patch.object(api,'key',return_value='private-key-do-not-echo'),patch.object(api,'query',side_effect=api.TravelError('IP rejected','IP_WHITELIST')),patch.object(api,'provider_opener')as opener:
   opener.return_value.open.return_value.__enter__.return_value=io.BytesIO('当前 IP：8.8.8.8 来自于：中国'.encode())
   result=api.diagnostics();self.assertTrue(result['configured']);self.assertFalse(result['connected']);self.assertEqual(result['publicIpHint'],'8.8.8.8');self.assertNotIn('private-key',json.dumps(result));self.assertEqual(opener.return_value.open.call_args.args[0],'https://myip.ipip.net')
 def test_diagnostic_ip_lookup_failure_keeps_provider_error(self):
  with patch.object(api,'key',return_value='configured'),patch.object(api,'query',side_effect=api.TravelError('IP rejected','IP_WHITELIST')),patch.object(api,'provider_opener',side_effect=OSError()):
   result=api.diagnostics();self.assertEqual(result['code'],'IP_WHITELIST');self.assertNotIn('publicIpHint',result)
 def test_walking_units_and_path(self):
  r=api.normalize_route({'distance':840,'duration':720,'steps':[{'instruction':'<b>向东</b>步行','distance':840,'duration':720,'path':'116.4,39.9;116.401,39.901;bad'}]},'walking')
  self.assertEqual(r['duration'],720);self.assertEqual(r['distance'],840);self.assertEqual(len(r['steps'][0]['path']),2);self.assertEqual(r['steps'][0]['instruction'],'向东步行');self.assertEqual(r['transfers'],0)
 def test_transit_alternatives_not_extra_transfers(self):
  walk={'type':5,'distance':120,'duration':100,'instructions':'步行到站'}
  rail={'type':3,'distance':3000,'duration':600,'vehicle':{'type':1,'name':'地铁1号线','start_name':'王府井','end_name':'建国门','stop_num':3}}
  bus={'type':3,'vehicle':{'type':0,'name':'公交','start_name':'甲','end_name':'乙'},'distance':500,'duration':200}
  r=api.normalize_route({'distance':3740,'duration':1000,'steps':[[walk],[rail,rail],[bus],[walk]]},'transit')
  self.assertEqual(r['transfers'],1);self.assertEqual(r['walkingDistance'],240);self.assertEqual(len(r['steps']),4);self.assertEqual(r['steps'][1]['kind'],'subway');self.assertEqual(r['steps'][1]['boarding'],'王府井')
 def test_missing_numbers_are_not_zero(self):
  with self.assertRaises(api.TravelError):api.normalize_route({'steps':[]},'walking')
 def test_missing_ak_fails_explicitly(self):
  with patch.object(api,'key',return_value=''):
   with self.assertRaises(api.TravelError) as e:api.query('/x',{})
   self.assertEqual(e.exception.code,'NOT_CONFIGURED')
 def test_coordinate_validation(self):
  for p in [{'lat':float('nan'),'lon':116},{'lat':40,'lon':100},{}]:
   with self.assertRaises(api.TravelError):api.point(p)
 def test_request_coordinates_uid_and_cache(self):
  api.CACHE.clear();body={'from':{'lat':39.91,'lon':116.4,'baiduUid':'safe123'},'to':{'lat':39.92,'lon':116.41},'mode':'walking'}
  with patch.object(api,'key',return_value='local-test-key'),patch.object(api,'query',return_value={'result':{'routes':[{'distance':1234,'duration':900,'steps':[]}]}}) as query:
   api.route(body);api.route(body);self.assertEqual(query.call_count,1)
   params=query.call_args.args[1];self.assertEqual(params['coord_type'],'wgs84');self.assertEqual(params['ret_coordtype'],'gcj02');self.assertEqual(params['origin_uid'],'safe123')
if __name__=='__main__':unittest.main()
