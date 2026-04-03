import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { MirofishClient } from "./client/mirofish-client.js";
import { registerAllTools } from "./tools/index.js";
import type { MirofishConfig } from "./types/index.js";

export function createMcpServer(config: MirofishConfig): {
  server: McpServer;
  client: MirofishClient;
} {
  const server = new McpServer({
    name: "mirofish-mcp",
    version: "0.1.0",
  });

  const client = new MirofishClient(config);

  registerAllTools(server, client);

  return { server, client };
}
