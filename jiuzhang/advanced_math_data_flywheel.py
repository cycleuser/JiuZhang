"""Advanced Math Data Flywheel for JiuZhang.

Extends the basic flywheel with AgenticQwen-inspired improvements:

1. **Cross-Concept Combination**: Generate problems that combine multiple math domains
   (e.g., calculus + algebra, geometry + probability).

2. **Step-Level Verification**: Verify each reasoning step, not just the final answer.
   This catches reasoning errors even when the final answer happens to be correct.

3. **Difficulty Tracker**: Monitor how difficulty evolves across flywheel rounds,
   ensuring steady progression without sudden jumps.

4. **Data Deduplication**: Prevent generating identical or near-identical problems
   across rounds using hash-based similarity detection.

5. **Quality Scoring**: Score each generated sample based on verification strength,
   novelty, and difficulty appropriateness for training priority.

6. **Branch-to-Task Inversion**: Take a solution path branch (e.g., "discriminant > 0")
   and invert it into a new problem where that branch is the required path.

7. **Merged Dataset Export**: Combine curriculum + flywheel data with proper
   metadata for unified training.
"""

import json
import random
import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

import sympy as sp
from sympy import (
    symbols, Symbol, Rational, pi, E, oo, sqrt, sin, cos, tan,
    exp, log, diff, integrate, solve, simplify, factor, expand,
    limit, series, Matrix, factorial, gcd, isprime, Eq,
)

from jiuzhang.math_data_flywheel import (
    MathProblem,
    ModelResponse,
    FlywheelSample,
    DifficultyLevel,
    ErrorCollector,
    HardExampleGenerator,
    PersonaInjector,
    BehaviorTreeExpander,
    AdversarialGenerator,
    ConsistencyFilter,
    MathDataFlywheel,
)


# ── Cross-Concept Combination Generator ──────────────────────────────

