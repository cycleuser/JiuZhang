"""Hybrid Reasoning Engine.

Combines symbolic computation (SymPy) with LLM reasoning for
comprehensive mathematical problem solving.

Architecture:
1. Problem Analysis → classify and decompose
2. Symbolic Computation → exact calculations where possible
3. LLM Reasoning → conceptual understanding and explanation
4. Cross-Verification → check LLM output against symbolic results
5. Synthesis → combine into coherent solution
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import time

from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.core.config import Config
from jiuzhang.solver.method_registry import MethodRegistry
from jiuzhang.solver.problem_classifier import ProblemClassifier, ProblemType
from jiuzhang.solver.pipeline import SolverPipeline, SolveResult
from jiuzhang.symbolic_verify import verify_equation, verify_derivative, verify_integral


@dataclass
class ReasoningResult:
    """Complete reasoning result."""
    success: bool
    problem: str
    analysis: str = ""
    symbolic_result: Optional[SolveResult] = None
    llm_result: str = ""
    synthesized_solution: str = ""
    verification_passed: bool = False
    verification_details: str = ""
    confidence: float = 0.0
    methods_used: list = field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[str] = None


class HybridReasoningEngine:
    """Hybrid symbolic + LLM reasoning engine.

    Uses symbolic computation for exact math and LLM for
    conceptual understanding, then cross-verifies results.
    """

    def __init__(self, config: Optional[Config] = None,
                 method_registry: Optional[MethodRegistry] = None):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)
        self.registry = method_registry or MethodRegistry()
        self.classifier = ProblemClassifier(self.registry)
        self.solver = SolverPipeline(self.registry, self.classifier)

    def reason(self, problem: str, language: str = "zh",
               mode: str = "full") -> ReasoningResult:
        """Perform hybrid reasoning on a problem.

        Args:
            problem: The problem statement
            language: Output language
            mode: "symbolic" (exact only), "llm" (reasoning only), "full" (both)

        Returns:
            ReasoningResult with complete analysis
        """
        start_time = time.time()
        result = ReasoningResult(success=False, problem=problem)

        try:
            # Step 1: Analyze the problem
            classification = self.classifier.classify(problem, language)
            result.analysis = self._generate_analysis(classification, language)
            result.methods_used = [m.id for m in classification.suggested_methods]

            # Step 2: Symbolic computation
            if mode in ("symbolic", "full"):
                result.symbolic_result = self.solver.solve(problem, language)

            # Step 3: LLM reasoning
            if mode in ("llm", "full"):
                result.llm_result = self._llm_reasoning(problem, classification, language)

            # Step 4: Cross-verification
            if result.symbolic_result and result.llm_result:
                result.verification_passed, result.verification_details = \
                    self._cross_verify(result.symbolic_result, result.llm_result)

            # Step 5: Synthesize
            result.synthesized_solution = self._synthesize(result, language)
            result.confidence = self._calculate_confidence(result)
            result.success = True

        except Exception as e:
            result.error = str(e)

        result.execution_time = time.time() - start_time
        return result

    def _generate_analysis(self, classification: ProblemType, language: str) -> str:
        """Generate problem analysis."""
        if language == "zh":
            return (
                f"## 问题分析\n\n"
                f"**领域**: {classification.domain.value}\n"
                f"**类型**: {classification.problem_type.value}\n"
                f"**难度**: {'★' * classification.difficulty}/10\n"
                f"**关键词**: {', '.join(classification.keywords)}\n"
                f"**建议方法**: {', '.join(m.name_cn for m in classification.suggested_methods)}\n"
            )
        else:
            return (
                f"## Problem Analysis\n\n"
                f"**Domain**: {classification.domain.value}\n"
                f"**Type**: {classification.problem_type.value}\n"
                f"**Difficulty**: {'★' * classification.difficulty}/10\n"
                f"**Keywords**: {', '.join(classification.keywords)}\n"
                f"**Suggested methods**: {', '.join(m.name for m in classification.suggested_methods)}\n"
            )

    def _llm_reasoning(self, problem: str, classification: ProblemType,
                       language: str) -> str:
        """Get LLM reasoning for the problem."""
        if language == "zh":
            prompt = f"""请分析并解决以下数学问题：

问题：{problem}

领域：{classification.domain.value}
类型：{classification.problem_type.value}
难度：{classification.difficulty}/10

请提供：
1. 详细的解题思路
2. 每一步的推导过程
3. 最终答案
4. 答案的验证方法

