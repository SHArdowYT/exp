# Google OAuth2 Sign-in

A Python web application providing Google OAuth2 sign-in with persistent sessions
and optional dummy users for testing.

```
google-oauth/
  dummy_users.json     Test user definitions
  INSTRUCTIONS.md      This file
  CHANGELOG.md         Change history
  instructions_history.md  History of project instructions
  scripts/             Maintenance and development scripts
    zip.sh             Creates a git archive zip
    update_fonts.py    Downloads latest Departure Mono from Google Fonts
    check_ascii.py     Checks all tracked files for non-ASCII characters
    lint.py            Runs ruff, mypy, and pylint against the Python source
  python/              Application source
```

---

## 1. Scripts

All scripts live in scripts/ and can be run from the repo root.

| Script              | Language | Purpose                                               |
|---------------------|----------|-------------------------------------------------------|
| scripts/zip.sh      | bash     | Create a git archive zip (prompts for confirmation)   |
| scripts/lint.py     | Python   | Run ruff, mypy, and pylint against python/            |
| scripts/check_ascii.py | Python | Check all tracked files for non-ASCII characters     |
| scripts/update_fonts.py | Python | Download latest Departure Mono from Google Fonts    |

```bash
python3 scripts/lint.py
python3 scripts/check_ascii.py
python3 scripts/update_fonts.py
bash scripts/zip.sh
```

---

## 2. Google Cloud setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create or select a project
3. Go to APIs & Services > OAuth consent screen and configure it
   (External is fine; add yourself as a test user while in testing mode)
4. Go to APIs & Services > Credentials
5. Click Create Credentials > OAuth client ID, choose Web application
6. Under Authorised redirect URIs, add:
   ```
   http://localhost:3000/auth/callback
   ```
   Adjust the port if you change PORT during setup.
7. Copy the Client ID and Client Secret -- the setup script will ask for them.

---

## 3. Setup

Requirements: Python 3.11+

```bash
cd python
bash setup.sh
```

The setup script will:
- Ask for your Google credentials and preferred port
- Ask whether to enable dummy auth for testing
- Write a .env file
- Create a .venv virtual environment
- Install all dependencies

---

## 4. Running

```bash
cd python
source .venv/bin/activate
uvicorn main:app --host localhost --port 3000 --reload
```

---

## 5. Configuration

All settings are read from environment variables or a .env file in the python/
directory. The setup script creates this file. Edit it directly to change settings
after setup.

| Variable                  | Description                              | Default              |
|---------------------------|------------------------------------------|----------------------|
| GOOGLE_CLIENT_ID          | OAuth2 client ID (required)              |                      |
| GOOGLE_CLIENT_SECRET      | OAuth2 client secret (required)          |                      |
| HOST                      | Hostname to bind                         | localhost            |
| PORT                      | Port to listen on                        | 3000                 |
| BASE_URL                  | Public base URL for OAuth2 redirect URI  | http://localhost:3000|
| ENABLE_DUMMY_AUTH         | Enable dummy login (true/false)          | false                |
| DUMMY_USERS_FILE          | Path to dummy users JSON                 | ../dummy_users.json  |
| SESSION_FILE              | Path to sessions JSON                    | sessions.json        |
| SESSION_TTL_SECONDS       | Session lifetime in seconds              | 604800 (7 days)      |
| COOKIE_NAME               | Session cookie name                      | session_id           |
| PKCE_MAX_PENDING          | Max in-flight PKCE states                | 256                  |
| USERINFO_TIMEOUT_SECONDS  | Timeout for Google userinfo request      | 10.0                 |
| LOG_LEVEL                 | Python logging level                     | DEBUG                |

---

## 6. Routes

| Method | Path              | Description                                          |
|--------|-------------------|------------------------------------------------------|
| GET    | /                 | Home -- profile when signed in, sign-in button when not |
| GET    | /auth/login       | Redirects to Google's consent screen                 |
| GET    | /auth/callback    | Handles the redirect back from Google                |
| GET    | /auth/logout      | Clears the session and redirects to /                |
| GET    | /auth/dummy       | Sign in as a test user (?id=<id>)                    |
| GET    | /auth/dummy/list  | HTML page listing all test users                     |

The /auth/dummy routes return 403 when ENABLE_DUMMY_AUTH is not true.

---

## 7. Dummy users (testing)

Enable dummy auth by answering yes during setup, or by setting
ENABLE_DUMMY_AUTH=true in python/.env.

Users are defined in dummy_users.json at the project root. Edit this file
to add, remove, or modify test users. Changes take effect on restart.

Format:

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

The picture field accepts any image URL. DiceBear (https://www.dicebear.com)
is a convenient source of avatar images.

Never enable dummy auth in production -- it bypasses all authentication.

---

## 8. Sessions

Sessions are stored in memory and written to python/sessions.json on every
change. They expire after SESSION_TTL_SECONDS (default 7 days). The file is
excluded from git -- do not commit it.

---

## 9. Extending

### Adding a route

Add a new @app.get function in python/main.py. Retrieve shared resources
from app.state via _get_state(request).

```python
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    state: AppState = _get_state(request)
    session = get_session(request, state.session_store, state.settings)
    if not session:
        return RedirectResponse("/auth/login")
    return state.templates.TemplateResponse(request, "dashboard.html", {"user": session.user})
```

### Swapping the session backend

Create a class that extends AbstractSessionStore from session/store.py,
implement get(), save(), and delete(), then replace JsonSessionStore in
the lifespan function in main.py.

### Adding a new auth backend

Create a class in auth/ with async handler methods that accept
Request and return Response. Register its routes in main.py and
add it to AppState.
