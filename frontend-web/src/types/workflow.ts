import { UUID, Timestamped, Status } from './common';

export interface WorkflowNode {
  id: string;
  type: 'agent' | 'condition' | 'parallel';
  agent_name?: string;
  config?: Record<string, any>;
}

export interface WorkflowEdge {
  from: string;
  to: string;
  condition?: string;
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  metadata: Record<string, any>;
}

export interface Workflow extends Timestamped {
  id: UUID;
  name: string;
  description: string;
  definition: WorkflowDefinition;
  status: Status;
  started_at?: string;
  completed_at?: string;
  current_node?: string;
  result?: Record<string, any>;
}

export interface WorkflowCreateRequest {
  name: string;
  description: string;
  definition: WorkflowDefinition;
}

export interface WorkflowExecuteRequest {
  input_data: Record<string, any>;
}
