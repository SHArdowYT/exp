import type { AppRequest, AppResponse } from "../types.js";

/**
 * Serves the home page. Shows the signed-in user's details if a session exists,
 * or a sign-in prompt otherwise.
 */
export function homePage(req: AppRequest, res: AppResponse): void {
  const user = req.session?.user;

  const body = user
    ? `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Home</title>
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
      padding: 2.5rem 3rem;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      text-align: center;
      max-width: 360px;
      width: 100%;
    }
    img { border-radius: 50%; margin-bottom: 1rem; }
    h1 { font-size: 1.3rem; margin-bottom: 0.25rem; }
    p { color: #555; font-size: 0.95rem; margin-bottom: 1.5rem; }
    a {
      display: inline-block;
      padding: 0.6rem 1.4rem;
      background: #222;
      color: #fff;
      text-decoration: none;
      border-radius: 6px;
      font-size: 0.9rem;
    }
    a:hover { background: #444; }
  </style>
</head>
<body>
  <div class="card">
    <img src="${user.picture}" width="72" height="72" alt="">
    <h1>${user.name}</h1>
    <p>${user.email}</p>
    <a href="/auth/logout">Sign out</a>
  </div>
</body>
</html>`
    : `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sign in</title>
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
      padding: 2.5rem 3rem;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      text-align: center;
      max-width: 360px;
      width: 100%;
    }
    h1 { font-size: 1.4rem; margin-bottom: 0.5rem; }
    p { color: #666; font-size: 0.95rem; margin-bottom: 1.75rem; }
    a {
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.65rem 1.4rem;
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 6px;
      font-size: 0.95rem;
      color: #333;
      text-decoration: none;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    a:hover { background: #fafafa; border-color: #bbb; }
    svg { flex-shrink: 0; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Welcome</h1>
    <p>Sign in to continue.</p>
    <a href="/auth/login">
      <svg width="18" height="18" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
        <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.2l6.7-6.7C35.8 2.5 30.2 0 24 0 14.6 0 6.6 5.5 2.7 13.5l7.8 6C12.4 13.2 17.8 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4 7.1-10 7.1-17z"/>
        <path fill="#FBBC05" d="M10.5 28.6A14.8 14.8 0 0 1 9.5 24c0-1.6.3-3.2.8-4.6l-7.8-6A23.9 23.9 0 0 0 0 24c0 3.9.9 7.5 2.7 10.7l7.8-6.1z"/>
        <path fill="#34A853" d="M24 48c6.2 0 11.4-2 15.2-5.5l-7.5-5.8c-2 1.4-4.6 2.2-7.7 2.2-6.2 0-11.5-4.2-13.4-9.9l-7.8 6C6.6 42.5 14.6 48 24 48z"/>
      </svg>
      Sign in with Google
    </a>
  </div>
</body>
</html>`;

  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(body);
}
