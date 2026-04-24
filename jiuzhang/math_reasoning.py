"""Mathematical Reasoning System for JiuZhang.

Enhanced mathematical reasoning capabilities with specialized prompting,
knowledge injection, symbolic computation integration, and code execution.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.core.config import Config
from jiuzhang.core.errors import ToolResult
from jiuzhang.math_prompts import get_math_prompt, MATH_KNOWLEDGE_BASE
from jiuzhang.math_config import get_optimal_math_config, MATHEMATICAL_PROMPTING_STRATEGIES
from jiuzhang.symbolic_verify import verify_equation, verify_llm_output
from jiuzhang.code_interpreter import CodeInterpreter, CodeExecutionResult


@dataclass
class MathReasoningResult:
    """Result of mathematical reasoning."""
    success: bool
    response: str
    steps: List[str]
    verification: str
    confidence: float
    symbolic_checks: List = None
    self_consistent: Optional[bool] = None
    error: Optional[str] = None


class MathReasoningEngine:
    """Enhanced mathematical reasoning engine with specialized prompting and code execution."""
    
    def __init__(self, client: MultiProviderClient, config: Config):
        self.client = client
        self.config = config
        self.math_config = get_optimal_math_config()
        self.code_interpreter = CodeInterpreter()

    def _send_math_message(self, prompt: str, task_type: str) -> ToolResult:
        """Send a message using math-optimized parameters."""
        params = self.math_config.get_reasoning_params(task_type)
        model = self.math_config.get_model_for_task(task_type)
        return self.client.send_message(
            [{"role": "user", "content": prompt}],
            model=model,
            max_tokens=params.get("max_tokens"),
            temperature=params.get("temperature"),
        )

    def prove_theorem(self, theorem: str, language: str = "zh") -> MathReasoningResult:
        prompt = get_math_prompt("theorem_proof", language, theorem=theorem)
        knowledge_context = self._get_relevant_knowledge("theorems", theorem)
        if knowledge_context:
            prompt = f"相关定理/Relevant theorems:\n{knowledge_context}\n\n{prompt}"
        if MATHEMATICAL_PROMPTING_STRATEGIES["chain_of_thought"]["enabled"]:
            prefix = MATHEMATICAL_PROMPTING_STRATEGIES["chain_of_thought"]["prefix"]
            prompt = f"{prefix}\n\n{prompt}"
        result = self._send_math_message(prompt, "theorem_proving")
        if not result.success:
            return MathReasoningResult(success=False, response="", steps=[], verification="", confidence=0.0, error=result.error)
        steps = self._extract_proof_steps(result.data)
        verification = self._verify_proof(result.data)
        confidence = self._calculate_confidence(result.data, verification)
        symbolic_checks = verify_llm_output(result.data)
        self_consistent = None
        if MATHEMATICAL_PROMPTING_STRATEGIES["self_consistency"]["enabled"]:
            consistent, _ = self.self_consistency_check(prompt, "theorem_proving")
            self_consistent = consistent
            if not consistent:
                confidence *= 0.7
        if symbolic_checks:
            failed = [c for c in symbolic_checks if not c.verified]
            if failed:
                confidence *= max(0.3, 1.0 - 0.15 * len(failed))
        return MathReasoningResult(
            success=True, response=result.data, steps=steps,
            verification=verification, confidence=round(confidence, 4),
            symbolic_checks=symbolic_checks, self_consistent=self_consistent,
        )

    def solve_problem(self, problem: str, language: str = "zh") -> MathReasoningResult:
        prompt = get_math_prompt("problem_solving", language, problem=problem)
        prompt = f"{self._get_problem_solving_tips()}\n\n{prompt}"
        if MATHEMATICAL_PROMPTING_STRATEGIES["chain_of_thought"]["enabled"]:
            prefix = MATHEMATICAL_PROMPTING_STRATEGIES["chain_of_thought"]["prefix"]
            prompt = f"{prefix}\n\n{prompt}"
        result = self._send_math_message(prompt, "problem_solving")
        if not result.success:
            return MathReasoningResult(success=False, response="", steps=[], verification="", confidence=0.0, error=result.error)
        steps = self._extract_solution_steps(result.data)
        verification = self._verify_solution(result.data)
        confidence = self._calculate_confidence(result.data, verification)
        symbolic_checks = verify_llm_output(result.data)
        self_consistent = None
        if MATHEMATICAL_PROMPTING_STRATEGIES["self_consistency"]["enabled"]:
            consistent, _ = self.self_consistency_check(prompt, "problem_solving")
            self_consistent = consistent
            if not consistent:
                confidence *= 0.7
        if symbolic_checks:
            failed = [c for c in symbolic_checks if not c.verified]
            if failed:
                confidence *= max(0.3, 1.0 - 0.15 * len(failed))
        return MathReasoningResult(
            success=True, response=result.data, steps=steps,
            verification=verification, confidence=round(confidence, 4),
            symbolic_checks=symbolic_checks, self_consistent=self_consistent,
        )

    def analyze_conjecture(self, conjecture: str, language: str = "zh") -> MathReasoningResult:
        prompt = get_math_prompt("conjecture_analysis", language, conjecture=conjecture)
        related_info = self._get_related_conjecture_info(conjecture)
        if related_info:
            prompt = f"相关背景/Background:\n{related_info}\n\n{prompt}"
        if MATHEMATICAL_PROMPTING_STRATEGIES["axiom_based"]["enabled"]:
            prefix = MATHEMATICAL_PROMPTING_STRATEGIES["axiom_based"]["prefix"]
            prompt = f"{prefix}\n\n{prompt}"
        result = self._send_math_message(prompt, "conjecture_analysis")
        if not result.success:
            return MathReasoningResult(success=False, response="", steps=[], verification="", confidence=0.0, error=result.error)
        steps = self._extract_analysis_steps(result.data)
        verification = self._assess_analysis_quality(result.data)
        confidence = self._calculate_confidence(result.data, verification)
        return MathReasoningResult(success=True, response=result.data, steps=steps, verification=verification, confidence=confidence)

    def symbolic_computation(self, expression: str, language: str = "zh") -> MathReasoningResult:
        prompt = get_math_prompt("symbolic_computation", language, computation=expression)
        prompt = f"{self._get_symbolic_computation_guidelines()}\n\n{prompt}"
        if MATHEMATICAL_PROMPTING_STRATEGIES["verifier_based"]["enabled"]:
            prefix = MATHEMATICAL_PROMPTING_STRATEGIES["verifier_based"]["prefix"]
            prompt = f"{prefix}\n\n{prompt}"
        result = self._send_math_message(prompt, "symbolic_computation")
        if not result.success:
            return MathReasoningResult(success=False, response="", steps=[], verification="", confidence=0.0, error=result.error)
        steps = self._extract_computation_steps(result.data)
        verification = self._verify_computation(result.data)
        confidence = self._calculate_confidence(result.data, verification)
        symbolic_checks = verify_llm_output(result.data)
        self_consistent = None
        if MATHEMATICAL_PROMPTING_STRATEGIES["self_consistency"]["enabled"]:
            consistent, _ = self.self_consistency_check(prompt, "symbolic_computation")
            self_consistent = consistent
            if not consistent:
                confidence *= 0.7
        if symbolic_checks:
            failed = [c for c in symbolic_checks if not c.verified]
            if failed:
                confidence *= max(0.3, 1.0 - 0.15 * len(failed))
        return MathReasoningResult(
            success=True, response=result.data, steps=steps,
            verification=verification, confidence=round(confidence, 4),
            symbolic_checks=symbolic_checks, self_consistent=self_consistent,
        )
    
    def solve_with_code(self, problem: str, language: str = "zh") -> MathReasoningResult:
        """Solve a problem by generating and executing Python/SymPy code."""
        prompt = f"""Please solve the following math problem by writing Python code using SymPy.
