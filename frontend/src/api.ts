import { z } from "zod";
import type { Category, SearchRequest, Settlement, Shop } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { signal });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export function getCategories(signal?: AbortSignal): Promise<Category[]> {
  return getJson<Category[]>("/categories", signal);
}

export function getLocations(query: string, signal?: AbortSignal): Promise<Settlement[]> {
  return getJson<Settlement[]>(`/locations?q=${encodeURIComponent(query)}`, signal);
}

const errorSchema = z.object({ detail: z.unknown().optional(), area: z.array(z.string()).optional() });

export async function streamRecommendations(
  request: SearchRequest,
  onShops: (shops: Shop[]) => void,
  onDelta: (text: string) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/recommendations?stream=true`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(request),
    signal,
  });
  if (!response.ok) {
    const payload: unknown = await response.json();
    const parsed = errorSchema.safeParse(payload);
    const detail = parsed.success && typeof parsed.data.detail === "string" ? parsed.data.detail : null;
    throw new Error(parsed.success && parsed.data.area?.[0] ? parsed.data.area[0] : detail ?? `Search failed (${response.status})`);
  }
  if (!response.body) throw new Error("Streaming is not supported by this browser.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const lines = frame.split("\n");
      const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
      const rawData = lines.find((line) => line.startsWith("data:"))?.slice(5).trim();
      if (!rawData) continue;
      const data: unknown = JSON.parse(rawData);
      if (event === "shops" && Array.isArray(data)) onShops(data as Shop[]);
      if (event === "answer_delta" && typeof data === "object" && data && "text" in data) onDelta(String(data.text));
      if (event === "error") throw new Error("The local assistant could not finish the answer.");
    }
  }
}
