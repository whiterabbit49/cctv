import os
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import web

class TestWebLive(unittest.TestCase):
    def test_live_returns_current_hour(self):
        with patch.object(web, 'get_archive_path', return_value='/tmp'), \
             patch('app.get_current_hour_identifier', return_value='2026-10-16-14'), \
             patch('os.path.exists', return_value=True):
            client = TestClient(web.app)
            r = client.get('/api/live')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json(), {
                'hour': '2026-10-16-14',
                'playlist_url': '/hls/playlist_2026-10-16-14.m3u8',
            })

    def test_live_404_when_no_playlist(self):
        with patch.object(web, 'get_archive_path', return_value='/tmp'), \
             patch('app.get_current_hour_identifier', return_value='2026-10-16-14'), \
             patch('os.path.exists', return_value=False):
            client = TestClient(web.app)
            r = client.get('/api/live')
            self.assertEqual(r.status_code, 404)

    def test_auth_rejects_bad_token(self):
        with patch.object(web, 'get_token', return_value='secret123'):
            client = TestClient(web.app)
            r = client.get('/api/live', headers={'X-CCTV-Token': 'wrong'})
            self.assertEqual(r.status_code, 401)

    def test_auth_accepts_valid_token(self):
        with patch.object(web, 'get_token', return_value='secret123'), \
             patch.object(web, 'get_archive_path', return_value='/tmp'), \
             patch('app.get_current_hour_identifier', return_value='2026-10-16-14'), \
             patch('os.path.exists', return_value=True):
            client = TestClient(web.app)
            r = client.get('/api/live', headers={'X-CCTV-Token': 'secret123'})
            self.assertEqual(r.status_code, 200)

    def test_auth_accepts_valid_cookie(self):
        with patch.object(web, 'get_token', return_value='secret123'), \
             patch.object(web, 'get_archive_path', return_value='/tmp'), \
             patch('app.get_current_hour_identifier', return_value='2026-10-16-14'), \
             patch('os.path.exists', return_value=True):
            client = TestClient(web.app)
            r = client.get('/api/live', cookies={'cctv_token': 'secret123'})
            self.assertEqual(r.status_code, 200)

    def test_auth_rejects_wrong_cookie(self):
        with patch.object(web, 'get_token', return_value='secret123'):
            client = TestClient(web.app)
            r = client.get('/api/live', cookies={'cctv_token': 'wrong'})
            self.assertEqual(r.status_code, 401)

    def test_open_when_token_unset(self):
        with patch.object(web, 'get_token', return_value=''), \
             patch.object(web, 'get_archive_path', return_value='/tmp'), \
             patch('app.get_current_hour_identifier', return_value='2026-10-16-14'), \
             patch('os.path.exists', return_value=True):
            client = TestClient(web.app)
            r = client.get('/api/live')
            self.assertEqual(r.status_code, 200)

class TestWebFiles(unittest.TestCase):
    def test_files_sorted_newest_first(self):
        fake = ['archive_2026-10-16-12.mp4', 'archive_2026-10-16-14.mp4', 'archive_2026-10-15-10.mp4', 'playlist_2026-10-16-14.m3u8', 'other.txt']
        with patch('os.listdir', return_value=fake), \
             patch('os.path.getsize', return_value=100), \
             patch('os.path.getmtime', return_value=1700000000.0), \
             patch.object(web, 'get_token', return_value=''):
            c = TestClient(web.app)
            r = c.get('/api/files')
            self.assertEqual(r.status_code, 200)
            names = [f['name'] for f in r.json()]
            self.assertEqual(names, ['archive_2026-10-16-14.mp4', 'archive_2026-10-16-12.mp4', 'archive_2026-10-15-10.mp4'])

    def test_files_date_filter(self):
        fake = ['archive_2026-10-16-14.mp4', 'archive_2026-10-15-10.mp4']
        with patch('os.listdir', return_value=fake), \
             patch('os.path.getsize', return_value=100), \
             patch('os.path.getmtime', return_value=1700000000.0), \
             patch.object(web, 'get_token', return_value=''):
            c = TestClient(web.app)
            r = c.get('/api/files?date=2026-10-15')
            self.assertEqual([f['name'] for f in r.json()], ['archive_2026-10-15-10.mp4'])

    def test_files_missing_archive_returns_empty(self):
        with patch('os.listdir', side_effect=FileNotFoundError), \
             patch.object(web, 'get_token', return_value=''):
            c = TestClient(web.app)
            r = c.get('/api/files')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json(), [])

class TestWebStatic(unittest.TestCase):
    def test_hls_rejects_traversal(self):
        with patch.object(web, 'get_token', return_value=''):
            c = TestClient(web.app)
            r = c.get('/hls/%2e%2e%2fapp.py')
            self.assertEqual(r.status_code, 404)
            r2 = web.serve_hls('../app.py')
            self.assertEqual(r2.status_code, 404)

    def test_hls_rejects_non_playlist_ts_names(self):
        with patch.object(web, 'get_token', return_value=''), \
             patch('os.path.exists', return_value=True), \
             patch.object(web, 'get_archive_path', return_value='/tmp'):
            c = TestClient(web.app)
            r = c.get('/hls/foo.ts')
            self.assertEqual(r.status_code, 404)

    def test_video_404_for_missing(self):
        with patch.object(web, 'get_token', return_value=''), \
             patch('os.path.exists', return_value=False):
            c = TestClient(web.app)
            r = c.get('/video/archive_2026-10-16-14.mp4')
            self.assertEqual(r.status_code, 404)

    def test_hls_serves_playlist_with_correct_mime(self):
        fd, p = tempfile.mkstemp(prefix='playlist_', suffix='.m3u8')
        os.close(fd)
        try:
            with open(p, 'w') as f:
                f.write('#EXTM3U\n')
            with patch.object(web, 'get_token', return_value=''), \
                 patch.object(web, 'get_archive_path', return_value=os.path.dirname(p)):
                c = TestClient(web.app)
                r = c.get('/hls/' + os.path.basename(p))
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.headers['content-type'].split(';')[0], 'application/vnd.apple.mpegurl')
        finally:
            os.remove(p)

class TestWebIndex(unittest.TestCase):
    def test_index_serves_html(self):
        with patch.object(web, 'get_token', return_value=''):
            c = TestClient(web.app)
            r = c.get('/')
            self.assertEqual(r.status_code, 200)
            self.assertIn('<video', r.text)
            self.assertIn('setUrl', r.text)
            self.assertIn('boot()', r.text)

    def test_index_open_with_token_set(self):
        with patch.object(web, 'get_token', return_value='secret123'):
            c = TestClient(web.app)
            r = c.get('/')
            self.assertEqual(r.status_code, 200)
