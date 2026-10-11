"""Proof Assistant for JiuZhang.

Helps verify and construct mathematical proofs using symbolic computation and AI.
"""

from typing import Optional, List
from sympy import symbols, simplify, expand, factor, solve, Eq, latex
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent


class ProofStep:
    """A single step in a mathematical proof."""

    def __init__(
        self, statement: str, justification: str, step_type: str = "assertion"
    ):
        self.statement = statement
        self.justification = justification
        self.step_type = step_type  # assertion, derivation, lemma, theorem, qed

    def __repr__(self):
        return f"ProofStep({self.step_type}: {self.statement[:50]}...)"


class Proof:
    """A mathematical proof consisting of steps."""

    def __init__(self, theorem: str, context: str = ""):
        self.theorem = theorem
        self.context = context
        self.steps: List[ProofStep] = []
        self.verified = False

    def add_step(
        self, statement: str, justification: str, step_type: str = "assertion"
    ):
        """Add a step to the proof."""
        step = ProofStep(statement, justification, step_type)
        self.steps.append(step)
        return step

    def add_derivation(self, from_step: int, to_step: int, derivation: str):
        """Add a derivation step."""
        step = ProofStep(derivation, f"From steps {from_step}-{to_step}", "derivation")
        self.steps.append(step)
        return step

    def add_lemma(self, statement: str, proof_text: str):
        """Add a lemma to the proof."""
        step = ProofStep(statement, proof_text, "lemma")
        self.steps.append(step)
        return step

    def add_qed(self):
        """Add the QED step."""
        step = ProofStep("Q.E.D.", "By the above steps", "qed")
        self.steps.append(step)
        return step

    def to_latex(self) -> str:
        """Convert proof to LaTeX."""
        latex_str = "\\begin{proof}\n"
        latex_str += f"\\textbf{{Theorem:}} {self.theorem}\n\n"

        for i, step in enumerate(self.steps, 1):
            if step.step_type == "qed":
                latex_str += "\\end{proof}\n"
            elif step.step_type == "lemma":
                latex_str += f"\\begin{{lemma}}\n{step.statement}\n\\end{{lemma}}\n\n"
                latex_str += (
                    f"\\begin{{proof}}\n{step.justification}\n\\end{{proof}}\n\n"
                )
            else:
                latex_str += (
                    f"\\item[{i}.] {step.statement} \\hfill ({step.justification})\n\n"
                )

        return latex_str

    def to_markdown(self) -> str:
        """Convert proof to Markdown."""
        md = f"**Theorem:** {self.theorem}\n\n"

        for i, step in enumerate(self.steps, 1):
            if step.step_type == "qed":
                md += f"**Q.E.D.**\n\n"
            elif step.step_type == "lemma":
                md += f"### Lemma {i}\n\n{step.statement}\n\n"
                md += f"*Proof:* {step.justification}\n\n"
            else:
                md += f"{i}. {step.statement} *({step.justification})*\n\n"

        return md


