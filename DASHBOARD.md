# Jarvis Command Centre

A local browser dashboard for the existing Windows ElevenLabs assistant. Launch it from the same `jarvis-main` directory that already contains your working `.env`, wake model, app configuration and memory database.

## Run

Stop other Jarvis microphone listeners first. In VS Code Git Bash:

```bash
cd "$HOME/jarvis-main"
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python jarvis_dashboard.py
```

The browser opens automatically. If it does not, copy the complete local link printed in the terminal, including the part after `#`. Keep that link private: its random token authorizes this dashboard session. On every server restart a new link is generated. Use `python jarvis_dashboard.py --port 8766` if port 8765 is already occupied, or `--no-browser` to print the link without opening it.

No Node.js, npm, new API key or additional Python package is needed for the dashboard. Existing Python dependencies are reused. Its HTML, CSS and JavaScript are served from this repository; no fonts or scripts load from a CDN.

## Controls

- **Start conversation:** opens the microphone and connects to the same ElevenLabs agent used by `jarvis_chat.py`. Wait for the greeting, then speak.
- **Enable wake word:** listens locally through Vosk for “Hey Jarvis”, then starts a cloud conversation. Wait for the greeting before your command.
- **Go to sleep:** ends the current conversation and returns to local wake listening. You can also say exactly “Go to sleep”, “Jarvis, go to sleep”, or “Hey Jarvis, go to sleep” during a conversation. Detection uses the cloud transcript, so it is not an instant offline mute. These phrases are intercepted by this new dashboard runtime; the old terminal launchers are unchanged.
- **Stop listening:** ends both the cloud conversation and wake listening. No microphone should remain open after the status becomes Standby.
- **Ctrl+C in the terminal:** shuts down the dashboard and its audio runtime. Closing the browser alone does not stop listening. Open another tab using the session link to reconnect.

One voice worker runs at a time. Switching from active wake mode to an immediate conversation requires Stop first. Start controls are unavailable while a worker is running. A pending cloud connection may take a few seconds to close after Stop.

## What each panel means

- **Voice core:** actual runtime state (Standby, Initializing, Wake listening, Connecting, Listening, Speaking, Stopping, Attention). Speaking follows audio playback activity; there is no invented thinking/LLM latency metric. The orbit rotates while a microphone stream is active. The centre glow responds to measured microphone RMS, with a display-only gain; it does not amplify uploaded audio.
- **Conversation:** user transcripts and agent responses for this server run, capped at 100 entries. The browser renders them as plain text, not HTML.
- **Activity:** voice lifecycle and actual local tool results, capped at 60 entries. A successful launch means the OS/browser accepted the request, not that a window has been visually verified. Dry-run actions are labelled simulated.
- **System:** whether a key is configured (not proof authentication works), whether the Vosk model folder exists, server uptime, conversation starts and tool calls. No fake CPU or GPU statistics.
- **Quick launch:** the existing enabled targets in `desktop_config.json`, executed through `DesktopTools` and its existing permissions.
- **Memory vault:** the same `.jarvis/memory.sqlite3` database used by your voice tools. Refresh is automatic every five seconds or manual. Delete asks for confirmation and removes only that exact key. Deleting locally does not remove cloud history.

The browser polls state about three times per second; these are live local snapshots, not a cloud monitoring service.

## Microphone and application settings

Open **Audio & preferences**. Stop listening, choose the input device, capture rate (16000 or 48000 Hz) and channels (1 or 2), then save. Settings persist in `.jarvis/dashboard.json`, which is already ignored by Git. Until saved, the dashboard uses your `.env` microphone settings. After saving, dashboard settings override them for this launcher only; your original terminal launchers still use `.env`.

Refresh the device list after reconnecting a headset. Numeric input indices can change on Windows. Output uses the Windows default playback device at 16 kHz mono, as in the working chat launcher.

**Manage** in Quick launch toggles existing targets. It changes only their `enabled` flags in `desktop_config.json`; file paths and URLs are edited manually as before. Those configuration changes are Git-visible, so inspect them before committing. Enabling the PesaIQ entry does not fill in its placeholder path: configure its real folder first.