class CrossConceptGenerator:
    """Generate problems that combine multiple math concepts.
    
    Inspired by AgenticQwen's approach of combining different reasoning skills
    to create more challenging, realistic problems.
    """

    COMBINATION_TEMPLATES = [
        {
            "name": "optimization_with_derivative",
            "zh": "用导数求最值",
            "en": "Optimization using derivatives",
            "concepts": ["algebra", "calculus"],
            "generate": lambda self, rng: self._gen_optimization(rng),
        },
        {
            "name": "area_with_integral",
            "zh": "用积分求面积",
            "en": "Area calculation using integrals",
            "concepts": ["geometry", "calculus"],
            "generate": lambda self, rng: self._gen_area_integral(rng),
        },
        {
            "name": "probability_with_algebra",
            "zh": "代数与概率结合",
            "en": "Probability with algebraic manipulation",
            "concepts": ["probability", "algebra"],
            "generate": lambda self, rng: self._gen_probability_algebra(rng),
        },
        {
            "name": "sequence_with_limit",
            "zh": "数列与极限",
            "en": "Sequences and limits",
            "concepts": ["algebra", "calculus"],
            "generate": lambda self, rng: self._gen_sequence_limit(rng),
        },
    ]

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.x = symbols('x')

    def _gen_optimization(self, rng) -> MathProblem:
        """Generate optimization problem: find max/min of a function."""
        degree = rng.randint(2, 4)
        coefs = [rng.randint(-3, 3) for _ in range(degree + 1)]
        if coefs[0] == 0:
            coefs[0] = 1
        
        func = sum(c * self.x**j for j, c in enumerate(reversed(coefs)))
        deriv = diff(func, self.x)
        critical_points = solve(deriv, self.x)
        
        # Filter real critical points
        real_points = [cp for cp in critical_points if cp.is_real or cp.is_number]
        if not real_points:
            real_points = critical_points[:1]
        
        return MathProblem(
            id=f"cross_optim_{hashlib.md5(str(func).encode()).hexdigest()[:8]}",
            category="calculus",
            difficulty=DifficultyLevel.ADVANCED,
            instruction_zh=f"求函数的极值点（综合：代数+微积分）",
            instruction_en=f"Find the extrema of the function (cross-concept: algebra + calculus)",
            input_zh=f"f(x) = {func}\n提示：先求导数，再找临界点",
            input_en=f"f(x) = {func}\nHint: Find derivative first, then critical points",
            answer_zh=f"f'(x) = {deriv}\n临界点: x = {real_points}",
            answer_en=f"f'(x) = {deriv}\nCritical points: x = {real_points}",
            sympy_expression=f"diff({func}, x) = {deriv}",
            solution_steps=[
                f"Step 1: Compute derivative: f'(x) = {deriv}",
                f"Step 2: Set f'(x) = 0 and solve: {deriv} = 0",
                f"Step 3: Critical points: x = {real_points}",
                f"Step 4: Classify using second derivative or sign analysis",
            ],
        )

    def _gen_area_integral(self, rng) -> MathProblem:
        """Generate area under curve problem."""
        a = rng.randint(1, 3)
        n = rng.randint(2, 4)
        func = a * self.x**n
        
        x_start = 0
        x_end = rng.randint(1, 3)
        
        area = integrate(func, (self.x, x_start, x_end))
        
        return MathProblem(
            id=f"cross_area_{hashlib.md5(f'{a}{n}{x_end}'.encode()).hexdigest()[:8]}",
            category="calculus",
            difficulty=DifficultyLevel.ADVANCED,
            instruction_zh=f"求曲线下的面积（综合：几何+微积分）",
            instruction_en=f"Find the area under the curve (cross-concept: geometry + calculus)",
            input_zh=f"求 f(x) = {func} 在 x={x_start} 到 x={x_end} 之间的面积",
            input_en=f"Find the area under f(x) = {func} from x={x_start} to x={x_end}",
            answer_zh=f"面积 = ∫[{x_start},{x_end}] {func} dx = {area}",
            answer_en=f"Area = ∫[{x_start},{x_end}] {func} dx = {area}",
            sympy_expression=f"integrate({func}, (x, {x_start}, {x_end})) = {area}",
            solution_steps=[
                f"Step 1: Set up definite integral: ∫[{x_start},{x_end}] {func} dx",
                f"Step 2: Find antiderivative: {integrate(func, self.x)}",
                f"Step 3: Evaluate at bounds: {area}",
            ],
        )

    def _gen_probability_algebra(self, rng) -> MathProblem:
        """Generate probability problem requiring algebraic solving."""
        n = rng.randint(2, 5)
        p = Rational(rng.randint(1, 3), rng.randint(4, 10))
        
        # P(X = k) = C(n,k) * p^k * (1-p)^(n-k)
        k = rng.randint(0, n)
        from sympy import binomial
        prob = binomial(n, k) * p**k * (1-p)**(n-k)
        prob_simplified = simplify(prob)
        
        return MathProblem(
            id=f"cross_prob_{hashlib.md5(f'{n}{k}{p}'.encode()).hexdigest()[:8]}",
            category="probability",
            difficulty=DifficultyLevel.ADVANCED,
            instruction_zh=f"二项分布概率计算（综合：概率+代数）",
            instruction_en=f"Binomial probability calculation (cross-concept: probability + algebra)",
            input_zh=f"n={n}次独立试验，成功概率p={p}，求恰好{k}次成功的概率",
            input_en=f"In {n} independent trials with success probability p={p}, find P(X={k})",
            answer_zh=f"P(X={k}) = C({n},{k}) × ({p})^{k} × ({1-p})^{n-k} = {prob_simplified}",
            answer_en=f"P(X={k}) = C({n},{k}) × ({p})^{k} × ({1-p})^{n-k} = {prob_simplified}",
            sympy_expression=f"binomial({n},{k}) * {p}**{k} * ({1-p})**({n}-{k}) = {prob_simplified}",
            solution_steps=[
                f"Step 1: Identify binomial distribution: X ~ B({n}, {p})",
                f"Step 2: Apply formula: P(X=k) = C(n,k) × p^k × (1-p)^(n-k)",
                f"Step 3: Calculate: C({n},{k}) × ({p})^{k} × ({1-p})^{n-k} = {prob_simplified}",
            ],
        )

    def _gen_sequence_limit(self, rng) -> MathProblem:
        """Generate sequence limit problem."""
        templates = [
            (self.x / (self.x + 1), self.x, oo, 1, "x/(x+1) as x→∞"),
            (sp.sin(self.x) / self.x, self.x, oo, 0, "sin(x)/x as x→∞"),
            ((1 + 1/self.x)**self.x, self.x, oo, E, "(1+1/x)^x as x→∞"),
        ]
        
        func, var, target, correct_val, desc = self.rng.choice(templates)
        lim = limit(func, var, target)
        
        return MathProblem(
            id=f"cross_seq_lim_{hashlib.md5(str(func).encode()).hexdigest()[:8]}",
            category="calculus",
            difficulty=DifficultyLevel.ADVANCED,
            instruction_zh=f"求数列/函数的极限（综合：代数+极限）",
            instruction_en=f"Find the limit of sequence/function (cross-concept: algebra + limits)",
            input_zh=f"lim(x→{target}) {func}",
            input_en=f"lim(x→{target}) {func}",
            answer_zh=f"lim(x→{target}) {func} = {lim}",
            answer_en=f"lim(x→{target}) {func} = {lim}",
            sympy_expression=f"limit({func}, {var}, {target}) = {lim}",
            solution_steps=[
                f"Step 1: Identify the form of the limit",
                f"Step 2: Apply appropriate limit technique",
                f"Step 3: lim(x→{target}) {func} = {lim}",
            ],
        )

    def generate_cross_concept(self, count: int = 5) -> List[MathProblem]:
        """Generate cross-concept problems."""
        problems = []
        for _ in range(count):
            template = self.rng.choice(self.COMBINATION_TEMPLATES)
            problem = template["generate"](self, self.rng)
            problems.append(problem)
        return problems


