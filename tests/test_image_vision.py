import base64
import json
import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'work' / 'python_deps'))
sys.path.insert(0, str(ROOT))
from backend import app as module


class ImageVisionEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = module.app.test_client()
        self.env = patch.dict(os.environ, {
            'AI_BASE_URL': 'https://example.test/v1beta/openai/',
            'AI_MODEL': 'gemini-3.5-flash-lite',
            'AI_API_KEY': 'test-only-not-a-real-key',
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.png = b'\x89PNG\r\n\x1a\n' + b'test-image-bytes'

    def fake(self, status=200, content=None):
        response = unittest.mock.Mock()
        response.status_code = status
        response.ok = 200 <= status < 300
        response.json.return_value = {'choices': [{'message': {'content': content or json.dumps({
            'summary': 'A red vehicle is parked beside a road.',
            'question_answer': 'The vehicle is red.',
        })}}]}
        return response

    def upload(self, image=None, question='What color is the vehicle?'):
        return self.client.post('/api/analyze-image', data={
            'image': (io.BytesIO(image or self.png), 'upload.png', 'image/png'),
            'question': question,
        }, content_type='multipart/form-data')

    def test_sends_actual_image_and_returns_grounded_fields(self):
        with patch.object(module.requests, 'post', return_value=self.fake()) as post:
            response = self.upload()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['image_summary'], 'A red vehicle is parked beside a road.')
        self.assertEqual(response.json['question_answer'], 'The vehicle is red.')
        body = post.call_args.kwargs['json']
        self.assertEqual(body['model'], 'gemini-3.5-flash-lite')
        self.assertEqual(body['response_format'], {'type': 'json_object'})
        content = body['messages'][1]['content']
        self.assertEqual(content[1]['type'], 'image_url')
        self.assertTrue(content[1]['image_url']['url'].startswith('data:image/png;base64,'))
        self.assertEqual(base64.b64decode(content[1]['image_url']['url'].split(',', 1)[1]), self.png)
        self.assertTrue(post.call_args.args[0].endswith('/chat/completions'))

    def test_accepts_supported_magic_signatures(self):
        cases = [
            (b"\x89PNG\r\n\x1a\nbody", 'image/png'),
            (b"\xff\xd8\xffbody", 'image/jpeg'),
            (b"RIFF\x00\x00\x00\x00WEBPbody", 'image/webp'),
        ]
        for image_bytes, mime in cases:
            with self.subTest(mime=mime), patch.object(module.requests, 'post', return_value=self.fake()) as post:
                response = self.upload(image=image_bytes, question='')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(post.call_args.kwargs['json']['messages'][1]['content'][1]['image_url']['url'].startswith(f'data:{mime};base64,'))

    def test_detects_actual_type_instead_of_trusting_extension(self):
        with patch.object(module.requests, 'post') as post:
            response = self.upload(image=b'not an image')
        self.assertEqual(response.status_code, 415)
        self.assertIn('not a supported', response.json['error'])
        post.assert_not_called()

    def test_rejects_oversized_image(self):
        with patch.object(module.requests, 'post') as post:
            response = self.upload(image=self.png + b'x' * (5 * 1024 * 1024))
        self.assertEqual(response.status_code, 413)
        post.assert_not_called()

    def test_question_length_is_validated(self):
        response = self.client.post('/api/analyze-image', data={
            'image': (io.BytesIO(self.png), 'upload.png', 'image/png'),
            'question': 'q' * 501,
        }, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)

    def test_missing_key_is_clear_and_does_not_call_provider(self):
        with patch.dict(os.environ, {'AI_API_KEY': ''}), patch.object(module.requests, 'post') as post:
            response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertIn('AI_API_KEY', response.json['error'])
        post.assert_not_called()

    def test_invalid_credentials_are_distinguished(self):
        with patch.object(module.requests, 'post', return_value=self.fake(401, '{}')):
            response = self.upload()
        self.assertEqual(response.status_code, 502)
        self.assertIn('rejected AI_API_KEY', response.json['error'])

    def test_dns_failure_is_explained_without_echoing_exception_details(self):
        error = module.requests.ConnectionError('NameResolutionError: private host detail')
        with patch.object(module.requests, 'post', side_effect=error):
            response = self.upload()
        self.assertEqual(response.status_code, 502)
        self.assertIn('DNS could not resolve Google Gemini', response.json['error'])
        self.assertNotIn('private host detail', response.json['error'])

    def test_tls_failure_is_explained(self):
        with patch.object(module.requests, 'post', side_effect=module.requests.exceptions.SSLError('certificate detail')):
            response = self.upload()
        self.assertEqual(response.status_code, 502)
        self.assertIn('TLS negotiation', response.json['error'])
        self.assertNotIn('certificate detail', response.json['error'])

    def test_unsupported_model_http_404_is_distinguished(self):
        with patch.object(module.requests, 'post', return_value=self.fake(404, '{}')):
            response = self.upload()
        self.assertEqual(response.status_code, 502)
        self.assertIn('could not find AI_MODEL', response.json['error'])

    def test_provider_quota_error_is_clear(self):
        with patch.object(module.requests, 'post', return_value=self.fake(429, '{}')):
            response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertIn('quota or rate limit', response.json['error'])

    def test_invalid_model_response_is_not_accepted(self):
        with patch.object(module.requests, 'post', return_value=self.fake(content='not-json')):
            response = self.upload()
        self.assertEqual(response.status_code, 502)
        self.assertIn('invalid response', response.json['error'])

    def test_timeout_is_distinguished(self):
        with patch.object(module.requests, 'post', side_effect=module.requests.Timeout()):
            response = self.upload()
        self.assertEqual(response.status_code, 504)
        self.assertIn('timed out', response.json['error'])


if __name__ == '__main__':
    unittest.main()
