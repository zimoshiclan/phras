"use client";
import { useEffect, useState } from "react";
import { supabase, API_URL } from "@/lib/supabase";

type Profile = {
  id: string;
  label: string;
  corpus_word_count: number;
  source_types: string[];
  updated_at: string;
};

const SOURCES = ["whatsapp", "telegram", "email", "twitter", "linkedin", "essay", "plain"];

export default function Dashboard() {
  const [apiKey, setApiKey] = useState<string>("");
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [source, setSource] = useState("whatsapp");
  const [sender, setSender] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    setApiKey(localStorage.getItem("phras_api_key") || "");
  }, []);

  async function refreshProfiles() {
    if (!apiKey) return;
    const r = await fetch(`${API_URL}/v1/account/export`, {
      headers: { "X-API-Key": apiKey },
    });
    if (!r.ok) return;
    const data = await r.json();
    setProfiles(data.style_profiles || []);
  }

  useEffect(() => { refreshProfiles(); /* eslint-disable-next-line */ }, [apiKey]);

  async function upload() {
    if (!file || !apiKey) { setStatus("need API key + file"); return; }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("source", source);
    if (sender) fd.append("target_sender", sender);
    setStatus("uploading (first request may take ~30s on cold start)...");
    const r = await fetch(`${API_URL}/v1/upload`, {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: fd,
    });
    if (!r.ok) { setStatus(`upload failed: ${await r.text()}`); return; }
    const { job_id } = await r.json();
    setStatus(`processing (job ${job_id})...`);
    const style_id = await poll(job_id, apiKey);
    setStatus(style_id ? `done — style ${style_id}` : `failed`);
    refreshProfiles();
  }

  async function poll(jobId: string, key: string): Promise<string | null> {
    for (let i = 0; i < 60; i++) {
      await new Promise(r => setTimeout(r, 3000));
      const r = await fetch(`${API_URL}/v1/job/${jobId}`, { headers: { "X-API-Key": key } });
      if (!r.ok) return null;
      const d = await r.json();
      if (d.status === "complete") return d.style_id;
      if (d.status === "failed") return null;
    }
    return null;
  }

  function saveKey(k: string) {
    localStorage.setItem("phras_api_key", k);
    setApiKey(k);
  }

  return (
    <main className="space-y-10">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      <section className="border border-neutral-800 rounded-lg p-6 space-y-3">
        <h2 className="font-semibold">API key</h2>
        <input
          className="w-full bg-neutral-900 border border-neutral-800 rounded px-3 py-2 font-mono text-sm"
          placeholder="phr_..."
          value={apiKey}
          onChange={e => saveKey(e.target.value)}
        />
        <p className="text-xs text-neutral-500">Stored in your browser only.</p>
      </section>

      <section className="border border-neutral-800 rounded-lg p-6 space-y-4">
        <h2 className="font-semibold">Upload</h2>
        <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} className="block" />
        <div className="flex gap-3">
          <select value={source} onChange={e => setSource(e.target.value)}
                  className="bg-neutral-900 border border-neutral-800 rounded px-3 py-2">
            {SOURCES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <input className="bg-neutral-900 border border-neutral-800 rounded px-3 py-2 flex-1"
                 placeholder="target sender (optional, for whatsapp/telegram)"
                 value={sender} onChange={e => setSender(e.target.value)} />
        </div>
        <button onClick={upload} className="bg-white text-black px-4 py-2 rounded font-medium">
          Analyze
        </button>
        {status && <p className="text-sm text-neutral-400">{status}</p>}
      </section>

      <section>
        <h2 className="font-semibold mb-4">Your style profiles</h2>
        {profiles.length === 0 ? (
          <p className="text-neutral-500 text-sm">No profiles yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profiles.map(p => (
              <div key={p.id} className="border border-neutral-800 rounded-lg p-4 space-y-1">
                <div className="font-medium">{p.label || "Default"}</div>
                <div className="text-xs text-neutral-500">{p.corpus_word_count} words · {(p.source_types || []).join(", ")}</div>
                <code className="text-xs text-neutral-400 break-all block">{p.id}</code>
                <button onClick={() => navigator.clipboard.writeText(p.id)}
                        className="text-xs underline">Copy Style ID</button>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
