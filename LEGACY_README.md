# 🤖 JARVIS — Voice-Activated Desktop Assistant

JARVIS is a Python-powered desktop assistant that combines **acoustic activation, desktop automation, AI voice conversations, and text-to-speech**.

A double clap can activate Jarvis, launch a personalized workspace, play a welcome message, or start a real-time voice conversation through ElevenLabs Conversational AI.

The project is inspired by the idea of a personal desktop assistant that responds naturally and helps prepare your computer for work.

---

## ✨ Features

### 👏 Double-Clap Activation

Jarvis continuously monitors the selected microphone and detects two claps within a configurable time window.

The detection system includes:

- Adaptive background-noise detection
- Configurable clap sensitivity
- False-trigger protection
- Automatic microphone selection
- Manual microphone override
- Input-device probing
- Cooldown and retrigger protection

No wake word is required.

---

### 🖥️ Desktop Workspace Automation

Running:

```bash
python jarvis.py
```

starts the desktop automation mode.

After detecting a double clap, Jarvis can:

- Open Spotify or another configured media URL
- Launch configured websites in Google Chrome
- Open or focus Cursor
- Move Chrome windows to configured monitors
- Open applications in fullscreen
- Play a personalized Jarvis-style welcome message
- Prepare a working environment automatically

The exact behaviour can be customized through environment variables and constants in `jarvis.py`.

---

### 🗣️ AI Voice Conversations

Jarvis also includes a conversational mode powered by **ElevenLabs Conversational AI**.

Run:

```bash
python jarvis_chat.py
```

Then clap twice to begin talking with Jarvis.

You can also bypass clap detection:

```bash
python jarvis_chat.py --now
```

Jarvis can then:

- Listen through your microphone
- Convert your speech for the AI agent
- Maintain a real-time conversation
- Generate intelligent responses
- Speak responses through your speakers/headphones
- Display both user transcripts and Jarvis responses in the terminal

Example:

```text
You: Explain APIs using a restaurant example.

Jarvis: Imagine you're sitting at a restaurant...
```

The conversation continues until the session ends or you press `Ctrl+C`.

---

## 🧠 How It Works

Jarvis currently has two primary operating modes.

### Mode 1 — Desktop Automation

```text
Microphone
    ↓
Audio Stream
    ↓
Adaptive Noise Detection
    ↓
Double-Clap Detection
    ↓
Jarvis Activation
    ↓
Desktop Automation
    ├── Spotify / Media
    ├── Chrome
    ├── Cursor
    └── ElevenLabs Welcome Voice
```

### Mode 2 — AI Conversation

```text
Microphone
    ↓
Double Clap
    ↓
Jarvis Conversation Mode
    ↓
ElevenLabs Conversational AI
    ↓
AI Response
    ↓
Jarvis Voice
    ↓
Speakers / Headphones
```

The microphone stream used for clap detection closes before the conversational audio stream begins so the two systems do not compete for the microphone.

---

## 🛠️ Technology Stack

Jarvis currently uses:

- **Python**
- **NumPy** — audio signal calculations
- **SoundDevice / PortAudio** — microphone and speaker access
- **ElevenLabs Text-to-Speech**
- **ElevenLabs Conversational AI**
- **WebSockets** — real-time AI communication
- **python-dotenv** — environment configuration
- **Windows APIs** — window detection, positioning and application control
- **Google Chrome**
- **Cursor**

---

## 📁 Project Structure

```text
jarvis/
│
├── jarvis.py
├── jarvis_chat.py
├── CHAT_SETUP.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### `jarvis.py`

Core desktop automation system.

Responsible for:

- Clap detection
- Microphone selection
- Desktop automation
- Chrome window management
- Cursor launching/focusing
- ElevenLabs welcome speech
- Welcome-audio caching

### `jarvis_chat.py`

Conversational AI companion.

Responsible for:

- Clap-to-talk activation
- Real-time microphone capture
- ElevenLabs Conversational AI connection
- Audio playback
- Conversation transcripts

### `CHAT_SETUP.md`

Additional configuration and troubleshooting instructions for conversational mode.

### `.env.example`

Template containing the environment variables used by Jarvis.

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/joramkirubi/jarvis.git
cd jarvis
```

