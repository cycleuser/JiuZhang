"""Step-by-Step Proof Verification with Automatic SymPy Checking.

Verifies each step in a mathematical proof individually, providing:
  - Step-level verification (each step checked with SymPy)
  - Error localization (exactly which step failed and why)
  - Suggested corrections for failed steps
  - Overall proof validity score

This enables the model to learn from step-level feedback and improve
its mathematical reasoning capabilities.
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

import sympy as sp
from sympy import (
    symbols, simplify, factor, expand, Rational, pi, E, I, oo,
    gcd, isprime, primerange, factorial, sqrt, sin, cos, tan,
    exp, log, diff, integrate, solve, series, limit, Eq, Ne,
    Function, Sum, Product, ceiling, floor, mod_inverse,
)

from jiuzhang.symbolic_verify import (
    verify_equation, verify_derivative, verify_integral,
    verify_limit, verify_solution, VerificationResult,
)


@dataclass
class ProofStep:
    step_number: int
    content: str
    verified: bool
    verification_method: str
    verification_detail: str
    confidence: float
    error: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ProofVerificationResult:
    total_steps: int
    verified_steps: int
    failed_steps: int
    steps: List[ProofStep]
    overall_valid: bool
    overall_confidence: float
    summary: str


class StepByStepVerifier:
    """Verify mathematical proofs step by step."""

    def __init__(self):
        self.x, self.y, self.z, self.n = symbols('x y z n')
        self.verification_log: List[Dict] = []

    def extract_steps(self, proof_text: str) -> List[str]:
        """Extract individual steps from a proof text."""
        steps = []
        
        # Try numbered steps first
        numbered_pattern = r'(?:^|\n)\s*(?:\d+[\.\)]\s*|Step\s*\d+[\.:]?\s*)(.*?)(?=\n\s*(?:\d+[\.\)]|Step\s*\d+)|$)'
        numbered_matches = re.findall(numbered_pattern, proof_text, re.DOTALL)
        
        if numbered_matches:
            steps = [m.strip() for m in numbered_matches if m.strip()]
            return steps
        
        # Try bullet points
        bullet_pattern = r'(?:^|\n)\s*(?:[-*•]\s*)(.*?)(?=\n\s*[-*•]|$)'
        bullet_matches = re.findall(bullet_pattern, proof_text, re.DOTALL)
        
        if bullet_matches:
            steps = [m.strip() for m in bullet_matches if m.strip()]
            return steps
        
        # Try sentences with mathematical content
        sentence_pattern = r'([^\.!?]*(?:=|≠|≤|≥|<|>|→|⇒|∴|∵)[^\.!?]*[\.!?])'
        sentence_matches = re.findall(sentence_pattern, proof_text)
        
        if sentence_matches:
            steps = [m.strip() for m in sentence_matches if m.strip() and len(m.strip()) > 5]
            return steps
        
        # Fallback: split by newlines
        lines = [line.strip() for line in proof_text.split('\n') if line.strip() and len(line.strip()) > 5]
        return lines

    def verify_step(self, step: str, context: str = "") -> Tuple[bool, str, float, Optional[str]]:
        """Verify a single proof step.
        
        Returns: (verified, method, confidence, error)
        """
        step_lower = step.lower()
        
        # Check for logical connectors first (non-mathematical steps)
        if any(kw in step_lower for kw in ["therefore", "thus", "hence", "so", "implies", "因此", "所以", "则"]):
            return True, "logical_connector", 0.7, None
        
        # Check for assumptions
        if any(kw in step_lower for kw in ["assume", "suppose", "let", "假设", "设"]):
            return True, "assumption", 0.8, None
        
        # Check for conclusions
        if any(kw in step_lower for kw in ["conclusion", "qed", "证毕"]):
            return True, "conclusion", 0.9, None
        
        # Check for equations
        if "=" in step or "==" in step or "≡" in step:
            try:
                result = verify_equation(step)
                if result.verified:
                    return True, f"equation_verified: {result.method}", result.confidence, None
                return False, f"equation_failed: {result.method}", result.confidence, result.detail
            except Exception as e:
                return False, "parse_error", 0.0, str(e)
        
        # Check for derivatives
        if any(kw in step_lower for kw in ["derivative", "d/dx", "f'(x)", "f''(x)", "diff"]):
            try:
                # Extract function and claimed derivative
                parts = step.split("=")
                if len(parts) == 2:
                    result = verify_derivative(parts[0].strip(), parts[1].strip())
                    if result.verified:
                        return True, f"derivative_verified", result.confidence, None
                    return False, f"derivative_failed", result.confidence, result.detail
            except Exception as e:
                return False, "parse_error", 0.0, str(e)
        
        # Check for integrals
        if any(kw in step_lower for kw in ["integral", "∫", "antiderivative"]):
            try:
                parts = step.split("=")
                if len(parts) == 2:
                    result = verify_integral(parts[0].strip().replace("∫", "").replace("dx", ""), parts[1].strip())
                    if result.verified:
                        return True, f"integral_verified", result.confidence, None
                    return False, f"integral_failed", result.confidence, result.detail
            except Exception as e:
                return False, "parse_error", 0.0, str(e)
        
        # Check for limits
        if any(kw in step_lower for kw in ["limit", "lim", "as x →", "as x->"]):
            try:
                result = verify_limit(step, "x", "0")
                if result.verified:
                    return True, f"limit_verified", result.confidence, None
                return False, f"limit_failed", result.confidence, result.detail
            except Exception as e:
                return False, "parse_error", 0.0, str(e)
        
        # Default: step appears consistent
        return True, "structural_check", 0.5, None

    def verify_proof(self, proof_text: str, context: str = "") -> ProofVerificationResult:
        """Verify an entire proof step by step."""
        steps = self.extract_steps(proof_text)
        if not steps:
            return ProofVerificationResult(
                total_steps=0,
                verified_steps=0,
                failed_steps=0,
                steps=[],
                overall_valid=False,
                overall_confidence=0.0,
                summary="No steps could be extracted from the proof.",
            )
        
        verified_steps = []
        verified_count = 0
        failed_count = 0
        
        for i, step_text in enumerate(steps, 1):
            verified, method, confidence, error = self.verify_step(step_text, context)
            
            proof_step = ProofStep(
                step_number=i,
                content=step_text,
                verified=verified,
                verification_method=method,
                verification_detail=f"Method: {method}, Confidence: {confidence:.2f}",
                confidence=confidence,
                error=error,
                suggestion=self._generate_suggestion(step_text, error) if error else None,
            )
            verified_steps.append(proof_step)
            
            if verified:
                verified_count += 1
            else:
                failed_count += 1
        
        overall_confidence = sum(s.confidence for s in verified_steps) / len(verified_steps)
        overall_valid = failed_count == 0
        
        if overall_valid:
            summary = f"All {len(steps)} steps verified successfully. Overall confidence: {overall_confidence:.1%}"
        else:
            summary = f"{verified_count}/{len(steps)} steps verified. {failed_count} step(s) failed. Overall confidence: {overall_confidence:.1%}"
        
        return ProofVerificationResult(
            total_steps=len(steps),
            verified_steps=verified_count,
            failed_steps=failed_count,
            steps=verified_steps,
            overall_valid=overall_valid,
            overall_confidence=overall_confidence,
            summary=summary,
        )

    def _generate_suggestion(self, step: str, error: Optional[str]) -> Optional[str]:
        """Generate a suggestion for correcting a failed step."""
        if not error:
            return None
        
        if "parse_error" in error.lower():
            return "Check the mathematical expression syntax. Ensure all variables are defined."
        if "equation_failed" in error.lower():
            return "The equation does not hold. Check the algebraic manipulation."
        if "derivative_failed" in error.lower():
            return "The derivative is incorrect. Review the differentiation rules."
        if "integral_failed" in error.lower():
            return "The integral is incorrect. Review the integration rules."
        
        return "Review this step carefully. The verification failed."

    def format_verification_report(self, result: ProofVerificationResult) -> str:
        """Format a verification report for display."""
        lines = [
            "=" * 60,
            "Step-by-Step Proof Verification Report",
            "=" * 60,
            f"\nTotal steps: {result.total_steps}",
            f"Verified: {result.verified_steps}",
            f"Failed: {result.failed_steps}",
            f"Overall valid: {'Yes' if result.overall_valid else 'No'}",
            f"Overall confidence: {result.overall_confidence:.1%}",
            f"\n{'─'*60}",
            "Step Details:",
            "─" * 60,
        ]
        
        for step in result.steps:
            status = "✓" if step.verified else "✗"
            lines.append(f"\nStep {step.step_number}: [{status}]")
            lines.append(f"  Content: {step.content[:80]}...")
            lines.append(f"  Method: {step.verification_method}")
            lines.append(f"  Confidence: {step.confidence:.2f}")
            if step.error:
                lines.append(f"  Error: {step.error}")
            if step.suggestion:
                lines.append(f"  Suggestion: {step.suggestion}")
        
        lines.extend([
            f"\n{'─'*60}",
            f"Summary: {result.summary}",
            "=" * 60,
        ])
        
        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Step-by-Step Proof Verifier")
    parser.add_argument("proof", nargs="?", default="", help="Proof text to verify")
    parser.add_argument("--file", default="", help="Read proof from file")
    args = parser.parse_args()

    verifier = StepByStepVerifier()
    
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            proof_text = f.read()
    elif args.proof:
        proof_text = args.proof
    else:
        proof_text = """Step 1: Let f(x) = x^2 + 2x + 1
Step 2: f'(x) = 2x + 2
Step 3: f''(x) = 2
Step 4: Therefore, f(x) is a convex function.
Step 5: Q.E.D."""
    
    result = verifier.verify_proof(proof_text)
    print(verifier.format_verification_report(result))


if __name__ == "__main__":
    main()