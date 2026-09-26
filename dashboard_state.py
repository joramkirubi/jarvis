"""Thread-safe dashboard state and constrained local settings/storage access."""
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from desktop_tools import DesktopTools
from google_tools import GoogleTools

class DashboardState:
    def __init__(self, root):
        self.root = Path(root)
        self.google = GoogleTools(self.root)
        self.lock = threading.RLock()
        self.started = time.time()
        self.status = 'idle'
        self.detail = 'Ready when you are.'
        self.transcript = []
        self.activity = []
        self.level = 0.0
        self.level_at = 0.0
        self.sequence = 0
        self.sessions = 0
        self.commands = 0
        self.devices = []
        self.device_error = None
        self.settings = {'device': os.getenv('JARVIS_INPUT_DEVICE', ''),
                         'rate': int(os.getenv('JARVIS_CHAT_INPUT_RATE', '16000')),
                         'channels': int(os.getenv('JARVIS_CHAT_INPUT_CHANNELS', '1'))}
        path = self.root / '.jarvis' / 'dashboard.json'
        if path.exists():
            self.settings.update(json.loads(path.read_text(encoding='utf-8')))

    def set_status(self, status, detail):
        with self.lock:
            self.status, self.detail = status, detail

    def event(self, title, detail='', kind='info'):
        with self.lock:
            self.sequence += 1
            self.activity.append(dict(id=self.sequence, time=time.time(), title=title, detail=detail, kind=kind))
            self.activity = self.activity[-60:]

    def message(self, role, text):
        with self.lock:
            self.sequence += 1
            self.transcript.append(dict(id=self.sequence, role=role, text=str(text), time=time.time()))
            self.transcript = self.transcript[-100:]

    def meter(self, level):
        with self.lock:
            self.level, self.level_at = min(1.0, max(0.0, float(level))), time.monotonic()

    def tool(self, parameters):
        with self.lock:
            handler = DesktopTools(self.root, dry_run=os.getenv('JARVIS_DRY_RUN', '').lower() == 'true')
            result = handler.handle(parameters)
            data = json.loads(result)
            self.commands += 1
            action = parameters.get('action', 'unknown')
            # Memory values and search queries are not copied into activity logs.
            target = parameters.get('target', '') if action == 'open' else ''
            label = 'Simulated' if data.get('simulated') else ('Completed' if data.get('ok') else 'Failed')
            self.event(f'{action.title()} {target}'.strip(), label + ': ' + data.get('message', 'Tool returned a result'), 'success' if data.get('ok') else 'error')
            return result

    def memory(self):
        path = self.root / '.jarvis' / 'memory.sqlite3'
        if not path.exists():
            return []
        with self.lock:
            connection = sqlite3.connect(path)
            try:
                rows = connection.execute('SELECT key,value FROM preferences ORDER BY key').fetchall()
                return [dict(key=k, value=v) for k, v in rows]
            finally:
                connection.close()

    def forget(self, key):
        if not isinstance(key, str) or not key or len(key) > 64:
            raise ValueError('Invalid memory key')
        with self.lock:
            path = self.root / '.jarvis' / 'memory.sqlite3'
            if not path.exists():
                return
            connection = sqlite3.connect(path)
            try:
                with connection:
                    connection.execute('DELETE FROM preferences WHERE key=?', (key,))
            finally:
                connection.close()
            self.event('Memory removed', key)

    def configure(self, body):
        device = body.get('device', '')
        rate, channels = body.get('rate'), body.get('channels')
        if not isinstance(device, str) or len(device) > 200 or rate not in (16000,48000) or channels not in (1,2):
            raise ValueError('Choose 16000/48000 Hz and one/two channels')
        with self.lock:
            directory = self.root / '.jarvis'
            directory.mkdir(exist_ok=True)
            settings = dict(device=device, rate=rate, channels=channels)
            temporary = directory / 'dashboard.json.tmp'
            temporary.write_text(json.dumps(settings, indent=2), encoding='utf-8')
            temporary.replace(directory / 'dashboard.json')
            self.settings = settings
            self.event('Audio settings saved', 'Applies to the next start in this dashboard')

    def toggle_target(self, key, enabled):
        with self.lock:
            path = self.root / 'desktop_config.json'
            config = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(key, str) or key not in config['targets'] or type(enabled) is not bool:
                raise ValueError('Unknown target or invalid toggle')
            config['targets'][key]['enabled'] = enabled
            temporary = path.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(config, indent=2)+'\n', encoding='utf-8')
            temporary.replace(path)
            self.event('App settings changed', key + (' enabled' if enabled else ' disabled'))

    def snapshot(self):
        with self.lock:
            config = json.loads((self.root/'desktop_config.json').read_text(encoding='utf-8'))
            targets = [dict(id=k, description=v.get('description', k), enabled=v.get('enabled') is True, type=v.get('type')) for k,v in config['targets'].items()]
            return dict(status=self.status, detail=self.detail,
                        level=self.level if time.monotonic()-self.level_at < .8 else 0,
                        uptime=int(time.time()-self.started), sessions=self.sessions, commands=self.commands,
                        transcript=list(self.transcript), activity=list(self.activity), settings=dict(self.settings),
                        devices=list(self.devices), device_error=self.device_error, targets=targets,
                        permissions=config['permissions'], dry_run=os.getenv('JARVIS_DRY_RUN','').lower()=='true',
                        has_key=bool(os.getenv('ELEVENLABS_API_KEY','').strip()),
                        has_model=(self.root/'models'/'vosk-model-small-en-us-0.15').is_dir())
