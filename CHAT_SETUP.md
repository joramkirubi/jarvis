# Jarvis conversation upgrade

Copy jarvis_chat.py into your existing jarvis-main folder beside jarvis.py.
Keep your current jarvis.py, .env, and virtual environment. No files need replacing.

In your existing activated Git Bash terminal:

```bash
python -m pip install -r requirements.txt
python jarvis_chat.py --now
```

A private agent named "Jarvis — Joram's voice companion" has been created in the
connected ElevenLabs workspace. The script contains its ID. Your local API key
must belong to that same workspace and allow the Agents / Conversational AI API,
including obtaining conversation signed URLs. Text-to-Speech permission alone
is insufficient. If access is denied, adjust the key's Agents permissions in
ElevenLabs and save the key locally in .env; never share it in chat.

Keep this line in your existing .env:

```env
JARVIS_INPUT_DEVICE=2
```

The new script uses the same microphone for claps and conversation, plus your
system's default output device. It requires support for mono 16kHz audio and
checks that before connecting. Headphones reduce echo.

Wait for "At your service, Joram...", then speak. Try "Explain an API using a
restaurant example" and follow with "Now give me a Python example."
Ctrl+C ends the session. Conversations use ElevenLabs Agents credits; microphone
audio is sent to ElevenLabs during the active session. This agent has a ten-minute
maximum session duration. It has no access to this ChatGPT conversation.

Once direct conversation works:

```bash
python jarvis_chat.py
```

Clap twice using the timing that worked before. The clap microphone stream closes
before the live conversation starts. No Spotify or browser launch runs in this
mode, so music does not interfere with the microphone. Your original launcher is
still available with `python jarvis.py`. Restart the new script for another chat.

Jarvis can converse and explain things. This version cannot browse, read your
screen/files, remember across sessions, or execute spoken desktop commands.
Its voice and prompt are configured on the ElevenLabs agent; the greeting in
jarvis.py and ELEVENLABS_VOICE_ID do not override the conversation agent.

Troubleshooting:
- No agent access: confirm the API key and agent are in the same workspace and
  that the key permits the Agents API. Agent ID:
  agent_5801m378382te8bs46qtwmncjqap
- SSL failure: your earlier Kaspersky issue may also affect WebSockets. Keep TLS
  verification enabled. Inspect the specific security alert.
- No sound: check default Windows output and volume; this script uses sounddevice,
  not PyAudio, so there is no extra PyAudio installation.
- No speech pickup: check JARVIS_INPUT_DEVICE and microphone privacy permissions.
- Different agent: set ELEVENLABS_AGENT_ID in .env to that agent's ID. This audio
  adapter expects 16kHz PCM for both agent input and output.

Validation: configuration read-back confirms private authentication and 16kHz
input/output. Local logic checks do not replace a Windows microphone and live
conversation test, which must be performed on your laptop.
