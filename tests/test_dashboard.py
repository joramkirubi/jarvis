"""Dashboard storage, local HTTP boundary, and voice lifecycle tests. No cloud calls."""
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from dashboard_state import DashboardState
from dashboard_runtime import VoiceRuntime
from jarvis_dashboard import DashboardServer

ROOT = Path(__file__).resolve().parents[1]

class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)
        (self.root/'desktop_config.json').write_text((ROOT/'desktop_config.json').read_text())
        self.state=DashboardState(self.root)
        self.runtime=VoiceRuntime(self.state)
    def test_state_never_contains_api_key(self):
        with patch.dict(os.environ,{'ELEVENLABS_API_KEY':'secret-test-key'}):
            snapshot=self.state.snapshot()
            self.assertTrue(snapshot['has_key'])
            self.assertNotIn('secret-test-key',json.dumps(snapshot))
    def test_memory_persists_and_deletes_exact_key(self):
        self.state.tool({'action':'remember','target':'style','value':'brief'})
        self.state.tool({'action':'remember','target':'other','value':'keep'})
        other=DashboardState(self.root)
        other.forget('style')
        self.assertEqual(other.memory(),[{'key':'other','value':'keep'}])
        self.assertNotIn('brief',json.dumps(self.state.activity))
    def test_toggle_does_not_change_paths(self):
        path=self.root/'desktop_config.json'
        original=json.loads(path.read_text())['targets']['github']['location']
        self.state.toggle_target('github',False)
        item=json.loads(path.read_text())['targets']['github']
        self.assertFalse(item['enabled']); self.assertEqual(item['location'],original)
        with patch('desktop_tools.webbrowser.open') as launch:
            result=json.loads(self.state.tool({'action':'open','target':'github','value':''}))
            self.assertFalse(result['ok']);launch.assert_not_called()
    def test_audio_settings_persist(self):
        self.state.configure(dict(device='1',rate=48000,channels=2))
        self.assertEqual(DashboardState(self.root).settings,dict(device='1',rate=48000,channels=2))
        with self.assertRaises(ValueError): self.state.configure(dict(device='1',rate=44100,channels=2))
    def test_bounded_history(self):
        for i in range(110): self.state.message('user',str(i)); self.state.event(str(i))
        self.assertEqual(len(self.state.transcript),100)
        self.assertEqual(len(self.state.activity),60)
    def test_meter_expires(self):
        self.state.meter(.6)
        self.assertEqual(self.state.snapshot()['level'],.6)
        self.state.level_at=time.monotonic()-1
        self.assertEqual(self.state.snapshot()['level'],0)
    def test_single_worker_and_stop(self):
        entered=threading.Event()
        def worker(action):
            entered.set();self.runtime.cancel.wait(3)
        with patch.object(self.runtime,'run',side_effect=worker):
            self.runtime.control('wake');self.assertTrue(entered.wait(1))
            with self.assertRaises(ValueError):self.runtime.control('talk')
            self.runtime.control('stop');self.runtime.worker.join(1)
            self.assertFalse(self.runtime.active())
    def test_sleep_transcript_closes_audio_and_blocks_late_tools(self):
        seen = {}
        done = threading.Event()
        runtime = self.runtime
        class FakeConversation:
            def __init__(self, **kwargs): seen.update(kwargs)
            def start_session(self):
                seen['audio_interface'].start(lambda pcm: None)
                seen['callback_user_transcript']('Jarvis, go to sleep!')
            def wait_for_session_end(self): done.wait(2)
            def end_session(self): done.set()
        sd = MagicMock()
        with patch('elevenlabs.conversational_ai.conversation.Conversation',FakeConversation), \
             patch('elevenlabs.client.ElevenLabs'), \
             patch.dict(os.environ, {'ELEVENLABS_API_KEY':'test-only'}):
            runtime.chat(sd,1,16000,1)
        self.assertTrue(runtime.rearm)
        self.assertTrue(seen['audio_interface'].closed)
        sd.RawInputStream.return_value.close.assert_called()
        sd.RawOutputStream.return_value.close.assert_called()
        handler = seen['client_tools'].tools['jarvis_desktop'][0]
        self.assertFalse(json.loads(handler({'action':'open','target':'github','value':''}))['ok'])

    def test_sleep_rearms_without_second_worker(self):
        def worker(action):self.runtime.cancel.wait(3)
        with patch.object(self.runtime,'run',side_effect=worker):
            self.runtime.control('talk');worker_thread=self.runtime.worker
            self.runtime.control('sleep')
            self.assertTrue(self.runtime.rearm);self.assertTrue(self.runtime.end_turn.is_set())
            self.assertIs(worker_thread,self.runtime.worker);self.runtime.close()

class HTTPTest(unittest.TestCase):
    def setUp(self):
        DashboardTest.setUp(self)
        self.server=DashboardServer(('127.0.0.1',0),self.state,self.runtime,'test-token')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.shutdown)
    def shutdown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(1);self.runtime.close()
    def request(self,path,body=None,token='test-token',extra=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        headers={'Authorization':'Bearer '+token}
        if body is not None:headers['Content-Type']='application/json'
        headers.update(extra or {})
        conn.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,headers)
        response=conn.getresponse();status=response.status;data=response.read();conn.close()
        return status,data
    def test_api_requires_token(self):
        self.assertEqual(self.request('/api/state',token='wrong')[0],401)
        self.assertEqual(self.request('/api/state')[0],200)
    def test_cross_origin_rejected(self):
        self.assertEqual(self.request('/api/forget',{'key':'test'},extra={'Origin':'https://example.org'})[0],403)
    def test_foreign_host_rejected(self):
        self.assertEqual(self.request('/api/state',extra={'Host':'evil.example'})[0],403)
    def test_no_file_server_escape(self):
        for path in ('/.env','/../.env','/desktop_config.json'):
            self.assertEqual(self.request(path)[0],404)
    def test_unknown_launch_is_rejected(self):
        status,data=self.request('/api/launch',{'target':'cmd /c anything'})
        self.assertEqual(status,200);self.assertFalse(json.loads(data)['ok'])
    def test_no_state_changing_get(self):
        self.assertEqual(self.request('/api/control?action=talk')[0],404)
    def test_settings_blocked_while_running(self):
        with patch.object(self.runtime,'active',return_value=True):
            self.assertEqual(self.request('/api/settings',dict(device='1',rate=16000,channels=1))[0],400)

if __name__=='__main__':unittest.main()
