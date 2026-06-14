import axios from "axios";
import { useAuth } from "./store";
import type {
  AuthResponse,
  DocumentItem,
  IndexResponse,
  SearchResponse,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const api = axios.create({ baseURL: API_URL });

// Attach the JWT from the persisted auth store to every request.
api.interceptors.request.use((config) => {
  const token = useAuth.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) useAuth.getState().logout();
    return Promise.reject(error);
  }
);

// ---- Auth ----
export async function register(name: string, email: string, password: string) {
  const { data } = await api.post<AuthResponse>("/auth/register", {
    name,
    email,
    password,
  });
  return data;
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const { data } = await api.post<AuthResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

// ---- Documents ----
export async function listDocuments() {
  const { data } = await api.get<DocumentItem[]>("/documents");
  return data;
}

export async function uploadDocument(
  file: File,
  onProgress?: (pct: number) => void
) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<DocumentItem>("/documents/upload", form, {
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return data;
}

export async function deleteDocument(id: number) {
  await api.delete(`/documents/${id}`);
}

// ---- Index ----
export async function generateIndex(documentId: number, enableOcr = false) {
  const { data } = await api.post<IndexResponse>("/generate-index", {
    document_id: documentId,
    enable_ocr: enableOcr,
  });
  return data;
}

export async function getIndex(id: number) {
  const { data } = await api.get<IndexResponse>(`/index/${id}`);
  return data;
}

export async function getHistory(documentId?: number) {
  const { data } = await api.get<IndexResponse[]>("/history", {
    params: documentId ? { document_id: documentId } : {},
  });
  return data;
}

export async function searchIndex(indexId: number, q: string) {
  const { data } = await api.get<SearchResponse>(`/index/${indexId}/search`, {
    params: { q },
  });
  return data;
}

export function exportUrl(fmt: string, indexId: number) {
  return `${API_URL}/export/${fmt}/${indexId}`;
}

export async function downloadExport(fmt: string, indexId: number) {
  const res = await api.get(`/export/${fmt}/${indexId}`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `index_${indexId}.${fmt === "markdown" ? "md" : fmt}`;
  a.click();
  URL.revokeObjectURL(url);
}
