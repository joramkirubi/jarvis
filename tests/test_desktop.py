import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from audio_pcm import InputPCM
from desktop_tools import DesktopTools, ROOT

class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'desktop_config.json').write_text((ROOT / 'desktop_config.json').read_text())
        self.tools = DesktopTools(self.root)
    def call(self, action, target='', value=''):
        return json.loads(self.tools.handle(dict(action=action, target=target, value=value)))
    def test_unknown_target_cannot_execute(self):
        with patch('desktop_tools.subprocess.Popen') as process:
            self.assertFalse(self.call('open', 'cmd.exe /c anything')['ok'])
            process.assert_not_called()
    def test_disabled_permission(self):
        self.tools.config['permissions']['search'] = False
        with patch('desktop_tools.webbrowser.open') as browser:
            self.assertFalse(self.call('search', 'anything')['ok'])
            browser.assert_not_called()
    def test_url_scheme_rejected(self):
        self.tools.config['targets']['github']['location'] = 'file:///C:/secret'
        self.assertFalse(self.call('open', 'github')['ok'])
    def test_browser_failure_not_success(self):
        with patch('desktop_tools.webbrowser.open', return_value=False):
            self.assertFalse(self.call('open', 'github')['ok'])
    def test_search_encoded(self):
        with patch('desktop_tools.webbrowser.open', return_value=True) as browser:
            self.assertTrue(self.call('search', 'a&b #c')['ok'])
            browser.assert_called_once_with('https://www.google.com/search?q=a%26b+%23c')
    def test_persistent_memory_and_update(self):
        self.assertTrue(self.call('remember', 'style', 'short answers')['ok'])
        self.tools = DesktopTools(self.root)
        self.assertEqual(self.call('recall')['preferences']['style'], 'short answers')
        self.call('remember', 'style', 'long answers')
        self.assertEqual(self.call('recall', 'style')['preferences'], {'style':'long answers'})
    def test_memory_validation(self):
        self.assertFalse(self.call('remember', '../escape', 'text')['ok'])
        self.assertFalse(self.call('remember', 'key', 'a'*1001)['ok'])
    def test_dry_run_has_no_external_effect(self):
        self.tools.dry_run = True
        with patch('desktop_tools.webbrowser.open') as browser:
            self.assertTrue(self.call('open', 'github')['simulated'])
            self.assertTrue(self.call('remember', 'key', 'text')['simulated'])
            browser.assert_not_called()
        self.assertFalse((self.root / '.jarvis').exists())
    def test_non_string_input(self):
        self.assertFalse(self.call('open', ['bad'])['ok'])

class AudioTest(unittest.TestCase):
    def test_mono_passthrough(self):
        raw = np.array([-32000, 0, 32000], dtype='<i2').tobytes()
        self.assertEqual(InputPCM().convert(raw), raw)
    def test_stereo_averages_without_overflow(self):
        raw = np.full((10, 2), 32000, dtype='<i2').tobytes()
        self.assertTrue(np.all(np.frombuffer(InputPCM(16000,2).convert(raw), dtype='<i2') == 32000))
    def test_streaming_resampling_matches_single_block(self):
        raw = (np.sin(np.arange(48000)*0.2)*10000).astype('<i2')
        whole = InputPCM(48000).convert(raw.tobytes())
        converter = InputPCM(48000)
        pieces = b''.join(converter.convert(x.tobytes()) for x in np.array_split(raw, 7))
        self.assertEqual(len(whole), 32000)
        self.assertEqual(whole, pieces)
    def test_unsupported_rate(self):
        with self.assertRaises(ValueError): InputPCM(44100)

if __name__ == '__main__': unittest.main()
