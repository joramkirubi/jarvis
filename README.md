# Jarvis Desktop for Joram

## Local dashboard

Run `python jarvis_dashboard.py` for the local Jarvis Command Centre: live voice state, conversation, app launchers, memory and audio settings. See [DASHBOARD.md](DASHBOARD.md) for setup, sleep/wake controls and troubleshooting.

Speak to Jarvis, launch approved apps and websites, open browser searches, and explicitly save preferences between sessions. This is a Windows desktop upgrade of [hectorg2211/jarvis](https://github.com/hectorg2211/jarvis).

## What is included

| Feature | Status |
| --- | --- |
| ElevenLabs voice conversation | Included; internet and your API key required |
| Double clap to start a conversation | Included; or use `--now` |
| Spoken app/website/folder launching | Included through a local allowlist |
| Browser searches | Included; opens Google, does not read results |
| Persistent preference memory | Included; local SQLite, explicit save/recall |
| Tool permissions and dry run | Included |
| Optional 48 kHz stereo microphone capture | Included; converts to 16 kHz mono for ElevenLabs |
| Automated unit tests and CI workflow | Included |
| Original Spotify/Chrome/Cursor welcome flow | Preserved in `jarvis.py` |
| “Hey Jarvis” wake activation and local dashboard | Included; see DASHBOARD.md |
| Screen reading, document reading/editing | Not included |
| Email, calendar, task management, autonomous multi-step routines | Not included |
| Offline voice conversation and plugin marketplace | Not included |

The modules provide a foundation for later features; this ZIP does not implement every item on the future roadmap.

## 1. Install without losing your working copy

1. Stop your old Jarvis with **Ctrl+C**.
2. Extract this ZIP to a **new folder**, for example `C:/Users/Joram Kirubi/jarvis-desktop-upgrade`. Keep the old folder as your backup.
3. Open the new folder in VS Code. The correct folder directly contains `jarvis_chat.py` and this README.
4. Copy your own `.env` from the old folder to this folder. Do not share it. Do not copy the old `.venv`; create a new one below.
5. If you never had a `.env`, copy `.env.example` to `.env`, then replace the key placeholder.

In the **VS Code Git Bash terminal**:

```bash
py -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

In PowerShell instead, activation is `.\.venv\Scripts\Activate.ps1`. Do not paste that command into Git Bash.

Use your current Python 3.14 first. If a dependency fails to install and reports no matching wheel, install Python 3.12 alongside it and create a fresh environment using `py -3.12 -m venv .venv` in a fresh project copy. Tests here were run on Python 3.12; the CI configuration also covers 3.14 but has not been run on GitHub for you.

## 2. Select the upgraded ElevenLabs agent

A separate agent has been configured in your connected ElevenLabs workspace:

- Name: **Jarvis Desktop — Apps, Search & Memory**
- Agent ID: `agent_5601m39sh6kne8tt9d7wxgpqwz2j`
- Client tool: `jarvis_desktop`
- Tool ID: `tool_2501m39shpv2emts6zgyf724j4px`

Edit `.env`. Keep your real key and your working microphone choice, and set this agent ID:

```dotenv
ELEVENLABS_API_KEY=your_real_key_here
ELEVENLABS_AGENT_ID=agent_5601m39sh6kne8tt9d7wxgpqwz2j
```

**Replace an existing `ELEVENLABS_AGENT_ID` line; do not add duplicates.** The old ID points to your old conversational agent and will not give you the new tools. A variable already exported in the terminal can override `.env`; open a fresh terminal if values seem stale. Restart the Python program after changing configuration.

Your key must belong to the workspace containing this agent and have **ElevenAgents → Write** permission (`convai_write`). Your earlier signed-URL request failed with Read-only permission. For the separate original fixed welcome speech, retain **Text to Speech → Access** and `ELEVENLABS_VOICE_ID`. Other unrelated API permissions are not needed for these desktop commands.

You do not need to recreate the tool in the dashboard. `agent_prompt.txt` and `agent_tool.json` are included as references if you later rebuild the agent in another workspace. For that case create a client tool from the JSON, attach it to your agent, use the prompt, set both agent audio formats to PCM 16000, enable authentication and the `client_tool_call` client event, and put the new agent ID in `.env`. Keep the tool name exactly `jarvis_desktop`.

The dashboard's browser preview does not execute Python tools on your laptop. Run this Python client to use desktop actions.

## 3. Check local tools, then talk

These commands do not use ElevenLabs:

```bash
python desktop_tools.py list
python desktop_tools.py open github --dry-run
python -m unittest discover -s tests -v
```

Start voice conversation:

```bash
python jarvis_chat.py --now
```

Wait for Jarvis's greeting, then say:

- “What applications can you open?”
- “Open GitHub.”
- “Open Notepad.”
- “Open VS Code.”
- “Search the web for Python desktop automation tutorials.”
- “Remember that I prefer short answers.”
- “What preferences have you saved for me?”

The terminal prints `Desktop tool: open OK` or `FAILED` when the local handler runs. An OK launch means Windows/browser accepted the request; it does not verify that a visible window appeared. Search opens a page and cannot summarize it. The model may need a clarification if a target is ambiguous.

End with **Ctrl+C**. For clap activation:

```bash
python jarvis_chat.py
```

Clap twice. One conversation starts; after it ends, run the command again. For “Hey Jarvis” activation, use `python jarvis_wake.py` or enable wake listening in the dashboard. While the conversation is active, speak normally without clapping again. The cloned agent currently has a 10-minute maximum session duration.

This chat launcher does not automatically open Spotify. To use the original welcome automation, run `python jarvis.py` instead; see `LEGACY_README.md` for its constants and behavior. Avoid running both microphone listeners at once.

## 4. Configure your apps and PesaIQ folder

Edit `desktop_config.json` in VS Code. This is trusted local configuration, not something the model can edit.

Built-in targets:

| ID | Default |
| --- | --- |
| `github` | GitHub in default browser |
| `chatgpt` | ChatGPT in default browser |
| `notepad` | Windows System32 Notepad |
| `calculator` | Windows System32 Calculator |
| `vscode` | Per-user VS Code install |
| `pesaiq` | Disabled until you enter your actual project folder |

For `pesaiq`, replace `location` with your existing folder and set `enabled` to `true`. Example (replace with your actual path):

```json
"pesaiq": {
  "type": "folder",
  "location": "C:/Users/Joram Kirubi/Documents/PesaIQ",
  "enabled": true,
  "description": "My PesaIQ project folder"
}
```

Then say “Open my PesaIQ folder.” It opens File Explorer; it does not read your files.

If VS Code fails, find `Code.exe` through its shortcut properties and edit its location. A system install may be `C:/Program Files/Microsoft VS Code/Code.exe`. Use forward slashes in JSON paths, or escape backslashes as `\\`. App entries must identify an existing absolute `.exe` path. `.cmd`, `.bat`, shell commands and model-provided paths are not accepted. This version does not support custom application arguments.

Add other entries using the same structure: `type` is `app`, `folder`, or `url`. URL entries must use HTTPS. Use a short unique ID and restart Jarvis after editing. Only enable programs you intend to make available by voice; do not add command interpreters as apps.

## 5. Memory, permissions and privacy

Memory is stored in `.jarvis/memory.sqlite3` under this installation. It persists across restarts in the same folder. It is plain local data, not encrypted, and is shared by anyone using this project copy. Copy this file only if you deliberately want to migrate saved preferences.

The agent is instructed to save only on explicit requests. This is a model instruction, not a secret detector: **do not ask it to store passwords, keys or sensitive records**. Saving the same key replaces its previous value. Keys allow lowercase letters, numbers, underscores and hyphens (1–64 characters). Values are limited to 1,000 characters. Recall returns up to 30 matching entries; search is a case-sensitive substring match, not semantic memory.

Local inspection and deletion:

```bash
python desktop_tools.py recall
python desktop_tools.py remember answer_style "Keep replies short"
python desktop_tools.py recall answer_style
python desktop_tools.py forget answer_style
```

Deletion is available locally, not as a voice tool. Stop Jarvis and delete `.jarvis/memory.sqlite3` in File Explorer to reset all local preferences. This does not delete cloud conversation history.

Voice audio, transcripts, and recalled preferences sent as tool results are processed by ElevenLabs. “Local memory” describes where the database lives; recalled content still reaches the cloud agent. The copied agent currently retains the original privacy configuration: voice recording enabled, retention value `-1`, no automatic transcript/audio deletion. Review its Privacy settings in ElevenLabs if you want different retention. Conversation service usage can incur ElevenLabs charges; no API key or credits are included in the ZIP.

In `desktop_config.json`, set any action under `permissions` to `false` to disable it, then restart Jarvis. For example disable `remember` and `recall` to prevent voice access to memory. Local `forget` remains available for cleanup. No general terminal execution, email sending or file editing tool is exposed. Allowed actions run immediately when called; voice input is not identity authentication, so nearby voices may trigger them during a session.

For simulated launch/search/save actions, add to `.env`:

```dotenv
JARVIS_DRY_RUN=true
```

In dry run, app launches/searches and memory writes are simulated. List/recall still work; recall may initialize an empty database. Change back to `false` for real actions. Terminal tool logs show action/status; conversation text is also printed. There is no separate persistent audit log.

## 6. Microphone settings and troubleshooting

Keep your working mic configuration first. Defaults remain **16000 Hz, mono** for chat. List devices with:

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Set `JARVIS_INPUT_DEVICE` in `.env` to the current input index or matching device name. Device indices may change after plugging in headphones or restarting Windows. Choose an input microphone, not Stereo Mix or a speaker output. The original automatic probe is retained and uses the clap capture format; its warning is not a definitive test of chat audio.

For a device that works at 48 kHz stereo, try:

```dotenv
JARVIS_CHAT_INPUT_RATE=48000
JARVIS_CHAT_INPUT_CHANNELS=2
```

These settings affect conversation input only; capture is averaged to mono and filtered/downsampled to 16 kHz before sending to ElevenLabs. Supported rates are 16000 and 48000, with 1 or 2 channels. They do not change Windows settings or clap detection. If stereo averaging causes cancellation or unclear voice, try one channel. Output remains 16 kHz mono on the Windows default playback device.

| Symptom | What to check |
| --- | --- |
| Jarvis talks but cannot hear you | Windows Sound input test first; select the correct microphone, check mute/privacy permission/input level; use headphones to reduce echo. Then verify the device index and input format. |
| `PortAudioError` | Device may reject the selected rate/channels or be busy. Close other listeners; try your previously working settings and `--now`. |
| Recording/listener hangs | Ctrl+C; restart terminal and audio device. Do not leave several Jarvis processes running. Test the mic in Windows before retrying Python. |
| Clap mode fails but `--now` works | Clap detection uses `jarvis.py` sample rate/constants separately. Tune those as described in the legacy README. |
| 401 / missing `convai_write` | Enable ElevenAgents Write on the actual API key loaded by this process. |
| 401 / missing `text_to_speech` | Enable Text to Speech Access for the original welcome script. |
| SSL certificate verification error | Check the existing Kaspersky encrypted-connection exception/trust configuration for `api.elevenlabs.io`; never disable Python TLS verification. |
| Jarvis talks but no tool log appears | Check the new agent ID in `.env`, fresh process, correct workspace and attached `jarvis_desktop` client tool. Old agent has no desktop tool. |
| Tool says FAILED | Check enabled target, action permission, exact existing `.exe`/folder path, default browser, and JSON syntax. Use local CLI below to isolate cloud from desktop. |
| `ModuleNotFoundError` | Activate this folder's `.venv`; reinstall requirements using `python -m pip`. |
| Changes seem ignored | Stop and restart; terminal environment values override dotenv values. |

Local launch test (really opens the target):

```bash
python desktop_tools.py open github
python desktop_tools.py open vscode
```

Keep your API key out of screenshots and support messages. Share the exception type, action name and relevant non-secret configuration instead.

## 7. Files and developer notes

- `jarvis.py`: original launcher, unchanged from the supplied ZIP.
- `jarvis_chat.py`: conversation client and clap activation, registers `jarvis_desktop`.
- `desktop_tools.py`: local allowlist, launch/search actions, SQLite memory and CLI.
- `audio_pcm.py`: stateful audio conversion.
- `desktop_config.json`: trusted target definitions and action permissions.
- `.env.example`: non-secret configuration template.
- `agent_prompt.txt`, `agent_tool.json`: saved agent instructions/tool definition.
- `tests/`: mocked desktop/SDK wiring tests and synthetic audio conversion tests.
- `.github/workflows/tests.yml`: Windows/Linux unit tests on Python 3.12/3.14 when pushed to GitHub. It does not deploy anything or make billable calls.
- `LEGACY_README.md`: original project documentation.

To add another capability, implement a constrained handler, update the client tool's schema and agent instructions, add tests, then register it in the Python client. Do not turn speech into an unrestricted shell command. No full plugin system is implemented yet.

Validation for this ZIP: 14 unit/integration-wiring tests passed on Linux/Python 3.12. Tests run with mocked browser/process effects; audio conversion checked with synthetic PCM. Agent prompt and tool attachment read back from ElevenLabs. Windows hardware, real app launch paths, live voice recognition and full voice-to-tool execution still need the first local run on your laptop.

## 8. Rollback

Stop this client and return to your old project folder/environment. Your original agent remains `agent_5801m378382te8bs46qtwmncjqap`; it was not modified. Alternatively use that ID in `.env` for the old conversational behavior. The new desktop tool will then not be invoked. Your original `jarvis.py` welcome flow is also still available here.

## Gmail and Google Calendar

Jarvis can search/read Gmail, inspect your primary Google Calendar, and prepare emails or meetings for your review. Only confirmation in the local dashboard sends an email or creates a meeting and invitations. Google tokens stay in Windows Credential Manager. Voice-requested results are shared with the ElevenLabs agent.

**Follow [GOOGLE_SETUP.md](GOOGLE_SETUP.md) from start to finish** for Google Cloud configuration, OAuth sign-in, the ElevenLabs client tool, testing, privacy, disconnect and troubleshooting. Install the optional `requirements-google.txt`; existing desktop features do not require Google credentials. This is a local Windows integration, not a Vercel deployment.
