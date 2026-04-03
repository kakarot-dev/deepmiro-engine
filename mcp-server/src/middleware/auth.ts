import type { Request, Response, NextFunction } from "express";
import { timingSafeEqual } from "node:crypto";

export function createAuthMiddleware(apiKey?: string) {
  if (!apiKey) {
    return (_req: Request, _res: Response, next: NextFunction) => next();
  }

  const keyBuffer = Buffer.from(apiKey);

  return (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith("Bearer ")) {
      res.status(401).json({ error: "Missing or invalid Authorization header" });
      return;
    }

    const provided = Buffer.from(authHeader.slice(7));
    if (provided.length !== keyBuffer.length || !timingSafeEqual(provided, keyBuffer)) {
      res.status(403).json({ error: "Invalid API key" });
      return;
    }

    next();
  };
}
