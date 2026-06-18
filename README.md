# IELTS Writing Multi-Agent Scoring System

An AI-powered IELTS Writing evaluation application using a multi-agent architecture with LLM APIs (Gemini, ChatGPT, DeepSeek, Grok). Scores essays across all 4 IELTS criteria, provides deep analysis, personalized feedback, vocabulary learning, and progress tracking.

## Features

- **7 AI Calls per Essay** — Specialized agents evaluate Task Response (incl. structure/type detection), Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy, plus vocabulary extraction, error analysis, and combined feedback/band-upgrade — optimized to use as few LLM calls as possible (overall band is computed deterministically, not via an extra LLM call)
- **Task 1 + Image Upload** — Drag-and-drop chart/graph image upload for Academic Task 1
- **Pre-Writing Assistant** — On-demand analysis of IELTS prompts (identifies essay/chart type, suggests structure, key trends, brainstorming ideas)
- **Multi-Criteria Scoring** — Detailed band scores with strengths, weaknesses, and missing requirements per criterion
- **Band Upgrade Suggestions** — Actionable steps to reach Band 7, 8, 9
- **Vocabulary Bank** — Automatic extraction with IPA pronunciation, definitions, example sentences, synonyms, collocations; export to JSON/CSV/Excel
- **Error Detection** — Grammar, spelling, punctuation, word choice, and coherence errors with corrections
- **Personalized Learning** — "Learn" button analyzes last 10 essays, identifies recurring mistakes and hidden patterns, generates improvement plan
- **Progress Tracking** — Band score history table with criterion breakdown, trend analysis, strongest/weakest areas
- **Real-time Scoring Progress** — Step-by-step agent status visualization during scoring
- **Multiple LLM Providers** — Gemini, ChatGPT, DeepSeek, Grok — configurable in Settings via the UI
- **Local Storage** — All data stored as JSON files in the `data/` directory
- **Dark/Light Mode** — Toggle theme with browser persistence
- **Writing Timer** — Full test mode (20/40 min) and custom timer with auto-save

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- At least one LLM API key (Gemini recommended)

## Quick Start

```bash
# 1. Navigate to project
cd CURWIELTS

# 2. Create data directories
mkdir -p data data/uploads knowledge-base/chroma

# 3. Install backend dependencies
cd backend
pip install -r requirements.txt

# 4. (Optional) Ingest the knowledge base
python -c "from app.knowledge_base.ingest import ingest_knowledge_base; print(ingest_knowledge_base())"

# 5. Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. In a new terminal, install and start the frontend
cd frontend
npm install
npm run dev

# 7. Open http://localhost:5173
#    Register an account
#    Go to Settings → Configure your LLM provider & API key
#    Go to Dashboard → New Essay → Write & Submit → Watch scoring
```

## Configuration

API keys are configured in the **Settings page** within the app (not in .env files). This means:

1. Register an account
2. Go to **Settings**
3. Select your provider (Gemini, ChatGPT, DeepSeek, or Grok)
4. Paste your API key
5. Select model and temperature
6. Click **Save Configuration**

All agents will use this provider/model. Your API key is stored locally in `data/users/<id>.json`.

## How It Works

### Scoring Pipeline
```
Phase 1 (Parallel):   Coherence & Cohesion → Lexical Resource → Grammatical Range
Phase 1b:             Task Response (also detects essay type/structure in the same call)
Phase 2 (Parallel):   Vocabulary Extraction → Error Analysis
Phase 3:              Overall band computed deterministically (IELTS rounding, no LLM call)
                      → Personalized Feedback + Band Upgrade Suggestions (single combined call)
```

### Agent Roles

| Agent | Role | Output |
|---|---|---|
| Task Response | Evaluate argument quality, position clarity, essay type, structure | TR band, type, structure issues |
| Coherence & Cohesion | Flow, paragraphing, cohesive devices | CC band, organization analysis |
| Lexical Resource | Vocabulary range, collocation, style | LR band, vocabulary issues |
| Grammatical Range | Sentence variety, accuracy, punctuation | GRA band, grammar errors |
| Vocabulary Extraction | Extract IPA, definitions, synonyms | Vocabulary bank with CEFR levels |
| Error Analysis | Identify specific errors with corrections | Error list with corrections |
| Feedback & Band Upgrade | Personalized improvement plan + steps to reach higher bands | Priority weaknesses, exercises, upgrade path |

