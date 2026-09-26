"""Single microphone owner; cancellable local wake detection and cloud conversations."""
import json
import os
import queue
import re
import threading
import time

class VoiceRuntime:
    def __init__(self, state):
        self.state = state
        self.guard = threading.RLock()
        self.worker = None
        self.cancel = threading.Event()
        self.end_turn = threading.Event()
        self.rearm = False
        self.model = None

    def active(self):
        return self.worker is not None and self.worker.is_alive()

    def control(self, action):
        with self.guard:
            if action == 'stop':
                self.cancel.set()
                self.end_turn.set()
                if self.active(): self.state.set_status('stopping', 'Closing the microphone and conversation…')
                return
            if action == 'sleep':
                if not self.active():
                    return self.control('wake')
                self.rearm = True
                self.end_turn.set()
                return
            if action not in ('talk', 'wake'):
                raise ValueError('Unknown voice action')
            if self.active():
                raise ValueError('Stop the current listener before starting another mode')
            self.cancel = threading.Event()
            self.end_turn = threading.Event()
            self.rearm = action == 'wake'
            self.state.set_status('starting', 'Preparing audio…')
            self.worker = threading.Thread(target=self.run, args=(action,), daemon=True)
            self.worker.start()

    def refresh_devices(self):
        try:
            import sounddevice as sd
            devices = [dict(id=i,name=d['name'],channels=d['max_input_channels']) for i,d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0]
            with self.state.lock:
                self.state.devices, self.state.device_error = devices, None
        except Exception:
            with self.state.lock:
                self.state.device_error = 'Audio devices unavailable. Install requirements and check Windows audio.'

    def wake(self, sd, device, rate, channels):
        from vosk import Model, KaldiRecognizer
        from audio_pcm import InputPCM
        path = self.state.root/'models'/'vosk-model-small-en-us-0.15'
        if not path.is_dir():
            raise RuntimeError('Wake model missing; see DASHBOARD.md')
        self.state.set_status('starting', 'Loading local wake-word model…')
        if self.model is None: self.model = Model(str(path))
        if self.cancel.is_set(): return False
        recognizer = KaldiRecognizer(self.model,16000,json.dumps(['hey jarvis','[unk]']))
        converter = InputPCM(rate,channels)
        audio = queue.Queue(maxsize=30)
        def capture(data, frames, timing, status):
            try: audio.put_nowait(bytes(data))
            except queue.Full: pass
        with sd.RawInputStream(device=device,samplerate=rate,channels=channels,dtype='int16',blocksize=rate//10,callback=capture):
            self.state.set_status('wake', 'Listening locally for “Hey Jarvis”.')
            last = time.monotonic()
            while not self.cancel.is_set():
                try: data = audio.get(timeout=.2)
                except queue.Empty:
                    if time.monotonic()-last > 5: raise RuntimeError('Microphone stopped delivering audio')
                    continue
                last = time.monotonic()
                pcm = converter.convert(data)
                self.measure(pcm)
                if recognizer.AcceptWaveform(pcm):
                    if json.loads(recognizer.Result()).get('text','').strip() == 'hey jarvis':
                        self.state.event('Wake phrase detected', 'Opening your conversation', 'success')
                        return True
        return False

    def measure(self, pcm):
        import numpy as np
        samples = np.frombuffer(pcm,dtype='<i2').astype(float)
        if samples.size:
            # A display gain makes quiet laptop microphones readable, without altering audio.
            self.state.meter(float(np.sqrt(np.mean(samples*samples)))/32768*12)

    def chat(self, sd, device, rate, channels):
        from elevenlabs.client import ElevenLabs
        from elevenlabs.conversational_ai.conversation import AudioInterface, Conversation, ClientTools
        from audio_pcm import InputPCM
        key = os.getenv('ELEVENLABS_API_KEY','').strip()
        if not key: raise RuntimeError('API key missing; set ELEVENLABS_API_KEY in .env')
        self.end_turn.clear()
        runtime = self
        class Audio(AudioInterface):
            def __init__(self):
                self.lock = threading.Lock()
                self.pending = bytearray()
                self.streams = []
                self.converter = InputPCM(rate,channels)
                self.speaking = False
                self.closed = False
                self.last_meter = 0
            def start(self, callback):
                if self.closed or runtime.cancel.is_set() or runtime.end_turn.is_set():
                    return
                def capture(data, frames, timing, status):
                    pcm = self.converter.convert(bytes(data))
                    if not runtime.cancel.is_set() and not runtime.end_turn.is_set(): callback(pcm)
                    if time.monotonic()-self.last_meter > .08:
                        runtime.measure(pcm)
                        self.last_meter = time.monotonic()
                def playback(out, frames, timing, status):
                    with self.lock:
                        data = bytes(self.pending[:len(out)])
                        del self.pending[:len(out)]
                    out[:] = data + bytes(len(out)-len(data))
                    speaking = bool(data)
                    if speaking != self.speaking:
                        self.speaking = speaking
                        if not runtime.cancel.is_set() and not runtime.end_turn.is_set():
                            runtime.state.set_status('speaking' if speaking else 'listening', 'Jarvis is speaking.' if speaking else 'Your microphone is live. Speak naturally.')
                try:
                    output = sd.RawOutputStream(samplerate=16000,channels=1,dtype='int16',blocksize=320,callback=playback)
                    self.streams.append(output); output.start()
                    if self.closed or runtime.cancel.is_set():
                        self.stop(); return
                    mic = sd.RawInputStream(device=device,samplerate=rate,channels=channels,dtype='int16',blocksize=rate//10,callback=capture)
                    self.streams.append(mic); mic.start()
                    if self.closed or runtime.cancel.is_set():
                        self.stop(); return
                    runtime.state.set_status('listening','Your microphone is live. Speak naturally.')
                except Exception:
                    self.stop(); raise
            def output(self, audio):
                with self.lock: self.pending.extend(audio)
            def interrupt(self):
                with self.lock: self.pending.clear()
            def stop(self):
                self.closed = True
                streams,self.streams = self.streams,[]
                for stream in reversed(streams):
                    try: stream.abort()
                    except Exception: pass
                    try: stream.close()
                    except Exception: pass
                self.interrupt()

        def transcript(text):
            self.state.message('user',text)
            phrase = re.sub(r'[^a-z ]','',text.lower()).strip()
            if phrase in ('go to sleep','jarvis go to sleep','hey jarvis go to sleep'):
                self.rearm = True
                self.end_turn.set()
                self.state.event('Sleep requested','Returning to local wake listening')
        def agent_response(text):
            self.state.message('assistant',text)
        def handler(parameters):
            if self.cancel.is_set() or self.end_turn.is_set():
                return json.dumps({'ok':False,'message':'Conversation is ending; no new action executed'})
            return self.state.tool(parameters)
        tools = ClientTools()
        tools.register('jarvis_desktop',handler)
        def google_handler(parameters):
            if self.cancel.is_set() or self.end_turn.is_set():
                return json.dumps({'ok':False,'message':'Conversation is ending'})
            return self.state.google.handle(parameters)
        tools.register('jarvis_google', google_handler)
        audio = Audio()
        conversation = Conversation(client=ElevenLabs(api_key=key),
            agent_id=os.getenv('ELEVENLABS_AGENT_ID','agent_5601m39sh6kne8tt9d7wxgpqwz2j'),
            requires_auth=True,audio_interface=audio,client_tools=tools,
            callback_user_transcript=transcript,callback_agent_response=agent_response)
        ended = threading.Event()
        watcher_started = False
        self.state.set_status('connecting','Connecting to ElevenLabs…')
        try:
            if self.cancel.is_set(): return
            conversation.start_session()
            with self.state.lock: self.state.sessions += 1
            self.state.event('Conversation started','ElevenLabs voice session')
            def wait():
                try: conversation.wait_for_session_end()
                finally: ended.set()
            threading.Thread(target=wait,daemon=True).start()
            watcher_started = True
            while not self.cancel.wait(.1) and not self.end_turn.is_set() and not ended.is_set(): pass
        finally:
            self.end_turn.set()
            audio.stop()
            try:
                conversation.end_session()
                if watcher_started and not ended.wait(12):
                    raise RuntimeError("Voice connection is still shutting down; restart the dashboard before starting another session")
            finally: audio.stop()
            self.state.event('Conversation ended','Microphone released')

    def run(self, action):
        failed = False
        try:
            import sounddevice as sd
            with self.state.lock: settings = dict(self.state.settings)
            raw = settings['device']
            device = int(raw) if raw.isdigit() else raw or None
            rate,channels = settings['rate'],settings['channels']
            sd.check_input_settings(device=device,samplerate=rate,channels=channels,dtype='int16')
            sd.check_output_settings(samplerate=16000,channels=1,dtype='int16')
            while not self.cancel.is_set():
                if action == 'wake' and not self.wake(sd,device,rate,channels): break
                if self.cancel.is_set(): break
                if action == 'wake' and os.name == 'nt':
                    try:
                        import winsound
                        winsound.Beep(880,150)
                    except Exception: pass
                self.chat(sd,device,rate,channels)
                if not self.rearm or self.cancel.wait(.5): break
                action = 'wake'
        except Exception as error:
            failed = True
            # Avoid exposing signed URLs, authentication payloads or credentials.
            self.state.set_status('error', f'{type(error).__name__}: check audio settings, API permissions and model installation. See DASHBOARD.md.')
            self.state.event('Voice session failed',type(error).__name__,'error')
        finally:
            self.state.meter(0)
            if not failed: self.state.set_status('idle','Microphone off. Ready when you are.')

    def close(self):
        self.control('stop')
        if self.worker: self.worker.join(timeout=5)
