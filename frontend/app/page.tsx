import Link from "next/link";

export default function Landing() {
  return (
    <main className="py-16 space-y-16">
      <section className="space-y-6">
        <h1 className="text-5xl font-bold tracking-tight">
          Phras <span className="text-neutral-500">— your linguistic fingerprint.</span>
        </h1>
        <p className="text-xl text-neutral-400 max-w-2xl">
          Upload your writing. Get a Style ID. Inject it into any AI tool and watch the output sound like
          <em> you</em>, not like a generic assistant.
        </p>
        <div className="flex gap-4">
          <Link href="/dashboard" className="bg-white text-black px-6 py-3 rounded-lg font-medium">
            Get started
          </Link>
          <Link href="/docs" className="border border-neutral-700 px-6 py-3 rounded-lg">
            Read the docs
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          ["1. Upload", "Drop in a WhatsApp export, emails, tweets, or an essay."],
          ["2. Get your Style ID", "We extract a statistical fingerprint — no LLMs, no raw text stored."],
          ["3. Use it anywhere", "Fetch a system prompt at any formality level and paste into Claude or GPT."],
        ].map(([t, d]) => (
          <div key={t} className="border border-neutral-800 rounded-lg p-6">
            <h3 className="font-semibold mb-2">{t}</h3>
            <p className="text-neutral-400 text-sm">{d}</p>
          </div>
        ))}
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-4">Example call</h2>
        <pre className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm overflow-x-auto">
{`curl "https://api.phras.app/v1/style/\${STYLE_ID}?formality=semi_formal&context=email" \\
  -H "X-API-Key: phr_..."`}
        </pre>
      </section>
    </main>
  );
}