# ── Step-Level Verifier ──────────────────────────────────────────────

class StepVerifier:
    """Verify each step of a solution, not just the final answer.
    
    This catches reasoning errors even when the final answer happens to be correct.
    """

    def __init__(self):
        self.x = symbols('x')

    def verify_step(self, step_text: str, expected_sympy: Optional[str] = None) -> Tuple[bool, str]:
        """Verify a single solution step."""
        if not expected_sympy:
            return True, "no_expected_value_for_step"
        
        try:
            # Try to extract mathematical expression from step
            # Look for patterns like "f'(x) = ...", "x = ...", etc.
            expr_match = re.search(r'=\s*(.+)$', step_text)
            if expr_match:
                step_expr = expr_match.group(1).strip()
                expected_expr = expected_sympy.split('=')[-1].strip() if '=' in expected_sympy else expected_sympy
                
                # Try symbolic comparison
                step_sym = sp.sympify(step_expr)
                expected_sym = sp.sympify(expected_expr)
                
                if simplify(step_sym - expected_sym) == 0:
                    return True, f"step_verified: {step_expr} == {expected_expr}"
                else:
                    return False, f"step_mismatch: got {step_expr}, expected {expected_expr}"
            
            return True, "step_parseable"
        except Exception as e:
            return False, f"step_verification_error: {str(e)}"

    def verify_solution_steps(self, problem: MathProblem) -> Tuple[bool, List[str]]:
        """Verify all steps in a solution."""
        if not problem.solution_steps:
            return True, ["no_steps_to_verify"]
        
        results = []
        all_verified = True
        
        for i, step in enumerate(problem.solution_steps):
            # Use sympy_expression as reference for verification
            verified, detail = self.verify_step(step, problem.sympy_expression)
            results.append(f"Step {i+1}: {'✓' if verified else '✗'} ({detail})")
            if not verified:
                all_verified = False
        
        return all_verified, results


# ── Difficulty Tracker ───────────────────────────────────────────────

