import { google } from "googleapis";
import { v4 as uuidv4 } from "uuid";
import type { AppRequest, AppResponse } from "../types.js";
import type { SessionStore } from "../session/store.js";
import { setSessionCookie, clearSessionCookie } from "../session/middleware.js";

const SCOPES = ["openid", "email", "profile"];

/**
 * Manages the Google OAuth2 sign-in flow.
 */
export class GoogleAuth {
  private oauth2Client;

  constructor(
    private readonly store: SessionStore,
    private readonly callbackUrl: string
  ) {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET,
      callbackUrl
    );
  }

  /**
   * Redirects the user to Google's consent screen.
   */
  handleLogin(_req: AppRequest, res: AppResponse): void {
    const url = this.oauth2Client.generateAuthUrl({
      access_type: "offline",
      scope: SCOPES,
      prompt: "select_account",
    });
    res.writeHead(302, { Location: url });
    res.end();
  }

  /**
   * Handles the redirect back from Google, exchanges the code for a session.
   */
  async handleCallback(req: AppRequest, res: AppResponse): Promise<void> {
    const url = new URL(req.url ?? "/", `http://${req.headers.host}`);
    const code = url.searchParams.get("code");

    if (!code) {
      res.writeHead(400);
      res.end("Missing OAuth2 code.");
      return;
    }

    try {
      const { tokens } = await this.oauth2Client.getToken(code);
      this.oauth2Client.setCredentials(tokens);

      const oauth2 = google.oauth2({ version: "v2", auth: this.oauth2Client });
      const { data } = await oauth2.userinfo.get();

      const session = {
        id: uuidv4(),
        user: {
          id: data.id ?? uuidv4(),
          email: data.email ?? "",
          name: data.name ?? "",
          picture: data.picture ?? "",
        },
        createdAt: Date.now(),
      };

      this.store.set(session);
      setSessionCookie(res, session.id);
      res.writeHead(302, { Location: "/" });
      res.end();
    } catch (err) {
      console.error("OAuth2 callback error:", err);
      res.writeHead(500);
      res.end("Authentication failed.");
    }
  }

  /**
   * Clears the session and redirects to the home page.
   */
  handleLogout(req: AppRequest, res: AppResponse): void {
    if (req.session) {
      this.store.delete(req.session.id);
    }
    clearSessionCookie(res);
    res.writeHead(302, { Location: "/" });
    res.end();
  }
}
