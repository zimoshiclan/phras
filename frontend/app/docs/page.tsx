export default function Docs() {
  return (
    <main className="space-y-10 max-w-3xl">
      <h1 className="text-3xl font-bold">API reference</h1>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Quick start</h2>
        <ol className="list-decimal ml-6 space-y-2 text-neutral-300">
          <li>POST <code className="bg-neutral-800 px-1 rounded">/auth/register</code> — returns your one-time API key</li>
          <li>POST <code className="bg-neutral-800 px-1 rounded">/v1/upload</code> with a text file + source</li>
          <li>GET <code className="bg-neutral-800 px-1 rounded">/v1/job/{'{'}id{'}'}</code> until <code className="bg-neutral-800 px-1 rounded">status = complete</code></li>
          <li>GET <code className="bg-neutral-800 px-1 rounded">/v1/style/{'{'}id{'}'}?formality=semi_formal&amp;context=email</code></li>
          <li>Inject the returned <code className="bg-neutral-800 px-1 rounded">system_prompt</code> into Claude</li>
        </ol>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Endpoints</h2>
        <EndpointTable />
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Python example</h2>
        <pre className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm overflow-x-auto text-neutral-200">
{`import requests, anthropic

style = requests.get(
    f"{API}/v1/style/{STYLE_ID}",
    params={"formality": "semi_formal", "context": "email"},
    headers={"X-API-Key": KEY},
).json()

client = anthropic.Anthropic()
msg = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    system=style["constraint"]["system_prompt"],
    messages=[{"role": "user", "content": "Write an email asking for Friday off."}],
)
print(msg.content[0].text)`}
        </pre>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">JavaScript example</h2>
        <pre className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm overflow-x-auto text-neutral-200">
{`const r = await fetch(\`\${API}/v1/style/\${styleId}?formality=casual\`, {
  headers: { "X-API-Key": key },
});
const { constraint } = await r.json();
// pass constraint.system_prompt as your AI system message`}
        </pre>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Formality levels</h2>
        <ul className="list-disc ml-6 space-y-1 text-neutral-300">
          <li><code className="bg-neutral-800 px-1 rounded">no_censor</code> — full voice, slang and profanity preserved</li>
          <li><code className="bg-neutral-800 px-1 rounded">casual</code> — friendly, natural contractions, emoji at user&apos;s rate</li>
          <li><code className="bg-neutral-800 px-1 rounded">family</code> — warm, inclusive, profanity removed</li>
          <li><code className="bg-neutral-800 px-1 rounded">semi_formal</code> — 12–15 word sentences, reduced contractions, max 1 emoji</li>
          <li><code className="bg-neutral-800 px-1 rounded">formal</code> — no contractions, no emoji, 15–20 word sentences</li>
        </ul>
      </section>
    </main>
  );
}

function EndpointTable() {
  const rows: [string, string, string][] = [
    ["POST", "/auth/register", "Create user + issue one-time API key"],
    ["POST", "/auth/login", "Email/password \u2192 JWT"],
    ["POST", "/v1/upload", "file + source \u2192 job_id"],
    ["GET", "/v1/job/{id}", "Poll job \u2192 style_id when complete"],
    ["GET", "/v1/style/{id}", "?formality & ?context \u2192 constraint + system_prompt"],
    ["GET", "/v1/style/{id}/profile", "Dashboard-friendly style vector"],
    ["POST", "/v1/style/{id}/refresh", "Merge new data into profile (60/40)"],
    ["DELETE", "/v1/style/{id}", "Delete profile"],
    ["GET", "/v1/account/export", "All your profiles as JSON (GDPR)"],
  ];
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border border-neutral-800 rounded">
        <thead className="bg-neutral-900">
          <tr>
            <th className="text-left p-3 text-neutral-300">Method</th>
            <th className="text-left p-3 text-neutral-300">Path</th>
            <th className="text-left p-3 text-neutral-300">Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([m, p, d]) => (
            <tr key={p} className="border-t border-neutral-800">
              <td className="p-3 font-mono text-green-400">{m}</td>
              <td className="p-3 font-mono text-neutral-200">{p}</td>
              <td className="p-3 text-neutral-400">{d}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
