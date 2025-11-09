import { UUID, Timestamped, Status } from './common';

export interface AgentConfig {
  name: string;
  description: string;
  system_prompt: string;
  model: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
  retry_attempts: number;
  context_sources: string[];
}

export interface AgentResult {
  status: Status;
  output: Record<string, any>;
  error?: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  metadata: Record<string, any>;
}

export interface Agent extends Timestamped {
  id: UUID;
  config: AgentConfig;
  status: Status;
  result?: AgentResult;
}

export interface AgentCreateRequest {
  config: AgentConfig;
}

export interface AgentExecuteRequest {
  input_data: Record<string, any>;
  timeout?: number;
}
