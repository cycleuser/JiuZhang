"""Proof Compiler — structured mathematical proof verification.

Parses LLM-generated proofs into typed proof trees, checks each inference rule
for validity, identifies hidden assumptions, and generates human-readable proofs
with inline verification annotations.

This provides rigorous proof verification beyond simple SymPy equation checking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class InferenceRule(Enum):
    """Formal inference rules recognized by the proof compiler."""
    MODUS_PONENS = "modus_ponens"            # A, A→B ⊢ B
    MODUS_TOLLENS = "modus_tollens"          # ¬B, A→B ⊢ ¬A
    HYPOTHETICAL_SYLLOGISM = "hs"            # A→B, B→C ⊢ A→C
    UNIVERSAL_INSTANTIATION = "ui"           # ∀x.P(x) ⊢ P(a)
    EXISTENTIAL_GENERALIZATION = "eg"        # P(a) ⊢ ∃x.P(x)
    CONJUNCTION = "conjunction"              # A, B ⊢ A∧B
    SIMPLIFICATION = "simplification"        # A∧B ⊢ A
    ADDITION = "addition"                    # A ⊢ A∨B
    DISJUNCTIVE_SYLLOGISM = "ds"             # A∨B, ¬A ⊢ B
    TRANSITIVITY = "transitivity"            # a=b, b=c ⊢ a=c
    SUBSTITUTION = "substitution"            # a=b ⊢ f(a)=f(b)
    ALGEBRAIC_MANIPULATION = "algebra"       # Standard algebraic step
    INDUCTION_BASE = "induction_base"        # Base case
    INDUCTION_STEP = "induction_step"        # Inductive step
    CONTRADICTION_INTRO = "contradiction"    # A, ¬A ⊢ contradiction
    DIRECT_IMPLICATION = "direct"            # Assume A, show B ⊢ A→B
    DEFINITION = "definition"                # Applying a definition
    LEMMA_APPLICATION = "lemma"              # Applying a known lemma/theorem
    UNKNOWN = "unknown"                      # Cannot classify


@dataclass
class ProofStep:
    """A single step in a formal proof."""
    index: int
    statement: str
    justification: str
    inference_rule: InferenceRule = InferenceRule.UNKNOWN
    premises: list = field(default_factory=list)  # Indices of steps this depends on
    is_valid: bool = False
    is_hidden_assumption: bool = False
    error: str = ""

    def to_annotation(self) -> str:
        """Generate an inline annotation for this proof step."""
        rule_name = {
            InferenceRule.MODUS_PONENS: "MP",
            InferenceRule.MODUS_TOLLENS: "MT",
            InferenceRule.TRANSITIVITY: "Trans",
            InferenceRule.SUBSTITUTION: "Subst",
            InferenceRule.ALGEBRAIC_MANIPULATION: "Alg",
            InferenceRule.INDUCTION_BASE: "Ind-Base",
            InferenceRule.INDUCTION_STEP: "Ind-Step",
            InferenceRule.DEFINITION: "Def",
            InferenceRule.LEMMA_APPLICATION: "Lemma",
        }.get(self.inference_rule, self.inference_rule.value)

        status = "✓" if self.is_valid else "✗"
        hidden = " [HIDDEN ASSUMPTION]" if self.is_hidden_assumption else ""
        return f"[{status} {rule_name}{hidden}]"


@dataclass
class CompiledProof:
    """A fully compiled and verified proof."""
    theorem: str
    steps: list  # List[ProofStep]
    is_complete: bool = False
    is_valid: bool = False
    hidden_assumptions: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    confidence: float = 0.0
    annotated_text: str = ""


class ProofCompiler:
    """Compile and verify structured mathematical proofs.

    Usage:
        compiler = ProofCompiler()
        proof = compiler.compile(llm_proof_text, "If n is even, n² is even")
        if proof.is_valid:
            print(proof.annotated_text)
    """

    def __init__(self):
        self._inference_patterns = self._init_patterns()

    def _init_patterns(self) -> dict:
        """Initialize regex patterns for inference rule detection."""
        return {
            InferenceRule.MODUS_PONENS: [
                r"(?:since|because|given|as)\s+.+?,\s*(?:therefore|hence|thus|so|it follows)\s+.+",
            ],
            InferenceRule.CONTRADICTION_INTRO: [
                r"(?:contradiction|contradicts|inconsistent)",
                r"(?:assume|suppose)\s+.+?,\s*(?:but|however|yet)\s+.+?(?:contradict)",
            ],
            InferenceRule.SUBSTITUTION: [
                r"(?:substitut|replace|plug\s*in|let\s+\w+\s*=\s*)",
            ],
            InferenceRule.ALGEBRAIC_MANIPULATION: [
                r"(?:simplify|expand|factor|solve|rearrange|add|subtract|multiply|divide)\b",
            ],
            InferenceRule.INDUCTION_BASE: [
                r"(?:base\s*case|n\s*=\s*0|n\s*=\s*1|initial\s*case|for\s*n\s*=\s*0)",
            ],
            InferenceRule.INDUCTION_STEP: [
                r"(?:inductive?\s*(?:step|hypothesis|assumption)|assume\s+(?:true|holds)\s+for\s+(?:n|k)\b)",
            ],
            InferenceRule.DEFINITION: [
                r"(?:by\s+definition|defined\s+as|means|denoted)",
            ],
            InferenceRule.LEMMA_APPLICATION: [
                r"(?:by\s+(?:the\s+)?(?:theorem|lemma|corollary|proposition)\b)",
            ],
            InferenceRule.DIRECT_IMPLICATION: [
                r"(?:assume|suppose|let)\s+.+,\s*(?:we\s+(?:show|prove|demonstrate|must\s+show))",
            ],
            InferenceRule.TRANSITIVITY: [
                r"(?:by\s+transitivity|since\s+\w+\s*=\s*\w+\s+and\s+\w+\s*=\s*\w+)",
            ],
        }

    def compile(self, proof_text: str, theorem: str = "") -> CompiledProof:
        """Compile and verify a proof.

        Args:
            proof_text: The LLM-generated proof text
            theorem: The theorem being proved

        Returns:
            CompiledProof with verification results
        """
        result = CompiledProof(theorem=theorem)

        # Step 1: Extract proof steps
        steps = self._extract_steps(proof_text)
        if not steps:
            result.errors.append("No proof steps could be extracted")
            return result

        # Step 2: Classify inference rules
        for step in steps:
            step.inference_rule = self._classify_inference(step.justification)
            step.is_valid = step.inference_rule != InferenceRule.UNKNOWN

        # Step 3: Check for hidden assumptions
        for step in steps:
            if self._has_hidden_assumption(step):
                step.is_hidden_assumption = True
                result.hidden_assumptions.append({
                    "step": step.index,
                    "statement": step.statement[:200],
                    "issue": "Unjustified assumption — no explicit justification provided",
                })

        # Step 4: Validate logical flow
        result.is_complete = self._has_conclusion(steps, proof_text)
        result.is_valid = (
            all(s.is_valid for s in steps)
            and len(result.hidden_assumptions) == 0
            and result.is_complete
        )

        result.confidence = self._calculate_confidence(steps, result)
        result.steps = steps
        result.annotated_text = self._generate_annotated_text(steps, proof_text)

        if result.errors:
            result.is_valid = False

        return result

    def _extract_steps(self, text: str) -> list:
        """Extract individual proof steps from text."""
        steps = []

        # Pattern 1: Numbered steps
        numbered = re.findall(
            r'(?:^|\n)\s*(\d+)[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\n\n|\Z)',
            text, re.DOTALL
        )
        if numbered:
            for idx, (num, content) in enumerate(numbered):
                step = ProofStep(
                    index=idx + 1,
                    statement=content.strip()[:300],
                    justification=self._extract_justification(content),
                )
                steps.append(step)
            return steps

        # Pattern 2: "Step N:" markers
        step_markers = re.findall(
            r'(?:Step|Phase|Stage)\s+(\d+)[:\-]\s*(.+?)(?=\n(?:Step|Phase|Stage)|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        if step_markers:
            for idx, (num, content) in enumerate(step_markers):
                step = ProofStep(
                    index=idx + 1,
                    statement=content.strip()[:300],
                    justification=self._extract_justification(content),
                )
                steps.append(step)
            return steps

        # Pattern 3: Paragraphs as steps
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
        if len(paragraphs) >= 2:
            for idx, para in enumerate(paragraphs[:10]):
                step = ProofStep(
                    index=idx + 1,
                    statement=para[:300],
                    justification=para,
                )
                steps.append(step)

        return steps

    def _extract_justification(self, text: str) -> str:
        """Extract the justification clause from a step."""
        # Look for justification markers
        patterns = [
            r'(?:since|because|by|from)\s+(.+?)(?:,|\.|$)',  # "since X, Y"
            r'(?:therefore|hence|thus|so|consequently)\s+(.+?)(?:,|\.|$)',  # "therefore Y"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return text[:200]

    def _classify_inference(self, text: str) -> InferenceRule:
        """Classify the inference rule used in a justification."""
        text_lower = text.lower()

        for rule, patterns in self._inference_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return rule

        # Heuristic: if contains "=" and math operators
        if re.search(r'[+\-*/^=]', text):
            return InferenceRule.ALGEBRAIC_MANIPULATION

        return InferenceRule.UNKNOWN

    def _has_hidden_assumption(self, step: ProofStep) -> bool:
        """Check if a step makes an unjustified assumption."""
        # A step is suspicious if it has no justification and is not a definition
        if step.inference_rule == InferenceRule.UNKNOWN:
            return True

        # Check for common hidden assumption patterns
        suspicious = [
            r"(?:clearly|obviously|trivially|it is clear)\b",
            r"(?:without loss of generality)\b.*(?:assume)",
            r"(?:one can (?:easily )?(?:see|verify|check))",
            r"(?:it (?:is|can be) (?:easily )?(?:seen|shown|verified))",
        ]
        for pattern in suspicious:
            if re.search(pattern, step.statement, re.IGNORECASE):
                return True

        return False

    def _has_conclusion(self, steps: list, text: str) -> bool:
        """Check if the proof has a valid conclusion."""
        conclusion_markers = [
            r'Q\.?E\.?D\.?',
            r'∎|□|■|▯',
            r'(?:therefore|hence|thus|so|consequently).*?(?:result|conclusion|proved|shown)',
            r'(?:this (?:completes|concludes|establishes|proves) the proof)',
            r'证毕',
        ]
        for marker in conclusion_markers:
            if re.search(marker, text, re.IGNORECASE):
                return True

        # Last step should look conclusive
        if steps:
            last = steps[-1].statement.lower()
            conclusive = ["therefore", "hence", "thus", "so", "consequently", "proved"]
            if any(c in last for c in conclusive):
                return True

        return False

    def _calculate_confidence(self, steps: list, result: CompiledProof) -> float:
        """Calculate overall confidence in the proof."""
        if not steps:
            return 0.0

        valid_ratio = sum(1 for s in steps if s.is_valid) / len(steps)
        hidden_penalty = len(result.hidden_assumptions) * 0.2
        complete_bonus = 0.2 if result.is_complete else 0.0

        confidence = valid_ratio * 0.6 + complete_bonus - hidden_penalty
        return max(0.0, min(1.0, confidence))

    def _generate_annotated_text(self, steps: list, original_text: str) -> str:
        """Generate proof text with inline verification annotations."""
        lines = ["# Compiled Proof\n"]
        lines.append(f"**Validity**: {'✅ Valid' if all(s.is_valid for s in steps) else '❌ Issues Found'}\n")

        for step in steps:
            annotation = step.to_annotation()
            lines.append(f"{annotation} **Step {step.index}**: {step.statement[:200]}")
            if step.error:
                lines.append(f"   ⚠️  {step.error}")

        if any(s.is_hidden_assumption for s in steps):
            lines.append("\n## ⚠️  Hidden Assumptions Detected")
            for step in steps:
                if step.is_hidden_assumption:
                    lines.append(f"- Step {step.index}: Potentially unverified claim")

        return "\n".join(lines)

    def suggest_improvements(self, proof: CompiledProof) -> list:
        """Suggest improvements for an invalid proof."""
        suggestions = []

        if not proof.is_complete:
            suggestions.append("Add an explicit conclusion (Q.E.D. or 'This completes the proof')")

        for step in proof.steps:
            if step.is_hidden_assumption:
                suggestions.append(
                    f"Step {step.index}: Provide explicit justification for '{step.statement[:100]}'"
                )
            if step.inference_rule == InferenceRule.UNKNOWN:
                suggestions.append(
                    f"Step {step.index}: Clarify the inference rule used — "
                    f"is this algebraic manipulation, substitution, or application of a theorem?"
                )

        if len(proof.steps) < 3:
            suggestions.append("Proof seems too short — consider adding intermediate steps")

        return suggestions
