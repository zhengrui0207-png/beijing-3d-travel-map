import http.client,json,threading,unittest
from unittest.mock import patch
import hosted_server as app
class HostedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=app.Server(('127.0.0.1',0),app.Handler);cls.thread=threading.Thread(target=cls.s.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.s.shutdown();cls.s.server_close()
 def request(self,path,body=None,**headers):
  c=http.client.HTTPConnection('127.0.0.1',self.s.server_port)
  h={'Host':app.HOST,'Content-Type':'application/json','Origin':app.ORIGIN,'X-Atlas-Token':app.TOKEN};h.update(headers)
  c.request('GET' if body is None else 'POST',path,None if body is None else json.dumps(body),h)
  r=c.getresponse();data=json.loads(r.read());status=r.status;c.close();return status,data
 def test_status_has_no_secret(self):
  with patch.object(app,'key',return_value='secret-should-never-leak'):
   status,data=self.request('/api/travel/status');self.assertEqual(status,200);self.assertTrue(data['readOnly']);self.assertNotIn('secret-should-never-leak',json.dumps(data))
 def test_configuration_cannot_be_changed(self):
  for p in ['config','diagnostics']:
   self.assertEqual(self.request('/api/travel/'+p,{})[0],403)
 def test_rejects_cross_origin_and_wrong_host_and_token(self):
  for h in [{'Origin':'https://evil.test'},{'Host':'evil.test'},{'X-Atlas-Token':'wrong'}]:self.assertEqual(self.request('/api/travel/search',{'query':'hotel'},**h)[0],403)
 def test_search_and_route_dispatch(self):
  with patch.object(app,'search',return_value={'places':[]}) as search:
   self.assertEqual(self.request('/api/travel/search',{'query':'故宫'})[0],200);search.assert_called_once_with('故宫')
  with patch.object(app,'route',return_value={'routes':[]}) as route:
   self.assertEqual(self.request('/api/travel/route',{'mode':'walking'})[0],200);route.assert_called_once_with({'mode':'walking'})
 def test_invalid_body_and_source_are_not_served(self):
  self.assertEqual(self.request('/api/travel/search',[])[0],400)
  self.assertEqual(self.request('/travel_api.py')[0],404)
if __name__=='__main__':unittest.main()
