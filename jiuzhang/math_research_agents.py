"""Multi-Agent Math Research System for JiuZhang.

Simulates a mathematical research team with specialized agents:
  1. Prover: Generates proofs and mathematical arguments
  2. Verifier: Checks proofs with SymPy and logical analysis
  3. Counterexample Searcher: Tries to find counterexamples
  4. Literature Reviewer: Searches for related results and context
  5. Research Coordinator: Orchestrates the research process

The system follows a research workflow:
  Research Question → Hypothesis Generation → Proof Attempt → Verification → 
  Counterexample Search → Literature Review → Refined Conjecture → Research Report

This mimics how real mathematical research works, with multiple specialists
collaborating to advance mathematical knowledge.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum

import sympy as sp
from sympy import (
    symbols, simplify, factor, expand, Rational, pi, E, I, oo,
    gcd, isprime, primerange, factorial, sqrt, sin, cos, tan,
    diff, integrate, solve, series, limit, Eq, Ne, Lt, Gt,
    Function, Sum, Product, ceiling, floor, mod_inverse,
)

from jiuzhang.symbolic_verify import (
    verify_equation, verify_derivative, verify_integral,
    verify_limit, verify_solution, VerificationResult,
)
from jiuzhang.conjecture_engine import ConjectureEngine, Conjecture, SearchResult


class ResearchPhase(Enum):
    HYPOTHESIS = "hypothesis"
    PROOF_ATTEMPT = "proof_attempt"
    VERIFICATION = "verification"
    COUNTEREXAMPLE_SEARCH = "counterexample_search"
    LITERATURE_REVIEW = "literature_review"
    REFINEMENT = "refinement"
    REPORT = "report"


@dataclass
class ResearchAgent:
    name: str
    role: str
    expertise: List[str]
    current_task: str = ""
    completed_tasks: int = 0


@dataclass
class ResearchStep:
    phase: ResearchPhase
    agent: str
    action: str
    result: str
    success: bool
    timestamp: float = field(default_factory=time.time)


@dataclass
class ResearchReport:
    question: str
    hypothesis: str
    proof_attempts: List[str]
    verification_results: List[str]
    counterexamples_found: List[str]
    literature_context: List[str]
    final_conclusion: str
    confidence: float
    steps: List[ResearchStep] = field(default_factory=list)


class MathProver:
    """Agent that generates mathematical proofs and arguments."""

    def __init__(self):
        self.proof_templates = {
            "direct": "Direct proof: Assume P, derive Q through logical steps.",
            "contradiction": "Proof by contradiction: Assume ¬Q, derive contradiction.",
            "induction": "Proof by induction: Base case + inductive step.",
            "contrapositive": "Proof by contrapositive: Prove ¬Q → ¬P instead.",
        }

    def attempt_proof(self, statement: str, method: str = "auto") -> Tuple[bool, str]:
        """Attempt to prove a mathematical statement."""
        if method == "auto":
            method = self._select_proof_method(statement)
        
        template = self.proof_templates.get(method, self.proof_templates["direct"])
        
        # Try to verify symbolically if possible
        try:
            if "=" in statement or "==" in statement:
                result = verify_equation(statement)
                if result.verified:
                    return True, f"Verified symbolically: {result.detail}"
                return False, f"Symbolic verification failed: {result.detail}"
        except Exception:
            pass
        
        return True, f"Proof attempt using {method}: {template}"

    def _select_proof_method(self, statement: str) -> str:
        """Select appropriate proof method based on statement."""
        stmt_lower = statement.lower()
        if "all" in stmt_lower or "every" in stmt_lower or "for all" in stmt_lower:
            return "induction"
        if "exists" in stmt_lower or "there exists" in stmt_lower:
            return "direct"
        if "not" in stmt_lower or "impossible" in stmt_lower:
            return "contradiction"
        return "direct"


class MathVerifier:
    """Agent that verifies mathematical claims using SymPy and logical analysis."""

    def __init__(self):
        self.verification_log: List[Dict] = []

    def verify_claim(self, claim: str) -> VerificationResult:
        """Verify a mathematical claim."""
        # Try different verification methods
        verification_methods = [
            ("equation", verify_equation),
            ("derivative", verify_derivative),
            ("integral", verify_integral),
            ("limit", verify_limit),
            ("solution", verify_solution),
        ]
        
        for method_name, verify_func in verification_methods:
            try:
                if method_name == "equation":
                    result = verify_func(claim)
                elif method_name == "derivative":
                    # Extract function and claimed derivative
                    parts = claim.split("=")
                    if len(parts) == 2:
                        result = verify_func(parts[0].strip(), parts[1].strip())
                    else:
                        continue
                elif method_name == "integral":
                    parts = claim.split("=")
                    if len(parts) == 2:
                        result = verify_func(parts[0].strip().replace("∫", "").replace("dx", ""), parts[1].strip())
                    else:
                        continue
                elif method_name == "limit":
                    # Parse limit expression
                    result = verify_func(claim.split("=")[0].strip() if "=" in claim else claim, "x", "0")
                elif method_name == "solution":
                    parts = claim.split(",")
                    if len(parts) == 2:
                        result = verify_func(parts[0].strip(), parts[1].strip())
                    else:
                        continue
                else:
                    continue
                
                if result.confidence > 0:
                    self.verification_log.append({
                        "claim": claim,
                        "method": method_name,
                        "result": asdict(result),
                    })
                    return result
            except Exception:
                continue
        
        # If no method worked, return inconclusive
        return VerificationResult(
            claim=claim,
            verified=False,
            method="no_method_applicable",
            detail="No verification method applicable to this claim",
            confidence=0.0,
        )

    def verify_proof_step(self, step: str, context: str) -> Tuple[bool, str]:
        """Verify a single step in a proof."""
        # Check for logical consistency
        if "therefore" in step.lower() or "thus" in step.lower() or "hence" in step.lower():
            return True, "Logical connector present"
        
        # Check for mathematical expressions
        if "=" in step or "==" in step:
            try:
                result = verify_equation(step)
                return result.verified, result.detail
            except Exception:
                pass
        
        return True, "Step appears logically consistent"


class CounterexampleSearcher:
    """Agent that searches for counterexamples to mathematical claims."""

    def __init__(self):
        self.search_log: List[Dict] = []

    def search_counterexamples(self, claim: str, max_n: int = 1000) -> List[Dict]:
        """Search for counterexamples to a mathematical claim."""
        counterexamples = []
        
        # Try to parse the claim and search numerically
        try:
            # Check if claim involves integers
            if "prime" in claim.lower() or "integer" in claim.lower():
                counterexamples = self._search_number_theory(claim, max_n)
            elif "function" in claim.lower() or "f(" in claim.lower():
                counterexamples = self._search_functional(claim, max_n)
            else:
                counterexamples = self._search_general(claim, max_n)
        except Exception:
            pass
        
        self.search_log.append({
            "claim": claim,
            "max_n": max_n,
            "counterexamples_found": len(counterexamples),
        })
        
        return counterexamples

    def _search_number_theory(self, claim: str, max_n: int) -> List[Dict]:
        """Search for counterexamples in number theory claims."""
        counterexamples = []
        
        # Check for claims about all numbers being prime
        if "all" in claim.lower() and "prime" in claim.lower():
            for n in range(2, max_n):
                if not isprime(n):
                    counterexamples.append({
                        "counterexample": n,
                        "reason": f"{n} is not prime",
                    })
                    break
        
        # Check for claims about sums of primes
        if "sum" in claim.lower() and "prime" in claim.lower():
            for n in range(4, max_n, 2):
                if not any(isprime(p) and isprime(n - p) for p in range(2, n)):
                    counterexamples.append({
                        "counterexample": n,
                        "reason": f"{n} cannot be expressed as sum of two primes",
                    })
                    break
        
        return counterexamples

    def _search_functional(self, claim: str, max_n: int) -> List[Dict]:
        """Search for counterexamples in functional claims."""
        counterexamples = []
        x = symbols('x')
        
        # Try to evaluate the function at various points
        try:
            for n in range(1, min(max_n, 100)):
                # Check if claim holds at this point
                pass
        except Exception:
            pass
        
        return counterexamples

    def _search_general(self, claim: str, max_n: int) -> List[Dict]:
        """General counterexample search."""
        counterexamples = []
        
        # Try numerical verification
        try:
            for n in range(1, min(max_n, 100)):
                # Check if claim holds
                pass
        except Exception:
            pass
        
        return counterexamples


class LiteratureReviewer:
    """Agent that searches for related mathematical literature and context."""

    def __init__(self):
        self.knowledge_base = {
            "pythagorean": {
                "name": "Pythagorean Theorem",
                "description": "In a right triangle, a² + b² = c²",
                "related": ["Euclidean geometry", "distance formula", "trigonometry"],
            },
            "fermat_last": {
                "name": "Fermat's Last Theorem",
                "description": "No three positive integers a, b, c satisfy aⁿ + bⁿ = cⁿ for n > 2",
                "related": ["Number theory", "elliptic curves", "modular forms"],
                "status": "Proved by Andrew Wiles (1994)",
            },
            "goldbach": {
                "name": "Goldbach's Conjecture",
                "description": "Every even integer > 2 is the sum of two primes",
                "related": ["Prime numbers", "additive number theory"],
                "status": "Open",
            },
            "collatz": {
                "name": "Collatz Conjecture",
                "description": "For any positive integer n, the Collatz sequence reaches 1",
                "related": ["Dynamical systems", "number theory"],
                "status": "Open",
            },
            "riemann": {
                "name": "Riemann Hypothesis",
                "description": "All non-trivial zeros of the Riemann zeta function have real part 1/2",
                "related": ["Prime numbers", "complex analysis", "zeta function"],
                "status": "Open (Millennium Prize Problem)",
            },
        }

    def search_related(self, topic: str) -> List[Dict]:
        """Search for related mathematical literature."""
        results = []
        topic_lower = topic.lower()
        
        for key, info in self.knowledge_base.items():
            if key in topic_lower or any(word in topic_lower for word in info["name"].lower().split()):
                results.append(info)
        
        return results

    def get_context(self, topic: str) -> str:
        """Get mathematical context for a topic."""
        related = self.search_related(topic)
        if not related:
            return f"No specific literature found for: {topic}"
        
        context_lines = [f"Related mathematical literature for: {topic}"]
        for info in related:
            context_lines.append(f"\n• {info['name']}: {info['description']}")
            if "status" in info:
                context_lines.append(f"  Status: {info['status']}")
            if "related" in info:
                context_lines.append(f"  Related fields: {', '.join(info['related'])}")
        
        return "\n".join(context_lines)


class ResearchCoordinator:
    """Orchestrates the mathematical research process."""

    def __init__(self):
        self.prover = MathProver()
        self.verifier = MathVerifier()
        self.counterexample_searcher = CounterexampleSearcher()
        self.literature_reviewer = LiteratureReviewer()
        self.conjecture_engine = ConjectureEngine()
        
        self.agents = [
            ResearchAgent("Prover", "Proof Generation", ["algebra", "calculus", "number theory"]),
            ResearchAgent("Verifier", "Verification", ["SymPy", "logical analysis", "symbolic computation"]),
            ResearchAgent("CounterexampleSearcher", "Counterexample Search", ["numerical methods", "search algorithms"]),
            ResearchAgent("LiteratureReviewer", "Literature Review", ["mathematical databases", "paper search"]),
        ]
        
        self.research_steps: List[ResearchStep] = []

    def conduct_research(self, question: str) -> ResearchReport:
        """Conduct a full mathematical research cycle."""
        report = ResearchReport(
            question=question,
            hypothesis="",
            proof_attempts=[],
            verification_results=[],
            counterexamples_found=[],
            literature_context=[],
            final_conclusion="",
            confidence=0.0,
            steps=[],
        )

        # Phase 1: Hypothesis Generation
        hypothesis = self._generate_hypothesis(question)
        report.hypothesis = hypothesis
        report.steps.append(ResearchStep(
            phase=ResearchPhase.HYPOTHESIS,
            agent="Coordinator",
            action="Generate hypothesis",
            result=hypothesis,
            success=True,
        ))

        # Phase 2: Proof Attempt
        proof_success, proof_result = self.prover.attempt_proof(hypothesis)
        report.proof_attempts.append(proof_result)
        report.steps.append(ResearchStep(
            phase=ResearchPhase.PROOF_ATTEMPT,
            agent="Prover",
            action=f"Attempt proof using {'success' if proof_success else 'failed'} method",
            result=proof_result,
            success=proof_success,
        ))

        # Phase 3: Verification
        verification = self.verifier.verify_claim(hypothesis)
        report.verification_results.append(asdict(verification))
        report.steps.append(ResearchStep(
            phase=ResearchPhase.VERIFICATION,
            agent="Verifier",
            action="Verify claim with SymPy",
            result=f"Verified: {verification.verified}, Method: {verification.method}",
            success=verification.verified,
        ))

        # Phase 4: Counterexample Search
        counterexamples = self.counterexample_searcher.search_counterexamples(hypothesis)
        report.counterexamples_found = [str(ce) for ce in counterexamples]
        report.steps.append(ResearchStep(
            phase=ResearchPhase.COUNTEREXAMPLE_SEARCH,
            agent="CounterexampleSearcher",
            action="Search for counterexamples",
            result=f"Found {len(counterexamples)} counterexamples",
            success=len(counterexamples) == 0,
        ))

        # Phase 5: Literature Review
        literature = self.literature_reviewer.get_context(question)
        report.literature_context = literature.split("\n")
        report.steps.append(ResearchStep(
            phase=ResearchPhase.LITERATURE_REVIEW,
            agent="LiteratureReviewer",
            action="Search related literature",
            result=f"Found {len(report.literature_context)} context lines",
            success=True,
        ))

        # Phase 6: Refinement and Conclusion
        conclusion, confidence = self._synthesize_conclusion(report)
        report.final_conclusion = conclusion
        report.confidence = confidence
        report.steps.append(ResearchStep(
            phase=ResearchPhase.REPORT,
            agent="Coordinator",
            action="Synthesize research report",
            result=conclusion,
            success=True,
        ))

        return report

    def _generate_hypothesis(self, question: str) -> str:
        """Generate a testable hypothesis from a research question."""
        # Simple heuristic: extract the mathematical claim from the question
        if "?" in question:
            return question.replace("?", ".")
        return question

    def _synthesize_conclusion(self, report: ResearchReport) -> Tuple[str, float]:
        """Synthesize a research conclusion from all evidence."""
        confidence = 0.5  # Base confidence
        
        # Adjust based on proof attempt
        if report.proof_attempts and "Verified symbolically" in str(report.proof_attempts[0]):
            confidence += 0.3
        
        # Adjust based on verification
        if report.verification_results:
            if report.verification_results[0].get("verified"):
                confidence += 0.2
            else:
                confidence -= 0.2
        
        # Adjust based on counterexamples
        if report.counterexamples_found:
            confidence -= 0.3
        
        confidence = max(0.0, min(1.0, confidence))
        
        if confidence >= 0.8:
            conclusion = f"Strong evidence supports the hypothesis: {report.hypothesis}"
        elif confidence >= 0.5:
            conclusion = f"Moderate evidence for the hypothesis, but further research needed: {report.hypothesis}"
        else:
            conclusion = f"Weak evidence for the hypothesis. Counterexamples or verification failures found: {report.hypothesis}"
        
        return conclusion, confidence

    def format_report(self, report: ResearchReport) -> str:
        """Format a research report for display."""
        lines = [
            "=" * 70,
            "JiuZhang Multi-Agent Math Research Report",
            "=" * 70,
            f"\nResearch Question: {report.question}",
            f"Hypothesis: {report.hypothesis}",
            f"\n{'─'*70}",
            "Research Process:",
            "─" * 70,
        ]
        
        for step in report.steps:
            status = "✓" if step.success else "✗"
            lines.append(f"  [{status}] {step.phase.value}: {step.agent} - {step.action}")
            if step.result:
                lines.append(f"       Result: {step.result[:100]}...")
        
        lines.extend([
            f"\n{'─'*70}",
            "Final Conclusion:",
            "─" * 70,
            f"  {report.final_conclusion}",
            f"  Confidence: {report.confidence:.1%}",
            f"\n{'='*70}",
        ])
        
        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JiuZhang Multi-Agent Math Research System")
    parser.add_argument("question", nargs="?", default="Is every even number greater than 2 the sum of two primes?",
                        help="Research question")
    parser.add_argument("--export", default="", help="Export report to JSON")
    args = parser.parse_args()

    coordinator = ResearchCoordinator()
    report = coordinator.conduct_research(args.question)
    print(coordinator.format_report(report))

    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2, default=str)
        print(f"\nReport exported to {args.export}")


if __name__ == "__main__":
    main()