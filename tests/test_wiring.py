"""Verify the real SDK's registration and client wiring without audio hardware."""
import importlib
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

class WiringTest(unittest.TestCase):
    def test_conversation_registers_handler(self):
        # Linux verification environment has no PortAudio. No device is opened.
        with patch.dict(sys.modules, {'sounddevice': MagicMock()}):
            chat = importlib.import_module('jarvis_chat')
            with patch.object(chat.jarvis, '_choose_input_device', return_value=2), \
                 patch.object(chat, 'Conversation') as conversation, \
                 patch.object(chat, 'ElevenLabs'), \
                 patch.dict(os.environ, {'ELEVENLABS_API_KEY':'test-only', 'JARVIS_CHAT_INPUT_RATE':'16000', 'JARVIS_CHAT_INPUT_CHANNELS':'1'}), \
                 patch.object(sys, 'argv', ['jarvis_chat.py','--now']):
                self.assertEqual(chat.main(), 0)
                kwargs = conversation.call_args.kwargs
                self.assertTrue(kwargs['requires_auth'])
                registered = kwargs['client_tools'].tools
                self.assertIn('jarvis_google', registered)
                handler = registered['jarvis_desktop']
                # SDK registration storage is a tuple (handler, is_async).
                if isinstance(handler, tuple): handler = handler[0]
                self.assertTrue(json.loads(handler({'action':'list','target':'','value':''}))['ok'])
                conversation.return_value.start_session.assert_called_once()

if __name__ == '__main__': unittest.main()
