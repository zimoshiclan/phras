@echo off
REM Phras — one-command local setup (Windows)

echo === Installing backend dependencies ===
cd backend
python -m pip install -r requirements.txt -q

echo === Downloading NLTK tagger (6 MB, one-time) ===
python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng', quiet=True); print('NLTK tagger ready')"

IF NOT EXIST .env (
  copy .env.example .env
  echo Created backend\.env -- fill in your SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, API_KEY_SALT
)

echo === Installing frontend dependencies ===
cd ..\frontend
IF NOT EXIST .env.local (
  copy .env.local.example .env.local
  echo Created frontend\.env.local -- fill in your NEXT_PUBLIC_* values
)
npm install

echo.
echo Setup complete.
echo.
echo Next:
echo   1. Fill in backend\.env with your Supabase credentials
echo   2. Fill in frontend\.env.local with your Supabase + API URL
echo   3. cd backend ^&^& uvicorn main:app --reload
echo   4. cd frontend ^&^& npm run dev
