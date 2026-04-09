// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026 kakarot-dev

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { MirofishClient } from "../client/mirofish-client.js";
import { toMcpError } from "../errors/index.js";

const inputSchema = {
  prompt: z
    .string()
    .min(10)
    .describe("Scenario description. E.g. 'How will crypto twitter react to a new ETH ETF rejection?'"),
  preset: z
    .enum(["quick", "standard", "deep"])
    .optional()
    .describe("Simulation preset: quick (10 agents, 20 rounds), standard (20/40), deep (50/72)"),
  agent_count: z.number().int().min(2).max(500).optional().describe("Override agent count"),
  rounds: z.number().int().min(1).max(100).optional().describe("Override simulation rounds"),
  platform: z
    .enum(["twitter", "reddit", "both"])
    .optional()
    .describe("Target platform(s). Default: both"),
  document_id: z
    .string()
    .optional()
    .describe("ID of a pre-uploaded document (from upload_document tool). Skips file upload and uses server-side sanitized text."),
};

export function registerCreateSimulation(server: McpServer, client: MirofishClient): void {
  server.registerTool(
    "create_simulation",
    {
      title: "Create Simulation",
      description:
        "Run a full swarm prediction. Builds a knowledge graph, generates agent personas, " +
        "runs a multi-agent social media simulation, and generates a prediction report. " +
        "Streams progress updates. Returns the final report when complete.",
      inputSchema,
      annotations: { readOnlyHint: false, destructiveHint: false, openWorldHint: true },
    },
    async (args, extra) => {
      try {
        const progressToken = (args as any)?._meta?.progressToken;

        const sendProgress = async (progress: number, total: number, message?: string) => {
          if (!progressToken) return;
          try {
            await extra.sendNotification({
              method: "notifications/progress",
              params: { progressToken, progress, total, ...(message ? { message } : {}) },
            } as any);
          } catch {
            // Client may not support progress — ignore
          }
        };

        // Phase 1: Build knowledge graph (0-20%)
        await sendProgress(0, 100, "Generating ontology...");
        const ontologyResp = await (client as any).generateOntology(args.prompt, undefined, args.document_id);
        const projectId = ontologyResp.project_id;

        await sendProgress(5, 100, "Building knowledge graph...");
        const buildTask = await (client as any).buildGraph(projectId);

        // Poll graph build
        const graphDeadline = Date.now() + 600_000;
        while (Date.now() < graphDeadline) {
          const task = await client.getGraphTaskStatus(buildTask.task_id);
          await sendProgress(5 + Math.round(task.progress * 0.15), 100, `Building knowledge graph... ${task.progress}%`);
          if (task.status === "completed") break;
          if (task.status === "failed") throw new Error(`Graph build failed: ${task.error ?? task.message}`);
          await sleep(3000);
        }

        // Phase 2: Create sim + generate profiles (20-60%)
        await sendProgress(20, 100, "Creating simulation...");
        const project = await (client as any).getProject(projectId);
        const enableTwitter = args.platform !== "reddit";
        const enableReddit = args.platform !== "twitter";
        const simState = await (client as any).createSimulationRecord(projectId, project.graph_id, enableTwitter, enableReddit);
        const simulationId = simState.simulation_id;

        await sendProgress(22, 100, "Generating agent personas...");
        const prepareResp = await (client as any).prepareSimulation(simulationId);

        // Poll prepare
        if (prepareResp.task_id) {
          const prepDeadline = Date.now() + 600_000;
          while (Date.now() < prepDeadline) {
            const resp = await client.getPrepareStatus(simulationId, prepareResp.task_id);
            const pct = 22 + Math.round((resp.progress ?? 0) * 0.38);
            const detail = resp.progress_detail;
            const msg = detail?.current_item && detail?.total_items
              ? `Generating personas: ${detail.current_item}/${detail.total_items}`
              : resp.message ?? "Generating personas...";
            await sendProgress(pct, 100, msg);
            if (resp.status === "completed" || resp.status === "ready") break;
            if (resp.status === "failed") throw new Error("Profile generation failed");
            await sleep(3000);
          }
        }

        // Phase 3: Run simulation (60-85%)
        await sendProgress(60, 100, "Starting simulation...");
        const maxRounds = args.rounds ?? resolveRounds(args.preset);
        const platform = args.platform === "both" || !args.platform ? "parallel" : args.platform;
        await (client as any).startSimulation(simulationId, platform, maxRounds);

        // Poll simulation
        const simDeadline = Date.now() + 1_800_000; // 30 min max
        while (Date.now() < simDeadline) {
          try {
            const sim = await client.getSimulation(simulationId);
            if (sim.status === "completed") break;
            if (sim.status === "failed") throw new Error(`Simulation failed: ${sim.error ?? "unknown"}`);

            const runStatus = await client.getSimulationRunStatus(simulationId);
            const totalActions = runStatus.twitter_actions_count + runStatus.reddit_actions_count;
            const simPct = runStatus.total_rounds > 0
              ? Math.round((runStatus.current_round / runStatus.total_rounds) * 25)
              : 0;
            await sendProgress(60 + simPct, 100, `Round ${runStatus.current_round}/${runStatus.total_rounds} — ${totalActions} actions`);
          } catch {
            // transient error — keep polling
          }
          await sleep(5000);
        }

        // Phase 4: Generate report (85-100%)
        await sendProgress(85, 100, "Generating prediction report...");
        let reportMarkdown = "";
        try {
          const report = await client.getOrGenerateReport(simulationId);
          reportMarkdown = report.markdown_content ?? "";

          // If report is still generating, poll a bit more
          if (report.status !== "completed" && report.report_id) {
            const reportDeadline = Date.now() + 600_000;
            while (Date.now() < reportDeadline) {
              await sendProgress(90, 100, "Writing report sections...");
              try {
                const r = await (client as any).get(`/api/report/${report.report_id}`);
                if (r.data?.status === "completed") {
                  reportMarkdown = r.data.markdown_content ?? "";
                  break;
                }
                if (r.data?.status === "failed") break;
              } catch { /* keep polling */ }
              await sleep(5000);
            }
          }
        } catch {
          reportMarkdown = "Report generation failed. Use get_report to retry.";
        }

        await sendProgress(100, 100, "Prediction complete");

        return {
          content: [
            {
              type: "text" as const,
              text: reportMarkdown || `Simulation ${simulationId} completed but report is empty. Use get_report to retry.`,
            },
          ],
        };
      } catch (err) {
        throw toMcpError(err);
      }
    },
  );
}

function resolveRounds(preset?: string): number | undefined {
  switch (preset) {
    case "quick": return 20;
    case "standard": return 40;
    case "deep": return 72;
    default: return undefined;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
