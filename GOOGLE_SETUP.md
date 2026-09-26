# Gmail and Google Calendar for Jarvis

This adds Google tools to the existing **local Windows Jarvis**. It does not deploy Jarvis to Vercel or turn the dashboard into a public website. Use one personal Google account for both services.

## What is included

| Feature | Behaviour |
| --- | --- |
| Gmail search | Searches your mailbox using Gmail queries; returns up to five messages per request and reports when more exist. |
| Read email | Reads selected message text; HTML is converted to text. Does not mark messages as read or download attachments. |
| Calendar lookup | Reads your primary calendar, including recurring instances; up to 30 events per range. Defaults to today through the next seven days. |
| Email drafting | Prepares a local proposal with exact recipient addresses, subject and body. This is **not** saved in Gmail Drafts. |
| Email sending | Only the authenticated dashboard's confirmation sends the prepared email. Sends a new message; threaded replies, CC/BCC and attachments are not implemented. |
| Meeting creation | Prepares an event on your primary calendar. Dashboard confirmation creates it and requests invitations to the listed attendees. |
| Approval queue | Shows account, exact recipients, full text, times and attendees. Proposals expire after 30 minutes. Rejection performs no Google write. |

There is no email deletion, calendar modification/deletion, recurring-event creation, Meet-link generation, background inbox monitoring, secondary-calendar support or autonomous sending. Google tools work in the dashboard, `jarvis_chat.py` and wake-triggered conversations. Approvals always require the dashboard.

## 1. Apply this update in VS Code Git Bash

Save `Jarvis-Google.patch` in Downloads. Stop Jarvis with Ctrl+C first.

```bash
cd "$HOME/jarvis-main"
git status --short
```

