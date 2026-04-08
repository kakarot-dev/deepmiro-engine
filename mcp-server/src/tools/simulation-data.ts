// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026 kakarot-dev

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { MirofishClient } from "../client/mirofish-client.js";
import { toMcpError } from "../errors/index.js";

const inputSchema = {
  simulation_id: z.string().describe("The simulation ID"),
  data_type: z
    .enum(["profiles", "config", "actions", "posts", "timeline", "agent_stats", "interview_history"])
    .describe(
      "What data to retrieve: " +
      "profiles (agent personas), " +
      "config (simulation parameters), " +
      "actions (agent action log), " +
      "posts (social media posts from SQLite), " +
      "timeline (per-round summaries), " +
      "agent_stats (per-agent activity breakdown), " +
      "interview_history (past interview transcripts)",
    ),
  platform: z
    .enum(["twitter", "reddit"])
    .optional()
    .describe("Filter by platform (for actions and posts)"),
  agent_name: z.string().optional().describe("Filter actions by agent name"),
  action_type: z.string().optional().describe("Filter actions by type (CREATE_POST, LIKE_POST, etc.)"),
  limit: z.number().int().min(1).max(200).optional().describe("Max results (default 50)"),
};

export function registerSimulationData(server: McpServer, client: MirofishClient): void {
  server.registerTool(
    "simulation_data",
    {
      title: "Simulation Data",
      description:
        "Access raw simulation data: agent profiles, configuration, action logs, " +
        "social media posts, round-by-round timeline, per-agent activity stats, " +
        "and interview history. Use this to inspect what happened during a simulation.",
      inputSchema,
      annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    },
    async (args) => {
      try {
        let data: unknown;

        switch (args.data_type) {
          case "profiles":
            data = await client.getSimulationProfiles(args.simulation_id);
            break;
          case "config":
            data = await client.getSimulationConfig(args.simulation_id);
            break;
          case "actions":
            data = await client.getSimulationActions(args.simulation_id, {
              platform: args.platform,
              agent_name: args.agent_name,
              action_type: args.action_type,
              limit: args.limit ?? 50,
            });
            break;
          case "posts":
            data = await client.getSimulationPosts(args.simulation_id, {
              platform: args.platform,
              limit: args.limit ?? 50,
            });
            break;
          case "timeline":
            data = await client.getSimulationTimeline(args.simulation_id);
            break;
          case "agent_stats":
            data = await client.getAgentStats(args.simulation_id);
            break;
          case "interview_history":
            data = await client.getInterviewHistory(args.simulation_id);
            break;
        }

        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      } catch (err) {
        throw toMcpError(err);
      }
    },
  );
}
