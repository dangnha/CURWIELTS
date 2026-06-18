import sys
import os

# PyInstaller sets sys.frozen, sys._MEIPASS to the temp extract dir.
# Before any imports, inject the bundle into the search path so
# 'from app.config import settings' resolves correctly.
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
