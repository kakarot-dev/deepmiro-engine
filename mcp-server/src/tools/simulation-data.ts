// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026 kakarot-dev

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { MirofishClient } from "../client/mirofish-client.js";
import { toMcpError } from "../errors/index.js";

async function buildOverview(client: MirofishClient, simulationId: string): Promise<Record<string, unknown>> {
  const [sim, profiles, config, agentStats, timeline] = await Promise.all([
    client.getSimulation(simulationId).catch(() => null),
    client.getSimulationProfiles(simulationId).catch(() => []),
    client.getSimulationConfig(simulationId).catch(() => ({})),
    client.getAgentStats(simulationId).catch(() => ({})),
    client.getSimulationTimeline(simulationId).catch(() => []),
  ]);

  // Fetch knowledge graph if graph_id is available
  const graphId = (sim as any)?.graph_id;
  let knowledgeGraph: { entities: number; relations: number; top_entities: any[] } | null = null;
  if (graphId) {
    try {
      const gd = await client.getGraphData(graphId) as any;
      const nodes = gd?.nodes ?? [];
      const edges = gd?.edges ?? [];
      knowledgeGraph = {
        entities: nodes.length,
        relations: edges.length,
        top_entities: nodes.slice(0, 15).map((n: any) => ({
          name: n.name,
          type: n.entity_type || n.type,
          summary: n.summary?.slice(0, 100) || "",
        })),
      };
    } catch { /* graph not available */ }
  }

  // Condense profiles to name + type + stance (not full bios)
  const agents = (profiles as any[]).map((p: any, i: number) => ({
    id: i,
    name: p.realname || p.name || p.username || `Agent ${i}`,
    type: p.entity_type || p.profession || "Unknown",
    stance: p.stance || p.persona?.slice(0, 80) || "",
  }));

  // Condense config
  const timeConfig = (config as any)?.time_config;
  const entityTypes = (config as any)?.entity_types || (sim as any)?.entity_types || [];

  // Condense timeline to first/middle/last rounds
  const tl = timeline as any[];
  const timelineSnapshot = tl.length <= 5 ? tl : [
    tl[0],
    tl[Math.floor(tl.length / 4)],
    tl[Math.floor(tl.length / 2)],
    tl[Math.floor(tl.length * 3 / 4)],
    tl[tl.length - 1],
  ];

  return {
    simulation_id: simulationId,
    status: (sim as any)?.status ?? "unknown",
    entity_types: entityTypes,
    agents_count: agents.length,
    agents,
    simulation_config: timeConfig ? {
      total_hours: timeConfig.total_simulation_hours,
      minutes_per_round: timeConfig.minutes_per_round,
      platforms: [(sim as any)?.enable_twitter && "twitter", (sim as any)?.enable_reddit && "reddit"].filter(Boolean),
    } : null,
    knowledge_graph: knowledgeGraph,
    activity: agentStats,
    timeline_snapshot: timelineSnapshot,
  };
}

const inputSchema = {
  simulation_id: z.string().describe("The simulation ID"),
  data_type: z
    .enum(["overview", "profiles", "config", "actions", "posts", "timeline", "agent_stats", "interview_history"])
    .describe(
      "What data to retrieve: " +
      "overview (condensed summary: entities, agents, graph, config, action stats — start here), " +
      "profiles (full agent personas), " +
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
          case "overview":
            data = await buildOverview(client, args.simulation_id);
            break;
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
