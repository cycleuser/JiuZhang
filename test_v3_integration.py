"""Integration test: existing AgentLoop + all V3 subsystems together."""
import os, subprocess, sys, tempfile, textwrap

PYTHON = "/Users/fred/miniconda3/bin/python"
ROOT = "/Users/fred/Documents/GitHub/cycleuser/JiuZhang"
ENV = {**os.environ, "PYTHONPATH": ROOT}

TMPDIR = tempfile.mkdtemp(prefix="jiuzhang_test_")

tests = {
    "AgentLoop constructs with V3 subsystems (no LLM)": f"""
from jiuzhang.core.config import Config
from jiuzhang.agent.loop import AgentLoop, AgentState

config = Config()
loop = AgentLoop(config=config, output_dir='{TMPDIR}')

assert loop.state == AgentState.IDLE
assert loop.program is not None
assert loop.program.goal
assert loop.code_interpreter is not None
assert loop.conjecture_engine is not None
assert loop.plan_tracker is not None
assert loop.context_budget is not None
assert loop.escalation is not None
assert loop._output_dir.as_posix() == '{TMPDIR}'

# Symbolic proof attempt (no LLM needed)
result = loop._symbolic_proof_attempt("a + b = b + a")
assert "equations_checked" in result

# Plan tracker
loop.plan_tracker.parse_plan_from_text("test", "1. Review\\n2. Prove\\n3. Verify")
anchor = loop.plan_tracker.get_anchor()
assert anchor

print("PASS: AgentLoop works with V3 subsystems")
""",

    "AsyncAgentLoop constructs with all subsystems (no LLM)": f"""
from jiuzhang.core.config import Config
from jiuzhang.agent.async_loop import AsyncAgentLoop, AgentState

config = Config()
loop = AsyncAgentLoop(config=config, output_dir='{TMPDIR}')

assert loop.state == AgentState.IDLE
assert loop.program is not None
assert loop.provider is not None
assert loop.factory is not None
assert loop.plan_tracker is not None
assert loop.tool_router is not None
assert loop._output_dir.as_posix() == '{TMPDIR}'

# Symbolic proof attempt (sync, no LLM needed)
result = loop._symbolic_proof_attempt("x + y = y + x")
assert "equations_checked" in result

# Scoring without LLM
strength = loop._calculate_strength(
    {{"llm_proof": "Proof: therefore it holds. QED", "symbolic_result": {{"results": [{{"verified": True}}]}}}},
    {{"passed": True, "confidence": 0.8}},
)
assert strength > 0.3

print("PASS: AsyncAgentLoop constructs OK")
""",

    "QualityController + FlywheelBridge + SkillManager integration": f"""
from jiuzhang.agent.quality_governance import QualityController
from jiuzhang.flywheel_bridge import ResearchFlywheelBridge
from jiuzhang.skills_system import SkillManager

qc = QualityController()
bridge = ResearchFlywheelBridge(output_dir='{TMPDIR}')
sm = SkillManager()

sm.activate("deep-proof")
sm.activate("multi-engine-verify")
ctx = sm.get_active_context()
assert "deep-proof" in ctx

# Quality check (no LLM)
report = qc.evaluate(
    hypothesis="All even numbers > 2 are sum of two primes",
    proof="By exhaustive search up to 4*10^18 verified. QED for that range.",
    verification={{"passed": True, "confidence": 0.7}},
    counterexamples=[],
)
assert report.verdict is not None
assert report.score >= 0.0

# Record in flywheel
entry = bridge.record_experiment(
    question="Goldbach conjecture",
    hypothesis="All even > 2 are sum of two primes",
    proof="Verified up to 4*10^18...",
    verification={{"passed": True, "confidence": 0.7}},
    strength=0.65,
    status="keep",
    tokens_cost=300,
)
assert entry is not None

progress = bridge.get_progress_report()
assert "Research Flywheel" in progress

# Guard check
guard_result = qc.guard_claim("sqrt(2) is irrational", "Proof: assume sqrt(2) = a/b in lowest terms...")
assert guard_result["allowed"]

# Stagnation check
stop, reason, msg = qc.check_stagnation(0.8, "keep")
assert not stop  # High score, shouldn't stop

print("PASS: Full integration pipeline works")
""",

    "Export pipeline: Session + PaperGenerator": f"""
import json
from jiuzhang.research_terminal import ResearchSession
from jiuzhang.advanced_protocols import PaperGenerator

session = ResearchSession(output_dir='{TMPDIR}')

for i in range(3):
    session.record_result({{
        "status": "keep",
        "conjecture_strength": 0.6 + i * 0.1,
        "proof_confidence": 0.7 + i * 0.1,
        "description": f"Result {{i}}",
        "verification": {{"passed": True}},
    }})

json_path = session.export_session("json")
assert json_path.exists()

md_path = session.export_session("markdown")
assert md_path.exists()

data = json.loads(json_path.read_text())
results = data["results"]
assert len(results) == 3

gen = PaperGenerator(output_dir='{TMPDIR}')
paper_path = gen.generate(results, topic="Automated Mathematical Discoveries")
assert paper_path.exists()
content = paper_path.read_text()
assert "documentclass" in content

# Summary
s = session.get_summary()
assert s["total_experiments"] == 3
assert s["kept"] == 3
print("PASS: Export pipeline works")
""",
}

print("="*70)
print("Integration Tests")
print("="*70)

all_ok = True
for name, script in tests.items():
    script = textwrap.dedent(script)
    r = subprocess.run(
        [PYTHON, "-c", script],
        capture_output=True, text=True, timeout=30,
        cwd=ROOT, env=ENV,
    )
    if r.returncode == 0:
        print(f"OK {name}")
    else:
        print(f"FAIL {name}")
        for line in (r.stdout + r.stderr).strip().split("\n")[-5:]:
            print(f"   {line}")
        all_ok = False

print()
if all_ok:
    print("ALL INTEGRATION TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    sys.exit(1)
