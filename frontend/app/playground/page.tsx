"use client";
import { useEffect, useState } from "react";
import { API_URL } from "@/lib/supabase";

const LEVELS = ["no_censor", "casual", "family", "semi_formal", "formal"] as const;
const CONTEXTS = ["general", "email", "reply", "tweet", "linkedin"] as const;

export default function Playground() {
  const [apiKey, setApiKey] = useState("");
  const [styleId, setStyleId] = useState("");
  const [level, setLevel] = useState<typeof LEVELS[number]>("semi_formal");
  const [context, setContext] = useState<typeof CONTEXTS[number]>("general");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setApiKey(localStorage.getItem("phras_api_key") || "");
    setStyleId(localStorage.getItem("phras_last_style") || "");
  }, []);

  async function fetchStyle() {
    setError("");
    if (!apiKey || !styleId) { setError("need API key + style ID"); return; }
    localStorage.setItem("phras_last_style", styleId);
    const url = `${API_URL}/v1/style/${styleId}?formality=${level}&context=${context}`;
    const r = await fetch(url, { headers: { "X-API-Key": apiKey } });
    if (!r.ok) { setError(`${r.status}: ${await r.text()}`); return; }
    setResult(await r.json());
  }

  const prompt = result?.constraint?.system_prompt || "";

  return (
    <main className="space-y-8">
      <h1 className="text-3xl font-bold">Playground</h1>

      <div className="space-y-3">
        <input className="w-full bg-neutral-900 border border-neutral-800 rounded px-3 py-2 font-mono text-sm"
               placeholder="API key (phr_...)"
               value={apiKey} onChange={e => { setApiKey(e.target.value); localStorage.setItem("phras_api_key", e.target.value); }} />
        <input className="w-full bg-neutral-900 border border-neutral-800 rounded px-3 py-2 font-mono text-sm"
               placeholder="style ID"
               value={styleId} onChange={e => setStyleId(e.target.value)} />
      </div>

      <div className="flex flex-wrap gap-2">
        {LEVELS.map(l => (
          <button key={l} onClick={() => setLevel(l)}
                  className={`px-3 py-1.5 rounded border text-sm ${level === l ? "bg-white text-black border-white" : "border-neutral-700"}`}>
            {l}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {CONTEXTS.map(c => (
          <button key={c} onClick={() => setContext(c)}
                  className={`px-3 py-1.5 rounded border text-sm ${context === c ? "bg-white text-black border-white" : "border-neutral-700"}`}>
            {c}
          </button>
        ))}
      </div>

      <button onClick={fetchStyle} className="bg-white text-black px-4 py-2 rounded font-medium">
        Fetch constraint
      </button>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {prompt && (
        <section className="border border-neutral-800 rounded-lg p-6 space-y-3">
          <h2 className="font-semibold">System prompt</h2>
          <p className="text-neutral-200 whitespace-pre-wrap">{prompt}</p>
          <div className="flex gap-2">
            <button onClick={() => navigator.clipboard.writeText(prompt)}
                    className="text-sm border border-neutral-700 rounded px-3 py-1">Copy</button>
            <a href="https://claude.ai" target="_blank" rel="noreferrer"
               className="text-sm border border-neutral-700 rounded px-3 py-1">Open claude.ai</a>
          </div>
        </section>
      )}

      {result && (
        <pre className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-xs overflow-x-auto">
          {JSON.stringify(result.constraint, null, 2)}
        </pre>
      )}
    </main>
  );
}
