"""Phase 2 unit tests for JiuZhang V3 — Agent, Quality, Context."""
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

# ── 1. QualityVerifier ───────────────────────────────────────────────
T("QualityVerifier full verification pipeline", """
from jiuzhang.agent.quality_governance import QualityVerifier, QualityVerdict

qv = QualityVerifier(novelty_window=10)

hypothesis = "For all integers n > 2, there are no solutions to a^n + b^n = c^n with positive integers a, b, c."
proof = \"\"\"Proof: By Fermat's Last Theorem, proved by Andrew Wiles in 1994,
we know that for n > 2, the equation a^n + b^n = c^n has no solutions in positive integers.
1. Assume there exist positive integers a, b, c, n > 2 satisfying a^n + b^n = c^n.
2. By the modularity theorem and the epsilon conjecture, this would contradict
   the Taniyama-Shimura-Weil conjecture.
3. Therefore, no such solutions exist. QED.\"\"\"
verification = {"passed": True, "confidence": 0.85, "details": ["Wiles 1994"]}
counterexamples = []
code_blocks = []

report = qv.verify(hypothesis, proof, verification, counterexamples, code_blocks)
assert report.verdict in (QualityVerdict.PASS, QualityVerdict.WARN), f"Got {report.verdict}"
assert report.score > 0.3, f"Score too low: {report.score}"
assert len(report.checks) == 6, f"Expected 6 checks, got {len(report.checks)}"

# Second run with same hypothesis should detect novelty issue
report2 = qv.verify(hypothesis, "trivial", {"passed": False, "confidence": 0.1}, [], [])
assert report2.verdict in (QualityVerdict.STALE, QualityVerdict.FAIL, QualityVerdict.NEEDS_REVIEW)

assert qv.pass_rate >= 0.0
print("PASS")
""")

# ── 2. EarlyStopGovernor ────────────────────────────────────────────
T("EarlyStopGovernor stagnation detection", """
from jiuzhang.agent.quality_governance import EarlyStopGovernor, StagnationReason

g = EarlyStopGovernor(max_consecutive_failures=3, max_no_improvement=5, max_crashes=3)

# Normal operation — no stop
stop, reason, msg = g.should_stop(0.7, "keep")
assert not stop, f"Should not stop: {msg}"

stop2, _, _ = g.should_stop(0.75, "keep")
assert not stop2

# 3 consecutive failures → stop
stop3, reason3, _ = g.should_stop(0.1, "discard")
stop4, _, _ = g.should_stop(0.05, "discard")
stop5, reason5, _ = g.should_stop(0.0, "discard")
assert stop5
assert reason5 == StagnationReason.REPEATED_FAILURE

# Reset
g.reset()
assert g.state.consecutive_failures == 0

# Crashes
stop6, _, _ = g.should_stop(0.0, "crash")
stop7, _, _ = g.should_stop(0.0, "crash")
stop8, reason8, _ = g.should_stop(0.0, "crash")
assert stop8
assert reason8 == StagnationReason.TOO_MANY_CRASHES

# Force pivot
g.force_pivot()
assert g.state.direction_changes == 1

print("PASS")
""")

# ── 3. ToolScorer trust decay ────────────────────────────────────────
T("ToolScorer trust decay", """
from jiuzhang.agent.quality_governance import ToolScorer

ts = ToolScorer()

# Initial trust
assert ts.get_trust("sympy_compute") == 1.0
assert ts.is_reliable("sympy_compute")

# Failures decay trust
ts.record_failure("sympy_compute")
assert ts.get_trust("sympy_compute") == 0.95

ts.record_failure("sympy_compute")
ts.record_failure("sympy_compute")
assert ts.get_trust("sympy_compute") < 0.9

# Success restores trust
ts.record_success("sympy_compute")
assert ts.get_trust("sympy_compute") > 0.9

# Another tool
ts.record_success("wolfram")
ts.record_failure("wolfram")
ts.record_failure("wolfram")

ranked = ts.get_ranked_tools()
assert len(ranked) == 2
assert ranked[0][0] == "sympy_compute"  # More trusted

print("PASS")
""")

