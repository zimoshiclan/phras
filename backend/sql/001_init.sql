-- Phras schema v1
-- Apply via Supabase Dashboard > SQL Editor, or `supabase db push`.

-- API keys (hashed, never raw)
CREATE TABLE IF NOT EXISTS api_keys (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  key_hash    TEXT UNIQUE NOT NULL,
  label       TEXT,
  created_at  TIMESTAMPTZ DEFAULT now(),
  last_used   TIMESTAMPTZ
);

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage own keys" ON api_keys;
CREATE POLICY "Users manage own keys"
  ON api_keys FOR ALL USING (auth.uid() = user_id);

-- Style profiles (one per persona per user)
CREATE TABLE IF NOT EXISTS style_profiles (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  label              TEXT DEFAULT 'Default',
  style_vector       JSONB NOT NULL,
  cached_constraints JSONB DEFAULT '{}'::jsonb,
  corpus_word_count  INT,
  source_types       TEXT[],
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE style_profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage own profiles" ON style_profiles;
CREATE POLICY "Users manage own profiles"
  ON style_profiles FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS style_profiles_user_idx ON style_profiles(user_id);
CREATE INDEX IF NOT EXISTS style_profiles_vector_idx ON style_profiles USING gin(style_vector);
CREATE INDEX IF NOT EXISTS style_profiles_cached_idx ON style_profiles USING gin(cached_constraints);

-- Upload jobs
CREATE TABLE IF NOT EXISTS upload_jobs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  style_id      UUID REFERENCES style_profiles(id) ON DELETE SET NULL,
  status        TEXT DEFAULT 'pending',
  source        TEXT,
  storage_path  TEXT,
  error         TEXT,
  created_at    TIMESTAMPTZ DEFAULT now(),
  completed_at  TIMESTAMPTZ
);

ALTER TABLE upload_jobs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own jobs" ON upload_jobs;
CREATE POLICY "Users view own jobs"
  ON upload_jobs FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS upload_jobs_user_idx ON upload_jobs(user_id);
CREATE INDEX IF NOT EXISTS upload_jobs_status_idx ON upload_jobs(status);
