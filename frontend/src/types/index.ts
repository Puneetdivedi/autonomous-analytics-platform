// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export enum UserRole {
  ADMIN = 'admin',
  ANALYST = 'analyst',
  VIEWER = 'viewer',
}

export type StreamEventType =
  | 'node_start'
  | 'node_end'
  | 'token'
  | 'artifact'
  | 'error'
  | 'done';

export type AgentStatus = 'pending' | 'running' | 'success' | 'error' | 'retrying';

export type ChartType =
  | 'bar'
  | 'line'
  | 'pie'
  | 'scatter'
  | 'area'
  | 'histogram'
  | 'heatmap';

// ---------------------------------------------------------------------------
// Core domain models
// ---------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  created_at?: string;
  updated_at?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface DataSource {
  id: string;
  project_id: string;
  name: string;
  type: string;
  status?: string;
  connection_string?: string;
  schema_json?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface Chat {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface Message {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  artifacts?: Artifacts;
  datasource_id?: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Artifacts
// ---------------------------------------------------------------------------

export interface ChartSpec {
  type: ChartType;
  title: string;
  x?: string;
  y?: string | string[];
  data: Array<Record<string, unknown>>;
  image_b64?: string;
}

export interface Insights {
  executive_summary: string;
  key_findings: string[];
  root_cause?: string;
  risks: string[];
  opportunities: string[];
}

export interface Recommendation {
  title: string;
  detail: string;
  impact: string;
  effort: string;
}

export interface StatisticsReport {
  [key: string]: unknown;
}

export interface ReportArtifact {
  report_id: string;
  format: string;
  file_path: string;
}

export interface Artifacts {
  sql?: string;
  charts?: ChartSpec[];
  statistics?: StatisticsReport;
  insights?: Insights;
  recommendations?: Recommendation[];
  report?: ReportArtifact;
}

// ---------------------------------------------------------------------------
// Observability
// ---------------------------------------------------------------------------

export interface AgentExecution {
  node_name: string;
  agent_name: string;
  status: AgentStatus;
  attempt: number;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  error?: string | null;
  created_at: string;
}

export interface TraceSpan {
  span_id: string;
  name: string;
  status: AgentStatus;
  latency_ms: number;
  start_time?: string;
  end_time?: string;
  attributes?: Record<string, unknown>;
}

export interface TraceSummary {
  trace_id: string;
  message_id: string;
  total_latency_ms: number;
  total_tokens: number;
  total_cost_usd: number;
  status: AgentStatus;
  spans?: TraceSpan[];
  created_at: string;
}

export interface Report {
  id: string;
  project_id: string;
  title?: string;
  format: string;
  file_path?: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Auth / streaming
// ---------------------------------------------------------------------------

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface StreamEvent {
  type: StreamEventType;
  node?: string;
  data?: unknown;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}

export interface SendMessagePayload {
  question: string;
  datasource_id?: string;
  stream?: boolean;
}
