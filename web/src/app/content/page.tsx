"use client";

import { useEffect, useState } from "react";
import { content } from "@/lib/api";
import type { PlanItem, GeneratedItem } from "@/lib/api";

export default function ContentPage() {
  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [suggestingTopics, setSuggestingTopics] = useState(false);
  const [autoGenerating, setAutoGenerating] = useState(false);
  const [autoResult, setAutoResult] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    content
      .listPlans()
      .then(setPlans)
      .catch(() => setPlans([]))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleAutoGenerate = async () => {
    setAutoGenerating(true);
    setAutoResult(null);
    try {
      const res = await content.autoGenerate("twitter", "post");
      setAutoResult(res.content.body);
      load();
    } catch (err: any) {
      setAutoResult(`Error: ${err.message}`);
    } finally {
      setAutoGenerating(false);
    }
  };

  const handleSuggest = async () => {
    setSuggestingTopics(true);
    try {
      const res = await content.suggest(5);
      setSuggestions(res.topics);
    } catch {
      setSuggestions(["Failed to load suggestions."]);
    } finally {
      setSuggestingTopics(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Content Planner</h1>
        <div className="flex gap-2">
          <button
            onClick={handleSuggest}
            disabled={suggestingTopics}
            className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-600 hover:text-white disabled:opacity-50"
          >
            {suggestingTopics ? "Thinking..." : "Suggest Topics"}
          </button>
          <button
            onClick={handleAutoGenerate}
            disabled={autoGenerating}
            className="rounded-lg border border-purple-700 bg-purple-600/20 px-4 py-2 text-sm font-medium text-purple-300 hover:bg-purple-600/30 disabled:opacity-50"
          >
            {autoGenerating ? "Generating..." : "Auto-Generate from Trends"}
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            {showForm ? "Cancel" : "New Plan"}
          </button>
        </div>
      </div>

      {/* AI Suggestions */}
      {suggestions.length > 0 && (
        <div className="rounded-xl border border-purple-800 bg-purple-900/20 p-5">
          <h3 className="mb-2 text-sm font-semibold text-purple-300">AI-Suggested Topics</h3>
          <div className="space-y-1 text-sm text-gray-300">
            {suggestions.map((s, i) => (
              <p key={i}>{s}</p>
            ))}
          </div>
        </div>
      )}

      {/* Auto-generated content result */}
      {autoResult && (
        <div className="rounded-xl border border-green-800 bg-green-900/20 p-5">
          <h3 className="mb-2 text-sm font-semibold text-green-300">Auto-Generated Content</h3>
          <p className="whitespace-pre-wrap text-sm text-gray-200">{autoResult}</p>
        </div>
      )}

      {showForm && <CreatePlanForm onCreated={() => { setShowForm(false); load(); }} />}

      {/* Plan list */}
      {loading ? (
        <div className="h-48 animate-pulse rounded-xl bg-gray-800/50" />
      ) : plans.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-700 p-12 text-center text-gray-500">
          No content plans yet. Create one or use <strong>Auto-Generate</strong>.
        </div>
      ) : (
        <div className="space-y-4">
          {plans.map((p) => (
            <PlanCard key={p.id} plan={p} onDelete={() => content.deletePlan(p.id).then(load)} />
          ))}
        </div>
      )}
    </div>
  );
}

function PlanCard({ plan: p, onDelete }: { plan: PlanItem; onDelete: () => void }) {
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<GeneratedItem[]>([]);
  const [showGenerated, setShowGenerated] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await content.generate(p.id);
      loadGenerated();
    } finally {
      setGenerating(false);
    }
  };

  const loadGenerated = () => {
    content.getGenerated(p.id).then((items) => {
      setGenerated(items);
      setShowGenerated(true);
    });
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold">{p.title}</h3>
          <div className="mt-1 flex items-center gap-2 text-xs text-gray-400">
            <span className="rounded bg-gray-800 px-2 py-0.5">{p.platform}</span>
            <span className="rounded bg-gray-800 px-2 py-0.5">{p.content_type}</span>
            <StatusBadge status={p.status} />
            {p.scheduled_for && (
              <span className="text-gray-500">Scheduled: {new Date(p.scheduled_for).toLocaleDateString()}</span>
            )}
          </div>
          {p.topic && <p className="mt-2 text-sm text-gray-400">Topic: {p.topic}</p>}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="rounded-lg border border-brand-700 px-3 py-1.5 text-xs font-medium text-brand-400 hover:bg-brand-600/20 disabled:opacity-50"
          >
            {generating ? "Generating..." : "Generate"}
          </button>
          {p.generated_count > 0 && (
            <button
              onClick={loadGenerated}
              className="rounded-lg border border-gray-700 px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200"
            >
              View ({p.generated_count})
            </button>
          )}
          <button onClick={onDelete} className="text-xs text-gray-500 hover:text-red-400" title="Delete">
            &times;
          </button>
        </div>
      </div>

      {showGenerated && generated.length > 0 && (
        <div className="mt-4 space-y-3 border-t border-gray-800 pt-4">
          {generated.map((g) => (
            <div key={g.id} className="rounded-lg bg-gray-800/50 p-4">
              <div className="mb-2 flex items-center justify-between text-xs text-gray-500">
                <span>v{g.version} &middot; {g.model_used}</span>
                {g.is_selected && <span className="text-green-400">Selected</span>}
              </div>
              <p className="whitespace-pre-wrap text-sm text-gray-200">{g.body}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-yellow-500/20 text-yellow-400",
    scheduled: "bg-blue-500/20 text-blue-400",
    published: "bg-green-500/20 text-green-400",
  };
  return (
    <span className={`rounded px-2 py-0.5 ${colors[status] ?? "bg-gray-700 text-gray-300"}`}>{status}</span>
  );
}

function CreatePlanForm({ onCreated }: { onCreated: () => void }) {
  const [title, setTitle] = useState("");
  const [platform, setPlatform] = useState("twitter");
  const [contentType, setContentType] = useState("post");
  const [topic, setTopic] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) return;
    setSaving(true);
    try {
      await content.createPlan({ title, platform, content_type: contentType, topic: topic || title, notes });
      onCreated();
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-3">
      <input type="text" placeholder="Plan title" value={title} onChange={(e) => setTitle(e.target.value)} required className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500" />
      <div className="grid gap-3 sm:grid-cols-3">
        <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100">
          <option value="twitter">Twitter/X</option>
          <option value="linkedin">LinkedIn</option>
          <option value="youtube">YouTube</option>
          <option value="blog">Blog</option>
          <option value="instagram">Instagram</option>
        </select>
        <select value={contentType} onChange={(e) => setContentType(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100">
          <option value="post">Post</option>
          <option value="thread">Thread</option>
          <option value="video_script">Video Script</option>
          <option value="article">Article</option>
        </select>
        <input type="text" placeholder="Topic" value={topic} onChange={(e) => setTopic(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500" />
      </div>
      <textarea placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500" />
      <button type="submit" disabled={saving} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
        {saving ? "Creating..." : "Create Plan"}
      </button>
    </form>
  );
}