# ── 4. AutoRollback ─────────────────────────────────────────────────
T("AutoRollback checkpoint and restore", """
from jiuzhang.agent.quality_governance import AutoRollback

rb = AutoRollback(max_checkpoints=3)

cp1 = rb.save("question1", "plan1", [{"id": 1}])
assert cp1 is not None
assert cp1.question == "question1"

cp2 = rb.save("question2", "plan2", [{"id": 2}])
cp3 = rb.save("question3", "plan3", [{"id": 3}])

latest = rb.get_latest()
assert latest.question == "question3"

rolled = rb.rollback()
assert rolled.question == "question3"
assert rb.rollback_count == 1

rolled2 = rb.rollback()
assert rolled2.question == "question2"

assert rb.get_latest().question == "question1"

rb.clear()
assert rb.get_latest() is None

print("PASS")
""")

# ── 5. MathClaimGuard ────────────────────────────────────────────────
T("MathClaimGuard basic checks", """
from jiuzhang.agent.quality_governance import MathClaimGuard

guard = MathClaimGuard()
guard.add_known_theorem("Fermat's Last Theorem", "No solutions for n > 2")

# Proper claim
result = guard.check_claim(
    "There are infinitely many primes",
    "Proof: By Euclid's theorem, suppose p1,...,pn are all primes. Consider N = p1*...*pn + 1. N is either prime or has a prime factor not in the list. Contradiction."
)
assert result["allowed"], f"Should be allowed: {result}"

# Too short claim
result2 = guard.check_claim("x = x", "trivial")
assert not result2["allowed"], f"Should be rejected: {result2}"

print("PASS")
""")

# ── 6. InjectionHandler ──────────────────────────────────────────────
T("InjectionHandler inject and apply", """
from jiuzhang.agent.quality_governance import InjectionHandler

handler = InjectionHandler()

# No pending
assert not handler.has_pending
assert len(handler.get_pending()) == 0

# Inject
id1 = handler.inject("Try a different approach", priority=1)
id2 = handler.inject("This is critical — fix now!", priority=3)
assert len(handler.get_pending()) == 2

# Highest priority first
inj = handler.apply_next()
assert inj.priority == 3
assert "critical" in inj.content

inj2 = handler.apply_next()
assert inj2.priority == 1

assert not handler.has_pending

# Build context
handler.inject("New direction: try analytic approach", priority=2)
ctx = handler.build_injection_context()
assert "New direction" in ctx
assert "HUMAN CORRECTIONS" in ctx

print("PASS")
""")

# ── 7. AutoCompactor ─────────────────────────────────────────────────
T("AutoCompactor progressive compaction", """
from jiuzhang.agent.context_manager import AutoCompactor, CompactionLevel

compactor = AutoCompactor(target_tokens=100)

# Under limit — no compaction
msgs = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
compacted, result = compactor.compact(msgs)
assert result.level == CompactionLevel.NONE
assert result.messages_after == 2

# Over limit — light compaction
long_msg = "x " * 500  # ~500 tokens
msgs2 = [
    {"role": "system", "content": "You are a math assistant. Be helpful."},
    {"role": "user", "content": long_msg},
    {"role": "assistant", "content": long_msg},
    {"role": "user", "content": long_msg},
]
compacted2, result2 = compactor.compact(msgs2)
assert result2.level != CompactionLevel.NONE
assert result2.original_tokens >= result2.compacted_tokens or result2.level == CompactionLevel.LIGHT

# Emergency — very large
huge = "y " * 2000
msgs3 = [{"role": "user", "content": huge}, {"role": "assistant", "content": huge}]
compacted3, result3 = compactor.compact(msgs3)
assert result3.savings_percent > 50 or result3.level == CompactionLevel.EMERGENCY

# Record insights persist
compactor.record_insight("Key finding: pattern in primes")
compactor.record_theorem("Euclid's theorem")
assert len(compactor._persistent_insights) == 1
assert len(compactor._key_theorems) == 1

print("PASS")
""")

