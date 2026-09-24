"""Local 'Hey Jarvis' listener. Run with --test to test without ElevenLabs."""

import argparse
import json
import os
import queue
import subprocess
import sys
import time
from pathlib import Path

import sounddevice as sd
from audio_pcm import InputPCM
from dotenv import load_dotenv
from vosk import KaldiRecognizer, Model

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def wait_for_wake(model, device, rate, channels, debug=False):
    audio_queue = queue.Queue(maxsize=30)
    converter = InputPCM(rate, channels)
    recognizer = KaldiRecognizer(model, 16000, json.dumps(["hey jarvis", "[unk]"]))

    def capture(data, frames, timing, status):
        if status:
            print("Microphone warning:", status, flush=True)
        try:
            audio_queue.put_nowait(bytes(data))
        except queue.Full:
            # Drop this block instead of blocking the audio callback.
            pass

    print('\nListening locally. Say "Hey Jarvis", then pause.', flush=True)

    with sd.RawInputStream(
        device=device,
        samplerate=rate,
        channels=channels,
        dtype="int16",
        blocksize=rate // 10,
        callback=capture,
    ):
        while True:
            try:
                data = audio_queue.get(timeout=5)
            except queue.Empty:
                raise RuntimeError("No microphone audio received for five seconds.")

            if recognizer.AcceptWaveform(converter.convert(data)):
                text = json.loads(recognizer.Result()).get("text", "")
                if debug and text:
                    print("Locally recognized:", text, flush=True)
                if text.strip() == "hey jarvis":
                    return
    # The context manager closes the microphone before chat starts.


def chime():
    if sys.platform == "win32":
        try:
            import winsound

            winsound.Beep(880, 150)
        except (RuntimeError, OSError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    model_path = ROOT / "models" / "vosk-model-small-en-us-0.15"
    if not model_path.is_dir():
        parser.error(f"Speech model missing: {model_path}")

    raw_device = os.getenv("JARVIS_INPUT_DEVICE", "").strip()
    device = int(raw_device) if raw_device.isdigit() else raw_device or None
    rate = int(os.getenv("JARVIS_CHAT_INPUT_RATE", "16000"))
    channels = int(os.getenv("JARVIS_CHAT_INPUT_CHANNELS", "1"))

    InputPCM(rate, channels)  # Validate format before opening audio.
    sd.check_input_settings(
        device=device, samplerate=rate, channels=channels, dtype="int16"
    )

    print("Loading local speech model...", flush=True)
    model = Model(str(model_path))
    child = None

    try:
        while True:
            wait_for_wake(model, device, rate, channels, args.test)
            print("Wake phrase detected.", flush=True)
            chime()

            if args.test:
                print("Test successful; no cloud conversation started.")
            else:
                print("Connecting. Wait for Jarvis's greeting.", flush=True)
                child = subprocess.Popen(
                    [sys.executable, str(ROOT / "jarvis_chat.py"), "--now"],
                    cwd=str(ROOT),
                )
                code = child.wait()
                child = None
                if code != 0:
                    print("Chat failed. Resolve its error before retrying.")
                    return code

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping wake listener.")
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Wake listener failed: {type(error).__name__}: {error}")
        raise SystemExit(1)
