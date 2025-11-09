import { UUID, Timestamped } from './common';

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: UUID;
  role: MessageRole;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChatSession extends Timestamped {
  id: UUID;
  title: string;
  messages: Message[];
  model: string;
  temperature: number;
  max_tokens: number;
}

export interface ChatSendRequest {
  message: string;
  context_documents?: UUID[];
  stream?: boolean;
}

export interface ChatStreamChunk {
  delta: string;
  finish_reason?: 'stop' | 'length' | 'error';
}