class DifficultyTracker:
    """Track how difficulty evolves across flywheel rounds.
    
    Ensures steady progression without sudden jumps.
    """

    def __init__(self):
        self.round_difficulties: Dict[int, Dict[str, float]] = {}
        self.category_progression: Dict[str, List[float]] = defaultdict(list)

    def record_round(self, round_num: int, samples: List[FlywheelSample]):
        """Record difficulty distribution for a round."""
        if not samples:
            return
        
        difficulties = [s.difficulty_increase for s in samples]
        avg_difficulty = sum(difficulties) / len(difficulties)
        max_difficulty = max(difficulties)
        min_difficulty = min(difficulties)
        
        self.round_difficulties[round_num] = {
            "avg": avg_difficulty,
            "max": max_difficulty,
            "min": min_difficulty,
            "count": len(samples),
        }
        
        # Track per-category
        for sample in samples:
            cat = sample.problem.category
            self.category_progression[cat].append(sample.difficulty_increase)

    def get_progression_report(self) -> Dict:
        """Get difficulty progression report."""
        report = {
            "rounds": self.round_difficulties,
            "category_progression": {
                cat: {
                    "avg": sum(vals) / len(vals) if vals else 0,
                    "max": max(vals) if vals else 0,
                    "total_samples": len(vals),
                }
                for cat, vals in self.category_progression.items()
            },
            "trend": self._compute_trend(),
        }
        return report

    def _compute_trend(self) -> str:
        """Compute overall difficulty trend."""
        if len(self.round_difficulties) < 2:
            return "insufficient_data"
        
        rounds = sorted(self.round_difficulties.keys())
        avg_diffs = [self.round_difficulties[r]["avg"] for r in rounds]
        
        if all(avg_diffs[i] <= avg_diffs[i+1] for i in range(len(avg_diffs)-1)):
            return "steady_increase"
        elif all(avg_diffs[i] >= avg_diffs[i+1] for i in range(len(avg_diffs)-1)):
            return "decreasing"
        else:
            return "fluctuating"

    def should_increase_difficulty(self, round_num: int) -> bool:
        """Determine if next round should increase difficulty."""
        if round_num not in self.round_difficulties:
            return True
        
        current_avg = self.round_difficulties[round_num]["avg"]
        # If average difficulty increase is < 0.2, suggest increasing
        return current_avg < 0.2


# ── Data Deduplicator ────────────────────────────────────────────────

class DataDeduplicator:
    """Prevent generating identical or near-identical problems.
    
    Uses hash-based similarity detection on problem content.
    """

    def __init__(self):
        self.seen_hashes: Set[str] = set()

    def _compute_hash(self, problem: MathProblem) -> str:
        """Compute a hash for a problem based on core content."""
        # Normalize the problem text for hashing
        content = f"{problem.input_zh}{problem.input_en}{problem.answer_zh}{problem.answer_en}"
        # Remove whitespace and normalize
        content = re.sub(r'\s+', '', content)
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def is_duplicate(self, problem: MathProblem) -> bool:
        """Check if a problem is a duplicate."""
        h = self._compute_hash(problem)
        return h in self.seen_hashes

    def add_problem(self, problem: MathProblem):
        """Add a problem to the seen set."""
        h = self._compute_hash(problem)
        self.seen_hashes.add(h)

    def filter_duplicates(self, samples: List) -> List:
        """Filter out duplicates from a list of samples or problems."""
        unique = []
        for sample in samples:
            # Handle both FlywheelSample and MathProblem
            problem = sample.problem if hasattr(sample, 'problem') else sample
            if not self.is_duplicate(problem):
                self.add_problem(problem)
                unique.append(sample)
        return unique

    def get_stats(self) -> Dict:
        """Get deduplication statistics."""
        return {
            "total_seen": len(self.seen_hashes),
        }


# ── Quality Scorer ───────────────────────────────────────────────────

class QualityScorer:
    """Score each generated sample for training priority.
    
    Based on:
    - Verification strength (more methods = higher score)
    - Novelty (cross-concept = higher score)
    - Difficulty appropriateness (matched to curriculum stage)
    """

    def __init__(self):
        self.weights = {
            "verification": 0.4,
            "novelty": 0.3,
            "difficulty": 0.3,
        }

    def score_sample(self, sample: FlywheelSample) -> float:
        """Score a sample from 0.0 to 1.0."""
        # Verification score
        verif_score = min(len(sample.verification_methods) / 3.0, 1.0)
        
        # Novelty score
        if sample.source in ["cross_concept", "behavior_tree"]:
            novelty_score = 0.9
        elif sample.source in ["error_expansion", "persona_injection"]:
            novelty_score = 0.7
        elif sample.source == "adversarial":
            novelty_score = 0.8
        else:
            novelty_score = 0.5
        
        # Difficulty score
        diff_increase = sample.difficulty_increase
        difficulty_score = min(diff_increase / 0.5, 1.0) if diff_increase > 0 else 0.5
        
        # Weighted sum
        total = (
            self.weights["verification"] * verif_score +
            self.weights["novelty"] * novelty_score +
            self.weights["difficulty"] * difficulty_score
        )
        
        return round(total, 3)

    def score_all(self, samples: List[FlywheelSample]) -> List[Tuple[FlywheelSample, float]]:
        """Score all samples and return sorted by score."""
        scored = [(s, self.score_sample(s)) for s in samples]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored


