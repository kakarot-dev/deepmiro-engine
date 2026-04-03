export interface MirofishConfig {
  mirofishUrl: string;
  llmApiKey: string;
  mcpApiKey?: string;
  transport: "stdio" | "http";
  httpPort: number;
  requestTimeoutMs: number;
  maxRetries: number;
}

export interface MirofishApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  traceback?: string;
  count?: number;
}

export type SimulationStatus =
  | "created"
  | "preparing"
  | "ready"
  | "running"
  | "completed"
  | "stopped"
  | "failed";

export type Platform = "twitter" | "reddit";

export interface SimulationState {
  simulation_id: string;
  project_id: string;
  graph_id: string;
  status: SimulationStatus;
  enable_twitter: boolean;
  enable_reddit: boolean;
  entities_count?: number;
  profiles_count?: number;
  entity_types?: string[];
  current_round?: number;
  created_at: string;
  updated_at?: string;
  error?: string;
}

export interface SimulationRunStatus {
  simulation_id: string;
  status: string;
  current_round: number;
  total_rounds: number;
  twitter_running: boolean;
  reddit_running: boolean;
  twitter_actions_count: number;
  reddit_actions_count: number;
  twitter_current_round: number;
  reddit_current_round: number;
  progress_percentage: number;
  recent_actions: AgentAction[];
}

export interface AgentAction {
  round_num: number;
  timestamp: string;
  platform: Platform;
  agent_id: number;
  agent_name: string;
  action_type: string;
  action_args: Record<string, unknown>;
  result?: string;
  success: boolean;
}

export interface SimulationSummary {
  simulation_id: string;
  project_id: string;
  project_name?: string;
  simulation_requirement?: string;
  status: SimulationStatus;
  entities_count?: number;
  created_at: string;
}

export type ReportStatus = "generating" | "completed" | "failed";

export interface Report {
  report_id: string;
  simulation_id: string;
  status: ReportStatus;
  outline?: { title: string; summary: string; sections: ReportSection[] };
  markdown_content?: string;
  created_at: string;
  completed_at?: string;
}

export interface ReportSection {
  title: string;
  content: string;
}

export interface InterviewResult {
  agent_id: number;
  prompt: string;
  result: {
    platforms?: Record<
      Platform,
      { agent_id: number; response: string; platform: Platform }
    >;
    agent_id?: number;
    response?: string;
    platform?: Platform;
  };
  timestamp: string;
}

export type TaskStatus = "pending" | "processing" | "completed" | "failed";

export interface TaskInfo {
  task_id: string;
  status: TaskStatus;
  progress: number;
  message: string;
  result?: Record<string, unknown>;
  error?: string;
}