Wrap your code in ```python ... ``` blocks.

Problem: {problem}

Code:"""
        result = self._send_math_message(prompt, "symbolic_computation")
        if not result.success:
            return MathReasoningResult(success=False, response="", steps=[], verification="", confidence=0.0, error=result.error)
        
        success, output, code = self.code_interpreter.solve_with_code(problem, result.data)
        
        if success:
            final_response = f"Code Execution Result:\n{output}\n\nModel Reasoning:\n{result.data}"
            return MathReasoningResult(
                success=True, response=final_response, steps=[code],
                verification="Code executed successfully", confidence=0.95,
                symbolic_checks=[], self_consistent=True,
            )
        else:
            return MathReasoningResult(
                success=False, response=result.data, steps=[],
                verification=f"Code execution failed: {output}", confidence=0.0,
                error=output,
            )
    
    def self_consistency_check(self, prompt: str, task_type: str, n: int = 2) -> Tuple[bool, List[str]]:
        """Run the same prompt n times and check if answers are consistent."""
        responses = []
        for i in range(n):
            result = self._send_math_message(
                f"{prompt}\n\n(Attempt {i+1}/{n} — please solve independently)", task_type
            )
            if result.success:
                responses.append(result.data)
        if len(responses) < 2:
            return (False, ["Could not generate multiple responses"])
        # Compare final answers (look for numeric or symbolic results)
        answers = []
        for resp in responses:
            # Extract potential final answers
            answer_patterns = [
                r'[Aa]nswer[:\s]*([^\n]+)',
                r'[Rr]esult[:\s]*([^\n]+)',
                r'[Ss]olution[:\s]*([^\n]+)',
                r'=\s*([0-9\.\-\+\/\w]+)\s*$',  # Final equals expression
                r'∴\s*([^\n]+)',
                r'Q\.E\.D\.',
            ]
            found = False
            for pattern in answer_patterns:
                match = re.search(pattern, resp, re.MULTILINE)
                if match:
                    try:
                        answers.append(match.group(1).strip())
                        found = True
                        break
                    except IndexError:
                        pass
            if not found:
                answers.append(resp[-200:])  # Fallback: last 200 chars
        # Check if any two answers match (even partially)
        consistent = False
        details = []
        for i in range(len(answers)):
            for j in range(i + 1, len(answers)):
                # Normalize for comparison
                a = answers[i].strip().lower().replace(' ', '')
                b = answers[j].strip().lower().replace(' ', '')
                if a == b or (len(a) > 5 and a in b) or (len(b) > 5 and b in a):
                    consistent = True
                    details.append(f"Attempt {i+1} and {j+1}: CONSISTENT")
                else:
                    details.append(f"Attempt {i+1} and {j+1}: differ")
        return (consistent, details)
    
    def verify_output_symbols(self, text: str) -> List:
        """Use SymPy to verify mathematical claims in LLM output."""
        return verify_llm_output(text)

    def _get_relevant_knowledge(self, knowledge_type: str, query: str) -> str:
        """Get relevant mathematical knowledge based on query."""
        if knowledge_type not in MATH_KNOWLEDGE_BASE:
            return ""
        
        knowledge = MATH_KNOWLEDGE_BASE[knowledge_type]
        relevant_items = []
        
        query_lower = query.lower()
        
        for key, item in knowledge.items():
            if isinstance(item, dict):
                # Search in name and statement
                name = item.get("name", "").lower() + " " + item.get("name_cn", "").lower()
                statement = item.get("statement", "").lower() + " " + item.get("statement_cn", "").lower()
                
                if query_lower in name or query_lower in statement:
                    if isinstance(item, dict):
                        desc = item.get("statement", item.get("statement_cn", str(item)))
                        relevant_items.append(f"- {desc}")
        
        return "\n".join(relevant_items) if relevant_items else ""
    
    def _get_problem_solving_tips(self) -> str:
        """Get general problem-solving tips."""
        return """通用解题技巧/General Problem-Solving Tips:
