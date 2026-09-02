import http from "http";
import { SessionStore } from "./session/store.js";
import { withSession } from "./session/middleware.js";
import { GoogleAuth } from "./auth/google.js";
import { DummyAuth } from "./auth/dummy.js";
import { Router } from "./router.js";
import { homePage } from "./pages/home.js";

const PORT = parseInt(process.env.PORT ?? "3000", 10);
const HOST = process.env.HOST ?? "localhost";
const BASE_URL = process.env.BASE_URL ?? `http://${HOST}:${PORT}`;

if (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET) {
  console.error("Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set.");
  process.exit(1);
}

const store = new SessionStore();
const auth = new GoogleAuth(store, `${BASE_URL}/auth/callback`);
const dummy = new DummyAuth(store);
const router = new Router();

router.get("/", withSession(store, homePage));
router.get("/auth/login",    withSession(store, (req, res) => auth.handleLogin(req, res)));
router.get("/auth/callback", withSession(store, (req, res) => auth.handleCallback(req, res)));
router.get("/auth/logout",   withSession(store, (req, res) => auth.handleLogout(req, res)));
router.get("/auth/dummy",    withSession(store, (req, res) => dummy.handleLogin(req, res)));
router.get("/auth/dummy/list", withSession(store, (req, res) => dummy.handleList(req, res)));

const server = http.createServer((req, res) => {
  router.handle(req as Parameters<typeof router.handle>[0], res);
});

server.listen(PORT, HOST, () => {
  console.log(`Server running at ${BASE_URL}`);
  if (dummy.isEnabled()) {
    console.log(`Dummy login list: ${BASE_URL}/auth/dummy/list`);
  }
});
