# Google OAuth2 Sign-in

Two equivalent implementations of Google OAuth2 sign-in with session persistence and optional dummy users for testing.

```
google-oauth/
  dummy_users.json     Dummy users shared by both implementations
  INSTRUCTIONS.md      This file
  typescript/          Node.js + TypeScript implementation
  python/              Python implementation
```

---

## 1. Google Cloud setup (required for both)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create or select a project
3. Go to **APIs & Services > OAuth consent screen** and configure it (External, test users if needed)
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth client ID**, choose **Web application**
6. Under **Authorised redirect URIs**, add:
   ```
   http://localhost:3000/auth/callback
   ```
   Adjust the port if you change it during setup.
7. Copy the **Client ID** and **Client Secret** - the setup script will ask for them.

---

## 2. TypeScript

**Requirements:** Node.js 18+

```bash
cd typescript
bash setup.sh
npm start
```

The setup script installs dependencies, compiles TypeScript, and writes `.env`.

**Development (watch mode):**
```bash
npm run dev
```

---

## 3. Python

**Requirements:** Python 3.11+

```bash
cd python
bash setup.sh
source .venv/bin/activate
python3 server.py
```

The setup script creates a virtual environment, installs dependencies, and writes `.env`.

---

## 4. Dummy users (testing)

Both implementations support dummy sign-in for testing without going through Google.

**Enable it** by answering "yes" when the setup script asks, or by setting `ENABLE_DUMMY_AUTH=true` in `.env` manually.

**Users** are defined in `dummy_users.json` at the project root. Both implementations read from the same file. Add, remove, or edit users there — the server picks up changes on restart.

The `picture` field accepts any image URL. The default users use [DiceBear](https://www.dicebear.com) avatars.

**dummy_users.json format:**
```json
[
  {
    "id": "unique-id",
    "email": "user@example.com",
    "name": "Display Name",
    "picture": "https://example.com/avatar.png"
  }
]
```

**Routes (when enabled):**

| Path | Description |
|---|---|
| `/auth/dummy/list` | HTML page listing all dummy users with sign-in buttons |
| `/auth/dummy?id=<id>` | Signs in immediately as that user |

Dummy auth responds 403 to both routes when `ENABLE_DUMMY_AUTH` is not `true`.

**Never enable dummy auth in production.** It bypasses all authentication.

---

## 5. Configuration

Both implementations use the same `.env` variables:

| Variable | Description | Default |
|---|---|---|
| `GOOGLE_CLIENT_ID` | OAuth2 client ID | required |
| `GOOGLE_CLIENT_SECRET` | OAuth2 client secret | required |
| `PORT` | Port to listen on | `3000` |
| `HOST` | Hostname to bind | `localhost` |
| `BASE_URL` | Public base URL (used for OAuth2 redirect URI) | `http://localhost:3000` |
| `ENABLE_DUMMY_AUTH` | Enable dummy login (`true`/`false`) | `false` |

---

## 6. Routes

| Path | Description |
|---|---|
| `GET /` | Home page — profile when signed in, sign-in button when not |
| `GET /auth/login` | Redirects to Google's consent screen |
| `GET /auth/callback` | Handles the redirect back from Google |
| `GET /auth/logout` | Clears the session, redirects to `/` |
| `GET /auth/dummy/list` | Dummy user picker (requires `ENABLE_DUMMY_AUTH=true`) |
| `GET /auth/dummy?id=<id>` | Dummy sign-in (requires `ENABLE_DUMMY_AUTH=true`) |

---

## 7. Sessions

Sessions are stored in memory and flushed to `sessions.json` in the implementation directory on every write. They expire after 7 days. The file is excluded from git — do not commit it.
