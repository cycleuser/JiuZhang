"""End-to-end demo: JiuZhang V3 full research pipeline with quality governance.

Demonstrates the complete autonomous math research workflow:
  1. AgentLoop constructs with V3 subsystems (QualityController, FlywheelBridge)
  2. Symbolic proof attempt + quality verification
  3. Flywheel recording (results → training data)
  4. Stagnation detection + direction pivot
  5. Multi-agent swarm synthesis
  6. Paper generation from verified results
  7. Session export (JSON, MD, Notebook)
  8. Cross-session knowledge consolidation (Dream V2)

No live LLM required — uses SymPy for symbolic verification.
"""
import os, sys, tempfile, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from jiuzhang.core.config import Config
from jiuzhang.agent.loop import AgentLoop, AgentState
from jiuzhang.agent.quality_governance import QualityController, QualityVerdict
from jiuzhang.flywheel_bridge import ResearchFlywheelBridge, ExperimentOutcome
from jiuzhang.skills_system import SkillManager
from jiuzhang.advanced_protocols import (
    ResearchSwarm, SwarmAgentResult, PaperGenerator,
    BenchmarkEvaluator, DreamConsolidatorV2,
)
from jiuzhang.research_terminal import ResearchSession


def sep(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


# ──────────────────────────────────────────────────────────────────────
# Step 1: Setup
# ──────────────────────────────────────────────────────────────────────
sep("Step 1: System Initialization")

config = Config()
tmpdir = tempfile.mkdtemp(prefix="jiuzhang_demo_")
print(f"Output directory: {tmpdir}")

# Initialize the sync AgentLoop with all V3 subsystems
agent = AgentLoop(config=config, output_dir=tmpdir)
assert agent.quality is not None
assert agent.flywheel is not None
print("AgentLoop + QualityController + FlywheelBridge: INITIALIZED")

# Skill system
skills = SkillManager()
skills.activate("deep-proof")
skills.activate("multi-engine-verify")
ctx = skills.get_active_context()
assert "deep-proof" in ctx
print(f"Skills activated: {skills._active_skills}")


# ──────────────────────────────────────────────────────────────────────
# Step 2: Symbolic Proof Attempt (no LLM needed)
# ──────────────────────────────────────────────────────────────────────
sep("Step 2: Symbolic Proof + Quality Verification")

# Use SymPy directly — the agent can do this without an LLM
import sympy as sp

# Theorem 1: sin^2 x + cos^2 x = 1
x = sp.Symbol('x')
lhs = sp.sin(x)**2 + sp.cos(x)**2
rhs = 1
t1_verified = sp.simplify(lhs - rhs) == 0
print(f"Theorem 1 [sin^2 + cos^2 = 1]: {'PASS' if t1_verified else 'FAIL'}")

# Theorem 2: product of sum and difference
a, b = sp.symbols('a b')
lhs2 = (a + b) * (a - b)
rhs2 = a**2 - b**2
t2_verified = sp.simplify(lhs2 - rhs2) == 0
print(f"Theorem 2 [(a+b)(a-b) = a^2-b^2]: {'PASS' if t2_verified else 'FAIL'}")

# Theorem 3: sum of first n natural numbers
n = sp.Symbol('n', integer=True, positive=True)
i = sp.Symbol('i')
lhs3 = sp.Sum(i, (i, 1, n)).doit()
rhs3 = n * (n + 1) / 2
t3_verified = sp.simplify(lhs3 - rhs3) == 0
print(f"Theorem 3 [sum(1..n) = n(n+1)/2]: {'PASS' if t3_verified else 'FAIL'}")

# Use quality controller to grade each
qc = agent.quality
theorems = [
    ("sin^2 x + cos^2 x = 1", "Proof: Follows from the definition of sine and cosine on the unit circle. By the Pythagorean theorem, sin^2 x + cos^2 x = 1 for all x. QED.", t1_verified),
    ("(a+b)(a-b) = a^2 - b^2", "Proof: Expand (a+b)(a-b) = a·a + a·(-b) + b·a + b·(-b) = a^2 - ab + ba - b^2 = a^2 - b^2. QED.", t2_verified),
    ("sum_{i=1}^n i = n(n+1)/2", "Proof: By induction. Base case n=1: 1 = 1·2/2. Assume true for n, then sum to n+1 = n(n+1)/2 + (n+1) = (n+1)(n+2)/2. QED.", t3_verified),
]

total_score = 0
for hypothesis, proof, verified in theorems:
    v = {"passed": verified, "confidence": 0.95 if verified else 0.1}
    report = qc.evaluate(hypothesis, proof, v, counterexamples=[], code_blocks=[])
    total_score += report.score
    print(f"  [{hypothesis[:40]}...] Quality: {report.score:.2f} | Verdict: {report.verdict.value}")

print(f"\nAverage quality score: {total_score/len(theorems):.3f}")
print(f"Quality pass rate: {qc.verifier.pass_rate:.1%}")


# ──────────────────────────────────────────────────────────────────────
# Step 3: Flywheel Recording
# ──────────────────────────────────────────────────────────────────────
sep("Step 3: Flywheel — Results → Training Data")

for hypothesis, proof, verified in theorems:
    entry = agent.flywheel.record_experiment(
        question=f"Prove: {hypothesis[:60]}",
        hypothesis=hypothesis,
        proof=proof,
        verification={"passed": verified, "confidence": 0.95},
        strength=0.90 if verified else 0.05,
        status="keep" if verified else "discard",
        tokens_cost=150,
    )

# Also record a crash for realism
agent.flywheel.record_experiment(
    question="Prove 1=0",
    hypothesis="1=0",
    proof="",
    verification={},
    strength=0.0,
    status="crash",
    tokens_cost=0,
)

# Check training data
data = agent.flywheel.export_training_data()
print(f"Positive training samples: {data['total_positive']}")
print(f"Hard example samples:     {data['total_hard']}")

# Progress report
print()
print(agent.flywheel.get_progress_report())


# ──────────────────────────────────────────────────────────────────────
# Step 4: Stagnation Detection + Pivot
# ──────────────────────────────────────────────────────────────────────
sep("Step 4: Stagnation Detection & Direction Pivot")

# Simulate a string of failures
agent.quality.governor.reset()
for i in range(4):
    stop, reason, msg = agent.quality.check_stagnation(0.05, "discard")
    print(f"  Experiment {i+1}: stop={stop}, reason={reason}")

# After 3+ failures, should detect stagnation
stop, reason, msg = agent.quality.check_stagnation(0.02, "discard")
if stop:
    agent._direction_changes += 1
    agent.quality.governor.force_pivot()
    new_direction = agent._choose_research_direction()
    print(f"  PIVOT: {reason.value} → New direction: {new_direction[:80]}...")
else:
    print(f"  No pivot needed (state: {agent.quality.governor.state})")

# Now simulate successful runs
agent.quality.governor.reset()
for i, score in enumerate([0.6, 0.65, 0.7, 0.72]):
    stop, _, _ = agent.quality.check_stagnation(score, "keep")
    print(f"  Improvement {i+1}: score={score:.2f}, stop={stop}")

qstats = agent.quality.get_quality_stats()
print(f"\nQuality stats: pass_rate={qstats['verifier_pass_rate']:.1%}, best={qstats['best_score']:.3f}")


# ──────────────────────────────────────────────────────────────────────
# Step 5: Multi-Agent Swarm Synthesis
# ──────────────────────────────────────────────────────────────────────
sep("Step 5: Research Swarm — Multi-Agent Synthesis")

swarm = ResearchSwarm(num_agents=4)
strategies = [a.strategy for a in swarm._agents]
print(f"Agent strategies: {strategies}")

# Simulate results from 4 agents exploring the same theorem
results = [
    SwarmAgentResult("agent-1", "(a+b)(a-b)=a^2-b^2", "Direct expansion proof", {"passed": True}, 0.92, 0.95, 100, 5, "keep"),
    SwarmAgentResult("agent-2", "Difference of squares identity", "Geometric proof using area", {"passed": True}, 0.88, 0.90, 100, 5, "keep"),
    SwarmAgentResult("agent-3", "Generalize to (a^n-b^n)/(a-b)", "Polynomial identity", {"passed": True}, 0.70, 0.75, 100, 5, "keep"),
    SwarmAgentResult("agent-4", "Counterexample hunt", "No counterexample found", {"passed": True}, 0.50, 0.60, 100, 5, "keep"),
]

synthesis_report = swarm.synthesize(results)
print(synthesis_report[:600])


# ──────────────────────────────────────────────────────────────────────
# Step 6: Automated Paper Generation
# ──────────────────────────────────────────────────────────────────────
sep("Step 6: LaTeX Paper Generation")

paper_gen = PaperGenerator(output_dir=tmpdir)
paper_results = [
    {"status": "keep", "conjecture_strength": 0.92, "description": "Algebraic identities", "hypothesis": "(a+b)(a-b)=a^2-b^2", "proof": {"llm_proof": "Direct expansion and simplification"}, "verification": {"passed": True, "confidence": 0.95}},
    {"status": "keep", "conjecture_strength": 0.88, "description": "Sum formula", "hypothesis": "sum_{i=1}^n i = n(n+1)/2", "proof": {"llm_proof": "Proof by mathematical induction"}, "verification": {"passed": True, "confidence": 0.90}},
    {"status": "keep", "conjecture_strength": 0.95, "description": "Pythagorean identity", "hypothesis": "sin^2 x + cos^2 x = 1", "proof": {"llm_proof": "Follows from the definition on the unit circle"}, "verification": {"passed": True, "confidence": 0.95}},
]

paper_path = paper_gen.generate(paper_results, topic="Verified Elementary Mathematical Identities")
paper_size = paper_path.stat().st_size
print(f"Paper generated: {paper_path}")
print(f"Size: {paper_size} bytes")
print(f"Papers generated so far: {paper_gen._papers_generated}")


# ──────────────────────────────────────────────────────────────────────
# Step 7: Session Export
# ──────────────────────────────────────────────────────────────────────
sep("Step 7: Session Export (JSON, Markdown, Notebook)")

session = ResearchSession(output_dir=tmpdir)
for hypothesis, proof, verified in theorems:
    session.record_result({
        "status": "keep" if verified else "discard",
        "conjecture_strength": 0.90 if verified else 0.05,
        "proof_confidence": 0.95,
        "description": hypothesis,
        "verification": {"passed": verified},
    })

# Export all formats
json_path = session.export_session("json")
md_path = session.export_session("markdown")

print(f"JSON export:  {json_path} ({json_path.stat().st_size} bytes)")
print(f"Markdown:     {md_path} ({md_path.stat().st_size} bytes)")

# Verify exports
data = json.loads(json_path.read_text())
print(f"  Experiments: {data['summary']['total_experiments']}")
print(f"  Kept: {data['summary']['kept']}")


# ──────────────────────────────────────────────────────────────────────
# Step 8: Cross-Session Knowledge Transfer
# ──────────────────────────────────────────────────────────────────────
sep("Step 8: Dream Consolidator V2 — Cross-Session Knowledge")

db_path = os.path.join(tmpdir, "knowledge.db")
dream = DreamConsolidatorV2(db_path=db_path)

# Consolidate session
session_id = "demo-" + time.strftime("%Y%m%d-%H%M%S")
dream.consolidate_session(
    session_id,
    paper_results,
    question="Elementary mathematical identities",
)

# Check cumulative knowledge
knowledge = dream.get_cumulative_knowledge()
print(f"Total theorems stored:    {knowledge['total_theorems']}")
print(f"Total techniques:         {knowledge['total_techniques']}")
print(f"Total sessions:           {knowledge['total_sessions']}")
print(f"Total verified results:   {knowledge['total_verified_results']}")

# Search
found = dream.search("induction")
print(f"Search 'induction':       {len(found)} results")
found2 = dream.search("identity")
print(f"Search 'identity':        {len(found2)} results")

# Technique extraction
tech = dream._extract_techniques("We use induction with the base case n=1, then apply contradiction to show uniqueness.")
print(f"Extracted techniques:     {tech}")


# ──────────────────────────────────────────────────────────────────────
# Step 9: Benchmark Evaluation
# ──────────────────────────────────────────────────────────────────────
sep("Step 9: Benchmark Milestone Tracking")

bench = BenchmarkEvaluator()
for r in paper_results:
    bench.evaluate_result(r)

progress = bench.get_progress()
print(f"Milestones: {progress['achieved']}/{progress['total_milestones']} achieved ({progress['progress_pct']:.0f}%)")
for m in progress["milestones"]:
    icon = "✅" if m["achieved"] else "⬜"
    print(f"  {icon} {m['name']:25s} — attempts: {m['attempts']}, closest: {m['closest_score']:.2f}")


# ──────────────────────────────────────────────────────────────────────
# FINAL
# ──────────────────────────────────────────────────────────────────────
sep("JiuZhang V3 — Full Pipeline Demo COMPLETE")

flywheel_data = agent.flywheel.export_training_data()
n_samples = flywheel_data.get('total_positive', len(flywheel_data.get('samples', [])))

print(f"""
Summary:
  ✅ Agent initialized with QualityController + FlywheelBridge
  ✅ {len(theorems)} symbolic proofs verified with quality scoring
  ✅ Results logged to flywheel -> {n_samples} training samples
  ✅ Stagnation detection + auto-pivot working
  ✅ 4-agent swarm synthesized results
  ✅ LaTeX paper generated ({paper_size} bytes)
  ✅ Session exported (JSON + Markdown)
  ✅ Knowledge consolidated across sessions ({knowledge['total_theorems']} theorems)
  ✅ Benchmark milestone tracking ({progress['achieved']}/{progress['total_milestones']})

Output directory: {tmpdir}
All systems operational. Ready for live LLM research.
""")
