# CURWIELTS — Setup Guide

Two ways to run this project: **dev mode** (terminal) for coding, or **desktop EXE** (double-click) for daily use.

---

## Option A: Desktop App (Windows EXE) — easiest

Once built, you double-click a single file and a browser opens. No terminal, no commands.

### One-time build

```bash
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt
pip install pyinstaller

# 2. Build React frontend
cd ../frontend
npm install
npm run build

# 3. Copy frontend into backend
cd ../backend
python build_frontend.py --skip-build

# 4. Build the EXE
python build_frontend.py --exe
```

The EXE is at `backend/dist/IELTS-Scorer/IELTS-Scorer.exe`.

### Running

1. Copy the entire `dist/IELTS-Scorer/` folder anywhere you want (e.g. Desktop)
2. Rename `.env.example` to `.env` and fill in your API keys
3. Double-click `IELTS-Scorer.exe`
4. Browser opens at `http://localhost:8000`

The first run auto-ingests the knowledge base (~30s). After that, startup is instant.

### Updating the EXE

```bash
cd backend
python build_frontend.py --exe    # rebuilds React + EXE
```

---

## Option B: Dev Mode (terminal) — for coding

```bash
# 1. Clone
git clone <repo-url> CURWIELTS
cd CURWIELTS

# 2. Python env (3.11+)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. Node.js (18+)
cd frontend
npm install

# 4. .env config
cd ..
cp .env.example .env
# Edit .env — add at least one API key

# 5. Create data dirs
mkdir -p data data/uploads knowledge-base/chroma

# 6. Start backend (terminal 1)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Start frontend (terminal 2)
cd frontend
npm run dev

# 8. Open http://localhost:5173
```

### Optional: ingest knowledge base (dev mode)

```bash
cd backend
python -c "from app.knowledge_base.ingest import ingest_knowledge_base; print(ingest_knowledge_base())"
```

---

## API Keys

You need at least one LLM provider's API key. Put it in `.env`:

| Provider | Key in `.env` | Sign up |
|----------|--------------|---------|
| Gemini (recommended) | `GEMINI_API_KEY=...` | https://aistudio.google.com |
| ChatGPT | `CHATGPT_API_KEY=sk-...` | https://platform.openai.com |
| DeepSeek | `DEEPSEEK_API_KEY=...` | https://platform.deepseek.com |
| Grok | `GROK_API_KEY=...` | https://console.x.ai |
| Groq | `GROQ_API_KEY=...` | https://console.groq.com |

Set `DEFAULT_LLM_PROVIDER` to the one you want to use.

---

## Project Structure

```
CURWIELTS/
├── backend/
│   ├── app/main.py                 # FastAPI server
│   ├── app/services/               # Scoring pipeline
│   ├── app/api/                    # REST endpoints
│   ├── app/llm/                    # LLM providers (5)
│   ├── app/knowledge_base/          # ChromaDB vector store
│   ├── run_exe.py                  # PyInstaller entry point
│   ├── build_frontend.py           # Build script
│   └── requirements.txt
├── frontend/
│   └── src/pages/                  # React pages (6)
├── data/                           # Runtime storage (auto-created)
├── information-prompts/            # Vietnamese KB source
└── .env                            # API keys & config
```

---

## Scoring Pipeline

7 LLM calls across 3 phases:

| Phase | Agents | |
|-------|--------|---|
| 1 (sequential for Groq, parallel otherwise) | Coherence & Cohesion, Lexical Resource, Grammatical Range | 3 calls |
| 1b | Task Response & Structure | 1 call |
| 2 | Vocabulary Extraction, Error Analysis | 2 calls |
| 3 | Personalized Feedback + Band Upgrade | 1 call |

Overall band is calculated deterministically (IELTS rounding), no LLM needed.

---

## Ports

| Mode | Backend | Frontend |
|------|---------|----------|
| Dev | `:8000` | `:5173` (proxies API to :8000) |
| EXE | `:8000` | served by backend |

---

## Troubleshooting

- **EXE won't start**: Make sure `.env` has a valid API key. Check `data/logs/server.log`.
- **Scoring fails**: Your API key may be invalid or rate-limited. Check Settings page.
- **Port 8000 already in use**: Kill the existing process or change the port in `.env`.
- **KB ingest fails in EXE**: This is non-fatal — scoring works without it, just less informed.
