"""Master test runner — runs all V3 test phases."""
import os, subprocess, sys

PYTHON = "/Users/fred/miniconda3/bin/python"
ROOT = "/Users/fred/Documents/GitHub/cycleuser/JiuZhang"

print("=" * 70)
print("JiuZhang V3 — Complete Test Suite")
print("=" * 70)

tests = [
    ("Phase 1 — Core (ProviderFactory, Async, Config)", "test_v3_phase1.py"),
    ("Phase 2 — Agent (Quality, Context, Loop)", "test_v3_phase2.py"),
    ("Phase 3 — Flywheel (Bridge, Benchmark, Curriculum)", "test_v3_phase3.py"),
    ("Phase 4 — Skills + MCP", "test_v3_phase4.py"),
    ("Phase 5 — Terminal + Web Dashboard", "test_v3_phase5.py"),
    ("Phase 6 — Advanced Protocols", "test_v3_phase6.py"),
]

all_ok = True
total_passed = 0
total_tests = 0

for name, filename in tests:
    print(f"\n--- {name} ---")
    r = subprocess.run(
        [PYTHON, filename],
        capture_output=True, text=True, timeout=120,
        cwd=ROOT, env={**os.environ, "PYTHONPATH": ROOT},
    )
    print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip()[-300:])
    if r.returncode != 0:
        all_ok = False

# Also verify all new modules compile
print(f"\n{'='*70}")
print("Compilation check — all new V3 modules:")
modules = [
    "jiuzhang.core.provider_factory",
    "jiuzhang.core.async_provider",
    "jiuzhang.core.multi_provider_api",
    "jiuzhang.core.__init__",
    "jiuzhang.agent.async_loop",
    "jiuzhang.agent.quality_governance",
    "jiuzhang.agent.context_manager",
    "jiuzhang.agent.__init__",
    "jiuzhang.flywheel_bridge",
    "jiuzhang.skills_system",
    "jiuzhang.mcp_client",
    "jiuzhang.research_terminal",
    "jiuzhang.web_dashboard",
    "jiuzhang.advanced_protocols",
    "jiuzhang.__init__",
]
for mod in modules:
    r = subprocess.run(
        [PYTHON, "-c", f"import {mod}"],
        capture_output=True, text=True, timeout=30,
        cwd=ROOT, env={**os.environ, "PYTHONPATH": ROOT},
    )
    status = "OK" if r.returncode == 0 else "FAIL"
    print(f"  {status} {mod}")
    if r.returncode != 0:
        all_ok = False
        print(f"    {r.stderr.strip()[-200:]}")

print(f"\n{'='*70}")
if all_ok:
    print("ALL TESTS PASSED — JiuZhang V3 is GO ✅")
else:
    print("SOME TESTS FAILED ❌")
    sys.exit(1)
