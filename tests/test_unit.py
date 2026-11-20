import json
import os
import tempfile
import unittest
from pathlib import Path
from app.server import Application, Config


class MemoryStore:
    value = None

    def request(self, method, value=None):
        if method == 'get':
            return self.value
        self.value = value
        return 1


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.file = Path(self.temp.name)/'key'
        self.file.write_text('unit-test-only')
        self.config = Config(version=os.getenv('APP_VERSION', '1.0.0'), secret_file=str(self.file))
        self.app = Application(self.config, MemoryStore())
        self.headers = {'X-API-Key': 'unit-test-only'}

    def tearDown(self):
        self.temp.cleanup()

    def test_identity_contract(self):
        code, data = self.app.handle('GET', '/')
        self.assertEqual((code, data['name'], data['roll_no']), (200, 'Rishav', '2301730245'))

    def test_version_contract(self):
        self.assertEqual(self.app.handle('GET', '/version')[1]['version'], '1.0.0')

    def test_health_needs_secret(self):
        self.file.unlink()
        self.assertEqual(self.app.handle('GET', '/health')[0], 503)

    def test_health_failure(self):
        self.config.fail_health = True
        self.assertEqual(self.app.handle('GET', '/health')[0], 503)

    def test_secure_requires_credentials(self):
        self.assertEqual(self.app.handle('GET', '/secure')[0], 401)

    def test_secure_success_without_leak(self):
        code, data = self.app.handle('GET', '/secure', self.headers)
        self.assertEqual(code, 200)
        self.assertNotIn('unit-test-only', json.dumps(data))

    def test_state_round_trip(self):
        self.assertEqual(self.app.handle('POST', '/data', self.headers, b'{"value":"record"}')[0], 200)
        self.assertEqual(self.app.handle('GET', '/data', self.headers)[1]['value'], 'record')

    def test_invalid_json(self):
        self.assertEqual(self.app.handle('POST', '/data', self.headers, b'not-json')[0], 400)

    def test_invalid_value(self):
        self.assertEqual(self.app.handle('POST', '/data', self.headers, b'{"value":7}')[0], 400)

    def test_unknown_route(self):
        self.assertEqual(self.app.handle('GET', '/unknown')[0], 404)

    def test_unsupported_method(self):
        self.assertEqual(self.app.handle('DELETE', '/')[0], 405)

    def test_canary_fault(self):
        self.config.fail_work = True
        self.assertEqual(self.app.handle('GET', '/work')[0], 500)


if __name__ == '__main__':
    unittest.main()
