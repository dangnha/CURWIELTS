# Plan: One-Click Desktop App (Windows)

## Goal
Bundle CURWIELTS into a single `.exe`. Double-click → browser opens → app works like a website. No terminal, no commands.

## Approach: PyInstaller + FastAPI serving React static files

Instead of running frontend + backend separately:
1. Build React into static files (`frontend/dist/`)
2. Make FastAPI serve those static files
3. Auto-open browser on startup
4. Bundle with PyInstaller into a single `.exe`

## Files to modify

| File | Change |
|------|--------|
| `backend/app/main.py` | Add static file serving, browser auto-open, `__main__` block |
| `frontend/vite.config.ts` | Set `base: '/'` (already correct) |

## Steps

### 1. FastAPI serves the React build (`backend/app/main.py`)
After all API routes, mount the frontend:
```python
# Serve React SPA (production) or fallback to Vite dev proxy
import os
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="frontend")
```
The `html=True` flag handles SPA routing — any path without a matching file returns `index.html`.

### 2. Auto-open browser on startup (`backend/app/main.py`)
```python
import webbrowser, threading
def _open_browser():
    import time; time.sleep(1.5)
    webbrowser.open("http://localhost:8000")
threading.Thread(target=_open_browser, daemon=True).start()
```
Add to lifespan startup.

### 3. Make main.py double-clickable (`backend/app/main.py`)
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
```

### 4. Build React into `backend/app/static/`
```bash
cd frontend && npm run build
cp -r dist ../backend/app/static
```

### 5. Build EXE with PyInstaller
```bash
pip install pyinstaller
cd backend
python -m PyInstaller --onefile --name "IELTS-Scorer" \
  --add-data "app/static;app/static" \
  --hidden-import chromadb \
  --hidden-import chromadb.config \
  --hidden-import chromadb.utils.embedding_functions \
  --hidden-import pydantic_settings \
  --collect-all chromadb \
  app/main.py
```

### 6. Create a launcher script for Windows
`backend/run.py` (same dir as .exe output):
```python
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from app.main import app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Output
- `dist/IELTS-Scorer.exe` — single file, double-click to run
- Put `.env` with API keys next to the EXE
- Browser auto-opens, full app works

## Verification
1. `cd frontend && npm run build && cp -r dist ../backend/app/static`
2. `cd backend && python -c "from app.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"`
3. Open `http://localhost:8000` — should show the app
4. Build EXE with PyInstaller
5. Double-click EXE — browser opens, app works
