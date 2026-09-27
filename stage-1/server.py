"""Threaded HTTP adapter; response delivery is outside the state transaction."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
import sys
import traceback

from application import Application
from validation import APIError, fail

app = Application()


def reject_constant(value):
    raise ValueError('Non-JSON number')


class Handler(BaseHTTPRequestHandler):
    def serve(self):
        try:
            body = {}
            if self.command in ('POST', 'PATCH', 'PUT'):
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if length < 0:
                        raise ValueError('Negative length')
                    data = self.rfile.read(length)
                    body = json.loads(data, parse_constant=reject_constant) if data else {}
                except (ValueError, UnicodeDecodeError, RecursionError):
                    fail('malformed_request', 400)
            status, payload = app.handle(self.command, self.path, self.headers, body)
            encoded = b'' if status == 204 else json.dumps(payload, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode('utf-8')
        except APIError as error:
            status = error.status
            encoded = json.dumps({'error': {'code': error.code, 'message': error.message}}).encode('utf-8')
        except (ValueError, OverflowError, RecursionError, UnicodeError):
            status = 422
            encoded = b'{"error":{"code":"validation_failed","message":"Invalid value"}}'
        except Exception:
            # Unexpected programming faults remain visible in container diagnostics.
            traceback.print_exc()
            status = 500
            encoded = b'{"error":{"code":"internal_error","message":"Internal error"}}'
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass  # A lost response does not roll back an already committed write.

    do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = serve

    def log_message(self, format, *args):
        # Do not log URLs, request bodies, authorization headers or portable state.
        pass


class Server(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


if __name__ == '__main__':
    sys.set_int_max_str_digits(0)
    Server(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()