### Pre-Writing Assistant (on-demand)
Click the **Pre-Writing** button next to the prompt input. The assistant will:
- Task 1: Identify chart type, key trends, suggested overview, paragraph structure
- Task 2: Identify essay type, question analysis, brainstorming ideas, suggested structure

### Learn Button (Personalized Learning)
Click **Learn** on the Dashboard or Essay Detail page. The agent:
1. Analyzes last 10 completed essays
2. Identifies recurring mistakes across essays
3. Discovers hidden patterns (e.g., strong grammar but weak ideas)
4. Lists priority weaknesses with severity
5. Suggests Weekly goals and exercises
6. Recommends essay types to practice

## Project Structure

```
CURWIELTS/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # Settings
│   │   ├── storage.py                 # JSON file-based storage
│   │   ├── api/                       # Route handlers
│   │   │   ├── auth.py                # Register, login, JWT
│   │   │   ├── essays.py              # CRUD + Task 1 image upload
│   │   │   ├── scoring.py             # Scoring trigger + results + SSE
│   │   │   ├── vocabulary.py          # Vocabulary bank + export
│   │   │   ├── errors.py              # Error analysis results
│   │   │   ├── feedback.py            # Personalized feedback
│   │   │   ├── learning.py            # Pre-writing + Learn button
│   │   │   └── admin.py               # Settings + KB management
│   │   ├── services/
│   │   │   └── scoring_service.py     # 7-call agent orchestration
│   │   ├── llm/                       # Provider abstraction (4 providers)
│   │   ├── knowledge_base/            # ChromaDB vector search
│   │   └── utils/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # Stats + Learn + history
│   │   │   ├── NewEssay.tsx           # Editor + timer + image + pre-writing
│   │   │   ├── EssayDetail.tsx        # Results + progress + feedback
│   │   │   ├── VocabularyPage.tsx      # Word bank + IPA + export
│   │   │   ├── ProgressPage.tsx        # Band history table
│   │   │   └── SettingsPage.tsx        # API key + provider config
│   │   └── components/layout/         # App shell with sidebar
│   └── package.json
├── data/                              # JSON storage (auto-created)
│   ├── users/
│   ├── essays/
│   ├── scoring_sessions/
│   ├── criteria_scores/
│   ├── vocabulary_items/
│   ├── error_records/
│   ├── agent_results/
│   ├── learning_plans/
│   └── uploads/                       # Task 1 images
├── information-prompts/               # Vietnamese IELTS knowledge base
└── README.md
```

## API Endpoints

```
POST /api/v1/auth/register          # Register account
POST /api/v1/auth/login             # Login → JWT token

POST /api/v1/essays                 # Submit Task 2 essay
POST /api/v1/essays/task1           # Submit Task 1 with image (multipart)
GET  /api/v1/essays                 # List user's essays
GET  /api/v1/essays/{id}            # Get essay detail
DELETE /api/v1/essays/{id}          # Delete essay

POST /api/v1/essays/{id}/score      # Trigger scoring (async)
GET  /api/v1/essays/{id}/score      # Get scoring results
GET  /api/v1/essays/{id}/score/stream  # SSE: real-time agent progress
GET  /api/v1/essays/{id}/criteria   # 4 criteria breakdown
GET  /api/v1/essays/{id}/band-upgrade  # Band upgrade steps
GET  /api/v1/essays/{id}/errors     # Error analysis
GET  /api/v1/essays/{id}/feedback   # Personalized feedback

GET  /api/v1/vocabulary             # Vocabulary bank (paginated, filterable)
GET  /api/v1/vocabulary/stats       # Vocabulary statistics
POST /api/v1/vocabulary/export      # Export (format=json|csv|excel)

POST /api/v1/learning/pre-write     # Pre-writing assistant
POST /api/v1/learning/analyze       # Learn button (10-essay analysis)
GET  /api/v1/learning/progress       # Band progression over time
GET  /api/v1/learning/plans          # Saved learning plans

GET  /api/v1/admin/settings         # Get LLM config
PUT  /api/v1/admin/settings         # Save LLM config
POST /api/v1/admin/kb/ingest        # Re-ingest knowledge base
GET  /api/v1/admin/kb/status        # KB status
```

## Troubleshooting

- **Scoring fails**: Ensure you've configured a valid API key in Settings
- **Pre-writing returns error**: Ensure `google-generativeai` is installed (`pip install google-generativeai`)
- **Knowledge base empty**: Run the KB ingest command
- **Dark mode not persisting**: Clear localStorage and toggle again
