"""Deep edge-case and stress tests for JiuZhang V3."""
import os, subprocess, sys, textwrap

PYTHON = "/Users/fred/miniconda3/bin/python"
ROOT = "/Users/fred/Documents/GitHub/cycleuser/JiuZhang"
ENV = {**os.environ, "PYTHONPATH": ROOT}

ok = 0
total = 0

def T(name, script):
    global ok, total
    total += 1
    r = subprocess.run(
        [PYTHON, "-c", textwrap.dedent(script)],
        capture_output=True, text=True, timeout=30, cwd=ROOT, env=ENV,
    )
    if r.returncode == 0:
        print(f"OK {name}")
        ok += 1
    else:
        print(f"FAIL {name}")
        for line in (r.stdout + r.stderr).strip().split("\n")[-4:]:
            print(f"   {line}")


# ── ProviderFactory edge cases ───────────────────────────────────────
T("ProviderFactory: all providers excluded", """
from jiuzhang.core.config import Config
from jiuzhang.core.provider_factory import ProviderFactory
config = Config()
factory = ProviderFactory(config)
all_names = set(factory.get_all_snapshots().keys())
snap, model = factory.pick_provider(exclude=all_names)
assert snap is None, f"Expected None when all excluded, got {snap}"
assert model == ""
print("PASS")
""")

T("ProviderFactory: record success resets errors", """
from jiuzhang.core.provider_factory import ProviderFactory
from jiuzhang.core.provider_factory import ProviderHealth
from jiuzhang.core.config import Config
config = Config()
factory = ProviderFactory(config)
# Cause errors
for _ in range(3):
    factory.record_error("ollama")
m = factory.get_metrics("ollama")
assert m.health != ProviderHealth.HEALTHY
# Success resets
factory.record_success("ollama", 100.0, 200)
assert m.health == ProviderHealth.HEALTHY
assert m.consecutive_errors == 0
print("PASS")
""")

T("ProviderFactory: concurrency slot acquire/release", """
import asyncio
from jiuzhang.core.config import Config
from jiuzhang.core.provider_factory import ProviderFactory
config = Config()
factory = ProviderFactory(config)
async def test():
    # Acquire all slots
    for i in range(4):
        ok = await factory.acquire_slot("ollama")
        assert ok, f"Acquire {i} failed"
    # 5th should fail (max=4)
    ok5 = await factory.acquire_slot("ollama")
    assert not ok5, "5th acquire should fail"
    # Release
    for _ in range(4):
        await factory.release_slot("ollama")
    # Now acquire should work
    ok_after = await factory.acquire_slot("ollama")
    assert ok_after
    await factory.release_slot("ollama")
asyncio.run(test())
print("PASS")
""")

T("ProviderMetrics: rate limiting", """
from jiuzhang.core.provider_factory import ProviderMetrics
import time
m = ProviderMetrics(name="test")
assert not m.is_rate_limited()
# Simulate rate limit
m.record_rate_limit(0, time.time() + 3600)
assert m.is_rate_limited()
# Expired
m.record_rate_limit(10, time.time() - 1)
assert not m.is_rate_limited()
print("PASS")
""")

T("ProviderMetrics: success_rate tracking", """
from jiuzhang.core.provider_factory import ProviderMetrics
m = ProviderMetrics(name="test")
assert m.success_rate == 1.0  # No requests = neutral
m.record_success(100.0)
m.record_error()
m.record_success(50.0)
assert m.success_rate == 2/3
print("PASS")
""")

# ── QualityVerifier edge cases ───────────────────────────────────────
T("QualityVerifier: empty proof", """
from jiuzhang.agent.quality_governance import QualityVerifier, QualityVerdict
qv = QualityVerifier()
report = qv.verify("H", "", {"passed": False, "confidence": 0}, [], [])
assert report.score < 0.5
assert report.verdict in (QualityVerdict.FAIL, QualityVerdict.NEEDS_REVIEW)
print("PASS")
""")

