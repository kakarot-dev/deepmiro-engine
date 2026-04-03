#!/usr/bin/env node

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import express from "express";
import { randomUUID } from "node:crypto";
import { loadConfig } from "./config.js";
import { createMcpServer } from "./server.js";
import { createAuthMiddleware } from "./middleware/auth.js";
import type { MirofishConfig } from "./types/index.js";

async function main() {
  const config = loadConfig();
  const { server } = createMcpServer(config);

  if (config.transport === "http") {
    await startHttpTransport(server, config);
  } else {
    await startStdioTransport(server);
  }
}

async function startStdioTransport(server: McpServer) {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write("mirofish-mcp: stdio transport connected\n");
}

async function startHttpTransport(server: McpServer, config: MirofishConfig) {
  const app = express();
  const auth = createAuthMiddleware(config.mcpApiKey);

  const sessions = new Map<string, StreamableHTTPServerTransport>();

  app.post("/mcp", auth, async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;

    if (sessionId && sessions.has(sessionId)) {
      const transport = sessions.get(sessionId)!;
      await transport.handleRequest(req, res, req.body);
      return;
    }

    // New session — create transport with session ID generator
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (id) => {
        sessions.set(id, transport);
      },
    });

    transport.onclose = () => {
      // Clean up any session pointing to this transport
      for (const [id, t] of sessions) {
        if (t === transport) sessions.delete(id);
      }
    };

    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  });

  app.get("/mcp", auth, async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    if (!sessionId || !sessions.has(sessionId)) {
      res.status(400).json({ error: "Invalid or missing session ID" });
      return;
    }
    const transport = sessions.get(sessionId)!;
    await transport.handleRequest(req, res);
  });

  app.delete("/mcp", auth, async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    if (sessionId && sessions.has(sessionId)) {
      const transport = sessions.get(sessionId)!;
      await transport.close();
      sessions.delete(sessionId);
    }
    res.status(200).json({ ok: true });
  });

  app.get("/health", (_req, res) => {
    res.json({ status: "ok", sessions: sessions.size });
  });

  app.listen(config.httpPort, () => {
    console.log(`mirofish-mcp: HTTP transport listening on port ${config.httpPort}`);
  });
}

main().catch((err) => {
  process.stderr.write(`mirofish-mcp fatal: ${err.message}\n`);
  process.exit(1);
});
