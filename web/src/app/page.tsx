"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { trends, accounts, influencers, content } from "@/lib/api";
import type { TrendItem, Account, PlanItem } from "@/lib/api";

export default function Dashboard() {
  const [topTrends, setTopTrends] = useState<TrendItem[]>([]);
  const [accts, setAccts] = useState<Account[]>([]);
  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [infCount, setInfCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      trends.list({ limit: 5, category: "ai" }),
      accounts.list(),
      content.listPlans(),
      influencers.list(),
    ]).then(([t, a, p, i]) => {
      if (t.status === "fulfilled") setTopTrends(t.value);
      if (a.status === "fulfilled") setAccts(a.value);
      if (p.status === "fulfilled") setPlans(p.value);
      if (i.status === "fulfilled") setInfCount(i.value.length);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <Skeleton />;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Trending Topics" value={topTrends.length > 0 ? "Live" : "No data"} sub="AI & Tech" href="/trends" />
        <StatCard label="My Accounts" value={String(accts.length)} sub="tracked" href="/accounts" />
        <StatCard label="AI Influencers" value={String(infCount)} sub="monitored" href="/influencers" />
        <StatCard label="Content Plans" value={String(plans.length)} sub={`${plans.filter((p) => p.status === "draft").length} drafts`} href="/content" />
      </div>

      {/* Recent AI trends */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Top AI Trends</h2>
          <Link href="/trends" className="text-sm text-brand-500 hover:underline">
            View all
          </Link>
        </div>
        {topTrends.length === 0 ? (
          <EmptyCard message='No trend data yet. Go to Trends and click "Collect" to fetch.' />
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-800">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-gray-800 bg-gray-900/50 text-xs uppercase text-gray-400">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Platform</th>
                  <th className="px-4 py-3 text-right">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {topTrends.map((t) => (
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
                    <td className="px-4 py-3 text-right font-mono">{t.score ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Recent content plans */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent Content Plans</h2>
          <Link href="/content" className="text-sm text-brand-500 hover:underline">
            Manage
          </Link>
        </div>
        {plans.length === 0 ? (
          <EmptyCard message="No content plans yet. Create one from the Content page." />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {plans.slice(0, 6).map((p) => (
              <div key={p.id} className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
                <p className="font-medium">{p.title}</p>
                <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
                  <span className="rounded bg-gray-800 px-2 py-0.5">{p.platform}</span>
                  <span className="rounded bg-gray-800 px-2 py-0.5">{p.content_type}</span>
                  <StatusBadge status={p.status} />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value, sub, href }: { label: string; value: string; sub: string; href: string }) {
  return (
    <Link href={href} className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 transition-colors hover:border-gray-700">
      <p className="text-sm text-gray-400">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
      <p className="mt-0.5 text-xs text-gray-500">{sub}</p>
    </Link>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-yellow-500/20 text-yellow-400",
    scheduled: "bg-blue-500/20 text-blue-400",
    published: "bg-green-500/20 text-green-400",
  };
  return (
    <span className={`rounded px-2 py-0.5 ${colors[status] ?? "bg-gray-700 text-gray-300"}`}>
      {status}
    </span>
  );
}

function EmptyCard({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-700 p-8 text-center text-sm text-gray-500">
      {message}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-8">
      <div className="h-8 w-40 animate-pulse rounded bg-gray-800" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-800/50" />
        ))}
      </div>
      <div className="h-64 animate-pulse rounded-xl bg-gray-800/50" />
    </div>
  );
}
