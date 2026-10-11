"""Phase 5 unit tests — Research Terminal, Session, Web Dashboard."""
import os, subprocess, sys

PYTHON = "/Users/fred/miniconda3/bin/python"
ROOT = "/Users/fred/Documents/GitHub/cycleuser/JiuZhang"
ENV = {**os.environ, "PYTHONPATH": ROOT}


def T(name, script):
    global ok, total
    total += 1
    r = subprocess.run([PYTHON, "-c", script], capture_output=True, text=True, timeout=60, cwd=ROOT, env=ENV)
    if r.returncode == 0:
        print(f"OK {name}")
        ok += 1
    else:
        print(f"FAIL {name}")
        for line in (r.stdout + r.stderr).strip().split("\n")[-4:]:
            print(f"   {line}")


ok = 0
total = 0

# ── 1. LiveResearchDisplay ───────────────────────────────────────────
T("LiveResearchDisplay construction + rendering", """
from jiuzhang.research_terminal import LiveResearchDisplay

display = LiveResearchDisplay()
display.set_question("Prove Goldbach conjecture")
display.add_activity("Starting research")
display.set_state("PLANNING")
display.set_proof("Assume every even number > 2...")
display.increment_experiment()
display.set_metrics({"tokens": 1500, "provider": "ollama", "best_score": 0.72})

output = display.render()
assert "JiuZhang Research" in output
assert "PLANNING" in output
assert "Goldbach" in output
assert "Experiment" in output

display.increment_experiment()
display.increment_experiment()
display.add_activity("Hypothesis formulated")
display.add_activity("Proof attempt started")

output2 = display.render()
assert len(output2) > 50

display.stop()
print("PASS")
""")

# ── 2. ResearchCommands ──────────────────────────────────────────────
T("ResearchCommands listing", """
from jiuzhang.research_terminal import ResearchCommands

cmds = ResearchCommands.COMMANDS
assert "p" in cmds
assert "r" in cmds
assert "s" in cmds
assert "i" in cmds
assert "q" in cmds
assert "?" in cmds

assert cmds["p"][0] == "pause"
assert cmds["q"][0] == "quit"
assert cmds["?"][0] == "help"

# show_help should not crash
ResearchCommands.show_help(console=None)
print("PASS")
""")

# ── 3. ResearchSession ───────────────────────────────────────────────
T("ResearchSession recording + export", """
import tempfile, os
from jiuzhang.research_terminal import ResearchSession

tmpdir = tempfile.mkdtemp()
session = ResearchSession(output_dir=tmpdir)

# Record events
session.record_event("start", {"question": "Test"})
session.record_event("phase", {"phase": "planning"})
session.record_event("proof", {"proof": "By induction..."})

# Record results
session.record_result({"status": "keep", "conjecture_strength": 0.8, "proof_confidence": 0.9, "description": "Test"})
session.record_result({"status": "discard", "conjecture_strength": 0.1, "proof_confidence": 0.2})

# Export JSON
json_path = session.export_session("json")
assert json_path.exists()
import json
data = json.loads(json_path.read_text())
assert data["summary"]["total_experiments"] == 2
assert data["summary"]["kept"] == 1

# Export Markdown
md_path = session.export_session("markdown")
assert md_path.exists()
md_content = md_path.read_text()
assert "Research Session" in md_content
assert "Experiment 1" in md_content

# Summary
summary = session.get_summary()
assert summary["total_experiments"] == 2
assert summary["kept"] == 1
assert summary["discarded"] == 1
assert summary["crashed"] == 0

print("PASS")
""")

# ── 4. WebDashboard app construction ─────────────────────────────────
T("WebDashboard FastAPI app", """
from jiuzhang.web_dashboard import app

# App should exist with routes
routes = [r.path for r in app.routes]
assert "/" in routes, f"Routes: {routes}"
assert "/api/activity" in routes
assert "/api/experiments" in routes
assert "/api/metrics" in routes
assert "/api/start" in routes
assert "/api/pause" in routes
assert "/api/resume" in routes
assert "/api/stop" in routes
assert "/api/inject" in routes
assert "/api/export/{format}" in routes
assert "/ws" in routes

# App metadata
assert app.title == "JiuZhang Research Dashboard"
assert "3.0.0" in app.version

print("PASS")
""")

# ── 5. WebDashboard API calls ────────────────────────────────────────
T("WebDashboard API endpoints respond", """
from jiuzhang.web_dashboard import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Dashboard page
resp = client.get("/")
assert resp.status_code == 200
assert "JiuZhang" in resp.text

# Activity API
resp2 = client.get("/api/activity")
assert resp2.status_code == 200

# Experiments API
resp3 = client.get("/api/experiments")
assert resp3.status_code == 200

# Metrics API
resp4 = client.get("/api/metrics")
assert resp4.status_code == 200

# Start
resp5 = client.post("/api/start")
assert resp5.status_code == 200
assert resp5.json()["status"] == "started"

# Pause
resp6 = client.post("/api/pause")
assert resp6.status_code == 200

# Resume
resp7 = client.post("/api/resume")
assert resp7.status_code == 200

# Inject
resp8 = client.post("/api/inject", json={"content": "Try a different approach"})
assert resp8.status_code == 200
assert resp8.json()["status"] == "injected"

# Stop
resp9 = client.post("/api/stop")
assert resp9.status_code == 200

print("PASS")
""")

# ── Summary ──────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"Phase 5: {ok}/{total} passed")
if ok == total:
    print("ALL PHASE 5 TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({total - ok} failures)")
    sys.exit(1)