## 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

# ⚙️ Environment Configuration

Jarvis loads environment variables from a `.env` file located in the same directory as `jarvis.py`.

Create it from the example configuration:

```bash
copy .env.example .env
```

Then edit `.env` with your configuration.

**Never commit your real `.env` file or API keys to GitHub.**

---

## ElevenLabs Configuration

```env
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_OUTPUT_FORMAT=pcm_24000
```

### `ELEVENLABS_API_KEY`

API key used to communicate with ElevenLabs.

For conversational mode, the key must have access to the required ElevenLabs Conversational AI / Agents functionality.

### `ELEVENLABS_VOICE_ID`

Voice used for the desktop welcome message.

The conversational agent has its own voice configuration.

### `ELEVENLABS_AGENT_ID`

Optional conversational-agent override:

```env
ELEVENLABS_AGENT_ID=your_agent_id
```

If supplied, `jarvis_chat.py` uses this agent instead of its default configured agent.

---

# 🎙️ Microphone Configuration

Jarvis attempts to detect a working microphone automatically.

If the Windows default input appears silent, Jarvis scans available input devices and selects an active one.

You can manually configure the microphone using:

```env
JARVIS_INPUT_DEVICE=2
```

The value can also be part of the microphone's device name.

To list available audio devices:

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

---

# 🌐 Browser Configuration

URLs opened by Jarvis can be configured through `.env`.

Example:

```env
CLAUDE_CODE_URL=https://chatgpt.com
TASARADAR_URL=https://github.com/your_github_username
```

Additional URL configuration may be available depending on the desktop workflow configured in `jarvis.py`.

---

# ▶️ Running Jarvis

## Desktop Automation Mode

Start Jarvis with:

```bash
python jarvis.py
```

You should see a message indicating that Jarvis is listening.

Clap twice.

When the double clap is detected, Jarvis runs the configured welcome sequence.

Stop Jarvis using:

```text
Ctrl+C
```

---

# 💬 Running Conversational Jarvis

Start clap-to-talk mode:

```bash
python jarvis_chat.py
```

Jarvis waits for a double clap before starting the conversation.

To begin immediately:

```bash
python jarvis_chat.py --now
```

Wait for Jarvis to connect, then start speaking.

The terminal displays conversation transcripts:

```text
You: What is an API?

Jarvis: An API is a way for two pieces of software to communicate...
```

Press:

```text
Ctrl+C
```

to end the session.

For additional configuration, see:

```text
CHAT_SETUP.md
```

---

# 🎚️ Clap Detection Tuning

Clap detection can be adjusted using constants near the top of `jarvis.py`.

| Constant            | Purpose                                                                                 |
| ------------------- | --------------------------------------------------------------------------------------- |
| `SPIKE_RATIO`       | Determines how much louder a sound must be than the background noise to count as a clap |
| `COOLDOWN_S`        | Minimum cooldown between detected clap events                                           |
| `MIN_DOUBLE_GAP_S`  | Minimum allowed time between the two claps                                              |
| `MAX_DOUBLE_GAP_S`  | Maximum allowed time between the two claps                                              |
| `BLOCK_MS`          | Audio-analysis window size                                                              |
| `MIN_RMS`           | Minimum absolute audio level considered                                                 |
| `SAMPLE_RATE`       | Microphone sampling rate                                                                |
| `RETRIGGER_RATIO`   | Determines when the detector becomes ready for another clap                             |
| `NOISE_FLOOR_ALPHA` | Controls how quickly Jarvis adapts to background noise                                  |

If Jarvis triggers too easily, increase `SPIKE_RATIO`.

If Jarvis misses claps, decrease it slightly.

---

# 🔊 Welcome Voice Caching

Jarvis can cache the generated ElevenLabs welcome message.

By default, cached audio is stored under:

```text
.cache/jarvis_welcome/
```

When the welcome phrase, voice, model and output format have not changed, Jarvis can replay the cached audio instead of requesting the same speech from ElevenLabs again.

