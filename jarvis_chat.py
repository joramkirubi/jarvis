"""Clap-to-talk companion. Leaves the original jarvis.py untouched."""
import argparse
import os
import threading
import time

import jarvis
import sounddevice as sd
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import AudioInterface, Conversation, ClientTools

from desktop_tools import DesktopTools
from google_tools import GoogleTools
from audio_pcm import InputPCM

AGENT_ID = 'agent_5601m39sh6kne8tt9d7wxgpqwz2j'


class DesktopAudio(AudioInterface):
    """16kHz mono PCM, using the same sounddevice mic as clap detection."""
    def __init__(self, device, rate=16000, channels=1):
        self.device = device
        self.rate, self.channels = rate, channels
        self.converter = InputPCM(rate, channels)
        self.lock = threading.Lock()
        self.pending = bytearray()
        self.streams = []

    def start(self, input_callback):
        def capture(data, frames, timing, status):
            input_callback(self.converter.convert(bytes(data)))

        def playback(out, frames, timing, status):
            size = len(out)
            with self.lock:
                data = bytes(self.pending[:size])
                del self.pending[:size]
            out[:] = data + bytes(size - len(data))

        try:
            output = sd.RawOutputStream(samplerate=16000, channels=1,
                dtype='int16', blocksize=320, callback=playback)
            self.streams.append(output)
            output.start()
            microphone = sd.RawInputStream(device=self.device, samplerate=self.rate,
                channels=self.channels, dtype='int16', blocksize=self.rate // 4, callback=capture)
            self.streams.append(microphone)
            microphone.start()
        except Exception:
            self.stop()
            raise

    def output(self, audio):
        with self.lock:
            self.pending.extend(audio)

    def interrupt(self):
        with self.lock:
            self.pending.clear()

    def stop(self):
        streams, self.streams = self.streams, []
        for stream in reversed(streams):
            try:
                stream.stop()
            finally:
                stream.close()
        self.interrupt()


def wait_for_claps(device):
    print('Clap twice to start a conversation. Ctrl+C cancels.')
    first = None
    armed = True
    floor = 1e-4
    block = jarvis.block_samples()
    with sd.InputStream(device=device, samplerate=jarvis.SAMPLE_RATE,
            channels=1, dtype='float32', blocksize=block) as stream:
        while True:
            data, overflow = stream.read(block)
            if overflow:
                first = None
                continue
            level = jarvis.rms_mono(data)
            if level < floor * jarvis.QUIET_GATE_MULT:
                floor = max(1e-7, jarvis.NOISE_FLOOR_ALPHA * floor +
                            (1 - jarvis.NOISE_FLOOR_ALPHA) * level)
            threshold = max(jarvis.MIN_RMS, floor * jarvis.SPIKE_RATIO)
            now = time.monotonic()
            if first is not None and now - first > jarvis.MAX_DOUBLE_GAP_S:
                first = None
            if level < threshold * jarvis.RETRIGGER_RATIO:
                armed = True
            if armed and level >= threshold:
                armed = False
                if first is None:
                    first = now
                elif jarvis.MIN_DOUBLE_GAP_S <= now - first <= jarvis.MAX_DOUBLE_GAP_S:
                    return  # Close clap stream before opening conversation microphone.


def main():
    parser = argparse.ArgumentParser(description='Talk to Jarvis through ElevenLabs Agents')
    parser.add_argument('--now', action='store_true', help='Start without clapping')
    args = parser.parse_args()
    key = os.getenv('ELEVENLABS_API_KEY', '').strip()
    if not key:
        parser.error('Save ELEVENLABS_API_KEY in your existing .env first.')
    conversation = None
    audio = None
    try:
        rate = int(os.getenv('JARVIS_CHAT_INPUT_RATE', '16000'))
        channels = int(os.getenv('JARVIS_CHAT_INPUT_CHANNELS', '1'))
        InputPCM(rate, channels)  # Validate before opening audio.
        desktop = DesktopTools(dry_run=os.getenv('JARVIS_DRY_RUN', '').lower() == 'true')
        client_tools = ClientTools()
        client_tools.register('jarvis_desktop', desktop.handle)
        client_tools.register('jarvis_google', GoogleTools().handle)
        device = jarvis._choose_input_device(jarvis.block_samples())
        sd.check_input_settings(device=device, samplerate=rate, channels=channels, dtype='int16')
        sd.check_output_settings(samplerate=16000, channels=1, dtype='int16')
        if not args.now:
            wait_for_claps(device)
        audio = DesktopAudio(device, rate, channels)
        conversation = Conversation(
            client=ElevenLabs(api_key=key),
            agent_id=os.getenv('ELEVENLABS_AGENT_ID', AGENT_ID),
            requires_auth=True,
            client_tools=client_tools,
            audio_interface=audio,
            callback_agent_response=lambda message: print('Jarvis:', message),
            callback_user_transcript=lambda message: print('You:', message),
        )
        print('Connecting. Wait for the greeting, then speak. Ctrl+C ends the session.')
        conversation.start_session()
        conversation.wait_for_session_end()
        print('Conversation ended. Run again for another session.')
    except KeyboardInterrupt:
        print('\nStopping Jarvis.')
    except Exception as error:
        # Avoid printing signed URLs, API keys or raw authentication responses.
        print(f'Connection/audio failed ({type(error).__name__}). Check microphone, network, '
              'and Agents permissions on your API key. See CHAT_SETUP.md.')
        return 1
    finally:
        if conversation is not None:
            try:
                conversation.end_session()
            except Exception:
                pass
        if audio is not None:
            audio.stop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
