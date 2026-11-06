const LOCAL_API_ORIGIN = "http://localhost:8000";
const PRODUCTION_API_ORIGIN = "https://orderflow-zo5f.onrender.com";

function resolveApiOrigin(): string {
  const configuredOrigin = import.meta.env.VITE_API_BASE_URL?.trim();
  const apiOrigin =
    configuredOrigin || (import.meta.env.DEV ? LOCAL_API_ORIGIN : PRODUCTION_API_ORIGIN);

  if (import.meta.env.PROD && /^(https?:\/\/)?localhost(?::\d+)?$/i.test(apiOrigin)) {
    throw new Error("VITE_API_BASE_URL must point to the deployed API in production.");
  }

  return apiOrigin.replace(/\/+$/, "");
}

export const API_BASE_URL = `${resolveApiOrigin()}/api/v1`;

const defaultHeaders = { "Content-Type": "application/json" };

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("orderflow_access");
  const headers = new Headers(options.headers);

  for (const [name, value] of Object.entries(defaultHeaders)) {
    if (!headers.has(name)) headers.set(name, value);
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item: { msg?: string }) => item.msg).join(", ")
      : body.detail;
    throw new Error(detail ?? "Request failed");
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
