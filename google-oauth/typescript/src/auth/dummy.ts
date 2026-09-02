import fs from "fs";
import path from "path";
import { v4 as uuidv4 } from "uuid";
import type { AppRequest, AppResponse, User } from "../types.js";
import type { SessionStore } from "../session/store.js";
import { setSessionCookie } from "../session/middleware.js";

const DUMMY_FILE = path.resolve("../dummy_users.json");

/**
 * Loads dummy users from the shared dummy_users.json file.
 * Returns an empty array (with a warning) if the file is missing or malformed.
 */
function loadDummyUsers(): Map<string, User> {
  try {
    const raw = fs.readFileSync(DUMMY_FILE, "utf8");
    const users = JSON.parse(raw) as User[];
    return new Map(users.map((u) => [u.id, u]));
  } catch {
    console.warn(`[DummyAuth] Could not load ${DUMMY_FILE} — dummy login disabled.`);
    return new Map();
  }
}

/**
 * Provides dummy sign-in for testing.
 *
 * Only active when ENABLE_DUMMY_AUTH=true in the environment.
 * Visit /auth/dummy?id=<user-id> to sign in as that user.
 * Users are defined in dummy_users.json at the project root.
 */
export class DummyAuth {
  private readonly users: Map<string, User>;
  private readonly enabled: boolean;

  constructor(private readonly store: SessionStore) {
    this.enabled = process.env.ENABLE_DUMMY_AUTH === "true";
    this.users = this.enabled ? loadDummyUsers() : new Map();
    if (this.enabled) {
      console.log(`[DummyAuth] Enabled with ${this.users.size} user(s): ${[...this.users.keys()].join(", ")}`);
    }
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Signs in as the dummy user matching ?id=<id>.
   * Responds 404 if the id is unknown, 403 if dummy auth is disabled.
   */
  handleLogin(req: AppRequest, res: AppResponse): void {
    if (!this.enabled) {
      res.writeHead(403);
      res.end("Dummy auth is not enabled. Set ENABLE_DUMMY_AUTH=true.");
      return;
    }

    const url = new URL(req.url ?? "/", `http://${req.headers.host}`);
    const id = url.searchParams.get("id") ?? "";
    const user = this.users.get(id);

    if (!user) {
      const list = [...this.users.keys()].join(", ");
      res.writeHead(404);
      res.end(`Unknown dummy user id "${id}". Available: ${list}`);
      return;
    }

    const session = { id: uuidv4(), user, createdAt: Date.now() };
    this.store.set(session);
    setSessionCookie(res, session.id);
    console.log(`[DummyAuth] Signed in as ${user.name} (${user.id})`);
    res.writeHead(302, { Location: "/" });
    res.end();
  }

  /**
   * Returns an HTML page listing all available dummy users with sign-in links.
   */
  handleList(_req: AppRequest, res: AppResponse): void {
    if (!this.enabled) {
      res.writeHead(403);
      res.end("Dummy auth is not enabled.");
      return;
    }

    const items = [...this.users.values()]
      .map(
        (u) => `
        <li>
          <img src="${u.picture}" width="36" height="36" alt="">
          <div>
            <strong>${u.name}</strong><br>
            <small>${u.email}</small>
          </div>
          <a href="/auth/dummy?id=${u.id}">Sign in</a>
        </li>`
      )
      .join("");

    const body = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dummy Login</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, sans-serif;
      background: #f5f5f5;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: #fff;
      border-radius: 10px;
      padding: 2rem 2.5rem;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      max-width: 400px;
      width: 100%;
    }
    h1 { font-size: 1.2rem; margin-bottom: 0.25rem; }
    p { color: #888; font-size: 0.85rem; margin-bottom: 1.5rem; }
    ul { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }
    li {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.6rem 0.75rem;
      border: 1px solid #eee;
      border-radius: 8px;
    }
    li img { border-radius: 50%; flex-shrink: 0; }
    li div { flex: 1; }
    li small { color: #888; }
    li a {
      padding: 0.35rem 0.85rem;
      background: #222;
      color: #fff;
      text-decoration: none;
      border-radius: 5px;
      font-size: 0.85rem;
      white-space: nowrap;
    }
    li a:hover { background: #444; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Dummy Login</h1>
    <p>Testing only. Users are defined in dummy_users.json.</p>
    <ul>${items}</ul>
  </div>
</body>
</html>`;

    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(body);
  }
}
