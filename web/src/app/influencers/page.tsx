"use client";

import { useEffect, useState } from "react";
import { influencers } from "@/lib/api";
import type { InfluencerItem, LeaderboardEntry } from "@/lib/api";

export default function InfluencersPage() {
  const [list, setList] = useState<InfluencerItem[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [tab, setTab] = useState<"list" | "leaderboard">("list");

  const load = () => {
    setLoading(true);
    Promise.allSettled([influencers.list(), influencers.leaderboard()]).then(
      ([l, lb]) => {
        if (l.status === "fulfilled") setList(l.value);
        if (lb.status === "fulfilled") setLeaderboard(lb.value);
        setLoading(false);
      },
    );
  };

  useEffect(load, []);

  const handleSeed = async () => {
    await influencers.seed();
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">AI Influencers</h1>
        <div className="flex gap-2">
          <button onClick={handleSeed} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-600 hover:text-white">
            Seed Defaults
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            {showForm ? "Cancel" : "Add Influencer"}
          </button>
        </div>
      </div>

      {showForm && <AddInfluencerForm onAdded={() => { setShowForm(false); load(); }} />}

      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg border border-gray-700 bg-gray-900/50 p-1 w-fit">
        <TabBtn active={tab === "list"} onClick={() => setTab("list")}>All Influencers</TabBtn>
        <TabBtn active={tab === "leaderboard"} onClick={() => setTab("leaderboard")}>Leaderboard</TabBtn>
      </div>

      {loading ? (
        <div className="h-64 animate-pulse rounded-xl bg-gray-800/50" />
      ) : tab === "list" ? (
        list.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-700 p-12 text-center text-gray-500">
            No influencers yet. Click <strong>Seed Defaults</strong> to load top AI influencers.
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((inf) => (
              <div key={inf.id} className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{inf.name}</p>
                    <p className="text-sm text-gray-400">{inf.handle}</p>
                  </div>
                  <div className="flex gap-2">
                    <span className="rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-400">{inf.platform}</span>
                    <CategoryTag category={inf.category} />
                  </div>
                </div>
                {inf.bio && <p className="mt-3 text-sm text-gray-400 leading-relaxed">{inf.bio}</p>}
              </div>
            ))}
          </div>
        )
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-800 bg-gray-900/50 text-xs uppercase text-gray-400">
              <tr>
                <th className="px-4 py-3 w-12">Rank</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Handle</th>
                <th className="px-4 py-3">Platform</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3 text-right">Followers</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {leaderboard.map((e, i) => (
                <tr key={e.id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3 text-gray-500">{i + 1}</td>
                  <td className="px-4 py-3 font-medium">{e.name}</td>
                  <td className="px-4 py-3 text-gray-400">{e.handle}</td>
                  <td className="px-4 py-3 text-gray-400">{e.platform}</td>
                  <td className="px-4 py-3"><CategoryTag category={e.category} /></td>
                  <td className="px-4 py-3 text-right font-mono">{e.followers != null ? e.followers.toLocaleString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
        active ? "bg-brand-600 text-white" : "text-gray-400 hover:text-gray-200"
      }`}
    >
      {children}
    </button>
  );
}

function CategoryTag({ category }: { category: string }) {
  const colors: Record<string, string> = {
    researcher: "bg-blue-500/20 text-blue-400",
    founder: "bg-green-500/20 text-green-400",
    creator: "bg-purple-500/20 text-purple-400",
    journalist: "bg-orange-500/20 text-orange-400",
  };
  return (
    <span className={`rounded px-2 py-0.5 text-xs ${colors[category] ?? "bg-gray-700 text-gray-400"}`}>
      {category}
    </span>
  );
}

function AddInfluencerForm({ onAdded }: { onAdded: () => void }) {
  const [name, setName] = useState("");
  const [handle, setHandle] = useState("");
  const [platform, setPlatform] = useState("twitter");
  const [category, setCategory] = useState("creator");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !handle) return;
    setSaving(true);
    try {
      await influencers.add({ name, handle, platform, category, bio });
      onAdded();
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <input type="text" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500" />
        <input type="text" placeholder="@handle" value={handle} onChange={(e) => setHandle(e.target.value)} required className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500" />
        <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100">
          <option value="twitter">Twitter/X</option>
          <option value="youtube">YouTube</option>
          <option value="linkedin">LinkedIn</option>
          <option value="github">GitHub</option>
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100">
          <option value="researcher">Researcher</option>
          <option value="founder">Founder</option>
          <option value="creator">Creator</option>
          <option value="journalist">Journalist</option>
        </select>
      </div>
      <textarea placeholder="Short bio..." value={bio} onChange={(e) => setBio(e.target.value)} rows={2} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500" />
      <button type="submit" disabled={saving} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
        {saving ? "Adding..." : "Add Influencer"}
      </button>
    </form>
  );
}