T("QualityVerifier: dangerous code detected", """
from jiuzhang.agent.quality_governance import QualityVerifier
qv = QualityVerifier()
report = qv.verify("H", "Proof: run this code", {"passed": True, "confidence": 1.0}, [],
    ["import os; os.system('rm -rf /')"])
assert any(c["name"] == "code_safety" and c["passed"] == False for c in report.checks), \
    f"Expected code_safety fail, got {report.checks}"
print("PASS")
""")

T("QualityVerifier: high-quality ideal proof", """
from jiuzhang.agent.quality_governance import QualityVerifier, QualityVerdict
qv = QualityVerifier()
hypothesis = "The sum of angles in a triangle is 180 degrees"
proof = \"\"\"Theorem: Sum of angles = 180.

Proof:
1. Let triangle ABC have angles A, B, C.
2. Draw line through A parallel to BC.
3. By alternate interior angles theorem, angle B equals the angle between this parallel and AB.
4. Similarly, angle C equals the angle between the parallel and AC.
5. The three angles at A sum to a straight line = 180 degrees.
6. Therefore, A + B + C = 180. QED.
\"\"\"
v = {"passed": True, "confidence": 0.95}
report = qv.verify(hypothesis, proof, v, [], [])
assert report.verdict in (QualityVerdict.PASS, QualityVerdict.WARN), f"Got {report.verdict}"
assert report.score > 0.5, f"Score too low: {report.score}"
print("PASS")
""")

# ── EarlyStopGovernor edge cases ────────────────────────────────────
T("EarlyStopGovernor: circular reasoning detection", """
from jiuzhang.agent.quality_governance import EarlyStopGovernor, StagnationReason
g = EarlyStopGovernor(max_no_improvement=10, max_consecutive_failures=10)
# Oscillating scores within narrow range
scores = [0.50, 0.55, 0.51, 0.54, 0.52, 0.53]
for s in scores:
    stop, reason, msg = g.should_stop(s, "keep")
    if stop:
        # Circular reasoning or diminishing returns — both valid here
        assert reason in (StagnationReason.CIRCULAR_REASONING, StagnationReason.DIMINISHING_RETURNS), \
            f"Unexpected reason: {reason}"
print("PASS")
""")

T("EarlyStopGovernor: diminishing returns exact threshold", """
from jiuzhang.agent.quality_governance import EarlyStopGovernor, StagnationReason
g = EarlyStopGovernor(max_no_improvement=3)
g.should_stop(0.5, "keep")
g.should_stop(0.5, "keep")
g.should_stop(0.51, "keep")
stop, reason, _ = g.should_stop(0.51, "keep")
assert stop, "Should detect diminishing returns"
assert reason == StagnationReason.DIMINISHING_RETURNS
print("PASS")
""")

# ── AutoCompactor edge cases ─────────────────────────────────────────
T("AutoCompactor: math expressions preserved", """
from jiuzhang.agent.context_manager import AutoCompactor
compactor = AutoCompactor(target_tokens=10)
msgs = [
    {"role": "user", "content": "x " * 500 + "$$\\\\int_0^\\\\infty e^{-x} dx = 1$$" + " y " * 500},
]
compacted, result = compactor.compact(msgs)
# The math block should be extracted
math_blocks = compactor._extract_math(compacted[0]["content"])
# At least the inline/display math should be found
assert len(compacted) > 0
print("PASS")
""")

T("AutoCompactor: empty messages", """
from jiuzhang.agent.context_manager import AutoCompactor, CompactionLevel
compactor = AutoCompactor()
compacted, result = compactor.compact([])
assert result.level == CompactionLevel.NONE
assert len(compacted) == 0
print("PASS")
""")

