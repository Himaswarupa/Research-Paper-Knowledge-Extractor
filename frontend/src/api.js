const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

export const getHealth = () => request("/health");
export const getConfig = () => request("/config");

export function uploadPaper(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/upload", { method: "POST", body: form });
}

export const getStatus = (name) => request(`/status/${encodeURIComponent(name)}`);
export const getPapers = () => request("/papers");
export const getGraphData = () => request("/graph/data");
export const queryNode = (q) => request(`/query?q=${encodeURIComponent(q)}`);