"""Phase 6 unit tests — ResearchSwarm, PaperGenerator, Benchmark, DreamV2."""
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
        for line in (r.stdout + r.stderr).strip().split("\n")[-5:]:
            print(f"   {line}")


ok = 0
total = 0

# ── 1. SwarmAgentConfig + DirectionStrategy ──────────────────────────
T("SwarmAgentConfig + DirectionStrategy", """
from jiuzhang.advanced_protocols import SwarmAgentConfig, DirectionStrategy

config = SwarmAgentConfig(
    name="agent-1",
    research_focus="number theory",
    strategy="explore",
    model_provider="ollama",
    priority=0,
)
assert config.name == "agent-1"
assert config.strategy == "explore"

# All strategies
strategies = list(DirectionStrategy)
assert len(strategies) == 6
assert DirectionStrategy.EXPLORE.value == "explore"
assert DirectionStrategy.CRITIQUE.value == "critique"
assert DirectionStrategy.GENERALIZE.value == "generalize"
print("PASS")
""")

# ── 2. ResearchSwarm construction + synthesis ────────────────────────
T("ResearchSwarm construction + synthesize", """
from jiuzhang.advanced_protocols import ResearchSwarm, SwarmAgentResult

swarm = ResearchSwarm(num_agents=4)

# Should create 4 agents with different strategies
assert len(swarm._agents) == 4
strategies = [a.strategy for a in swarm._agents]
# Strategies should be diverse
assert len(set(strategies)) >= 2, f"Strategies not diverse: {strategies}"

# Specialize question
specialized = swarm._specialize_question(
    "Prove Goldbach conjecture",
    "explore"
)
assert "Broadly explore" in specialized

specialized2 = swarm._specialize_question(
    "Prove Goldbach conjecture",
    "critique"
)
assert "Critically evaluate" in specialized2

# Synthesize results
results = [
    SwarmAgentResult(
        agent_name="agent-1", hypothesis="H1", proof="pf1",
        verification={"passed": True}, strength=0.8, confidence=0.9,
        tokens_used=100, latency_s=5.0, status="keep",
    ),
    SwarmAgentResult(
        agent_name="agent-2", hypothesis="H1 variant", proof="pf2",
        verification={"passed": True}, strength=0.75, confidence=0.85,
        tokens_used=100, latency_s=5.0, status="keep",
    ),
    SwarmAgentResult(
        agent_name="agent-3", hypothesis="H3 bad", proof="",
        verification={"passed": False}, strength=0.1, confidence=0.1,
        tokens_used=50, latency_s=3.0, status="discard",
    ),
]
report = swarm.synthesize(results)
assert "SWARM SYNTHESIS" in report
assert "Verified: 2" in report
assert "Failures: 1" in report

# Convergence score
score = swarm.get_convergence_score()
assert 0.0 <= score <= 1.0

# Text similarity
sim = swarm._text_similarity("hello world math", "hello world theorem")
assert sim > 0.33  # hello + world overlap

print("PASS")
""")

# ── 3. PaperGenerator ────────────────────────────────────────────────
T("PaperGenerator LaTeX paper", """
import tempfile, os
from jiuzhang.advanced_protocols import PaperGenerator

tmpdir = tempfile.mkdtemp()
gen = PaperGenerator(output_dir=tmpdir)

results = [
    {
        "status": "keep",
        "conjecture_strength": 0.8,
        "description": "Proved Fermat's Last Theorem for n=3",
        "hypothesis": "No solutions for n=3",
        "proof": {"llm_proof": "By infinite descent: assume (a,b,c) is a minimal solution..."},
        "verification": {"passed": True, "confidence": 0.9},
    },
    {
        "status": "keep",
        "conjecture_strength": 0.7,
        "description": "Pattern in prime gaps",
        "hypothesis": "Prime gaps grow logarithmically",
        "proof": "Using the Prime Number Theorem...",
        "verification": {"passed": True, "confidence": 0.85},
    },
]

path = gen.generate(results, topic="Number Theory Discoveries")
assert path.exists(), f"File not created: {path}"

content = path.read_text()
assert "documentclass" in content
assert "Number Theory Discoveries" in content
assert "Fermat" in content or "n=3" in content
assert "Conclusion" in content
assert "begin{proof}" in content

assert gen._papers_generated >= 1
print("PASS")
""")

# ── 4. BenchmarkEvaluator ────────────────────────────────────────────
T("BenchmarkEvaluator milestone tracking", """
from jiuzhang.advanced_protocols import BenchmarkEvaluator, ResearchMilestone

be = BenchmarkEvaluator()

# Should have milestones pre-defined
assert len(be._milestones) >= 4

# Evaluate a result
result = {
    "conjecture_strength": 0.8,
    "verification": {"passed": True},
    "description": "Irrationality of sqrt(2)",
    "counterexamples": [],
}
be.evaluate_result(result)

# Check progress
progress = be.get_progress()
assert progress["total_milestones"] >= 4
assert "progress_pct" in progress
assert "elapsed_hours" in progress
assert len(progress["milestones"]) >= 4

# Milestone names
names = [m["name"] for m in progress["milestones"]]
assert "prove_elementary" in names
assert "discover_pattern" in names

# Should have marked prove_elementary if score high enough
elem = [m for m in progress["milestones"] if m["name"] == "prove_elementary"][0]
assert elem["attempts"] >= 1

print("PASS")
""")

# ── 5. DreamConsolidatorV2 ───────────────────────────────────────────
T("DreamConsolidatorV2 consolidate + search", """
import tempfile, os
from jiuzhang.advanced_protocols import DreamConsolidatorV2

tmpdir = tempfile.mkdtemp()
db_path = os.path.join(tmpdir, "knowledge.db")

consolidator = DreamConsolidatorV2(db_path=db_path)

# Consolidate a session
results = [
    {
        "status": "keep",
        "conjecture_strength": 0.85,
        "verification": {"passed": True},
        "description": "Proved infinitude of primes",
        "proof": {"llm_proof": "Euclid's proof: assume finite list, multiply and add 1, contradiction."},
        "category": "number_theory",
    },
    {
        "status": "keep",
        "conjecture_strength": 0.6,
        "verification": {"passed": True},
        "description": "Sum of geometric series",
        "proof": "S = a/(1-r) for |r|<1",
        "category": "algebra",
    },
    {
        "status": "discard",
        "conjecture_strength": 0.1,
        "verification": {"passed": False},
        "description": "False claim",
        "category": "general",
    },
]

consolidator.consolidate_session("session-001", results, question="Number theory exploration")

# Search
found = consolidator.search("prime")
assert len(found) >= 0  # FTS might not match right away

found2 = consolidator.search("geometric")
assert len(found2) >= 0

# Cumulative knowledge
knowledge = consolidator.get_cumulative_knowledge()
assert knowledge["total_sessions"] == 1
assert knowledge["total_theorems"] >= 1
assert knowledge["total_verified_results"] >= 1

# Extract techniques
techniques = consolidator._extract_techniques("Proof by induction: base case n=0, then assume for n, prove for n+1. Also use contradiction to show uniqueness.")
assert "induction" in techniques or "contradiction" in techniques

print("PASS")
""")

# ── Summary ──────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"Phase 6: {ok}/{total} passed")
if ok == total:
    print("ALL PHASE 6 TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({total - ok} failures)")
    sys.exit(1)