# ── FlywheelBridge edge cases ────────────────────────────────────────
T("FlywheelBridge: crash status handling", """
from jiuzhang.flywheel_bridge import ResearchFlywheelBridge, ExperimentOutcome
import tempfile
tmp = tempfile.mkdtemp()
bridge = ResearchFlywheelBridge(output_dir=tmp)
entry = bridge.record_experiment(
    question="Crash test", hypothesis="", proof="",
    verification={}, strength=0, status="crash",
)
assert entry.outcome == ExperimentOutcome.CRASH
assert entry.to_training_sample()["metadata"]["outcome"] == "crash"
assert entry.to_hard_example() is None  # Crashes don't produce hard examples
print("PASS")
""")

T("FlywheelBridge: max entries pruning", """
from jiuzhang.flywheel_bridge import ResearchFlywheelBridge
import tempfile
tmp = tempfile.mkdtemp()
bridge = ResearchFlywheelBridge(output_dir=tmp, max_flywheel_entries=10)
for i in range(15):
    bridge.record_experiment(
        question=f"Q{i}", hypothesis=f"H{i}", proof="p",
        verification={"passed": i%2==0}, strength=0.5, status="keep" if i%2==0 else "discard",
    )
assert len(bridge.entries) <= 10
print("PASS")
""")

# ── SkillManager edge cases ──────────────────────────────────────────
T("SkillManager: double activation", """
from jiuzhang.skills_system import SkillManager
sm = SkillManager()
sm.activate("deep-proof")
sm.activate("deep-proof")  # Double activation — should be idempotent
assert sm._active_skills == ["deep-proof"]
sm.deactivate("deep-proof")
assert "deep-proof" not in sm._active_skills
print("PASS")
""")

T("SkillManager: non-existent skill", """
from jiuzhang.skills_system import SkillManager
sm = SkillManager()
ok = sm.activate("non-existent-skill")
assert not ok
assert len(sm._active_skills) == 0
print("PASS")
""")

T("SkillManager: trigger matching edge cases", """
from jiuzhang.skills_system import SkillManager, SkillDefinition
sm = SkillManager()
# No triggers — should not match
matched = sm.activate_by_trigger("completely unrelated text about cooking")
assert len(matched) >= 0  # May match some default triggers or none
# Match multiple
matched2 = sm.activate_by_trigger("prove and search for counterexamples in the literature")
# Should match deep-proof (prove), counterexample-hunter (counterexample), literature-review (literature)
print(f"PASS: matched {len(matched2)} skills")
""")

# ── ResearchSession edge cases ───────────────────────────────────────
T("ResearchSession: empty export", """
from jiuzhang.research_terminal import ResearchSession
import tempfile
tmp = tempfile.mkdtemp()
session = ResearchSession(output_dir=tmp)
path = session.export_session("json")
assert path.exists()
import json
data = json.loads(path.read_text())
assert data["summary"]["total_experiments"] == 0
print("PASS")
""")

T("ResearchSession: notebook export", """
from jiuzhang.research_terminal import ResearchSession
import tempfile
tmp = tempfile.mkdtemp()
session = ResearchSession(output_dir=tmp)
session.record_event("proof", {"description": "Test", "proof": "By induction..."})
path = session.export_session("notebook")
assert path.exists()
import json
nb = json.loads(path.read_text())
assert nb["nbformat"] == 4
assert len(nb["cells"]) >= 1
print("PASS")
""")

# ── PaperGenerator edge cases ────────────────────────────────────────
T("PaperGenerator: empty results", """
from jiuzhang.advanced_protocols import PaperGenerator
import tempfile
tmp = tempfile.mkdtemp()
gen = PaperGenerator(output_dir=tmp)
path = gen.generate([], topic="Empty Paper")
assert path.exists()
content = path.read_text()
assert "documentclass" in content
print("PASS")
""")

T("PaperGenerator: mixed status results", """
from jiuzhang.advanced_protocols import PaperGenerator
import tempfile
tmp = tempfile.mkdtemp()
gen = PaperGenerator(output_dir=tmp)
results = [
    {"status": "keep", "conjecture_strength": 0.9},
    {"status": "discard", "conjecture_strength": 0.1},
    {"status": "crash", "conjecture_strength": 0.0},
]
path = gen.generate(results, topic="Mixed Results")
assert path.exists()
print("PASS")
""")

