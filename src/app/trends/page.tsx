"use client";

import { useEffect, useState } from "react";
import { trends } from "@/lib/api";
import type { TrendItem } from "@/lib/api";

const PLATFORMS = ["all", "hackernews", "reddit_ai", "youtube"];
const CATEGORIES = ["all", "ai", "tech", "general"];

export default function TrendsPage() {
  const [items, setItems] = useState<TrendItem[]>([]);
  const [platform, setPlatform] = useState("all");
  const [category, setCategory] = useState("all");
  const [collecting, setCollecting] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    trends
      .list({
        platform: platform === "all" ? undefined : platform,
        category: category === "all" ? undefined : category,
        limit: 50,
      })
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(load, [platform, category]);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await trends.collect();
      load();
    } finally {
      setCollecting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Trending Topics</h1>
        <button
          onClick={handleCollect}
          disabled={collecting}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:opacity-50"
        >
          {collecting ? "Collecting..." : "Collect Now"}
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <FilterGroup label="Platform" options={PLATFORMS} value={platform} onChange={setPlatform} />
        <FilterGroup label="Category" options={CATEGORIES} value={category} onChange={setCategory} />
      </div>

      {/* Table */}
      {loading ? (
        <div className="h-64 animate-pulse rounded-xl bg-gray-800/50" />
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-700 p-12 text-center text-gray-500">
          No trends found. Click <strong>Collect Now</strong> to fetch fresh data.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-800 bg-gray-900/50 text-xs uppercase text-gray-400">
              <tr>
                <th className="px-4 py-3 w-12">#</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3 w-28">Platform</th>
                <th className="px-4 py-3 w-24">Category</th>
                <th className="px-4 py-3 w-20 text-right">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {items.map((t) => (
                <tr key={t.id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3 text-gray-500">{t.rank}</td>
                  <td className="px-4 py-3">
                    {t.url ? (
                      <a href={t.url} target="_blank" rel="noreferrer" className="hover:text-brand-500 hover:underline">
                        {t.title}
                      </a>
                    ) : (
                      t.title
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{t.platform}</td>
                  <td className="px-4 py-3">
                    <CategoryBadge category={t.category} />
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{t.score != null ? Math.round(t.score) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function FilterGroup({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400">{label}:</span>
      <div className="flex rounded-lg border border-gray-700 bg-gray-900/50">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              value === opt ? "bg-brand-600 text-white" : "text-gray-400 hover:text-gray-200"
            } ${opt === options[0] ? "rounded-l-lg" : ""} ${opt === options[options.length - 1] ? "rounded-r-lg" : ""}`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}

function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    ai: "bg-purple-500/20 text-purple-400",
    tech: "bg-blue-500/20 text-blue-400",
    general: "bg-gray-700/50 text-gray-400",
  };
  return (
    <span className={`rounded px-2 py-0.5 text-xs ${colors[category] ?? colors.general}`}>
      {category}
    </span>
  );
}