If there are local edits, preserve them before proceeding. From the merged dashboard version of main:

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/google-integration
git apply --check "$HOME/Downloads/Jarvis-Google.patch"
git apply "$HOME/Downloads/Jarvis-Google.patch"
source .venv/Scripts/activate
python -m pip install -r requirements-google.txt
python -m unittest discover -s tests -v
mkdir -p .jarvis/google
```

An empty result from `git apply --check` means the patch fits. If it reports a conflict, stop and share the error rather than forcing the patch. The update does not replace your .env, microphone settings, Google account, memory or existing ElevenLabs agent.

For a completely fresh clone, also install `requirements.txt` and complete the normal README setup.

## 2. Create your Google project

Open https://console.cloud.google.com/ in your browser and sign in to your Google account.

1. Use the project selector at the top to create a project, for example **Jarvis Personal**.
2. Select that project.
3. Go to **APIs & Services → Library**.
4. Search for **Gmail API**, open it and click **Enable**.
5. Return to the library, search for **Google Calendar API** and enable it too.

Use one project for both. You do not need a service account or a Gmail password.

## 3. Configure Google consent

In **Google Auth platform**, choose **Get started** if needed.

- Branding: use **Jarvis Personal**, your email for support and your email as the developer contact.
- Audience: for a personal Gmail account choose **External**. Keep this personal app in **Testing** for now.
- In **Audience → Test users**, add the exact Gmail address you will connect.
- In **Data Access → Add or remove scopes**, add these exact scopes (manual entry can be used):

```text
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/calendar.events.owned
```

Save the configuration. Scope descriptions may sound broader than the implemented tools: Calendar's scope grants event editing on owned calendars, while this code only reads/creates events on the primary calendar. Gmail read permission covers your mailbox; Jarvis reads only the requested results.

Testing-mode grants for these scopes normally need reauthorization after seven days. Run the connect command again when access expires. Public distribution is a separate project: Gmail read access is a restricted scope and Google verification/data-handling requirements need review before other users are onboarded. Do not publish this personal setup as a shared credential service.

## 4. Download Desktop OAuth credentials

Go to **Google Auth platform → Clients → Create client**.

1. Application type: **Desktop app**.
2. Name: **Jarvis Windows**.
3. Create it and download its JSON file.
4. In VS Code, move or copy the downloaded file into the repo's `.jarvis/google/` folder and rename it **client_secret.json**.

The exact path is:

```text
C:\Users\Joram Kirubi\jarvis-main\.jarvis\google\client_secret.json
```

Use the whole downloaded JSON without editing its contents. The Desktop app uses a temporary loopback callback; do not create a Web application credential or paste a Vercel redirect URL here.

Do not paste the JSON, tokens or client secret into chat, the ElevenLabs prompt, screenshots or GitHub. `.jarvis/` and common OAuth download filenames are ignored by Git. No Google value needs to be added to .env.

## 5. Connect both services

In the activated VS Code Git Bash terminal:

```bash
python google_tools.py connect
```

Your browser opens Google's sign-in page. Choose your test-user account and review/grant all requested Gmail and Calendar permissions. Finish within three minutes. If the consent screen identifies an unverified testing app, verify that it is **your own Jarvis Personal project** and account before proceeding. Organization restrictions cannot be bypassed by this code.

The terminal reports success and your connected email address. Tokens are stored through **Windows Credential Manager**, not in a plaintext token.json. The entry belongs to this checkout path, so moving the project requires connecting again. No browser login is needed for each normal call while the saved grant remains valid.

```bash
python google_tools.py status
python jarvis_dashboard.py
```

The new **Gmail & Google Calendar** panel should show your account. Try **Unread emails** and **Calendar · next 7 days**. These buttons work even before configuring voice tools. Status reports stored credentials; an actual read checks whether Google still accepts them.

## 6. Give the ElevenLabs agent its Google client tool

The local code now registers a tool named `jarvis_google`, but your hosted ElevenLabs agent must also know its schema. The update does not silently change your live agent.

1. Open the ElevenLabs Agents dashboard and select the same agent referenced by `ELEVENLABS_AGENT_ID` in your local .env.
2. Add a **Client tool**, with the definition from **google_agent_tool.json**. Use the tool editor's JSON view/import if available; otherwise copy the fields from that file.
3. Exact tool name: **jarvis_google**. Enable waiting for a response (`expects_response: true`); use a 120-second response timeout.
4. If entered manually, add the string parameters `action`, `query`, `message_id`, `subject`, `body`, `to`, `start`, `end`. Only `action` is required. Copy its allowed values and each field's description from the JSON.
5. Keep the existing `jarvis_desktop` tool attached.
6. Append the contents of **google_agent_prompt.txt** to the existing system prompt. Do not replace your current desktop instructions or personal context.
7. Save/publish the agent changes as required by the ElevenLabs editor, then restart your Jarvis conversation.

Do not put your Google client secret, Google tokens or ElevenLabs API key in the tool definition. This is a **client tool**, not a webhook. The connected desktop handles Google requests locally.

## 7. Test it step by step

Start with reads:

- “Jarvis, which Google account are you connected to?”
- “Summarize my unread emails.”
- “Read the email about [specific subject].”
- “What is on my calendar tomorrow?”

Times default to **Africa/Nairobi (UTC+03:00)**. For a whole day, the agent uses midnight to the following midnight. Read results are capped; Jarvis must narrow searches before claiming it has reviewed everything.

Then prepare a harmless email to **your own exact email address**:

- “Draft an email to [your exact Gmail address], subject Jarvis test, saying this is my first Jarvis email test.”
- The dashboard should show an **AWAITING YOUR APPROVAL** email. Nothing has been sent.
- Review the From account, exact To address, subject and message. Click **Confirm & send email**, then confirm the displayed details.
- Check Gmail Sent and your inbox. You may instead choose **Reject** to verify that nothing is sent.

Try a calendar entry without guests first:

- “Prepare a Jarvis test meeting tomorrow from 10 to 10:15 a.m. with no attendees.”
- Review the title, date, start/end, timezone offsets and account.
- Confirm and check Google Calendar. Delete the test event manually in Google Calendar afterwards if desired.

With attendees, approving an event also requests Google to send their invitations. Saying “yes” by voice cannot approve a proposal. The model cannot call the confirmation endpoint through `jarvis_google`.

## Data and privacy

- Google tokens: Windows Credential Manager; the OAuth client download remains inside ignored `.jarvis/google/`.
- Local proposals: `.jarvis/google/approvals.sqlite3`, including full email bodies, recipients, meeting details and recent outcome states. This is a local, unencrypted SQLite file protected by your Windows account's file access. Do not share it. Closing the dashboard does not delete it. Stop Jarvis before deleting this file if you want to clear proposal history.
- Google tool results requested during voice sessions go to ElevenLabs and the agent's configured model, and may appear in its conversation history under your existing retention settings. Local Google reads from the dashboard buttons do not themselves call ElevenLabs.
- Retrieved email/calendar text is treated as untrusted data. Prompt instructions forbid obeying instructions inside messages. The confirmation boundary is enforced in Python, independent of those prompt instructions.
- Authentication is still the existing random dashboard session token plus loopback Host/Origin checks. Do not expose the Python server publicly or remove those checks to connect a Vercel page.
- `JARVIS_DRY_RUN=true` prevents Google draft persistence and approval writes, but intentionally permits requested Google reads.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| JSON file missing | Check `.jarvis/google/client_secret.json`; Windows may hide file extensions. |
| Access blocked / not a test user | Select the correct Cloud project and add your exact account under Audience → Test users. Workspace administrators may also restrict consent. |
| Permission or API error | Enable both APIs, verify all three scopes, then run connect again and grant all requested permissions. |
| Access stops after a week | Expected for this testing-mode grant; reconnect. |
| Redirect mismatch | Use a **Desktop app** credential, not a Web application credential. |
| Keyring unavailable | Activate .venv and install requirements-google.txt on Windows. No insecure token-file fallback is used. |
| Jarvis talks but cannot use Gmail | Attach `jarvis_google` to the correct hosted agent, append the prompt and restart the conversation. |
| Agent says sent but proposal is pending | Nothing has been sent. Confirm only in the dashboard; verify the added prompt instructions. |
| Outcome unknown / check Google | A network failure can occur after Google accepts a write. Check Gmail Sent or Calendar before preparing a new action. The same proposal never retries automatically. |
| In progress remains after a crash | Check Google directly before doing anything again. A claimed proposal is not automatically re-run after restart. |
| Too many email/event results | Ask for a narrower query or date range; the first page is not the whole mailbox/calendar. |
| SSL/Kaspersky error | Use your established trusted HTTPS configuration. Do not disable certificate verification. |

Disconnect local access:

```bash
python google_tools.py disconnect
```

This removes local tokens and cancels pending proposals. To revoke the Google grant itself, use https://myaccount.google.com/connections and remove access for Jarvis Personal. Existing sent emails and calendar entries are not undone.

## Validation and Git

Automated tests use mocked Google calls. They check read-only behaviour, exact approval payloads, duplicated clicks, concurrent confirmations, expiry/rejection, account changes, ambiguous network failures, header injection, dry run and voice registration. No real message was sent or meeting created during development. Live Google sign-in and Windows Credential Manager must be checked on your Windows laptop.

After the steps above work:

```bash
git status --short
git ls-files -- .env .jarvis client_secret.json credentials.json token.json
git add .gitignore README.md GOOGLE_SETUP.md requirements-google.txt google_tools.py google_agent_tool.json google_agent_prompt.txt jarvis_chat.py dashboard_runtime.py dashboard_state.py jarvis_dashboard.py dashboard/ tests/ .github/workflows/tests.yml
git diff --cached --stat
git commit -m "Add Google email and calendar tools with dashboard approvals"
git push -u origin feature/google-integration
```

The `git ls-files` command should print no credentials or `.jarvis` files. Review the staged file list before committing.

## Official references

- Gmail Python quickstart: https://developers.google.com/workspace/gmail/api/quickstart/python
- Google Calendar scopes: https://developers.google.com/workspace/calendar/api/auth
- Installed-app OAuth: https://developers.google.com/identity/protocols/oauth2/native-app
- OAuth token lifetime: https://developers.google.com/identity/protocols/oauth2#expiration
- Gmail send API: https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send
- Calendar insert API: https://developers.google.com/workspace/calendar/api/v3/reference/events/insert
