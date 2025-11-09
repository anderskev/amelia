import { UUID, Timestamped } from './common';

export type DocumentType = 'pdf' | 'markdown' | 'text' | 'html' | 'code' | 'web_page';

export interface Document extends Timestamped {
  id: UUID;
  title: string;
  content: string;
  document_type: DocumentType;
  source_url?: string;
  file_path?: string;
  file_size?: number;
  metadata: Record<string, any>;
}

export interface DocumentUploadRequest {
  file: File;
  metadata?: Record<string, any>;
}

export interface DocumentSearchRequest {
  query: string;
  top_k?: number;
  similarity_threshold?: number;
}

export interface DocumentSearchResult {
  document: Document;
  chunk_content: string;
  similarity: number;
  chunk_index: number;
}
