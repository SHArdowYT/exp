import type { AppRequest, AppResponse, Handler } from "../types.js";
import type { SessionStore } from "./store.js";

export const COOKIE_NAME = "session_id";

/**
 * Parses cookies from the Cookie header into a plain object.
 */
export function parseCookies(header: string | undefined): Record<string, string> {
  if (!header) return {};
  return Object.fromEntries(
    header.split(";").map((part) => {
      const [key, ...rest] = part.trim().split("=");
      return [key.trim(), decodeURIComponent(rest.join("="))];
    })
  );
}

/**
 * Sets a session cookie on the response.
 */
export function setSessionCookie(res: AppResponse, sessionId: string): void {
  res.setHeader(
    "Set-Cookie",
    `${COOKIE_NAME}=${sessionId}; HttpOnly; SameSite=Lax; Path=/; Max-Age=${7 * 24 * 60 * 60}`
  );
}

/**
 * Clears the session cookie.
 */
export function clearSessionCookie(res: AppResponse): void {
  res.setHeader("Set-Cookie", `${COOKIE_NAME}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0`);
}

/**
 * Wraps a handler to attach the session (if any) to the request before calling it.
 */
export function withSession(store: SessionStore, handler: Handler): Handler {
  return (req, res) => {
    const cookies = parseCookies(req.headers.cookie);
    const sessionId = cookies[COOKIE_NAME];
    if (sessionId) {
      req.session = store.get(sessionId);
    }
    return handler(req, res);
  };
}
