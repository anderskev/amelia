export type UUID = string;

export interface Timestamped {
  created_at: string;
  updated_at: string;
}

export type Status = 'idle' | 'running' | 'completed' | 'failed' | 'paused';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}