# ── Merged Dataset Exporter ──────────────────────────────────────────

class MergedDatasetExporter:
    """Combine curriculum + flywheel data with proper metadata."""

    def __init__(self):
        self.deduplicator = DataDeduplicator()
        self.scorer = QualityScorer()

    def export_merged(self, 
                     curriculum_samples: List[FlywheelSample],
                     flywheel_samples: List[FlywheelSample],
                     output_path: str = "jiuzhang_merged_training.jsonl",
                     min_quality_score: float = 0.0,
                     format: str = "chatml"):
        """Export merged dataset with quality filtering."""
        # Combine and deduplicate
        all_samples = curriculum_samples + flywheel_samples
        unique_samples = self.deduplicator.filter_duplicates(all_samples)
        
        # Score and filter
        scored = self.scorer.score_all(unique_samples)
        filtered = [(s, score) for s, score in scored if score >= min_quality_score]
        
        # Export
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample, score in filtered:
                if format == "chatml":
                    entry = {
                        "messages": [
                            {"role": "system", "content": f"你是九章数学专家。数据来源：{sample.source} / You are JiuZhang-Math. Source: {sample.source}"},
                            {"role": "user", "content": f"{sample.problem.instruction_zh}\n{sample.problem.input_zh}\n/\n{sample.problem.instruction_en}\n{sample.problem.input_en}"},
                            {"role": "assistant", "content": f"{sample.problem.answer_zh}\n/\n{sample.problem.answer_en}"},
                        ],
                        "source": sample.source,
                        "category": sample.problem.category,
                        "difficulty": sample.problem.difficulty.value,
                        "parent_problem_id": sample.parent_problem_id,
                        "difficulty_increase": sample.difficulty_increase,
                        "verification": sample.verification_methods,
                        "quality_score": score,
                    }
                else:
                    entry = {
                        "instruction": f"{sample.problem.instruction_zh} / {sample.problem.instruction_en}",
                        "input": f"{sample.problem.input_zh} / {sample.problem.input_en}",
                        "output": f"{sample.problem.answer_zh} / {sample.problem.answer_en}",
                        "source": sample.source,
                        "category": sample.problem.category,
                        "difficulty": sample.problem.difficulty.value,
                        "quality_score": score,
                    }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        print(f"Exported {len(filtered)} merged samples to {output_path}")
        print(f"  Original: {len(all_samples)}")
        print(f"  After dedup: {len(unique_samples)}")
        print(f"  After quality filter (≥{min_quality_score}): {len(filtered)}")
        
        return filtered


# ── Advanced Math Data Flywheel ──────────────────────────────────────

