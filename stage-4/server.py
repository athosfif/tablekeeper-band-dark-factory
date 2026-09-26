"""Dependency-free threaded JSON HTTP adapter. Never log request bodies or tokens."""

import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from engine import Engine
from json_values import dumps, loads
from model import APIError, obj


class Server(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    engine = Engine()

    def log_message(self, *_args):
        pass

    def send_error(self, code, message=None, explain=None):
        # Keep even HTTP-adapter errors in the JSON contract. Unsupported methods
        # are missing routes, not internal server failures.
        status = 404 if code == 501 else code
        error = 'not_found' if status == 404 else 'malformed_request'
        self.respond(status, {'error': {'code': error, 'message': 'Invalid HTTP request'}})

    def respond(self, status, value, content_type='application/json; charset=utf-8'):
        payload = b'' if status == 204 else (value if isinstance(value, bytes) else dumps(value).encode('utf-8'))
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(payload)

    def handle_request(self):
        try:
            target = urlsplit(self.path)
            if self.command in ('GET', 'HEAD'):
                assets = {'/assets/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                          '/assets/style.css': ('style.css', 'text/css; charset=utf-8'),
                          '/assets/Serif-Regular.ttf': ('Serif-Regular.ttf', 'font/ttf'),
                          '/assets/Sans-Regular.ttf': ('Sans-Regular.ttf', 'font/ttf')}
                if target.path in ('/', '/signup', '/login', '/lookup'):
                    asset = ('index.html', 'text/html; charset=utf-8')
                else:
                    asset = assets.get(target.path)
                if asset:
                    file = Path(__file__).parent / 'static' / asset[0]
                    if file.is_file():
                        self.respond(200, file.read_bytes(), asset[1])
                        return
                    raise APIError(404, 'not_found')
            body = {}
            if self.command in ('POST', 'PATCH', 'PUT'):
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    if size < 0:
                        raise ValueError()
                    raw = self.rfile.read(size)
                    # Cancel has no required body. Every other write requires an object.
                    if not raw and self.path.endswith('/cancel'):
                        body = {}
                    else:
                        body = loads(raw)
                        obj(body)
                except (ValueError, UnicodeError, RecursionError):
                    raise APIError(400, 'malformed_request') from None
            query = {k: v[0] for k, v in parse_qs(target.query, keep_blank_values=True).items()}
            status, value = self.engine.handle(self.command, target.path, query, self.headers, body)
        except APIError as error:
            status, value = error.status, {'error': {'code': error.code, 'message': error.message}}
        except (ValueError, OverflowError, RecursionError):
            status, value = 422, {'error': {'code': 'validation_failed', 'message': 'Invalid value'}}
        try:
            self.respond(status, value)
        except (BrokenPipeError, ConnectionResetError):
            pass

    do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = do_OPTIONS = do_HEAD = handle_request


if __name__ == '__main__':
    Server(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()
