import fs from "fs";
import path from "path";
import type { Session } from "../types.js";

const SESSION_FILE = path.resolve("sessions.json");
const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

/**
 * Stores sessions in memory and flushes to disk so they survive restarts.
 */
export class SessionStore {
  private sessions = new Map<string, Session>();

  constructor() {
    this.load();
  }

  get(id: string): Session | undefined {
    const session = this.sessions.get(id);
    if (!session) return undefined;

    if (Date.now() - session.createdAt > SESSION_TTL_MS) {
      this.delete(id);
      return undefined;
    }

    return session;
  }

  set(session: Session): void {
    this.sessions.set(session.id, session);
    this.flush();
  }

  delete(id: string): void {
    this.sessions.delete(id);
    this.flush();
  }

  private load(): void {
    try {
      const raw = fs.readFileSync(SESSION_FILE, "utf8");
      const entries = JSON.parse(raw) as [string, Session][];
      for (const [id, session] of entries) {
        if (Date.now() - session.createdAt <= SESSION_TTL_MS) {
          this.sessions.set(id, session);
        }
      }
    } catch {
      // No session file yet — start fresh.
    }
  }

  private flush(): void {
    const entries = Array.from(this.sessions.entries());
    fs.writeFileSync(SESSION_FILE, JSON.stringify(entries), "utf8");
  }
}