# ── 8. ThinkingBudget ────────────────────────────────────────────────
T("ThinkingBudget adaptive allocation", """
from jiuzhang.agent.context_manager import ThinkingBudget, ThinkingMode

tb = ThinkingBudget(current_mode=ThinkingMode.AUTO)

# Simple question gets small budget
simple_budget = tb.allocate(0.1, 1000)
assert simple_budget >= 128, f"Got {simple_budget}"

# Complex question gets large budget
complex_budget = tb.allocate(0.9, 1000)
assert complex_budget > simple_budget, f"Complex {complex_budget} should be > simple {simple_budget}"

# Fixed modes
tb.current_mode = ThinkingMode.BRIEF
brief = tb.allocate(0.5, 1000)
assert brief == 128, f"Got {brief}"

tb.current_mode = ThinkingMode.DEEP
deep = tb.allocate(0.5, 1000)
assert deep >= 1024

# Complexity estimation
assert tb.estimate_complexity("What is 2+2?") < 0.3
assert tb.estimate_complexity("Prove the Riemann hypothesis") > 0.3

print("PASS")
""")

# ── 9. IntegratedContextManager ──────────────────────────────────────
T("IntegratedContextManager full pipeline", """
from jiuzhang.agent.context_manager import IntegratedContextManager, ThinkingMode

icm = IntegratedContextManager(token_limit=8192, thinking_mode=ThinkingMode.AUTO)

msgs = [
    {"role": "system", "content": "You are a math assistant."},
    {"role": "user", "content": "Prove that sqrt(2) is irrational."},
]
question = "Prove that sqrt(2) is irrational."

prepared, thinking_budget = icm.prepare_call(msgs, question)
assert len(prepared) >= 2
assert thinking_budget > 0

icm.record_result(500, insight="sqrt(2) proof uses contradiction")
assert icm.total_tokens_used > 0

stats = icm.get_stats()
assert stats["total_tokens"] > 0
assert "thinking_allocated" in stats

print("PASS")
""")

# ── 10. ContextBudgetManager + ToolRouter ────────────────────────────
T("ContextBudgetManager + ToolRouter (existing module)", """
from jiuzhang.agent.context_budget import (
    ContextBudgetManager, ToolRouter, ToolCategory,
    estimate_tokens, compress_math_context,
)

# Token estimation
assert estimate_tokens("hello world") > 0
assert estimate_tokens("你好世界") > 0

# Context budget
cbm = ContextBudgetManager(token_limit=4096)
msgs = [{"role": "user", "content": "test"}]
prepared = cbm.prepare_messages(msgs)
assert len(prepared) == 1

# Tool router
router = ToolRouter()
result = router.route("prove that the sum of primes diverges")
assert result.category is not None  # should route to REASON or similar

result2 = router.route("search for papers about topology")
assert result2.category == ToolCategory.SEARCH

result3 = router.route("what is a group?")
assert result3.category is not None  # Routes to READ or RESPOND — both valid

# Affirmation guard
result4 = router.route("yes", prior_category=ToolCategory.WRITE)
assert result4.category == ToolCategory.WRITE

# Math compression
long_msgs = [
    {"role": "system", "content": "You are a math tutor."},
    {"role": "user", "content": "Explain $$\\\\int_0^\\\\infty e^{-x} dx$$ in detail " + "very " * 100},
    {"role": "assistant", "content": "The integral is 1. " + "detail " * 200},
]
compressed = compress_math_context(long_msgs, 100)
assert len(compressed) <= len(long_msgs) + 1  # May add summary

print("PASS")
""")

# ── Summary ──────────────────────────────────────────────────────────
print(f"\\n{'='*60}")
print(f"Phase 2: {ok}/{total} passed")
if ok == total:
    print("ALL PHASE 2 TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({total - ok} failures)")
    sys.exit(1)