`JARVIS_DRY_RUN=true` is honored by launch and voice tools. Explicit memory deletion in the dashboard is still real; the confirmation dialog applies.

## Local access and data

The HTTP listener binds only to `127.0.0.1`. API calls require a random per-run bearer token and a matching Host/Origin. There is no cross-origin API access, general filesystem endpoint, arbitrary command runner, public hosting or remote-control setup. Do not expose this server through a proxy or router port forwarding.

The API key stays in Python/.env and is never returned to the browser. It is shown only as configured/missing. UI preferences and memory remain on your computer. Conversation audio and transcripts use ElevenLabs, and recalled preferences go to its agent as tool results. Existing agent retention settings still apply. Dashboard transcripts and activity are in RAM and disappear when the server exits; that does not delete ElevenLabs history. Any trusted user who possesses the local session link can control this dashboard.

This server is intended for your personal local desktop, not multi-user production hosting.

## First-run verification

1. Launch the dashboard. Confirm Standby and a zero microphone meter.
2. Open audio settings and confirm the working internal microphone.
3. Start conversation, wait for the greeting, and say “Open GitHub”. Confirm both the browser action and the activity result.
4. Say “Remember that I prefer short answers”. Confirm the memory panel updates.
5. Click Go to sleep. Confirm Wake listening and say “Hey Jarvis” to reconnect.
6. Click Stop listening. Confirm Standby. Test that speaking the wake phrase no longer starts a session.
7. Optionally test local memory deletion and disable/enable a configured app.
8. Stop the server with Ctrl+C.

## Troubleshooting

- **Disconnected / session link error:** use the full new link from the current Python process. A bookmark without its token does not authorize a new session.
- **No audio devices:** activate the project's venv and reinstall requirements; check Windows audio and microphone permissions. The dashboard can open even when audio discovery fails.
- **Mic silent:** select the working input (your device numbers have changed before). Try the same rate/channels that worked in chat. Only run one Jarvis launcher at a time.
- **Wake disabled:** check `models/vosk-model-small-en-us-0.15` exists. Reuse your already downloaded model. No download is automatic.
- **Start disabled / key missing:** retain your real API key in this folder's `.env`, then restart the server.
- **Voice fails / Attention:** check the Python terminal, microphone format, ElevenAgents Write permission, network and certificate trust. API response bodies are not forwarded to the browser. Start the known-working `python jarvis_chat.py --now` separately to isolate a cloud/audio issue. Do not disable TLS verification.
- **Sleep phrase not detected:** the transcription must match one of the exact phrases above, after punctuation is removed. Use the Go to sleep button if recognition differs.
- **Model loads slowly:** the first wake start loads Vosk. Stop will take effect once that load completes.
- **Memory or config read error:** check that `desktop_config.json` is valid JSON and that the memory SQLite file is intact. Do not delete existing data as a first troubleshooting step.

## Development and rollback

Added files: `jarvis_dashboard.py`, `dashboard_state.py`, `dashboard_runtime.py`, `dashboard/`, this guide and `tests/test_dashboard.py`. `README.md` adds a link to this guide. Original `jarvis.py`, `jarvis_chat.py`, `jarvis_wake.py`, tools and agent configuration are unchanged.

```bash
python -m unittest discover -s tests -v
```

Tests use temporary databases, mocked desktop effects/audio/ElevenLabs calls and a loopback HTTP server. They cover local authorization, cross-origin rejection, path restrictions, allowed targets, persistent preferences, audio settings, single-worker control and sleep cleanup. Real Windows microphone capture, voice quality and end-to-end ElevenLabs sessions require the first-run check on your laptop.

To roll back, stop this launcher and use `python jarvis_wake.py` or `python jarvis_chat.py --now`. The existing launchers and `.env` are preserved. A saved dashboard microphone preference does not change them.

## Validation of this patch

30 Python tests passed on Linux/Python 3.12. JavaScript syntax was checked. Chromium rendered the dashboard at 1440 px and 390 px widths with no page-script errors or horizontal overflow; audio and app-settings dialogs opened correctly. No Windows microphone or live ElevenLabs session was available in the build environment. The first-run steps above are the required local hardware check.
