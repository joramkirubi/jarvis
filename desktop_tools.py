"""Allowlisted desktop tools. No model-supplied command or executable is accepted."""
import argparse
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import webbrowser
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parent

class DesktopTools:
    def __init__(self, root=ROOT, dry_run=False):
        self.root = Path(root)
        self.dry_run = dry_run
        self.config = json.loads((self.root / 'desktop_config.json').read_text(encoding='utf-8'))
        if not isinstance(self.config.get('targets'), dict) or not isinstance(self.config.get('permissions'), dict):
            raise ValueError('Invalid desktop_config.json')

    def database(self):
        directory = self.root / '.jarvis'
        directory.mkdir(exist_ok=True)
        connection = sqlite3.connect(directory / 'memory.sqlite3')
        connection.execute('CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        return connection

    def handle(self, parameters):
        try:
            action = parameters.get('action', '')
            target = parameters.get('target', '')
            value = parameters.get('value', '')
            if action not in ('list', 'open', 'search', 'remember', 'recall'):
                raise ValueError('Unknown action')
            if not isinstance(target, str) or not isinstance(value, str):
                raise ValueError('Text parameters required')
            if len(target) > 500 or len(value) > 1000:
                raise ValueError('Text too long (target: 500; preference: 1000 characters)')
            if self.config['permissions'].get(action) is not True:
                raise ValueError('Action disabled in desktop_config.json')
            result = self.execute(action, target.strip(), value.strip())
            result['ok'] = True
        except (ValueError, OSError, sqlite3.Error, TypeError, AttributeError):
            result = {'ok': False, 'message': 'Action failed or not permitted. Check target, permissions and local configuration.'}
        print('Desktop tool:', action if 'action' in locals() and isinstance(action, str) and action in ('list','open','search','remember','recall') else 'invalid', 'OK' if result['ok'] else 'FAILED', flush=True)
        return json.dumps(result, ensure_ascii=False)

    def execute(self, action, target, value):
        if action == 'list':
            return {'targets': [{'id': k, 'description': v.get('description', k)} for k, v in self.config['targets'].items() if v.get('enabled') is True]}
        if action == 'open':
            item = self.config['targets'].get(target)
            if not item or item.get('enabled') is not True:
                raise ValueError('Unknown or disabled target')
            kind = item.get('type')
            location = item.get('location', '')
            if kind == 'url':
                parsed = urlsplit(location)
                if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError('Only HTTPS URLs allowed')
            elif kind in ('app', 'folder'):
                location = Path(os.path.expandvars(location)).expanduser()
                if not location.is_absolute() or not location.exists():
                    raise ValueError('Configure an existing absolute path')
                if kind == 'app' and (location.suffix.lower() != '.exe' or not location.is_file()):
                    raise ValueError('Only configured EXE applications allowed')
                if kind == 'folder' and not location.is_dir():
                    raise ValueError('Folder required')
                if os.name != 'nt':
                    raise ValueError('Desktop app/folder actions require Windows')
            else:
                raise ValueError('Unsupported target type')
            if self.dry_run:
                return {'simulated': True, 'message': 'Validated target; nothing opened', 'target': target}
            if kind == 'url':
                if not webbrowser.open(location):
                    raise ValueError('Browser did not accept request')
            elif kind == 'app':
                subprocess.Popen([str(location)], shell=False)
            else:
                os.startfile(str(location))
            return {'message': 'Launch request sent; window state not verified', 'target': target}
        if action == 'search':
            if not target:
                raise ValueError('Search query required')
            url = 'https://www.google.com/search?' + urlencode({'q': target})
            if not self.dry_run and not webbrowser.open(url):
                raise ValueError('Browser did not accept request')
            return {'simulated': self.dry_run, 'message': 'Browser search requested; results are NOT read or researched'}
        if action == 'remember':
            if not re.fullmatch(r'[a-z0-9_\-]{1,64}', target) or not value:
                raise ValueError('Use a short lowercase memory key')
            if self.dry_run:
                return {'simulated': True, 'message': 'Nothing saved'}
            with self.database() as connection:
                connection.execute('INSERT OR REPLACE INTO preferences VALUES (?, ?)', (target, value))
            connection.close()
            return {'message': 'Preference saved', 'key': target}
        with self.database() as connection:
            rows = connection.execute('SELECT key,value FROM preferences WHERE instr(key,?)>0 OR instr(value,?)>0 ORDER BY key LIMIT 30', (target, target)).fetchall()
        connection.close()
        return {'preferences': dict(rows), 'limit': 30}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'open', 'search', 'remember', 'recall', 'forget'])
    parser.add_argument('target', nargs='?', default='')
    parser.add_argument('value', nargs='?', default='')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    tools = DesktopTools(dry_run=args.dry_run)
    if args.action == 'forget':
        if not args.target:
            parser.error('Specify the exact memory key to delete')
        if args.dry_run:
            print('Simulated: nothing deleted')
        else:
            with tools.database() as connection:
                cursor = connection.execute('DELETE FROM preferences WHERE key=?', (args.target,))
                print('Preferences removed:', cursor.rowcount)
            connection.close()
    else:
        result = tools.handle(vars(args))
        print(result)
        return 0 if json.loads(result)['ok'] else 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