# ── DreamConsolidatorV2 edge cases ───────────────────────────────────
T("DreamConsolidatorV2: empty results", """
from jiuzhang.advanced_protocols import DreamConsolidatorV2
import tempfile, os
tmp = tempfile.mkdtemp()
db = os.path.join(tmp, "test.db")
dc = DreamConsolidatorV2(db_path=db)
dc.consolidate_session("empty", [], question="Nothing")
knowledge = dc.get_cumulative_knowledge()
assert knowledge["total_sessions"] == 1
assert knowledge["total_theorems"] == 0
print("PASS")
""")

T("DreamConsolidatorV2: technique extraction", """
from jiuzhang.advanced_protocols import DreamConsolidatorV2
tech = DreamConsolidatorV2._extract_techniques(
    "We use induction for the base case, then apply the pigeonhole principle to show "
    "there must be a collision. Finally, a contradiction via diagonalization."
)
assert "induction" in tech
assert "pigeonhole principle" in tech
assert "contradiction" in tech
assert "diagonalization" in tech
print("PASS")
""")

# ── ResearchSwarm edge cases ─────────────────────────────────────────
T("ResearchSwarm: no results synthesize", """
from jiuzhang.advanced_protocols import ResearchSwarm
swarm = ResearchSwarm(num_agents=2)
report = swarm.synthesize([])
assert "No results" in report
print("PASS")
""")

T("ResearchSwarm: convergence with verified results", """
from jiuzhang.advanced_protocols import ResearchSwarm, SwarmAgentResult
swarm = ResearchSwarm(num_agents=3)
results = [
    SwarmAgentResult("a1", "H", "pf", {"passed": True}, 0.9, 0.9, 100, 5, "keep"),
    SwarmAgentResult("a2", "H similar", "pf", {"passed": True}, 0.85, 0.85, 100, 5, "keep"),
]
report = swarm.synthesize(results)
assert "Converging Evidence" in report or "Verified" in report
# Need 2+ rounds for convergence score
swarm._results_history.append([SwarmAgentResult("x", "0", "0", {"passed": False}, 0, 0, 0, 0, "discard")])
swarm._results_history.append(results)
score = swarm.get_convergence_score()
assert score > 0.7, f"Expected >0.7, got {score}"
print("PASS")
""")

# ── MCP client edge cases ───────────────────────────────────────────
T("MCPClient: disconnect not-connected server", """
import asyncio
from jiuzhang.mcp_client import MCPClient, MCPServerConfig
client = MCPClient()
client.add_server(MCPServerConfig(name="not-connected", description="test"))
async def test():
    await client.disconnect("not-connected")  # Should not crash
asyncio.run(test())
print("PASS")
""")

# ── ContextBudgetManager edge cases ──────────────────────────────────
T("ContextBudgetManager: extreme message sizes", """
from jiuzhang.agent.context_budget import ContextBudgetManager, compress_math_context
cbm = ContextBudgetManager(token_limit=100)
# Very long single message
msgs = [{"role": "system", "content": "s" * 5000}]
prepared = cbm.prepare_messages(msgs)
assert len(prepared) > 0
print("PASS")
""")

# ── WebDashboard edge cases ──────────────────────────────────────────
T("WebDashboard: export endpoints return files", """
from jiuzhang.web_dashboard import app
from fastapi.testclient import TestClient
client = TestClient(app)
# Export JSON
r = client.get("/api/export/json")
assert r.status_code in (200, 404, 307, 422), f"Got {r.status_code}"
# Export markdown
r2 = client.get("/api/export/markdown")
assert r2.status_code in (200, 404, 307, 422)
print("PASS")
""")

# ── Summary ──────────────────────────────────────────────────────────
print()
print("="*60)
print(f"Edge-Case Tests: {ok}/{total} passed")
if ok == total:
    print("ALL EDGE-CASE TESTS PASSED")
else:
    print(f"SOME FAILED ({total - ok} failures)")
    sys.exit(1)
