"""Private, stdlib-only uploader and launcher behind nginx Basic Auth.

This process listens on 127.0.0.1 only. Untrusted files are not automatically
run until requested by the authenticated owner. Only 64-bit PE exe is accepted.
"""
import json
import os
from pathlib import Path
import struct
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

STORE = Path('/home/app/Uploads')
STORE.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD = 32 * 1024 * 1024


def is_x64_pe(path: Path) -> bool:
    """Reject wrong architectures, corrupt files and non-PE content."""
    try:
        with path.open('rb') as f:
            if f.read(2) != b'MZ':
                return False
            f.seek(0x3c)
            offset = struct.unpack('<I', f.read(4))[0]
            if offset > MAX_UPLOAD - 6:
                return False
            f.seek(offset)
            if f.read(4) != b'PE\x00\x00':
                return False
            machine = struct.unpack('<H', f.read(2))[0]
            return machine == 0x8664
    except (OSError, struct.error):
        return False


def launch(args):
    env = os.environ.copy()
    env.update(DISPLAY=':99', HOME='/home/app', WINEPREFIX='/home/app/.wine',
               WINEARCH='win64', WINEDEBUG='-all')
    subprocess.Popen(['wine', *args], cwd=str(STORE), env=env,
                     stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     start_new_session=True)


class API(BaseHTTPRequestHandler):
    def respond(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if urlparse(self.path).path != '/api/list':
            return self.respond(404, {'error': 'Not found'})
        files = sorted(p.name for p in STORE.iterdir()
                       if p.is_file() and p.suffix.lower() == '.exe')
        self.respond(200, {'files': files})

    def do_POST(self):
        # A non-simple request header prevents cross-site form submissions.
        if self.headers.get('X-MiniWin-Action') != '1':
            return self.respond(403, {'error': 'Missing action header'})
        route = urlparse(self.path)
        try:
            length = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            return self.respond(400, {'error': 'Missing size'})
        if length < 0 or length > MAX_UPLOAD:
            return self.respond(413, {'error': '32 MB maximum'})

        if route.path == '/api/notepad':
            launch(['notepad.exe'])
            return self.respond(200, {'message': 'Запускаю Блокнот Wine'})

        if route.path == '/api/run':
            try:
                payload = json.loads(self.rfile.read(length))
                name = payload.get('name', '')
            except (ValueError, AttributeError, UnicodeDecodeError):
                return self.respond(400, {'error': 'Invalid JSON'})
            if not isinstance(name, str) or not name or Path(name).name != name:
                return self.respond(400, {'error': 'Invalid filename'})
            path = STORE / name
            if not path.is_file() or not is_x64_pe(path):
                return self.respond(404, {'error': '64-bit EXE not found'})
            launch([str(path)])
            return self.respond(200, {'message': f'Запускаю {name}'})

        if route.path == '/api/upload':
            names = parse_qs(route.query).get('name', [])
            name = names[0] if names else ''
            if (not name or len(name) > 120 or Path(name).name != name
                    or '/' in name or '\\' in name or name.startswith('.')
                    or not name.lower().endswith('.exe')):
                return self.respond(400, {'error': 'Choose a .exe file with a simple name'})
            if length < 128:
                return self.respond(400, {'error': 'File is too small'})
            dest = STORE / name
            temp = STORE / (name + '.uploading')
            try:
                with temp.open('wb') as f:
                    left = length
                    while left:
                        chunk = self.rfile.read(min(left, 65536))
                        if not chunk:
                            raise ConnectionError('Upload interrupted')
                        f.write(chunk)
                        left -= len(chunk)
                if not is_x64_pe(temp):
                    temp.unlink(missing_ok=True)
                    return self.respond(400, {'error': 'Only real Windows x64 EXE files are supported'})
                temp.replace(dest)
                return self.respond(200, {'message': f'Загружен {name}', 'name': name})
            except (OSError, ConnectionError) as exc:
                temp.unlink(missing_ok=True)
                return self.respond(500, {'error': str(exc)})

        return self.respond(404, {'error': 'Not found'})


if __name__ == '__main__':
    print('MiniWin API ready on 127.0.0.1:8765', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), API).serve_forever()
