"""Test scoring pipeline with real API. Run from backend directory."""
import json
import time
import requests
import sys
import os

os.chdir("/home/dangnha/CURWIELTS/backend")
os.system("pkill -f 'uvicorn app.main' 2>/dev/null; sleep 1")

# Start server
import subprocess
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(3)

# Read API key from .env
key = ""
with open("../.env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            key = line.strip().split("=", 1)[1]
            break

print(f"API key found: {bool(key)} (len={len(key)})")

# Login
r = requests.post("http://localhost:8000/api/v1/auth/login",
    json={"username": "tester", "password": "tester123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Save settings
requests.put("http://localhost:8000/api/v1/admin/settings", headers=headers, json={
    "provider": "gemini", "api_key": key, "model": "gemini-2.0-flash",
    "temperature": 0.3, "max_tokens": 4096,
})

# Submit essay
essay_text = """Some people think that governments should spend more money on railways rather than roads. To what extent do you agree or disagree?

In my opinion, while both railways and roads are essential for transportation infrastructure, I strongly agree that governments should prioritize spending on railways. There are several compelling reasons for this position.

Firstly, railways are far more environmentally friendly than roads. Trains produce significantly lower carbon emissions per passenger compared to cars and buses. For example, a study by the European Environment Agency found that rail travel produces up to 80 percent less CO2 than car travel for the same distance. By investing in railways, governments can contribute to reducing air pollution and combating climate change.

Secondly, railways are more efficient for mass transit. A single train can transport hundreds of passengers at once, reducing traffic congestion on roads. In cities like Tokyo and London, well-developed railway systems allow millions of commuters to travel daily without the gridlock that plagues car-dependent cities. Moreover, high-speed rail networks can connect cities more effectively, promoting economic growth and regional development.

However, roads remain necessary for last-mile connectivity and rural areas where railway construction is not feasible. Investment in roads should not be completely eliminated, but the bulk of transportation funding should shift toward modernizing and expanding rail infrastructure.

In conclusion, governments should allocate more funds to railways because of their environmental benefits and superior efficiency for mass transportation, while maintaining adequate road networks for local connectivity."""

r = requests.post("http://localhost:8000/api/v1/essays", headers=headers, json={
    "task_type": "task2", "essay_text": essay_text,
    "prompt_text": "Some people think governments should spend more money on railways rather than roads. To what extent do you agree or disagree?"
})
essay_id = r.json()["id"]
print(f"Essay: {essay_id[:8]}... words={r.json()['word_count']}")

# Trigger
r = requests.post(f"http://localhost:8000/api/v1/essays/{essay_id}/score", headers=headers)
print(f"Scoring: {r.json()['status']}")

# Poll
for i in range(80):
    r = requests.get(f"http://localhost:8000/api/v1/essays/{essay_id}/score", headers=headers)
    d = r.json()
    status = d.get("status", "?")
    band = d.get("overall_band", "?")
    n_crit = len(d.get("criteria", []))
    print(f"  [{i+1:2d}] status={status} band={band} criteria={n_crit}")
    if status in ("completed", "failed"):
        print()
        print("="*60)
        print("FULL RESULT")
        print("="*60)
        print(f"Overall Band: {band}")
        print(f"Status: {status}")
        for c in d.get("criteria", []):
            fb = str(c.get("detailed_feedback", ""))[:200]
            strengths = c.get("strengths", [])
            weaknesses = c.get("weaknesses", [])
            print(f"\n  [{c['criterion']}] Score: {c['score']}")
            if fb:
                print(f"    Feedback: {fb}")
            if strengths:
                print(f"    Strengths: {json.dumps(strengths[:3])}")
            if weaknesses:
                print(f"    Weaknesses: {json.dumps(weaknesses[:3])}")

        # Errors
        r3 = requests.get(f"http://localhost:8000/api/v1/essays/{essay_id}/errors", headers=headers)
        errors = r3.json()
        print(f"\n  ERRORS: {len(errors)} found")
        for err in errors[:5]:
            print(f"    {err['error_type']}({err['severity']}): \"{err['error_text']}\" -> \"{err.get('correction','')}\"")

        # Vocabulary
        r4 = requests.get("http://localhost:8000/api/v1/vocabulary?page_size=10", headers=headers)
        vd = r4.json()
        print(f"\n  VOCABULARY: {vd['total']} words extracted")
        for v in vd.get("items", [])[:10]:
            ipa_str = v.get("ipa", "")
            print(f"    {v['word']} ({v.get('pos','?')}) [{v.get('cefr_level','?')}] /{ipa_str}/")

        # Feedback
        r5 = requests.get(f"http://localhost:8000/api/v1/essays/{essay_id}/feedback", headers=headers)
        fb_data = r5.json()
        print(f"\n  FEEDBACK: {fb_data.get('overall_assessment','')[:200]}")
        print(f"    Priority: {fb_data.get('priority_weakness','')}")
        exercises = fb_data.get("recommended_exercises", [])
        for ex in exercises[:3]:
            print(f"    Exercise: {ex[:80]}")

        # Band upgrade
        r6 = requests.get(f"http://localhost:8000/api/v1/essays/{essay_id}/band-upgrade", headers=headers)
        bu = r6.json()
        print(f"\n  BAND UPGRADE from {bu.get('current_band','?')}:")
        for step in bu.get("steps", [])[:3]:
            print(f"    To {step.get('target_band','?')}: {len(step.get('required_improvements',[]))} improvements")
        break
    time.sleep(2)

proc.terminate()
proc.wait()

# Print server logs
print("\n" + "="*60)
print("SERVER LOGS (last 80 lines)")
print("="*60)
output = proc.stdout.read() if proc.stdout else ""
lines = output.split("\n")
for line in lines[-80:]:
    if "Error" in line or "error" in line or "FAILED" in line or "agent" in line.lower() or "band" in line.lower() or "score" in line.lower() or "token" in line.lower() or "parse" in line.lower() or "Traceback" in line:
        print(line)
