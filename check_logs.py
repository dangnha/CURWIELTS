"""Test: start server, hit endpoints, show logs."""
import subprocess, sys, time, requests, os

os.chdir("/home/dangnha/CURWIELTS/backend")

# Kill old
subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
time.sleep(1)

# Start server
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(4)

# Hit endpoints
try:
    requests.get("http://localhost:8000/api/v1/admin/kb/status", timeout=3)
    requests.post("http://localhost:8000/api/v1/auth/login",
                  json={"username": "tester", "password": "tester123"}, timeout=3)
    requests.get("http://localhost:8000/api/v1/essays?page_size=1",
                 headers={"Authorization": "Bearer fake"}, timeout=3)
except Exception as e:
    print(f"Request error: {e}")

# Read log file
time.sleep(0.5)
log_file = "/home/dangnha/CURWIELTS/data/logs/server.log"
if os.path.exists(log_file):
    print("=" * 60)
    print("SERVER.LOG CONTENTS:")
    print("=" * 60)
    with open(log_file) as f:
        print(f.read())
else:
    print("No log file at", log_file)

proc.terminate()