This reduces unnecessary API calls and improves startup responsiveness.

A custom location can be configured using:

```env
JARVIS_WELCOME_CACHE_DIR=your_cache_directory
```

---

# 🔐 Security & Privacy

Jarvis interacts with microphones, external APIs and desktop applications, so credentials and permissions should be handled carefully.

### API Keys

Never place real API keys directly inside source code.

Store them in:

```text
.env
```

The repository should only contain:

```text
.env.example
```

with placeholder values.

### Microphone

Jarvis accesses the computer's microphone for clap detection and conversational interaction.

During an active ElevenLabs conversational session, microphone audio is transmitted to ElevenLabs for processing.

### Logs

Jarvis avoids intentionally printing API keys or raw authentication responses when conversational connection errors occur.

### External Services

Using Jarvis may involve third-party services including ElevenLabs, Spotify, websites opened through Chrome, and other services configured by the user.

Their respective privacy policies and terms apply.

---

# ⚠️ Current Limitations

Jarvis is currently an experimental desktop assistant rather than a complete autonomous computer-control agent.

The conversational version currently does **not** independently:

- Browse the web
- Read arbitrary files
- Inspect the computer screen
- Maintain persistent memory across sessions
- Execute arbitrary spoken desktop commands
- Control every desktop application
- Understand everything currently displayed on the computer

These capabilities may be introduced gradually as the architecture evolves.

---

# 🗺️ Roadmap

Potential future development includes:

- [ ] Wake-word activation such as **"Jarvis"**
- [ ] Spoken desktop commands
- [ ] Application launching through natural language
- [ ] Web search and research
- [ ] Screen understanding
- [ ] File and document interaction
- [ ] Persistent conversational memory
- [ ] Calendar integration
- [ ] Email integration
- [ ] Task management
- [ ] Custom tools and function calling
- [ ] Multi-step AI workflows
- [ ] Improved desktop automation
- [ ] Modular plugin architecture
- [ ] Local/offline capabilities
- [ ] Graphical control panel
- [ ] User-configurable automation routines
- [ ] Improved security controls and permissions
- [ ] Automated tests and CI/CD

The long-term direction is to evolve Jarvis from a clap-triggered desktop automation experiment into a more capable **personal AI desktop assistant**.

---

# 🧰 Troubleshooting

### Wrong or quiet microphone

Jarvis probes the default Windows input.

If it appears silent, Jarvis attempts to locate another working input.

To force a particular microphone:

```env
JARVIS_INPUT_DEVICE=2
```

---

### No reaction to claps

Try lowering:

```python
SPIKE_RATIO
```

slightly.

Also try clapping closer to the microphone.

---

### Too many false triggers

Increase:

```python
SPIKE_RATIO
```

or adjust:

```python
COOLDOWN_S
```

---

### PortAudio / audio errors

Check:

- Windows microphone permissions
- Audio drivers
- Input-device configuration
- Supported sample rates

If necessary, try changing:

```python
SAMPLE_RATE = 48000
```

---

### No welcome speech

Confirm that `.env` contains:

```env
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

Then restart the terminal and Jarvis.

---

### Conversational Jarvis will not connect

Check:

- Internet connection
- ElevenLabs API key
- ElevenLabs Agents / Conversational AI permissions
- Agent ID
- Microphone permissions
- WebSocket connectivity

See `CHAT_SETUP.md` for additional troubleshooting.

---

# 💡 Project Vision

Jarvis started as a simple experiment:

> **Can a computer recognize two claps and prepare my workspace automatically?**

That experiment has evolved into a voice-enabled desktop assistant capable of combining audio detection, desktop automation and conversational AI.

The project explores how AI can move beyond traditional chat interfaces and become part of the everyday desktop environment.

---

# 👨‍💻 Author

**Joram Kirubi**

Software Engineer | AI & Automation Developer

GitHub: `@joramkirubi`

---

## ⭐ Support the Project

If you find Jarvis interesting, consider starring the repository.

Contributions, experiments and ideas for extending the assistant are welcome.

---

**JARVIS is under active development.**
