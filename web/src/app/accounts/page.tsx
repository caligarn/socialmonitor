"use client";

import { useEffect, useState } from "react";
import { accounts } from "@/lib/api";
import type { Account } from "@/lib/api";

export default function AccountsPage() {
  const [accts, setAccts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const load = () => {
    setLoading(true);
    accounts
      .list()
      .then(setAccts)
      .catch(() => setAccts([]))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">My Accounts</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          {showForm ? "Cancel" : "Add Account"}
        </button>
      </div>

      {showForm && <AddAccountForm onAdded={() => { setShowForm(false); load(); }} />}

      {loading ? (
        <div className="h-48 animate-pulse rounded-xl bg-gray-800/50" />
      ) : accts.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-700 p-12 text-center text-gray-500">
          No accounts tracked yet. Click <strong>Add Account</strong> to start.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {accts.map((a) => (
            <AccountCard key={a.id} account={a} onDelete={() => { accounts.remove(a.id).then(load); }} />
          ))}
        </div>
      )}
    </div>
  );
}

function AccountCard({ account: a, onDelete }: { account: Account; onDelete: () => void }) {
  const [showMetrics, setShowMetrics] = useState(false);
  const [recording, setRecording] = useState(false);
  const [followers, setFollowers] = useState("");
  const [engagement, setEngagement] = useState("");

  const handleRecord = async () => {
    setRecording(true);
    try {
      await accounts.recordMetrics(a.id, {
        followers: followers ? parseInt(followers) : undefined,
        engagement_rate: engagement ? parseFloat(engagement) : undefined,
      });
      setShowMetrics(false);
      setFollowers("");
      setEngagement("");
    } finally {
      setRecording(false);
    }
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{a.platform}</p>
          <p className="text-lg font-semibold">{a.handle}</p>
          {a.display_name && <p className="text-sm text-gray-400">{a.display_name}</p>}
        </div>
        <button onClick={onDelete} className="text-xs text-gray-500 hover:text-red-400" title="Remove">
          &times;
        </button>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
        <MiniStat label="Followers" value={a.current_followers != null ? String(a.current_followers) : "-"} />
        <MiniStat
          label="Growth"
          value={a.follower_growth != null ? `${a.follower_growth > 0 ? "+" : ""}${a.follower_growth}` : "-"}
        />
        <MiniStat label="Engagement" value={a.avg_engagement_rate != null ? `${a.avg_engagement_rate}%` : "-"} />
      </div>

      <button
        onClick={() => setShowMetrics(!showMetrics)}
        className="mt-3 w-full rounded-lg border border-gray-700 px-3 py-1.5 text-xs text-gray-400 hover:border-gray-600 hover:text-gray-200"
      >
        Record Metrics
      </button>

      {showMetrics && (
        <div className="mt-3 space-y-2">
          <input
            type="number"
            placeholder="Followers"
            value={followers}
            onChange={(e) => setFollowers(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500"
          />
          <input
            type="number"
            step="0.1"
            placeholder="Engagement %"
            value={engagement}
            onChange={(e) => setEngagement(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500"
          />
          <button
            onClick={handleRecord}
            disabled={recording}
            className="w-full rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {recording ? "Saving..." : "Save"}
          </button>
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  );
}

function AddAccountForm({ onAdded }: { onAdded: () => void }) {
  const [platform, setPlatform] = useState("twitter");
  const [handle, setHandle] = useState("");
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle) return;
    setSaving(true);
    try {
      await accounts.add({ platform, handle, display_name: name });
      onAdded();
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
      <div className="grid gap-3 sm:grid-cols-3">
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
        >
          <option value="twitter">Twitter/X</option>
          <option value="linkedin">LinkedIn</option>
          <option value="youtube">YouTube</option>
          <option value="instagram">Instagram</option>
          <option value="tiktok">TikTok</option>
          <option value="github">GitHub</option>
        </select>
        <input
          type="text"
          placeholder="@handle"
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
          required
          className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500"
        />
        <input
          type="text"
          placeholder="Display name (optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500"
        />
      </div>
      <button
        type="submit"
        disabled={saving || !handle}
        className="mt-3 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
      >
        {saving ? "Adding..." : "Add Account"}
      </button>
    </form>
  );
}
