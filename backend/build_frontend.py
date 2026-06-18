"""Build the React frontend + bundle into a Windows EXE.

Usage:
    python build_frontend.py              # build React + copy to app/static/
    python build_frontend.py --exe        # build React + create PyInstaller EXE
    python build_frontend.py --skip-build # copy only (already built)
"""

import subprocess
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
STATIC_DIR = Path(__file__).resolve().parent / "app" / "static"
BACKEND = Path(__file__).resolve().parent

skip_build = "--skip-build" in sys.argv
do_exe = "--exe" in sys.argv


def main():
    if not skip_build:
        print("🔨 Building React frontend ...")
        subprocess.run(["npm", "run", "build"], cwd=FRONTEND, check=True)
        print("✅ React built to frontend/dist/")

    print(f"📦 Copying {FRONTEND / 'dist'} → {STATIC_DIR}")
    if STATIC_DIR.exists():
        shutil.rmtree(STATIC_DIR)
    shutil.copytree(FRONTEND / "dist", STATIC_DIR)
    print(f"✅ Copied to {STATIC_DIR}")

    if do_exe:
        print("\n🔨 Building EXE with PyInstaller ...")
        dist_dir = BACKEND / "dist" / "IELTS-Scorer"
        build_dir = BACKEND / "build"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        if build_dir.exists():
            shutil.rmtree(build_dir)

        args = [
            "python", "-m", "PyInstaller", "--onedir", "--name", "IELTS-Scorer",
            "--add-data", f"app/static{';' if sys.platform == 'win32' else ':'}app/static",
            "--add-data", f"../information-prompts{';' if sys.platform == 'win32' else ':'}information-prompts",
            "--collect-all", "chromadb",
            "--collect-all", "passlib",
            "--collect-all", "onnxruntime",
            "--collect-all", "sentence_transformers",
            "--collect-all", "tokenizers",
            "--hidden-import", "passlib",
            "--hidden-import", "passlib.handlers.bcrypt",
            "--hidden-import", "passlib.hash.bcrypt",
            "--hidden-import", "bcrypt",
            "--hidden-import", "google.generativeai",
            "--hidden-import", "openai",
            "--hidden-import", "pydantic_settings",
            "--hidden-import", "sse_starlette",
            "run_exe.py",
        ]
        subprocess.run(args, cwd=BACKEND, check=True)
        print(f"✅ EXE built at {dist_dir}/IELTS-Scorer")
        print(f"   Size: {sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file()) / (1024*1024):.0f} MB")

    print("\n🎉 Done! To run:")
    print("   cd backend/dist/IELTS-Scorer && ./IELTS-Scorer")
    print("   (copy .env with API keys next to the EXE first)")


if __name__ == "__main__":
    main()