要求：
- 使用严谨的数学语言
- 每一步都要有充分的解释
- 如果有多种解法，请都列出
- 最后验证答案的正确性"""
        else:
            prompt = f"""Please analyze and solve the following mathematical problem:

Problem: {problem}

Domain: {classification.domain.value}
Type: {classification.problem_type.value}
Difficulty: {classification.difficulty}/10

Please provide:
1. Detailed solution approach
2. Step-by-step derivation
3. Final answer
4. Verification method

Requirements:
- Use rigorous mathematical language
- Explain each step thoroughly
- List alternative solutions if available
- Verify the correctness of the answer"""

        messages = [{"role": "user", "content": prompt}]
        response = self.client.send_message(messages)
        return response.data if response.success else ""

    def _cross_verify(self, symbolic: SolveResult, llm_text: str) -> tuple:
        """Cross-verify symbolic and LLM results."""
        import re

        # Extract answers from LLM text
        llm_answers = re.findall(r"=\s*([0-9.]+)", llm_text)

        # Check against symbolic results
        if symbolic.final_answer:
            symbolic_str = str(symbolic.final_answer)
            symbolic_numbers = re.findall(r"([0-9.]+)", symbolic_str)

            matching = 0
            for llm_num in llm_answers:
                for sym_num in symbolic_numbers:
                    try:
                        if abs(float(llm_num) - float(sym_num)) < 1e-6:
                            matching += 1
                            break
                    except ValueError:
                        continue

            if llm_answers:
                accuracy = matching / len(llm_answers)
                passed = accuracy > 0.5
                detail = f"LLM与符号结果匹配度: {accuracy:.0%}"
                return passed, detail

        # Check if all symbolic steps verified
        if symbolic.all_verified:
            return True, "所有符号计算步骤已验证"

        return False, "无法验证"

    def _synthesize(self, result: ReasoningResult, language: str) -> str:
        """Synthesize symbolic and LLM results."""
        parts = []

        if language == "zh":
            parts.append(f"# 完整解答\n\n")
            parts.append(f"## 问题\n\n{result.problem}\n\n")
            parts.append(result.analysis)
            parts.append("\n---\n\n")

            if result.symbolic_result:
                parts.append("## 符号计算结果\n\n")
                parts.append(result.symbolic_result.explanation)
                parts.append("\n---\n\n")

            if result.llm_result:
                parts.append("## 推理过程\n\n")
                parts.append(result.llm_result)
                parts.append("\n---\n\n")

            if result.verification_passed:
                parts.append(f"## 验证\n\n✅ {result.verification_details}\n")
            elif result.verification_details:
                parts.append(f"## 验证\n\n⚠️ {result.verification_details}\n")
        else:
            parts.append(f"# Complete Solution\n\n")
            parts.append(f"## Problem\n\n{result.problem}\n\n")
            parts.append(result.analysis)
            parts.append("\n---\n\n")

            if result.symbolic_result:
                parts.append("## Symbolic Computation\n\n")
                parts.append(result.symbolic_result.explanation)
                parts.append("\n---\n\n")

            if result.llm_result:
                parts.append("## Reasoning Process\n\n")
                parts.append(result.llm_result)
                parts.append("\n---\n\n")

            if result.verification_passed:
                parts.append(f"## Verification\n\n✅ {result.verification_details}\n")
            elif result.verification_details:
                parts.append(f"## Verification\n\n⚠️ {result.verification_details}\n")

        return "\n".join(parts)

    def _calculate_confidence(self, result: ReasoningResult) -> float:
        """Calculate confidence in the reasoning result."""
        confidence = 0.5  # Base confidence

        # Symbolic verification boosts confidence
        if result.symbolic_result and result.symbolic_result.all_verified:
            confidence += 0.3

        # Cross-verification boosts confidence
        if result.verification_passed:
            confidence += 0.2

        # More methods used = higher confidence
        if len(result.methods_used) > 0:
            confidence += min(len(result.methods_used) * 0.05, 0.2)

        return min(confidence, 1.0)

    def solve_with_explanation(self, problem: str, language: str = "zh") -> ReasoningResult:
        """Solve a problem with full explanation."""
        return self.reason(problem, language, mode="full")

    def symbolic_only(self, problem: str, language: str = "zh") -> ReasoningResult:
        """Solve using only symbolic computation."""
        return self.reason(problem, language, mode="symbolic")

    def llm_only(self, problem: str, language: str = "zh") -> ReasoningResult:
        """Solve using only LLM reasoning."""
        return self.reason(problem, language, mode="llm")
