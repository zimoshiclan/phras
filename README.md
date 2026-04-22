# Phras

**Style-as-a-Service.** Upload your writing — WhatsApp exports, emails, tweets, essays — and get back a persistent Style ID that captures how *you* write. Inject that ID into any AI tool and the output sounds like you, not like a generic assistant.

Built by **Zoraiz Al Raz**.

---

## Why I built this

Every AI assistant sounds the same. The words are technically correct but the voice is flat — corporate, hedging, lifeless. The problem isn't the model, it's the missing context: the model doesn't know *you*.

Phras solves this by running a deterministic statistical analysis on your own text — measuring sentence rhythm, vocabulary fingerprint, punctuation habits, emoji usage, formality score — and condensing it into a reusable system prompt. No generative AI in the extraction step. No raw text stored after analysis. Just math on your words, turned into a constraint object any LLM can follow.

I built Phras because I was tired of editing every AI-generated draft back into my own voice. Now the voice comes first.

---

## How it works

```
Your text  →  normalize  →  extract features  →  Style UUID
                                                      ↓
                                          GET /v1/style/{id}?formality=semi_formal
                                                      ↓
                                             system_prompt  →  any LLM
```

1. **Upload** — drop in a `.txt` export (WhatsApp, Telegram JSON, email, Twitter archive, LinkedIn CSV, essay, or plain text)
2. **Analyze** — a pure-Python pipeline (NLTK + regex, ~50 MB install) extracts 40+ stylometric features: Yule's K, Heylighen F-score, function-word z-scores, emoji position distribution, contraction rate, and more
3. **Fetch** — call the REST API with your Style ID and a formality level (`no_censor` / `casual` / `family` / `semi_formal` / `formal`). Get back a `system_prompt` you paste straight into any AI
4. **Speak** — the AI output matches your register, your vocabulary, your rhythm

Privacy: raw files are deleted immediately after analysis. Only the statistical vector is stored — never the original text.

---

## Quick start

### Register and get your API key

```bash
curl -X POST https://your-backend.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
# → {"user_id":"...","api_key":"phr_..."}   ← save this key, shown once
```

### Upload a text file

```bash
curl -X POST https://your-backend.onrender.com/v1/upload \
  -H "X-API-Key: phr_..." \
  -F "file=@whatsapp_export.txt" \
  -F "source=whatsapp" \
  -F "target_sender=Zoraiz"
# → {"job_id":"...","status":"processing"}
```

### Poll until done

```bash
curl https://your-backend.onrender.com/v1/job/{job_id} \
  -H "X-API-Key: phr_..."
# → {"status":"complete","style_id":"..."}
```

### Get your style prompt

```bash
curl "https://your-backend.onrender.com/v1/style/{style_id}?formality=semi_formal&context=email" \
  -H "X-API-Key: phr_..."
# → {"constraint":{"system_prompt":"Write in direct sentences averaging 12–15 words..."}}
```

### Use it in Python with the Anthropic API

```python
import requests, anthropic

style = requests.get(
    "https://your-backend.onrender.com/v1/style/{STYLE_ID}",
    params={"formality": "semi_formal", "context": "email"},
    headers={"X-API-Key": "phr_..."},
).json()

client = anthropic.Anthropic()
msg = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    system=style["constraint"]["system_prompt"],
    messages=[{"role": "user", "content": "Write an email asking for Friday off."}],
)
print(msg.content[0].text)
```

---

## Formality levels

| Level | What it does |
|-------|-------------|
| `no_censor` | Full voice — slang and profanity preserved exactly as you use them |
| `casual` | Natural contractions, emoji at your natural rate |
| `family` | Warm, inclusive, profanity removed |
| `semi_formal` | 12–15 word sentences, reduced contractions, max 1 emoji |
| `formal` | No contractions, no emoji, 15–20 word sentences, impersonal constructions |

Context modifiers: `email`, `reply`, `tweet`, `linkedin`, `general` — appended to the prompt to shape format and sign-off.

---

## Supported text sources