- 检查单位一致性/Check unit consistency
- 画图辅助理解/Draw diagrams for visualization
- 尝试简单特例/Start with simple special cases
- 验证边界条件/Test boundary conditions
- 逆向思考/Think backwards from the goal"""
    
    def _get_symbolic_computation_guidelines(self) -> str:
        """Get symbolic computation guidelines."""
        return """符号计算指南/Symbolic Computation Guidelines:
- 保持等价变换/Maintain equivalent transformations
- 注意定义域限制/Respect domain restrictions
- 验证每步变换/Verify each transformation step
- 最简形式优先/Aim for simplest form"""
    
    def _get_related_conjecture_info(self, conjecture: str) -> str:
        """Get related conjecture information."""
        # This could be expanded with actual mathematical databases
        return f"已知相关信息/Related known information for: {conjecture[:100]}..."
    
    def _extract_proof_steps(self, text: str) -> List[str]:
        """Extract proof steps from response."""
        steps = []
        # Look for numbered steps or labeled sections
        patterns = [
            r'\d+\.\s*(.*?)(?=\n\d+\.|\n\n|$)',
            r'\*\*([^*]+)\*\*[^a-z]*([^\n]*)',
            r'[Ss]tep\s+\d+:?\s*(.*?)(?=\n[Ss]tep|\n\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            if matches:
                steps.extend([match if isinstance(match, str) else match[-1] for match in matches])
                break
        
        return [step.strip() for step in steps if step.strip()][:10]  # Limit to 10 steps
    
    def _extract_solution_steps(self, text: str) -> List[str]:
        """Extract solution steps from response."""
        return self._extract_proof_steps(text)  # Similar extraction logic
    
    def _extract_analysis_steps(self, text: str) -> List[str]:
        """Extract analysis steps from response."""
        return self._extract_proof_steps(text)
    
    def _extract_computation_steps(self, text: str) -> List[str]:
        """Extract computation steps from response."""
        steps = []
        # Look for calculation steps
        patterns = [
            r'([A-Za-z0-9].*?=.*?)\n(?=[A-Za-z0-9].*?=|$)',
            r'(.+?)[\n\r]+(=|→|⇒|∴)\s*(.+?)[\n\r]+',
            r'(.+?)\s*[=\-+×÷]\s*(.+?)[\n\r]+'  # Simple expression patterns
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.replace('\n\n', '\n####\n'))
            for match in matches:
                if isinstance(match, tuple):
                    step = ' '.join(str(m).strip() for m in match if m.strip())
                else:
                    step = match.strip()
                if len(step) > 5 and len(step) < 200:  # Valid step length
                    steps.append(step)
            if steps:
                break
        
        return steps[:10]
    
    def _verify_proof(self, text: str) -> str:
        """Basic proof verification."""
        # Check for common logical flow indicators
        checks = {
            "has_implication": bool(re.search(r'(⇒|→|∴|Therefore|所以|则)', text)),
            "has_assumption": bool(re.search(r'(Assume|Suppose|设|假设|如果)', text)),
            "has_contradiction": bool(re.search(r'(Contradiction|矛盾|contradicts)', text, re.I)),
            "has_induction": bool(re.search(r'(Induction|归纳|inductive)', text, re.I)),
            "has_conclusion": bool(re.search(r'(Q\.E\.D\.|□|证毕|Conclusion|因此)', text, re.I))
        }
        
        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        
        return f"Verification: {passed_checks}/{total_checks} logical indicators present"
    
    def _verify_solution(self, text: str) -> str:
        """Basic solution verification."""
        checks = {
            "has_answer": bool(re.search(r'(Answer|解|答案|=\s*[\d\w])', text, re.I)),
            "has_verification": bool(re.search(r'(Check|Verify|验证|代入)', text, re.I)),
            "has_units": bool(re.search(r'(units?|米|kg|seconds?|units)', text, re.I)),
            "has_substitution": bool(re.search(r'(Substitut|代入|plug)', text, re.I))
        }
        
        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        
        return f"Verification: {passed_checks}/{total_checks} solution indicators present"
    
    def _verify_computation(self, text: str) -> str:
        """Basic computation verification."""
        checks = {
            "has_step_by_step": bool(re.search(r'(Step|步骤|step)', text, re.I)),
            "has_simplification": bool(re.search(r'(Simplify|化简|reduce)', text, re.I)),
            "has_final_form": bool(re.search(r'(Final|最终|final|answer)', text, re.I)),
            "has_verification": bool(re.search(r'(Check|验证|verify)', text, re.I))
        }
        
        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        
        return f"Verification: {passed_checks}/{total_checks} computation indicators present"
    
    def _assess_analysis_quality(self, text: str) -> str:
        """Assess quality of mathematical analysis."""
        aspects = {
            "background": bool(re.search(r'(Background|背景|History|历史)', text, re.I)),
            "evidence": bool(re.search(r'(Evidence|证据|Data|数据|Verified|验证)', text, re.I)),
            "obstacles": bool(re.search(r'(Obstacle|困难|Challenge|难点|Hard|困难)', text, re.I)),
            "approaches": bool(re.search(r'(Approach|方法|Strategy|策略|Method|方法)', text, re.I))
        }
        
        covered_aspects = sum(1 for v in aspects.values() if v)
        total_aspects = len(aspects)
        
        return f"Analysis Quality: {covered_aspects}/{total_aspects} required aspects covered"
    
    def _calculate_confidence(self, text: str, verification: str) -> float:
        """Calculate confidence score based on various factors."""
        # Length factor (longer responses tend to be more detailed)
        length_score = min(len(text) / 500, 1.0)  # Normalize to 0-1
        
        # Verification factor
        verification_match = re.search(r'(\d+)/(\d+)', verification)
        if verification_match:
            try:
                passed, total = map(int, verification_match.groups())
                verification_score = passed / total if total > 0 else 0.5
            except:
                verification_score = 0.5
        else:
            verification_score = 0.5
        
        # Combine scores
        combined = (length_score * 0.3 + verification_score * 0.7)
        return min(combined, 1.0)  # Ensure it's not above 1.0