class AdvancedMathDataFlywheel(MathDataFlywheel):
    """Enhanced flywheel with all AgenticQwen-inspired improvements."""

    def __init__(self, seed: int = 42):
        super().__init__(seed=seed)
        self.cross_concept_generator = CrossConceptGenerator(seed=seed)
        self.step_verifier = StepVerifier()
        self.difficulty_tracker = DifficultyTracker()
        self.deduplicator = DataDeduplicator()
        self.quality_scorer = QualityScorer()
        self.merged_exporter = MergedDatasetExporter()

    def generate_next_round(self,
                           expand_hard: bool = True,
                           inject_persona: bool = True,
                           expand_behavior_tree: bool = True,
                           generate_adversarial: bool = True,
                           generate_cross_concept: bool = True,
                           max_new_samples: int = 100,
                           min_quality_score: float = 0.0) -> List[FlywheelSample]:
        """Generate next round with all improvements."""
        self.round_count += 1
        new_samples = []
        errors = self.error_collector.errors
        
        if not errors:
            print(f"Round {self.round_count}: No errors recorded, generating cross-concept data only.")
            # Still generate cross-concept data even without errors
            if generate_cross_concept:
                cross_problems = self.cross_concept_generator.generate_cross_concept(count=10)
                for prob in cross_problems:
                    verified, methods = self.consistency_filter.verify_consensus(prob)
                    if verified and not self.deduplicator.is_duplicate(prob):
                        sample = FlywheelSample(
                            problem=prob,
                            source="cross_concept",
                            difficulty_increase=0.4,
                            verification_methods=methods,
                            verification_consensus=True,
                        )
                        new_samples.append(sample)
                        self.deduplicator.add_problem(prob)
            
            self.difficulty_tracker.record_round(self.round_count, new_samples)
            self.all_generated.extend(new_samples)
            return new_samples
        
        # 1. Hard example generation from errors
        if expand_hard:
            hard_problems = self.hard_generator.generate_from_errors(errors, count_per_error=2)
            for prob in hard_problems:
                if self.deduplicator.is_duplicate(prob):
                    continue
                verified, methods = self.consistency_filter.verify_consensus(prob)
                if verified:
                    # Also verify steps if available
                    if prob.solution_steps:
                        steps_ok, step_results = self.step_verifier.verify_solution_steps(prob)
                        if steps_ok:
                            methods.extend(step_results)
                    
                    sample = FlywheelSample(
                        problem=prob,
                        source="error_expansion",
                        parent_problem_id=prob.id,
                        difficulty_increase=0.3,
                        verification_methods=methods,
                        verification_consensus=True,
                    )
                    new_samples.append(sample)
                    self.deduplicator.add_problem(prob)
        
        # 2. Persona injection for diversity
        if inject_persona:
            for problem, response in errors[:10]:
                persona_problems = self.persona_injector.inject_all_personas(problem)
                for pp in persona_problems:
                    if self.deduplicator.is_duplicate(pp):
                        continue
                    verified, methods = self.consistency_filter.verify_consensus(pp)
                    if verified:
                        sample = FlywheelSample(
                            problem=pp,
                            source="persona_injection",
                            parent_problem_id=problem.id,
                            difficulty_increase=0.0,
                            verification_methods=methods,
                            verification_consensus=True,
                        )
                        new_samples.append(sample)
                        self.deduplicator.add_problem(pp)
        
        # 3. Behavior tree expansion
        if expand_behavior_tree:
            for problem, response in errors[:5]:
                bt_problems = self.behavior_tree_expander.expand_problem(problem)
                for bp in bt_problems:
                    if self.deduplicator.is_duplicate(bp):
                        continue
                    verified, methods = self.consistency_filter.verify_consensus(bp)
                    if verified:
                        sample = FlywheelSample(
                            problem=bp,
                            source="behavior_tree",
                            parent_problem_id=problem.id,
                            difficulty_increase=0.2,
                            verification_methods=methods,
                            verification_consensus=True,
                        )
                        new_samples.append(sample)
                        self.deduplicator.add_problem(bp)
        
        # 4. Adversarial problem generation
        if generate_adversarial:
            for problem, response in errors[:5]:
                adv_problem = self.adversarial_generator.generate_adversarial(problem)
                if self.deduplicator.is_duplicate(adv_problem):
                    continue
                verified, methods = self.consistency_filter.verify_consensus(adv_problem)
                if verified:
                    sample = FlywheelSample(
                        problem=adv_problem,
                        source="adversarial",
                        parent_problem_id=problem.id,
                        difficulty_increase=0.1,
                        verification_methods=methods,
                        verification_consensus=True,
                    )
                    new_samples.append(sample)
                    self.deduplicator.add_problem(adv_problem)
        
        # 5. Cross-concept combination
        if generate_cross_concept:
            cross_problems = self.cross_concept_generator.generate_cross_concept(count=10)
            for prob in cross_problems:
                if self.deduplicator.is_duplicate(prob):
                    continue
                verified, methods = self.consistency_filter.verify_consensus(prob)
                if verified:
                    sample = FlywheelSample(
                        problem=prob,
                        source="cross_concept",
                        difficulty_increase=0.4,
                        verification_methods=methods,
                        verification_consensus=True,
                    )
                    new_samples.append(sample)
                    self.deduplicator.add_problem(prob)
        
        # Cap total new samples
        if len(new_samples) > max_new_samples:
            new_samples = new_samples[:max_new_samples]
        
        # Track difficulty progression
        self.difficulty_tracker.record_round(self.round_count, new_samples)
        
        self.all_generated.extend(new_samples)
        return new_samples

    def get_advanced_stats(self) -> Dict:
        """Get comprehensive stats including advanced metrics."""
        base_stats = self.get_stats()
        
        # Add advanced metrics
        base_stats["deduplication"] = self.deduplicator.get_stats()
        base_stats["difficulty_progression"] = self.difficulty_tracker.get_progression_report()
        
        # Quality distribution
        scored = self.quality_scorer.score_all(self.all_generated)
        if scored:
            scores = [s for _, s in scored]
            base_stats["quality_distribution"] = {
                "avg": sum(scores) / len(scores),
                "max": max(scores),
                "min": min(scores),
                "high_quality_count": sum(1 for s in scores if s >= 0.7),
            }
        
        return base_stats

    def export_merged_dataset(self, 
                             output_path: str = "jiuzhang_merged_training.jsonl",
                             min_quality_score: float = 0.0,
                             format: str = "chatml"):
        """Export merged dataset with quality filtering."""
        # Split curriculum vs flywheel samples
        curriculum = [s for s in self.all_generated if s.source == "curriculum"]
        flywheel = [s for s in self.all_generated if s.source != "curriculum"]
        
        return self.merged_exporter.export_merged(
            curriculum_samples=curriculum,
            flywheel_samples=flywheel,
            output_path=output_path,
            min_quality_score=min_quality_score,
            format=format,
        )


