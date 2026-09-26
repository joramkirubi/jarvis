"""No live Google account, email delivery, or calendar mutation in these tests."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from google_tools import GoogleTools, GoogleError, GMAIL, message_body

class GoogleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.tools = GoogleTools(Path(self.directory.name))
        self.tools._saved = Mock(return_value={'email':'joram@example.com'})
        self.tools.request = Mock(return_value={'id':'server-id'})
        self.env = patch.dict('os.environ',{'JARVIS_DRY_RUN':'false'}); self.env.start()
    def tearDown(self):
        self.env.stop(); self.directory.cleanup()
    def draft(self):
        return json.loads(self.tools.handle({'action':'draft_email','to':'person@example.com','subject':'Meeting','body':'Hello'}))
    def test_voice_only_proposes(self):
        proposal = self.draft()
        self.assertTrue(proposal['ok']); self.tools.request.assert_not_called()
        for action in ('send','approve','confirm','delete','connect'):
            self.assertFalse(json.loads(self.tools.handle({'action':action}))['ok'])
        self.tools.request.assert_not_called()
    def test_double_confirm_sends_once(self):
        identifier = self.draft()['approval_id']
        self.assertTrue(self.tools.decide(identifier,True)['ok'])
        with self.assertRaises(GoogleError): self.tools.decide(identifier,True)
        self.tools.request.assert_called_once()
        args,kw = self.tools.request.call_args
        self.assertEqual(args,('POST',GMAIL+'/messages/send'))
        self.assertEqual(kw['expected_account'],'joram@example.com')
        raw = base64.urlsafe_b64decode(kw['json']['raw']).decode()
        self.assertIn('To: person@example.com',raw)
        self.assertEqual(self.tools.pending()[0]['state'],'done')
    def test_concurrent_confirmation_claim(self):
        identifier = self.draft()['approval_id']
        def decide():
            try: return self.tools.decide(identifier,True)['ok']
            except GoogleError: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: decide(),range(2)))
        self.assertEqual(sorted(results),[False,True]); self.tools.request.assert_called_once()
    def test_reject_and_expired_never_send(self):
        identifier = self.draft()['approval_id']; self.tools.decide(identifier,False)
        with self.assertRaises(GoogleError): self.tools.decide(identifier,True)
        identifier = self.draft()['approval_id']
        db = self.tools.database()
        with db: db.execute('UPDATE proposals SET created=? WHERE id=?',(time.time()-1900,identifier))
        db.close()
        with self.assertRaises(GoogleError): self.tools.decide(identifier,True)
        self.tools.request.assert_not_called()
    def test_uncertain_write_never_retried(self):
        identifier = self.draft()['approval_id']; self.tools.request.side_effect = TimeoutError('private details')
        with self.assertRaises(GoogleError): self.tools.decide(identifier,True)
        self.assertEqual(self.tools.pending()[0]['state'],'check_google')
        with self.assertRaises(GoogleError): self.tools.decide(identifier,True)
        self.tools.request.assert_called_once()
    def test_account_change_blocks_send(self):
        identifier = self.draft()['approval_id']
        self.tools._saved.return_value = {'email':'different@example.com'}
        with self.assertRaises(GoogleError): self.tools.decide(identifier,True)
        self.tools.request.assert_not_called()
    def test_dry_run_blocks_proposals_and_approvals(self):
        identifier = self.draft()['approval_id']
        with patch.dict('os.environ',{'JARVIS_DRY_RUN':'true'}):
            self.assertTrue(self.draft()['simulated'])
            with self.assertRaises(GoogleError): self.tools.decide(identifier,True)
        self.assertEqual(len(self.tools.pending()),1); self.tools.request.assert_not_called()
    def test_header_injection_rejected(self):
        for bad in ({'to':'a@example.com\nBcc: b@example.com'}, {'subject':'Hello\r\nBcc: b@example.com'}):
            result = json.loads(self.tools.handle({'action':'draft_email','to':'a@example.com','subject':'Hello','body':'World',**bad}))
            self.assertFalse(result['ok'])
        self.assertEqual(self.tools.pending(),[])
    def test_event_requires_offset_and_end_after_start(self):
        event = {'action':'draft_event','subject':'PesaIQ','start':'2026-10-01T10:00:00','end':'2026-10-01T11:00:00+03:00'}
        self.assertFalse(json.loads(self.tools.handle(event))['ok'])
        event['start']='2026-10-01T12:00:00+03:00'
        self.assertFalse(json.loads(self.tools.handle(event))['ok'])
        event['start']='2026-10-01T10:00:00+03:00'; event['to']='person@example.com'
        result=json.loads(self.tools.handle(event)); self.assertTrue(result['ok'])
        self.tools.request.assert_not_called()
        self.tools.decide(result['approval_id'],True)
        body=self.tools.request.call_args.kwargs['json']
        self.assertEqual(body['start']['dateTime'],'2026-10-01T10:00:00+03:00')
        self.assertEqual(body['attendees'],[{'email':'person@example.com'}])
        self.assertEqual(self.tools.request.call_args.kwargs['params'],{'sendUpdates':'all'})
    def test_read_only_calls_and_pagination(self):
        self.tools.request.side_effect = [{'messages':[{'id':'abc'}],'nextPageToken':'next'}, {'id':'abc','snippet':'Hi','payload':{'headers':[]}}]
        data=json.loads(self.tools.handle({'action':'search_email','query':'is:unread'}))
        self.assertTrue(data['more_available']); self.assertEqual(len(data['items']),1)
        self.assertTrue(all(c.args[0]=='GET' for c in self.tools.request.call_args_list))
    def test_mime_html_and_attachments(self):
        enc=lambda s:base64.urlsafe_b64encode(s.encode()).decode()
        body,truncated=message_body({'parts':[{'mimeType':'text/html','body':{'data':enc('<p>Hello</p><script>bad</script>')}}, {'mimeType':'text/plain','filename':'secret.txt','body':{'data':enc('attachment')}}]})
        self.assertIn('Hello',body); self.assertNotIn('bad',body); self.assertNotIn('attachment',body)
        body,truncated=message_body({'mimeType':'text/plain','body':{'data':enc('x'*13000)}})
        self.assertEqual(len(body),12000); self.assertTrue(truncated)
    def test_errors_do_not_leak_response_or_credentials(self):
        self.tools.request.side_effect=RuntimeError('secret-token')
        result=self.tools.handle({'action':'search_email'})
        self.assertNotIn('secret-token',result); self.assertFalse(json.loads(result)['ok'])

if __name__=='__main__': unittest.main()