class ProofAssistant:
    """Assists in constructing and verifying mathematical proofs."""

    def __init__(self):
        self._proofs = {}

    def create_proof(self, theorem: str, context: str = "") -> Proof:
        """Create a new proof."""
        proof = Proof(theorem, context)
        self._proofs[theorem] = proof
        return proof

    def verify_algebraic_identity(self, lhs, rhs, variables: list) -> dict:
        """Verify an algebraic identity.

        Args:
            lhs: Left-hand side (sympy expression)
            rhs: Right-hand side (sympy expression)
            variables: List of variables

        Returns:
            Verification result
        """
        diff = simplify(lhs - rhs)
        is_verified = diff == 0

        proof = self.create_proof(f"{latex(lhs)} = {latex(rhs)}")
        proof.add_step(f"Consider the difference: {latex(lhs)} - {latex(rhs)}", "Setup")
        proof.add_step(
            f"Simplify: {latex(simplify(lhs - rhs))}", "Algebraic simplification"
        )

        if is_verified:
            proof.add_step("The difference is zero", "Simplification result")
            proof.add_step(f"Therefore, {latex(lhs)} = {latex(rhs)}", "Conclusion")
        else:
            proof.add_step(
                f"The difference is {latex(diff)} ≠ 0", "Simplification result"
            )
            proof.add_step("The identity does NOT hold", "Counterexample found")

        proof.add_qed()
        proof.verified = is_verified

        return {"verified": is_verified, "difference": latex(diff), "proof": proof}

    def verify_inequality(
        self, lhs, rhs, variables: list, assumptions: str = ""
    ) -> dict:
        """Verify an inequality under assumptions.

        Args:
            lhs: Left-hand side
            rhs: Right-hand side
            variables: List of variables
            assumptions: Assumptions as string

        Returns:
            Verification result
        """
        import random

        # Numerical verification
        test_results = []
        for _ in range(50):
            try:
                subs = {v: random.uniform(0.1, 10) for v in variables}
                lhs_val = float(lhs.subs(subs))
                rhs_val = float(rhs.subs(subs))
                test_results.append(lhs_val >= rhs_val - 1e-10)
            except Exception:
                pass

        all_hold = all(test_results) if test_results else False

        proof = self.create_proof(f"{latex(lhs)} \\geq {latex(rhs)}")
        proof.add_step(
            f"Consider the inequality: {latex(lhs)} \\geq {latex(rhs)}", "Statement"
        )
        if assumptions:
            proof.add_step(f"Assumptions: {assumptions}", "Given")

        proof.add_step(
            f"Tested {len(test_results)} random points", "Numerical verification"
        )
        if all_hold:
            proof.add_step(
                "All test points satisfy the inequality", "Numerical evidence"
            )
        else:
            failed = sum(1 for r in test_results if not r)
            proof.add_step(
                f"{failed} test points violate the inequality", "Counterexample found"
            )

        proof.add_qed()
        proof.verified = all_hold

        return {
            "verified": all_hold,
            "tests_passed": sum(test_results),
            "tests_total": len(test_results),
            "proof": proof,
        }

    def generate_proof_template(self, theorem_type: str, topic: str) -> Proof:
        """Generate a proof template for common theorem types.

        Args:
            theorem_type: Type of theorem (direct, contradiction, induction, contrapositive)
            topic: Topic description

        Returns:
            Proof template
        """
        proof = self.create_proof(f"Theorem about {topic}")

        if theorem_type == "direct":
            proof.add_step("Assume the hypothesis holds", "Given")
            proof.add_step(
                "Apply relevant definitions and theorems", "Direct reasoning"
            )
            proof.add_step("Derive the conclusion", "Logical deduction")
        elif theorem_type == "contradiction":
            proof.add_step("Assume the negation of the conclusion", "For contradiction")
            proof.add_step("Derive a contradiction", "Logical deduction")
            proof.add_step(
                "Therefore, the original statement must be true",
                "Contradiction principle",
            )
        elif theorem_type == "induction":
            proof.add_step("Base case: Verify for n=1 (or smallest value)", "Base case")
            proof.add_step(
                "Inductive hypothesis: Assume true for n=k", "Inductive hypothesis"
            )
            proof.add_step("Inductive step: Prove for n=k+1", "Inductive step")
            proof.add_step(
                "By mathematical induction, the statement holds for all n", "Conclusion"
            )
        elif theorem_type == "contrapositive":
            proof.add_step(
                "State the contrapositive: If not Q, then not P", "Contrapositive"
            )
            proof.add_step("Prove the contrapositive", "Direct proof of contrapositive")
            proof.add_step(
                "Therefore, the original implication holds", "Logical equivalence"
            )

        proof.add_qed()
        return proof

    def get_proof(self, theorem: str) -> Optional[Proof]:
        """Get a stored proof."""
        return self._proofs.get(theorem)

    def list_proofs(self) -> list:
        """List all stored proofs."""
        return list(self._proofs.keys())
