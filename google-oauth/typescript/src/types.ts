import type { IncomingMessage, ServerResponse } from "http";

export interface User {
  id: string;
  email: string;
  name: string;
  picture: string;
}

export interface Session {
  id: string;
  user: User;
  createdAt: number;
}

export interface AppRequest extends IncomingMessage {
  session?: Session;
}

export type AppResponse = ServerResponse;

export type Handler = (req: AppRequest, res: AppResponse) => void | Promise<void>;