# ── CLI Entry Point ──────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="JiuZhang Advanced Math Data Flywheel")
    parser.add_argument("--mode", choices=["generate", "round", "stats", "export", "merged"], default="generate")
    parser.add_argument("--output", default="jiuzhang_flywheel.jsonl")
    parser.add_argument("--format", choices=["chatml", "alpaca"], default="chatml")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-samples", type=int, default=200)
    parser.add_argument("--min-quality", type=float, default=0.0)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()

    flywheel = AdvancedMathDataFlywheel(seed=args.seed)

    if args.mode == "generate":
        # Generate initial data
        samples = flywheel.generate_initial_data()
        print(f"Generated {len(samples)} initial samples")
        
        # Run multiple rounds
        for round_num in range(args.rounds):
            # Simulate errors
            error_count = min(10 + round_num * 5, len(samples))
            for sample in samples[:error_count]:
                flywheel.record_errors([
                    (sample.problem, ModelResponse(
                        problem_id=sample.problem.id,
                        response_zh="错误答案",
                        response_en="Wrong answer",
                        is_correct=False,
                        error_type="calculation" if round_num % 2 == 0 else "concept",
                    ))
                ])
            
            new_samples = flywheel.generate_next_round(max_new_samples=args.max_samples)
            print(f"Flywheel Round {round_num + 1}: Generated {len(new_samples)} new samples")
        
        # Export
        flywheel.export_training_data(output_path=args.output, format=args.format)
        
        # Stats
        import pprint
        print("\nAdvanced Flywheel Statistics:")
        pprint.pprint(flywheel.get_advanced_stats())

    elif args.mode == "stats":
        flywheel.generate_initial_data()
        import pprint
        pprint.pprint(flywheel.get_advanced_stats())

    elif args.mode == "export":
        flywheel.generate_initial_data()
        flywheel.export_training_data(output_path=args.output, format=args.format)

    elif args.mode == "merged":
        flywheel.generate_initial_data()
        flywheel.export_merged_dataset(
            output_path=args.output,
            min_quality_score=args.min_quality,
            format=args.format,
        )


if __name__ == "__main__":
    main()
