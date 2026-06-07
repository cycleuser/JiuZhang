"""Phase 3 unit tests — Flywheel Bridge, AutoBenchmark, Curriculum."""
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

# ── 1. FlywheelEntry ─────────────────────────────────────────────────
T("FlywheelEntry creation + training sample", """
from jiuzhang.flywheel_bridge import FlywheelEntry, ExperimentOutcome

entry = FlywheelEntry(
    id="test-001",
    question="Prove sum of first n natural numbers",
    hypothesis="Sum(n) = n(n+1)/2",
    proof="Proof by induction: base case n=1...",
    verification={"passed": True, "confidence": 0.9},
    outcome=ExperimentOutcome.SUCCESS,
    strength=0.85,
    category="arithmetic",
    difficulty="elementary",
    tokens_cost=500,
)
assert entry.outcome == ExperimentOutcome.SUCCESS
assert entry.to_training_sample()["messages"][2]["role"] == "assistant"

# Failure generates hard example
entry2 = FlywheelEntry(
    id="test-002",
    question="Prove false thing",
    hypothesis="1 = 0",
    proof="bad proof",
    verification={"passed": False},
    outcome=ExperimentOutcome.FAILURE,
    strength=0.0,
    counterexamples=[{"value": 1}],
    category="general",
)
hard = entry2.to_hard_example()
assert hard is not None
assert "hard_" in hard["id"]
print("PASS")
""")

# ── 2. CapabilityFrontier ───────────────────────────────────────────
T("CapabilityFrontier topic tracking", """
from jiuzhang.flywheel_bridge import CapabilityFrontier

cf = CapabilityFrontier()

assert cf.estimate_level() == "elementary"

cf.record_success("arithmetic")
cf.record_success("algebra")
assert "arithmetic" in cf.mastered_topics
assert "algebra" in cf.mastered_topics

cf.record_failure("topology")
cf.record_failure("topology")

frontier = cf.get_next_topics(["arithmetic", "algebra", "topology", "calculus", "number_theory"])
# "topology" should be first (struggling), then unknown topics
assert "topology" in frontier
assert len(frontier) >= 3

level = cf.estimate_level()
assert level in ("elementary", "intermediate", "advanced", "research")
print("PASS")
""")

# ── 3. AutoBenchmark ────────────────────────────────────────────────
T("AutoBenchmark eval scheduling", """
from jiuzhang.flywheel_bridge import AutoBenchmark

bm = AutoBenchmark(eval_every_n=5)

# Should evaluate at 5, 10, 15...
assert not bm.should_evaluate(1)
assert not bm.should_evaluate(4)
assert bm.should_evaluate(5)
assert not bm.should_evaluate(6)
assert bm.should_evaluate(10)

# Hold-out problems
bm.add_held_out_problem({"question": "Prove sqrt(2) irrational", "category": "number_theory"})
problems = bm.build_benchmark_problems()
assert len(problems) >= 1

# Improvement curve
from jiuzhang.flywheel_bridge import BenchmarkResult
bm.record_result(BenchmarkResult(
    timestamp="2024-01-01", total_problems=10, solved=5,
    accuracy=0.5, avg_strength=0.6, by_category={}, flywheel_round=1,
))
curve = bm.get_improvement_curve()
assert len(curve) == 1

# Regression detection
assert not bm.detect_regression()  # Not enough data
print("PASS")
""")

# ── 4. ProgramIterator ───────────────────────────────────────────────
T("ProgramIterator strategy and domain tracking", """
from jiuzhang.flywheel_bridge import ProgramIterator

pi = ProgramIterator()

pi.record_strategy_result("induction", 0.8)
pi.record_strategy_result("induction", 0.9)
pi.record_strategy_result("contradiction", 0.5)
pi.record_strategy_result("direct", 0.3)

best = pi.get_best_strategies(2)
assert len(best) == 2
assert best[0][0] == "induction"
assert best[0][1] > best[1][1]

pi.record_domain_result("number_theory", 0.7)
pi.record_domain_result("algebra", 0.4)
pi.record_domain_result("number_theory", 0.8)

best_domains = pi.get_best_domains(2)
assert best_domains[0][0] == "number_theory"

suggestion = pi.suggest_program_update()
assert "Best Strategies" in suggestion
assert "induction" in suggestion
assert "Productive Domains" in suggestion
print("PASS")
""")

# ── 5. ResearchFlywheelBridge full cycle ────────────────────────────
T("ResearchFlywheelBridge record + progress", """
from jiuzhang.flywheel_bridge import ResearchFlywheelBridge, ExperimentOutcome
import tempfile, os

tmpdir = tempfile.mkdtemp()
bridge = ResearchFlywheelBridge(output_dir=tmpdir, eval_every_n=3, max_flywheel_entries=100)

# Record experiments
for i in range(5):
    entry = bridge.record_experiment(
        question=f"Prove theorem {i}",
        hypothesis=f"Hypothesis {i}",
        proof="Proof by induction...",
        verification={"passed": i % 2 == 0, "confidence": 0.5 + i * 0.1},
        strength=0.3 + i * 0.1,
        status="keep" if i % 2 == 0 else "discard",
        tokens_cost=100 * (i + 1),
    )
    assert entry is not None
    assert entry.id

# Check accumulation
assert bridge._total_experiments == 5
assert bridge._total_verified >= 1

# Export training data
data = bridge.export_training_data()
assert "samples" in data
assert "hard_examples" in data

# Progress report
report = bridge.get_progress_report()
assert "Research Flywheel" in report
assert "5" in report or "Total experiments" in report

# Next direction
direction = bridge.get_next_research_direction(["number_theory", "topology", "algebra"])
assert len(direction) > 0

# Save and load state
path = bridge.save_state()
assert path.exists()

bridge2 = ResearchFlywheelBridge(output_dir=tmpdir)
bridge2.load_state()
assert bridge2._total_experiments == 5

print("PASS")
""")

# ── Summary ──────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"Phase 3: {ok}/{total} passed")
if ok == total:
    print("ALL PHASE 3 TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({total - ok} failures)")
    sys.exit(1)
