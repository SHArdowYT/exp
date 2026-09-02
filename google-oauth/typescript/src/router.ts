import type { AppRequest, AppResponse, Handler } from "./types.js";

type Route = { method: string; path: string; handler: Handler };

/**
 * Minimal router. Matches exact paths only.
 * For a real app you'd add pattern matching, but this keeps things simple.
 */
export class Router {
  private routes: Route[] = [];

  get(path: string, handler: Handler): void {
    this.routes.push({ method: "GET", path, handler });
  }

  handle(req: AppRequest, res: AppResponse): void {
    const urlPath = new URL(req.url ?? "/", `http://${req.headers.host}`).pathname;
    const method = req.method ?? "GET";

    const route = this.routes.find((r) => r.method === method && r.path === urlPath);

    if (route) {
      Promise.resolve(route.handler(req, res)).catch((err) => {
        console.error("Unhandled route error:", err);
        if (!res.headersSent) {
          res.writeHead(500);
          res.end("Internal server error.");
        }
      });
    } else {
      res.writeHead(404);
      res.end("Not found.");
    }
  }
}
