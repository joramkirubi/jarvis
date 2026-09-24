"""Launch the local Jarvis dashboard: python jarvis_dashboard.py"""
import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import threading
import webbrowser
from urllib.parse import urlsplit

from dashboard_state import DashboardState
from dashboard_runtime import VoiceRuntime

ROOT = Path(__file__).resolve().parent

class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, address, state, runtime, token):
        self.state, self.runtime, self.token = state, runtime, token
        super().__init__(address, Handler)
        self.origin = f'http://127.0.0.1:{self.server_port}'

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # Never log the session token.
    def send(self, status, data, content_type='application/json'):
        body = json.dumps(data).encode() if content_type=='application/json' else data
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError): pass
    def authorized(self):
        expected = self.server.origin.removeprefix('http://')
        if self.headers.get('Host') != expected:
            self.send(403,{'error':'Invalid host'}); return False
        if self.headers.get('Origin',self.server.origin) != self.server.origin:
            self.send(403,{'error':'Invalid origin'}); return False
        if not secrets.compare_digest(self.headers.get('Authorization',''), 'Bearer '+self.server.token):
            self.send(401,{'error':'Open the dashboard using the link printed by its launcher.'}); return False
        return True
    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith('/api/'):
            if not self.authorized(): return
            try:
                if path == '/api/state': self.send(200,self.server.state.snapshot())
                elif path == '/api/memory': self.send(200,{'items':self.server.state.memory()})
                else: self.send(404,{'error':'Not found'})
            except Exception: self.send(500,{'error':'Local data could not be read. Check desktop_config.json and memory database.'})
            return
        assets = {'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/styles.css':('styles.css','text/css; charset=utf-8')}
        if path not in assets: self.send(404,{'error':'Not found'}); return
        name,kind = assets[path]
        self.send(200,(ROOT/'dashboard'/name).read_bytes(),kind)
    def do_POST(self):
        if not self.authorized(): return
        try:
            size = int(self.headers.get('Content-Length','0'))
            if size < 1 or size > 16384: raise ValueError('Invalid request size')
            if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                raise ValueError('JSON required')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError('JSON object required')
            state,runtime = self.server.state,self.server.runtime
            path = urlsplit(self.path).path
            if path == '/api/control': runtime.control(data.get('action'))
            elif path == '/api/launch':
                self.send(200,json.loads(state.tool(dict(action='open',target=data.get('target'),value='')))); return
            elif path == '/api/forget': state.forget(data.get('key'))
            elif path == '/api/settings':
                with runtime.guard:
                    if runtime.active(): raise ValueError('Stop the listener before changing audio settings')
                    state.configure(data)
            elif path == '/api/target': state.toggle_target(data.get('id'),data.get('enabled'))
            elif path == '/api/devices':
                with runtime.guard:
                    if runtime.active(): raise ValueError('Stop the listener before refreshing devices')
                    runtime.refresh_devices()
            else: self.send(404,{'error':'Not found'}); return
            self.send(200,{'ok':True})
        except (ValueError,TypeError,KeyError):
            self.send(400,{'error':'Invalid request, or listener is active. Stop it before changing audio settings.'})
        except Exception:
            self.send(500,{'error':'Local operation failed. Check your configuration.'})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-browser',action='store_true')
    args = parser.parse_args()
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    state = DashboardState(ROOT)
    runtime = VoiceRuntime(state)
    token = secrets.token_urlsafe(32)
    server = DashboardServer(('127.0.0.1',args.port),state,runtime,token)
    # Audio scanning does not block opening the UI and does not start listening.
    threading.Thread(target=runtime.refresh_devices,daemon=True).start()
    url = server.origin+'/#'+token
    print('Jarvis dashboard (local session link; keep private):\n'+url,flush=True)
    print('Ctrl+C stops the dashboard and microphone. Closing the browser alone does not.',flush=True)
    if not args.no_browser: webbrowser.open(url)
    try: server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt: print('\nStopping Jarvis dashboard.')
    finally:
        runtime.close()
        server.server_close()

if __name__=='__main__': main()
