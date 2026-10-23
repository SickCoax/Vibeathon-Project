import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work'/'python_deps'))
sys.path.insert(0,str(ROOT))
from backend import app as module

class ProviderEndpointTests(unittest.TestCase):
 def setUp(self):
  self.client=module.app.test_client()
  self.env=patch.dict(os.environ,{'AI_BASE_URL':'https://example.test/v1beta/openai/','AI_MODEL':'gemini-3.5-flash-lite','AI_API_KEY':'test-only-not-a-real-key'})
  self.env.start()
  self.addCleanup(self.env.stop)
  self.payload={'text':'Can we move the launch by two days?','persona':'Executive / C-Level','length':'Keep original length','language':'Keep original language'}
 def fake(self,status=200,body=None):
  r=unittest.mock.Mock();r.status_code=status;r.ok=200<=status<300;r.json.return_value=body or {'choices':[{'message':{'content':'Please consider moving the launch by two days.'}}]};return r
 def test_success_is_valid_json_and_contains_real_provider_field(self):
  with patch.object(module.requests,'post',return_value=self.fake()) as post:
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.json['rewritten'],'Please consider moving the launch by two days.')
  self.assertEqual(response.json['original'],self.payload['text'])
  self.assertEqual(post.call_args.kwargs['json']['model'],'gemini-3.5-flash-lite')
  self.assertTrue(post.call_args.args[0].endswith('/chat/completions'))
 def test_missing_key_has_clear_json_error(self):
  with patch.dict(os.environ,{'AI_API_KEY':''}),patch.object(module.requests,'post') as post:
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,503);self.assertIn('AI_API_KEY',response.json['error']);post.assert_not_called()
 def test_invalid_credentials_are_distinguished(self):
  with patch.object(module.requests,'post',return_value=self.fake(401,{})):
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,502);self.assertIn('rejected AI_API_KEY',response.json['error'])
 def test_quota_exhaustion_is_distinguished(self):
  with patch.object(module.requests,'post',return_value=self.fake(429,{})):
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,503);self.assertIn('quota or rate limit',response.json['error'])
 def test_invalid_provider_response_is_not_reported_as_success(self):
  with patch.object(module.requests,'post',return_value=self.fake(200,{'choices':[]})):
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,502);self.assertIn('invalid response',response.json['error'])
 def test_connection_failure_is_distinguished(self):
  with patch.object(module.requests,'post',side_effect=module.requests.ConnectionError()):
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,502);self.assertIn('Could not reach',response.json['error'])
 def test_timeout_is_distinguished(self):
  with patch.object(module.requests,'post',side_effect=module.requests.Timeout()):
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,504);self.assertIn('timed out',response.json['error'])
 def test_non_json_provider_response_is_distinguished(self):
  fake=unittest.mock.Mock();fake.status_code=200;fake.ok=True;fake.json.side_effect=ValueError('bad json')
  with patch.object(module.requests,'post',return_value=fake):
   response=self.client.post('/api/transform',json=self.payload)
  self.assertEqual(response.status_code,502);self.assertIn('invalid response',response.json['error'])

if __name__=='__main__':unittest.main()
