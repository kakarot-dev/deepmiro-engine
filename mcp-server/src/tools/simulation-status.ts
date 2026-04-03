import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { MirofishClient } from "../client/mirofish-client.js";
import { toMcpError } from "../errors/index.js";

const inputSchema = {
  simulation_id: z.string().describe("The simulation ID returned by create_simulation"),
  detailed: z.boolean().optional().describe("Include recent agent actions in the response"),
};

export function registerSimulationStatus(server: McpServer, client: MirofishClient): void {
  server.registerTool(
    "simulation_status",
    {
      title: "Simulation Status",
      description: "Check the progress and status of a running or completed simulation.",
      inputSchema,
      annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    },
    async (args) => {
      try {
        const sim = await client.getSimulation(args.simulation_id);
        let runStatus = null;

        if (sim.status === "running" || sim.status === "completed") {
          try {
            runStatus = await client.getSimulationRunStatus(args.simulation_id);
          } catch {
            // Run status may not be available yet
          }
        }

        const result: Record<string, unknown> = {
          simulation_id: sim.simulation_id,
          status: sim.status,
          entities_count: sim.entities_count,
          profiles_count: sim.profiles_count,
        };

        if (runStatus) {
          result.current_round = runStatus.current_round;
          result.total_rounds = runStatus.total_rounds;
          result.progress_percentage = runStatus.progress_percentage;
          result.twitter_actions = runStatus.twitter_actions_count;
          result.reddit_actions = runStatus.reddit_actions_count;
          result.twitter_running = runStatus.twitter_running;
          result.reddit_running = runStatus.reddit_running;

          if (args.detailed && runStatus.recent_actions?.length) {
            result.recent_actions = runStatus.recent_actions.slice(0, 10).map((a) => ({
              agent: a.agent_name,
              action: a.action_type,
              platform: a.platform,
              round: a.round_num,
            }));
          }
        }

        if (sim.error) result.error = sim.error;

        return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        throw toMcpError(err);
      }
    },
  );
}
