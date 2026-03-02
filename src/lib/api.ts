/**
 * Thin fetch wrapper for the SocialMonitor API.
 * All paths are relative (/api/...) – Next.js rewrites proxy them in dev.
 */

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// --- Trends ------------------------------------------------------------------

export const trends = {
  list: (params?: { platform?: string; category?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.platform) q.set("platform", params.platform);
    if (params?.category) q.set("category", params.category);
    if (params?.limit) q.set("limit", String(params.limit));
    return request<TrendItem[]>(`/api/trends?${q}`);
  },
  collect: (platform?: string) =>
    request<{ platforms_collected?: number; total_items?: number }>(
      `/api/trends/collect${platform ? `?platform=${platform}` : ""}`,
      { method: "POST" },
    ),
};

// --- Accounts ----------------------------------------------------------------

export const accounts = {
  list: () => request<Account[]>("/api/accounts"),
  add: (body: { platform: string; handle: string; display_name?: string }) =>
    request<{ id: number }>("/api/accounts", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  remove: (id: number) =>
    request<{ deleted: boolean }>(`/api/accounts/${id}`, { method: "DELETE" }),
  recordMetrics: (
    id: number,
    body: { followers?: number; engagement_rate?: number },
  ) =>
    request(`/api/accounts/${id}/metrics`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getMetrics: (id: number) =>
    request<MetricPoint[]>(`/api/accounts/${id}/metrics`),
};

// --- Influencers -------------------------------------------------------------

export const influencers = {
  list: (params?: { platform?: string; category?: string }) => {
    const q = new URLSearchParams();
    if (params?.platform) q.set("platform", params.platform);
    if (params?.category) q.set("category", params.category);
    return request<InfluencerItem[]>(`/api/influencers?${q}`);
  },
  seed: () => request<{ seeded: number }>("/api/influencers/seed", { method: "POST" }),
  add: (body: {
    name: string;
    handle: string;
    platform: string;
    category?: string;
    bio?: string;
  }) =>
    request<{ id: number }>("/api/influencers", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  leaderboard: () => request<LeaderboardEntry[]>("/api/influencers/leaderboard"),
};

// --- Content -----------------------------------------------------------------

export const content = {
  listPlans: (params?: { status?: string; platform?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.platform) q.set("platform", params.platform);
    return request<PlanItem[]>(`/api/content/plans?${q}`);
  },
  createPlan: (body: {
    title: string;
    platform?: string;
    content_type?: string;
    topic?: string;
    notes?: string;
  }) =>
    request<{ id: number; title: string }>("/api/content/plans", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deletePlan: (id: number) =>
    request(`/api/content/plans/${id}`, { method: "DELETE" }),
  generate: (planId: number, extra_context?: string) =>
    request<GeneratedItem>(`/api/content/generate/${planId}`, {
      method: "POST",
      body: JSON.stringify({ extra_context: extra_context ?? "" }),
    }),
  getGenerated: (planId: number) =>
    request<GeneratedItem[]>(`/api/content/plans/${planId}/generated`),
  autoGenerate: (platform?: string, content_type?: string) =>
    request<{ plan: { id: number; title: string }; content: GeneratedItem }>(
      "/api/content/auto-generate",
      {
        method: "POST",
        body: JSON.stringify({ platform: platform ?? "twitter", content_type: content_type ?? "post" }),
      },
    ),
  suggest: (count?: number) =>
    request<{ topics: string[] }>(
      `/api/content/suggest?count=${count ?? 5}`,
      { method: "POST" },
    ),
};

// --- Types -------------------------------------------------------------------

export interface TrendItem {
  id: number;
  rank: number;
  title: string;
  url: string;
  score: number | null;
  category: string;
  platform: string | null;
  captured_at: string | null;
}

export interface Account {
  id: number;
  platform: string;
  handle: string;
  display_name: string;
  added_at: string | null;
  current_followers: number | null;
  follower_growth: number | null;
  avg_engagement_rate: number | null;
  data_points: number;
}

export interface MetricPoint {
  id: number;
  captured_at: string;
  followers: number | null;
  engagement_rate: number | null;
  likes_recent: number | null;
  comments_recent: number | null;
}

export interface InfluencerItem {
  id: number;
  name: string;
  handle: string;
  platform: string;
  category: string;
  bio: string;
}

export interface LeaderboardEntry {
  id: number;
  name: string;
  handle: string | null;
  platform: string;
  category: string;
  followers: number | null;
  engagement_rate: number | null;
}

export interface PlanItem {
  id: number;
  title: string;
  platform: string;
  content_type: string;
  status: string;
  topic: string;
  notes: string;
  scheduled_for: string | null;
  created_at: string | null;
  generated_count: number;
}

export interface GeneratedItem {
  id: number;
  version: number;
  body: string;
  model_used: string;
  is_selected?: boolean;
  created_at?: string;
}
