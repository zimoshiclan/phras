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
          <li>Inject the returned <code className="bg-neutral-800 px-1 rounded">system_prompt</code> into any AI</li>
        </ol>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Claude Code skill</h2>
        <p className="text-neutral-400 text-sm">
          Use <code className="bg-neutral-800 px-1 rounded">/phras</code> directly inside Claude Code to fetch and apply your style without leaving your editor.
        </p>

        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-neutral-300 mb-1">Install globally (works in any project)</p>
            <pre className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm overflow-x-auto text-neutral-200">
{`# Mac / Linux
cp .claude/commands/phras.md ~/.claude/commands/phras.md

# Windows PowerShell
Copy-Item .claude\\commands\\phras.md "$env:USERPROFILE\\.claude\\commands\\phras.md"`}
            </pre>
          </div>

          <div>
            <p className="text-sm font-medium text-neutral-300 mb-1">One-time setup — store your credentials</p>
            <pre className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm overflow-x-auto text-neutral-200">
{`claude config set env.PHRAS_API_KEY phr_your_key_here
claude config set env.PHRAS_STYLE_ID your_style_id_here`}
            </pre>
          </div>

          <div>
            <p className="text-sm font-medium text-neutral-300 mb-1">Usage</p>
            <pre className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm overflow-x-auto text-neutral-200">
{`/phras                      # semi_formal, general context
/phras casual               # casual voice
/phras formal email         # formal + email format
/phras no_censor            # full unfiltered voice
/phras semi_formal linkedin # semi-formal for LinkedIn`}
            </pre>
            <p className="text-xs text-neutral-500 mt-2">Claude fetches your style constraint and writes in your voice for the rest of that conversation.</p>
          </div>
        </div>
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
    ["POST", "/auth/login", "Email/password → JWT"],
    ["POST", "/v1/upload", "file + source → job_id"],
    ["GET", "/v1/job/{id}", "Poll job → style_id when complete"],
    ["GET", "/v1/style/{id}", "?formality & ?context → constraint + system_prompt"],
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
