"""Small standard-library application for the deployment experiments."""
import hmac
import json
import os
import socket
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class RedisConnection:
    def __init__(self, host, port=6379):
        self.socket = socket.create_connection((host, port), timeout=0.4)
        self.stream = self.socket.makefile('rb')

    def command(self, *parts):
        encoded = [str(p).encode() for p in parts]
        self.socket.sendall(b'*%d\r\n' % len(parts) + b''.join(
            b'$%d\r\n' % len(p) + p + b'\r\n' for p in encoded))
        line = self.stream.readline()
        if not line:
            raise OSError('Redis connection closed')
        kind, value = line[:1], line[1:-2]
        if kind == b'-':
            raise OSError('Redis rejected the command')
        if kind == b':':
            return int(value)
        if kind == b'$':
            length = int(value)
            if length < 0:
                return None
            data = self.stream.read(length)
            self.stream.read(2)
            return data.decode()
        return value.decode()

    def close(self):
        self.stream.close()
        self.socket.close()


class RedisStore:
    def __init__(self, hosts):
        self.hosts = hosts

    def request(self, method, value=None):
        for host in self.hosts:
            connection = None
            try:
                connection = RedisConnection(host)
                if method == 'get':
                    return connection.command('GET', 'lab4:record')
                connection.command('SET', 'lab4:record', value)
                # WAIT must use the same connection as SET.
                return connection.command('WAIT', 1, 300)
            except OSError:
                continue
            finally:
                if connection:
                    connection.close()
        raise OSError('No writable or reachable Redis server')


@dataclass
class Config:
    version: str = '1.0.0'
    environment: str = 'blue'
    secret_file: str = '/run/secrets/app-api-key'
    fail_health: bool = False
    fail_work: bool = False


class Application:
    def __init__(self, config, store):
        self.config, self.store = config, store

    def secret(self):
        try:
            return Path(self.config.secret_file).read_text().strip()
        except OSError:
            return ''

    def handle(self, method, path, headers=None, body=b''):
        headers = headers or {}
        details = dict(name='Rishav', roll_no='2301730245',
                       version=self.config.version, environment=self.config.environment)
        if method not in ('GET', 'POST'):
            return 405, {'error': 'Method not allowed'}
        if path == '/health':
            healthy = bool(self.secret()) and not self.config.fail_health
            return (200 if healthy else 503), dict(details, status='UP' if healthy else 'DOWN')
        if path in ('/', '/version') and method == 'GET':
            return 200, details
        if path == '/work' and method == 'GET':
            return (500 if self.config.fail_work else 200), dict(details, result='error' if self.config.fail_work else 'ok')
        if path in ('/secure', '/data'):
            secret = self.secret()
            if not secret:
                return 503, {'error': 'Secret unavailable'}
            if not hmac.compare_digest(headers.get('X-API-Key', ''), secret):
                return 401, {'error': 'Unauthorized'}
            if path == '/secure':
                return 200, dict(details, authenticated=True)
            try:
                if method == 'GET':
                    return 200, dict(details, value=self.store.request('get'))
                payload = json.loads(body)
                value = payload.get('value')
                if not isinstance(value, str) or len(value) > 256:
                    return 400, {'error': 'value must be a string of at most 256 characters'}
                acks = self.store.request('set', value)
                return 200, dict(details, value=value, replicas_acked=acks)
            except (ValueError, AttributeError):
                return 400, {'error': 'Invalid JSON object'}
            except OSError:
                return 503, {'error': 'Data service unavailable'}
        return 404, {'error': 'Not found'}


def create_application():
    return Application(Config(
        version=os.getenv('APP_VERSION', '1.0.0'),
        environment=os.getenv('APP_ENV', 'blue'),
        secret_file=os.getenv('API_KEY_FILE', '/run/secrets/app-api-key'),
        fail_health=os.getenv('FAIL_HEALTH', 'false') == 'true',
        fail_work=os.getenv('FAIL_WORK', 'false') == 'true',
    ), RedisStore(os.getenv('REDIS_HOSTS', 'redis-primary,redis-standby').split(',')))


def serve():
    application = create_application()

    class Handler(BaseHTTPRequestHandler):
        def run_request(self):
            length = int(self.headers.get('Content-Length', '0'))
            if length > 1024:
                code, payload = 413, {'error': 'Request too large'}
            else:
                code, payload = application.handle(self.command, self.path.split('?')[0], self.headers, self.rfile.read(length))
            data = json.dumps(payload).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = run_request
        do_POST = run_request
        do_DELETE = run_request

        def log_message(self, *args):
            # Request paths and authentication values are deliberately not logged.
            pass

    ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()


if __name__ == '__main__':
    serve()
