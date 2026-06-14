export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DocumentItem {
  id: number;
  filename: string;
  page_count: number;
  status: "uploaded" | "processing" | "completed" | "failed";
  error: string | null;
  created_at: string;
}

export interface IndexEntry {
  topic: string;
  pages: number[];
}

export interface IndexGroup {
  letter: string;
  entries: IndexEntry[];
}

export interface IndexData {
  groups: IndexGroup[];
  total_topics: number;
  total_pages_referenced: number;
}

export interface IndexResponse {
  id: number;
  document_id: number;
  version: number;
  index: IndexData;
  index_text: string;
  created_at: string;
}

export interface SearchResult {
  topic: string;
  pages: number[];
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}