| Source | Format |
|--------|--------|
| `whatsapp` | `.txt` export from WhatsApp (both bracket and dash timestamp formats) |
| `telegram` | `.json` from Telegram's "Export chat history" |
| `email` | Raw `.eml` or pasted email body |
| `twitter` | Twitter data archive (`tweet.js`) |
| `linkedin` | LinkedIn data export CSV (posts or messages) |
| `essay` | Any long-form document |
| `plain` | Free-form text |

---

## Self-hosting

### Requirements

- Python 3.10+
- Node.js 18+
- A free [Supabase](https://supabase.com) project
- (Optional) [Render](https://render.com) for backend, [Vercel](https://vercel.com) for frontend

### 1. Clone and install

```bash
git clone https://github.com/zimoshiclan/phras.git
cd phras

# Windows
setup.bat

# macOS / Linux
chmod +x setup.sh && ./setup.sh
```

### 2. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. SQL Editor → paste `backend/sql/001_init.sql` → Run
3. Storage → New bucket → name `raw-uploads`, set **private**
4. Project Settings → API → copy:
   - **URL** → `SUPABASE_URL` (backend) and `NEXT_PUBLIC_SUPABASE_URL` (frontend)
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` (backend only)
   - **anon** key → `NEXT_PUBLIC_SUPABASE_ANON_KEY` (frontend)
5. Authentication → Providers → Email → disable **Confirm email** (for local dev)

### 3. Configure environment

```bash
# backend/.env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
API_KEY_SALT=any-random-string

# frontend/.env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run locally

```bash
# Terminal 1
cd backend && uvicorn main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Backend: `http://localhost:8000` · Frontend: `http://localhost:3000`

### 5. Deploy

**Backend → Render** (repo has a `render.yaml` — Render reads it automatically):
- Connect your GitHub repo
- Add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the Render dashboard
- First cold start takes ~60s (NLTK tagger downloads once)

**Frontend → Vercel**:
- Import repo, set root directory to `frontend`
- Add `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create account + issue one-time API key |
| `POST` | `/auth/login` | Email/password → JWT |
| `POST` | `/v1/upload` | `file` + `source` → `job_id` |
| `GET` | `/v1/job/{id}` | Poll job status → `style_id` when complete |
| `GET` | `/v1/style/{id}` | `?formality` + `?context` → constraint + system_prompt |
| `GET` | `/v1/style/{id}/profile` | Full style vector for dashboard display |
| `POST` | `/v1/style/{id}/refresh` | Merge new text into existing profile (60/40 blend) |
| `DELETE` | `/v1/style/{id}` | Delete a style profile |
| `GET` | `/v1/account/export` | All profiles as JSON (GDPR export) |

---

## Tech stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI · Python 3.11 · NLTK · vaderSentiment · emoji |
| Database | Supabase (Postgres + Auth + Storage) |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS |
| Deploy | Render (backend) · Vercel (frontend) |

No LLMs or large model files in the extraction pipeline. The heaviest dependency is the NLTK averaged perceptron tagger at ~6 MB.

---

## Project structure

```
phras/
├── backend/
│   ├── main.py               FastAPI app, CORS, health check
│   ├── requirements.txt
│   ├── engine/
│   │   ├── normalizers.py    Per-source text cleaning (WhatsApp, email, etc.)
│   │   ├── extractor.py      40+ stylometric features
│   │   └── formality.py      5-level constraint generator + system_prompt builder
│   ├── routes/
│   │   ├── auth.py           Register / login
│   │   ├── upload.py         File upload + background analysis job
│   │   ├── jobs.py           Job status polling
│   │   ├── style.py          Style retrieval, refresh, delete, export
│   │   └── security.py       API key hashing + verification middleware
│   ├── db/
│   │   └── supabase_client.py
│   ├── sql/
│   │   └── 001_init.sql      Schema: api_keys, style_profiles, upload_jobs
│   └── tests/
└── frontend/
    ├── app/
    │   ├── page.tsx          Landing
    │   ├── dashboard/        Upload panel + profile cards
    │   ├── playground/       Style selector + system prompt preview
    │   └── docs/             API reference
    └── lib/
        └── supabase.ts
```

---

## License

MIT — do whatever you want with it.
