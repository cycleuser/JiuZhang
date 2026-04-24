"""
Mathematical Reasoning Training Data Generator for JiuZhang.

Generates training datasets for mathematical reasoning tasks to fine-tune local models.
"""

import json
import random
from typing import List, Dict, Any
from dataclasses import dataclass
import sympy as sp
import numpy as np


@dataclass
class MathTrainingSample:
    """A single training sample for mathematical reasoning."""
    instruction: str
    input: str
    output: str
    category: str
    difficulty: str
    tags: List[str]


class MathTrainingDataGenerator:
    """Generates training data for mathematical reasoning models."""
    
    def __init__(self):
        self.categories = ["algebra", "calculus", "geometry", "number_theory", "combinatorics", "analysis", "linear_algebra"]
        self.difficulties = ["beginner", "intermediate", "advanced", "research"]
        self.conversation_templates = [
            {
                "system": "你是一个专业的数学助手，擅长数学证明、问题求解和符号计算。",
                "user_prefix": "请解决以下数学问题：",
                "assistant_prefix": "好的，我来解决这个问题："
            },
            {
                "system": "你是数学专家，专注于严格的数学推理和证明。",
                "user_prefix": "请证明以下定理：",
                "assistant_prefix": "我将按照严格的数学推理来证明："
            },
            {
                "system": "你是符号计算专家，熟练使用SymPy等数学软件。",
                "user_prefix": "请进行符号计算：",
                "assistant_prefix": "我将使用符号计算方法："
            }
        ]
    
    def generate_algebra_samples(self, count: int = 100) -> List[MathTrainingSample]:
        """Generate algebra training samples."""
        samples = []
        
        for _ in range(count):
            a, b = random.randint(1, 10), random.randint(-10, 10)
            x = sp.Symbol('x')
            equation = sp.Eq(a*x + b, 0)
            solution = sp.solve(equation, x)[0]
            
            instruction = "Solve the linear equation for x"
            input_text = f"Solve: {a}*x + {b} = 0"
            output_text = f"Solution: x = {solution}\nSteps:\n1. Given equation: {a}x + {b} = 0\n2. Subtract {b} from both sides: {a}x = {-b}\n3. Divide both sides by {a}: x = {solution}"
            
            samples.append(MathTrainingSample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                category="algebra",
                difficulty=random.choice(["beginner", "intermediate"]),
                tags=["linear_equation", "solve", "algebra"]
            ))
        
        # Quadratic equations
        for _ in range(count // 3):
            a_coef = random.randint(1, 5)
            b_coef = random.randint(-10, 10)
            c_coef = random.randint(-10, 10)
            x = sp.Symbol('x')
            quad = a_coef*x**2 + b_coef*x + c_coef
            solutions = sp.solve(quad, x)
            disc = b_coef**2 - 4*a_coef*c_coef
            
            instruction = "Solve the quadratic equation"
            input_text = f"Solve: {a_coef}x² + {b_coef}x + {c_coef} = 0"
            output_text = f"Solution: x = {solutions}\nSteps:\n1. Identify coefficients: a={a_coef}, b={b_coef}, c={c_coef}\n2. Discriminant: Δ = b²-4ac = {b_coef}²-4·{a_coef}·{c_coef} = {disc}\n3. Apply quadratic formula: x = (-b ± √Δ) / (2a)\n4. x = ({-b_coef} ± √{disc}) / {2*a_coef} = {solutions}"
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="algebra", difficulty="intermediate",
                tags=["quadratic", "solve", "algebra", "discriminant"]
            ))
        
        return samples
    
    def generate_calculus_samples(self, count: int = 50) -> List[MathTrainingSample]:
        """Generate calculus training samples."""
        samples = []
        
        for _ in range(count):
            x = sp.Symbol('x')
            degree = random.randint(2, 4)
            coeffs = [random.randint(-5, 5) for _ in range(degree + 1)]
            poly = sum(c * x**i for i, c in enumerate(coeffs))
            
            derivative = sp.diff(poly, x)
            
            instruction = "Find the derivative of the given function"
            input_text = f"Find the derivative: f(x) = {sp.latex(poly)}"
            output_text = f"Derivative: f'(x) = {sp.latex(derivative)}\nSteps:\n1. Original function: f(x) = {poly}\n2. Apply power rule term by term\n3. f'(x) = {derivative}"
            
            samples.append(MathTrainingSample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                category="calculus", 
                difficulty=random.choice(["intermediate", "advanced"]),
                tags=["differentiation", "calculus", "derivative"]
            ))
        
        # Integration samples
        for _ in range(count // 2):
            x = sp.Symbol('x')
            a_coef = random.randint(1, 5)
            n_pow = random.randint(1, 4)
            func = a_coef * x**n_pow
            integral = sp.integrate(func, x) + sp.Symbol('C')
            
            instruction = "Find the indefinite integral"
            input_text = f"Integrate: ∫{func} dx"
            output_text = f"Integral: ∫{func} dx = {integral}\nSteps:\n1. Apply power rule for integration: ∫xⁿ dx = xⁿ⁺¹/(n+1) + C\n2. ∫{a_coef}x{n_pow} dx = {a_coef} · x^({n_pow}+1)/({n_pow}+1) + C\n3. = {integral}"
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="calculus", difficulty="intermediate",
                tags=["integration", "calculus", "integral"]
            ))
        
        for _ in range(count // 3):
            x = sp.Symbol('x')
            inner = random.choice([sp.sin(x), sp.cos(x), sp.exp(x)])
            outer_coeff = random.randint(1, 3)
            func = outer_coeff * inner
            deriv = sp.diff(func, x)
            
            instruction = "Find the derivative of a trigonometric or exponential function"
            input_text = f"Find d/dx: f(x) = {func}"
            output_text = f"f'(x) = {deriv}\nSteps:\n1. f(x) = {func}\n2. Apply chain rule / standard derivative rules\n3. f'(x) = {deriv}"
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="calculus", difficulty="advanced",
                tags=["derivative", "trigonometric", "exponential", "chain_rule"]
            ))
        
        return samples
    
    def generate_proof_samples(self, count: int = 30) -> List[MathTrainingSample]:
        """Generate mathematical proof training samples."""
        samples = []
        
        # Prove that square root of 2 is irrational
        for _ in range(count // 3):
            instruction = "Prove that the square root of 2 is irrational"
            input_text = "Prove that √2 is irrational"
            output_text = """Proof that √2 is irrational using proof by contradiction:

1. **Assume the opposite**: Suppose √2 is rational
2. **Rational form**: Then √2 = a/b for integers a, b with b ≠ 0 and gcd(a,b) = 1 (in lowest terms)
3. **Square both sides**: 2 = a²/b²
4. **Rearrange**: 2b² = a²
5. **a² is even**: Since 2b² is even, a² is even
6. **a is even**: If a² is even, then a is even (a = 2k for some integer k)
7. **Substitute**: 2b² = (2k)² = 4k²
8. **Simplify**: b² = 2k²
9. **b² is even**: Since b² = 2k², b² is even
10. **b is even**: If b² is even, then b is even
11. **Contradiction**: Both a and b are even, so gcd(a,b) ≥ 2, contradicting gcd(a,b) = 1
12. **Conclusion**: Our assumption was wrong, so √2 is irrational. Q.E.D."""
            
            samples.append(MathTrainingSample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                category="analysis",
                difficulty="advanced",
                tags=["proof", "irrational", "contradiction", "theorem"]
            ))
        
        # Sum of first n natural numbers
        for _ in range(count // 3):
            instruction = "Prove the formula for sum of first n natural numbers using mathematical induction"
            input_text = "Prove that 1 + 2 + ... + n = n(n+1)/2 using induction"
            output_text = """Proof by mathematical induction that 1 + 2 + ... + n = n(n+1)/2:

**Base Case** (n = 1):
- Left side: 1
- Right side: 1(1+1)/2 = 2/2 = 1
- Both sides equal, so base case holds

**Inductive Hypothesis**:
Assume that for some k ≥ 1: 1 + 2 + ... + k = k(k+1)/2

**Inductive Step** (show for n = k+1):
We want to show: 1 + 2 + ... + k + (k+1) = (k+1)((k+1)+1)/2

Starting with the left side:
1 + 2 + ... + k + (k+1) = [1 + 2 + ... + k] + (k+1)
                           = k(k+1)/2 + (k+1)    [by inductive hypothesis]
                           = k(k+1)/2 + 2(k+1)/2
                           = [k(k+1) + 2(k+1)]/2
                           = (k+1)(k + 2)/2
                           = (k+1)((k+1) + 1)/2

This matches the right side, so the inductive step holds.

**Conclusion**:
By mathematical induction, 1 + 2 + ... + n = n(n+1)/2 for all positive integers n. Q.E.D."""
            
            samples.append(MathTrainingSample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                category="algebra",
                difficulty="advanced",
                tags=["proof", "induction", "formula", "sum"]
            ))
        
        return samples
    
    def generate_geometric_samples(self, count: int = 40) -> List[MathTrainingSample]:
        """Generate geometry training samples."""
        samples = []
        
        for _ in range(count):
            radius = random.randint(1, 10)
            area = sp.pi * radius**2
            
            instruction = "Calculate the area of a circle given its radius"
            input_text = f"What is the area of a circle with radius {radius}?"
            output_text = f"The area of a circle with radius {radius} is {area}\nFormula: Area = πr²\nCalculation: Area = π × {radius}² = π × {radius**2} = {area}"
            
            samples.append(MathTrainingSample(
                instruction=instruction,
                input=input_text,
                output=output_text,
                category="geometry",
                difficulty="beginner",
                tags=["area", "circle", "geometry", "formula"]
            ))
        
        # Pythagorean theorem
        for _ in range(count // 3):
            a_side = random.randint(1, 12)
            b_side = random.randint(1, 12)
            c_sq = a_side**2 + b_side**2
            c_side = sp.sqrt(c_sq)
            
            instruction = "Apply the Pythagorean theorem"
            input_text = f"In a right triangle with legs a={a_side} and b={b_side}, find the hypotenuse c."
            output_text = f"c = √({a_side}² + {b_side}²) = √{c_sq} = {c_side}\nBy the Pythagorean theorem: a² + b² = c²\n{a_side}² + {b_side}² = {a_side**2} + {b_side**2} = {c_sq}\nc = √{c_sq} = {c_side}"
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="geometry", difficulty="intermediate",
                tags=["pythagorean", "triangle", "geometry"]
            ))
        
        return samples
    
    def generate_number_theory_samples(self, count: int = 40) -> List[MathTrainingSample]:
        """Generate number theory training samples."""
        samples = []
        
        for _ in range(count // 4):
            p = random.choice([3, 5, 7, 11, 13, 17, 19, 23, 29, 31])
            a = random.randint(2, p - 1)
            result = pow(a, p - 1, p)
            
            instruction = "Verify Fermat's Little Theorem for given values"
            input_text = f"Verify Fermat's Little Theorem: a={a}, p={p}"
            output_text = f"""Fermat's Little Theorem states: if p is prime and gcd(a,p)=1, then a^(p-1) ≡ 1 (mod p).

Given: a={a}, p={p}
1. Check p={p} is prime: YES
2. Check gcd({a},{p})=1: YES
3. Compute a^(p-1) mod p = {a}^{p-1} mod {p} = {result}
4. Since {result} ≡ 1 (mod {p}), Fermat's Little Theorem is verified. ✓"""
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="number_theory", difficulty="intermediate",
                tags=["fermat", "modular", "prime", "number_theory"]
            ))
        
        for _ in range(count // 4):
            n = random.randint(2, 100)
            is_prime = sp.isprime(n)
            
            instruction = "Determine if a number is prime and explain"
            input_text = f"Is {n} a prime number?"
            if is_prime:
                output_text = f"Yes, {n} is prime.\n\nA prime number is divisible only by 1 and itself. Checking divisibility by primes up to √{n} ≈ {int(sp.sqrt(n))+1}, none divide {n}. Therefore {n} is prime."
            else:
                factors = sp.factorint(n)
                factor_str = " × ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in factors.items())
                output_text = f"No, {n} is not prime. {n} = {factor_str}"
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="number_theory", difficulty="beginner",
                tags=["primality", "factorization", "number_theory"]
            ))
        
        for _ in range(count // 4):
            a, b = random.randint(2, 30), random.randint(2, 30)
            g = sp.gcd(a, b)
            
            instruction = "Compute the GCD using Euclidean algorithm"
            input_text = f"Find gcd({a}, {b}) using the Euclidean algorithm"
            
            steps = []
            x_val, y_val = max(a, b), min(a, b)
            while y_val:
                q, r = divmod(x_val, y_val)
                steps.append(f"{x_val} = {q}·{y_val} + {r}")
                x_val, y_val = y_val, r
            output_text = f"gcd({a}, {b}) = {g}\n\nEuclidean algorithm steps:\n" + "\n".join(steps) + f"\n\nThe last non-zero remainder is {g}, so gcd({a}, {b}) = {g}."
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="number_theory", difficulty="intermediate",
                tags=["gcd", "euclidean", "number_theory"]
            ))
        
        for _ in range(count - 3*(count//4)):
            base = random.randint(2, 10)
            mod = random.choice([7, 11, 13, 17, 19])
            exp = random.randint(2, mod - 1)
            result = pow(base, exp, mod)
            
            instruction = "Compute modular exponentiation efficiently"
            input_text = f"Compute {base}^{exp} mod {mod}"
            output_text = f"Using repeated squaring:\n{base}^{exp} mod {mod} = {result}\n\nVerification: {base}^{exp} = {base**exp}, {base**exp} mod {mod} = {result}"
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="number_theory", difficulty="advanced",
                tags=["modular", "exponentiation", "number_theory"]
            ))
        
        return samples
    
    def generate_analysis_samples(self, count: int = 30) -> List[MathTrainingSample]:
        """Generate real analysis training samples."""
        samples = []
        
        for _ in range(count // 3):
            num = random.randint(1, 20)
            den = random.randint(1, 20)
            dec_val = num / den
            instruction = "Convert a fraction to a decimal and determine if it terminates"
            input_text = f"Is {num}/{den} a terminating decimal?"
            factors = sp.factorint(den)
            only_2_5 = all(p in [2, 5] for p in factors)
            if only_2_5 and factors:
                output_text = f"Yes, {num}/{den} = {dec_val:.10g} terminates.\nA fraction terminates iff its denominator (in lowest terms) has only 2 and 5 as prime factors. {den} = {' × '.join(f'{p}^{e}' if e>1 else str(p) for p,e in factors.items())}, which contains only 2s and 5s."
            else:
                output_text = f"No, {num}/{den} = {dec_val:.10g}... repeats.\nThe denominator {den} has prime factors other than 2 and 5, so the decimal expansion repeats."
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="analysis", difficulty="intermediate",
                tags=["decimal", "terminating", "analysis"]
            ))
        
        for _ in range(count // 3):
            instruction = "Prove that the limit of 1/n as n→∞ equals 0 using the ε-N definition"
            input_text = "Prove: lim(n→∞) 1/n = 0 using the ε-N definition"
            output_text = """Proof using ε-N definition:

We need to show: for every ε > 0, there exists N ∈ ℕ such that for all n ≥ N, |1/n - 0| < ε.

Let ε > 0 be given.
Choose N > 1/ε (such N exists by the Archimedean property).
For all n ≥ N:
  |1/n - 0| = 1/n ≤ 1/N < ε

Since N > 1/ε, we have 1/N < ε, so 1/n < ε for all n ≥ N.
Therefore lim(n→∞) 1/n = 0. Q.E.D."""
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="analysis", difficulty="advanced",
                tags=["limit", "epsilon", "proof", "analysis"]
            ))
        
        for _ in range(count - 2*(count//3)):
            instruction = "State and apply the Intermediate Value Theorem"
            input_text = "Use the IVT to show that x³ - x - 1 = 0 has a root in [1, 2]"
            output_text = """By the Intermediate Value Theorem:
If f is continuous on [a,b] and f(a) and f(b) have opposite signs, then ∃ c ∈ (a,b) with f(c) = 0.

Let f(x) = x³ - x - 1.
f(1) = 1 - 1 - 1 = -1 < 0
f(2) = 8 - 2 - 1 = 5 > 0

Since f is continuous (polynomial) and f(1) < 0 < f(2), by IVT there exists c ∈ (1,2) such that f(c) = 0. ✓"""
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="analysis", difficulty="advanced",
                tags=["IVT", "intermediate_value", "continuous", "analysis"]
            ))
        
        return samples
    
    def generate_linear_algebra_samples(self, count: int = 30) -> List[MathTrainingSample]:
        """Generate linear algebra training samples."""
        samples = []
        
        for _ in range(count // 3):
            size = random.choice([2, 3])
            entries = [random.randint(-5, 5) for _ in range(size * size)]
            matrix = sp.Matrix(size, size, entries)
            det_val = matrix.det()
            
            instruction = "Compute the determinant of a matrix"
            input_text = f"Find the determinant of:\n{matrix}"
            output_text = f"det = {det_val}\n\nUsing cofactor expansion along the first row:\ndet(A) = {det_val}"
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="linear_algebra", difficulty="intermediate",
                tags=["determinant", "matrix", "linear_algebra"]
            ))
        
        for _ in range(count // 3):
            a_val, b_val = random.randint(-5, 5), random.randint(-5, 5)
            c_val, d_val = random.randint(-5, 5), random.randint(-5, 5)
            if a_val * d_val - b_val * c_val == 0:
                c_val += 1
            m = sp.Matrix([[a_val, b_val], [c_val, d_val]])
            inv = m.inv()
            
            instruction = "Find the inverse of a 2×2 matrix"
            input_text = f"Find A⁻¹ for A = [[{a_val}, {b_val}], [{c_val}, {d_val}]]"
            output_text = f"""For 2×2 matrix A = [[{a_val},{b_val}],[{c_val},{d_val}]]:
det(A) = {a_val}·{d_val} - {b_val}·{c_val} = {m.det()}
A⁻¹ = (1/det(A)) · [[{d_val}, {-b_val}], [{-c_val}, {a_val}]]
A⁻¹ = {inv}"""
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="linear_algebra", difficulty="intermediate",
                tags=["inverse", "matrix", "linear_algebra"]
            ))
        
        for _ in range(count - 2*(count//3)):
            size = random.choice([2, 3])
            m = sp.Matrix(size, size, [random.randint(-3, 3) for _ in range(size*size)])
            eigenvals = m.eigenvals()
            
            instruction = "Find the eigenvalues of a matrix"
            input_text = f"Find the eigenvalues of:\n{m}"
            eig_str = ", ".join(f"λ={k} (mult={v})" for k, v in eigenvals.items())
            output_text = f"Eigenvalues: {eig_str}\n\nFound by solving det(A - λI) = 0."
            
            samples.append(MathTrainingSample(
                instruction=instruction, input=input_text, output=output_text,
                category="linear_algebra", difficulty="advanced",
                tags=["eigenvalue", "matrix", "linear_algebra"]
            ))
        
        return samples
    
    def generate_training_dataset(self, size_per_category: Dict[str, int] = None) -> List[Dict[str, Any]]:
        """Generate a complete training dataset."""
        if size_per_category is None:
            size_per_category = {
                "algebra": 150,
                "calculus": 100, 
                "proofs": 50,
                "geometry": 100,
                "number_theory": 40,
                "analysis": 30,
                "linear_algebra": 30,
            }
        
        all_samples = []
        
        if "algebra" in size_per_category:
            all_samples.extend(self.generate_algebra_samples(size_per_category["algebra"]))
        if "calculus" in size_per_category:
            all_samples.extend(self.generate_calculus_samples(size_per_category["calculus"]))
        if "proofs" in size_per_category:
            all_samples.extend(self.generate_proof_samples(size_per_category["proofs"]))
        if "geometry" in size_per_category:
            all_samples.extend(self.generate_geometric_samples(size_per_category["geometry"]))
        if "number_theory" in size_per_category:
            all_samples.extend(self.generate_number_theory_samples(size_per_category["number_theory"]))
        if "analysis" in size_per_category:
            all_samples.extend(self.generate_analysis_samples(size_per_category["analysis"]))
        if "linear_algebra" in size_per_category:
            all_samples.extend(self.generate_linear_algebra_samples(size_per_category["linear_algebra"]))
        
        # Convert to training format suitable for fine-tuning
        training_data = []
        for sample in all_samples:
            # Pick a random conversation template
            template = random.choice(self.conversation_templates)
            
            training_entry = {
                "messages": [
                    {"role": "system", "content": template["system"]},
                    {"role": "user", "content": f"{template['user_prefix']}\n{sample.input}"},
                    {"role": "assistant", "content": f"{template['assistant_prefix']}\n{sample.output}"}
                ],
                "category": sample.category,
                "difficulty": sample.difficulty,
                "tags": sample.tags
            }
            training_data.append(training_entry)
        
        return training_data
    
    def save_training_data(self, training_data: List[Dict[str, Any]], filename: str):
        """Save training data to JSONL file."""
        with open(filename, 'w', encoding='utf-8') as f:
            for entry in training_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def generate_formatted_dataset(self, output_file: str = "math_reasoning_dataset.jsonl"):
        """Generate and save a complete mathematical reasoning training dataset."""
        print("Generating mathematical reasoning training dataset...")
        
        dataset = self.generate_training_dataset({
            "algebra": 200,
            "calculus": 150,
            "proofs": 80,
            "geometry": 120,
            "number_theory": 60,
            "analysis": 45,
            "linear_algebra": 45,
        })
        
        self.save_training_data(dataset, output_file)
        print(f"Generated {len(dataset)} training samples in {output_file}")
        
        # Print statistics
        categories = {}
        difficulties = {}
        for entry in dataset:
            cat = entry['category']
            diff = entry['difficulty']
            categories[cat] = categories.get(cat, 0) + 1
            difficulties[diff] = difficulties.get(diff, 0) + 1
        
        print(f"Dataset statistics:")
        print(f"  Categories: {categories}")
        print(f"  Difficulties: {difficulties}")
        
        return dataset


def main():
    """Generate mathematical reasoning training data."""
    generator = MathTrainingDataGenerator()
    dataset = generator.generate_formatted_dataset("jiuzhang_math_training.jsonl")
    print(f"Successfully generated {len(dataset)} training samples!")


if __name__ == "__main__":
    main()