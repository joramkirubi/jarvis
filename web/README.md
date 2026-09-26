# Jarvis web

The hosted Jarvis works on a phone while the laptop is off. Google sign-in restricts the site to the owner; Gmail and Calendar have a separate **Connect Gmail and Calendar** button. Google refresh tokens are encrypted before storage in Neon.

## Deploy

The Vercel project's root directory is `web`. Set these server environment variables for Production (and Preview if used):

- `AUTH_SECRET`, `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`
- `ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID`
- `DATABASE_URL` (installed by the Neon integration)
- `GOOGLE_TOKEN_ENCRYPTION_KEY` (create one using the command below)

From `web/`, generate a 32-byte encryption key locally with:

```bash
node -e 'console.log(require("node:crypto").randomBytes(32).toString("base64url"))'
```

Copy it privately into Vercel as `GOOGLE_TOKEN_ENCRYPTION_KEY`. Keep this value consistent across deployments. Losing or changing it makes existing Google connections unreadable; connect again if that happens. Never commit the key or your `.env.local` file. The database table is created when the site first connects Google.

The same Google Cloud project used for Google sign-in needs Gmail API and Google Calendar API enabled. In its OAuth Data Access page, add `gmail.readonly`, `gmail.send`, and `calendar.events.owned`; keep the app in Testing with the owner's Google address listed as a test user during personal development. The authorized redirect URI for the web client is `https://jarvis-delta-blond.vercel.app/api/auth/callback/google` (plus `http://localhost:3000/api/auth/callback/google` for local development). The desktop OAuth credentials are separate.

Run `npm install` in `web/` after applying this change to update `package-lock.json`, then `npm run build` and commit the lockfile alongside the changes. Deploy, sign in, press **Connect Gmail and Calendar**, approve Google's consent screen, and use the **Recent email** and **Upcoming events** buttons to verify. Disconnect deletes the stored refresh token; revoke the grant in Google Account permissions if you want to revoke Google's authorization itself.

If the Google OAuth consent screen is External and in Testing, Google refresh tokens granted with Gmail or Calendar permissions expire after seven days. Reconnect at the site when prompted. Publishing a public app with restricted Gmail read scope has additional Google verification requirements.

## Voice actions

The browser supplies the `jarvis_google` client tool. It accepts `{ "action": "gmail_recent", "query": "optional search" }`, `{ "action": "gmail_search", "query": "from:someone@example.com" }`, `{ "action": "calendar_upcoming" }`, `{ "action": "gmail_send", "to": "person@example.com", "subject": "Hello", "body": "Message" }`, or `{ "action": "calendar_create", "title": "Meeting", "start": "2026-09-26T15:00:00+03:00", "end": "2026-09-26T15:30:00+03:00" }`. Email sending and event creation prompt for confirmation on screen. The ElevenLabs agent must be configured to call `jarvis_google` with these action names and fields; existing desktop-only tool names may differ. No desktop actions run on the hosted site.

Only the authenticated owner can use the Google routes. The website handles Google API calls on the server and does not send Google tokens to the voice agent or browser.
