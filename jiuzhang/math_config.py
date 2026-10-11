"""Mathematical Model Configuration for JiuZhang.

Optimized configuration settings for mathematical reasoning tasks.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Mathematical reasoning specific configurations
@dataclass
class MathModelConfig:
    """Configuration for mathematical reasoning models."""
    
    # Model selection for different mathematical tasks
    theorem_proving_model: str = "deepseek-math:7b"
    symbolic_computation_model: str = "deepseek-coder:6.7b"  # Good for symbolic manipulation
    numerical_computation_model: str = "llama3:8b"
    proof_verification_model: str = "deepseek-math:7b"
    
    # Mathematical reasoning parameters
    temperature: float = 0.1  # Lower temperature for more consistent math reasoning
    max_tokens: int = 2048    # Higher for detailed proofs
    top_p: float = 0.8        # Nucleus sampling for math precision
    presence_penalty: float = 0.3  # Reduce repetition in proofs
    frequency_penalty: float = 0.3
    
    # Mathematical reasoning settings
    enable_chain_of_thought: bool = True
    use_formal_verification: bool = False
    require_step_by_step: bool = True
    enable_symbolic_validation: bool = True
    use_mathematical_axioms: bool = True
    
    # Knowledge base settings
    use_internal_math_knowledge: bool = True
    enable_external_fact_checking: bool = True
    use_proof_techniques_database: bool = True
    enable_counterexample_search: bool = True
    
    def get_model_for_task(self, task_type: str) -> str:
        """Get the appropriate model for a specific mathematical task."""
        model_map = {
            "theorem_proving": self.theorem_proving_model,
            "proof_generation": self.theorem_proving_model,
            "symbolic_computation": self.symbolic_computation_model,
            "numerical_computation": self.numerical_computation_model,
            "proof_verification": self.proof_verification_model,
            "problem_solving": self.theorem_proving_model,
            "conjecture_analysis": self.theorem_proving_model,
        }
        return model_map.get(task_type, self.theorem_proving_model)
    
    def get_reasoning_params(self, task_type: str) -> Dict[str, float]:
        """Get optimal parameters for mathematical reasoning."""
        base_params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        
        # Adjust parameters based on task type
        if task_type in ["theorem_proving", "proof_generation", "proof_verification"]:
            # Need more precision and consistency
            base_params["temperature"] = 0.05  # Even lower for proofs
            base_params["presence_penalty"] = 0.4
        elif task_type in ["symbolic_computation"]:
            # Need accuracy for symbolic manipulation
            base_params["temperature"] = 0.1
        elif task_type in ["conjecture_analysis"]:
            # May need more creative exploration
            base_params["temperature"] = 0.2
        
        return base_params


# Mathematical prompting strategies
MATHEMATICAL_PROMPTING_STRATEGIES = {
    "chain_of_thought": {
        "prefix": "Let's reason step by step to solve this mathematical problem.",
        "template": "Problem: {problem}\n\nLet's think step by step:\n1. ",
        "enabled": True
    },
    "self_consistency": {
        "prefix": "I will solve this problem multiple times and verify consistency.",
        "template": "Problem: {problem}\n\nApproach 1:...\nApproach 2:...\nConsistency Check:",
        "enabled": False  # Requires multiple model calls
    },
    "verifier_based": {
        "prefix": "I will generate a solution and then verify it.",
        "template": "Problem: {problem}\n\nSolution:...\n\nVerification: Let me check this solution...",
        "enabled": True
    },
    "axiom_based": {
        "prefix": "I will use established mathematical axioms and theorems.",
        "template": "Problem: {problem}\n\nUsing axioms: [list relevant axioms]\nSolution based on axioms:",
        "enabled": True
    }
}


# Mathematical knowledge base
MATHEMATICAL_KNOWLEDGE_BASE = {
    "algebra": {
        "theorems": [
            "Fundamental Theorem of Algebra",
            "Binomial Theorem", 
            "Quadratic Formula",
            "Polynomial Remainder Theorem"
        ],
        "identities": [
            "a² - b² = (a-b)(a+b)",
            "a² + 2ab + b² = (a+b)²",
            "e^(iπ) + 1 = 0 (Euler's identity)"
        ]
    },
    "calculus": {
        "theorems": [
            "Fundamental Theorem of Calculus",
            "Mean Value Theorem",
            "Intermediate Value Theorem",
            "Taylor's Theorem"
        ],
        "rules": [
            "Chain Rule: (f(g(x)))' = f'(g(x)) * g'(x)",
            "Product Rule: (fg)' = f'g + fg'",
            "Quotient Rule: (f/g)' = (f'g - fg')/g²"
        ]
    },
    "geometry": {
        "theorems": [
            "Pythagorean Theorem",
            "Law of Sines",
            "Law of Cosines",
            "Euler's Formula for Polyhedra"
        ]
    },
    "number_theory": {
        "theorems": [
            "Fundamental Theorem of Arithmetic",
            "Fermat's Little Theorem",
            "Chinese Remainder Theorem",
            "Euclid's Lemma"
        ]
    }
}


def get_optimal_math_config(task_type: str = "general") -> MathModelConfig:
    """Get optimal configuration for mathematical reasoning."""
    config = MathModelConfig()
    
    # Adjust based on task type if specified
    if task_type == "theorem_proving":
        config.temperature = 0.05
        config.max_tokens = 3072  # Longer proofs need more tokens
        config.use_proof_techniques_database = True
    elif task_type == "symbolic_computation":
        config.temperature = 0.1
        config.enable_symbolic_validation = True
    elif task_type == "numerical_computation":
        config.temperature = 0.15
        config.require_step_by_step = False  # Can be more direct
    elif task_type == "conjecture_analysis":
        config.temperature = 0.2
        config.enable_counterexample_search = True
    
    return config


def load_math_config_from_env() -> MathModelConfig:
    """Load mathematical configuration from environment variables."""
    config = MathModelConfig()
    
    # Override with environment variables if present
    if os.environ.get("JIUZHANG_MATH_TEMPERATURE"):
        config.temperature = float(os.environ["JIUZHANG_MATH_TEMPERATURE"])
    if os.environ.get("JIUZHANG_MATH_MAX_TOKENS"):
        config.max_tokens = int(os.environ["JIUZHANG_MATH_MAX_TOKENS"])
    if os.environ.get("JIUZHANG_MATH_TOP_P"):
        config.top_p = float(os.environ["JIUZHANG_MATH_TOP_P"])
    
    # Model selections
    if os.environ.get("JIUZHANG_THEOREM_MODEL"):
        config.theorem_proving_model = os.environ["JIUZHANG_THEOREM_MODEL"]
    if os.environ.get("JIUZHANG_SYMBOLIC_MODEL"):
        config.symbolic_computation_model = os.environ["JIUZHANG_SYMBOLIC_MODEL"]
    if os.environ.get("JIUZHANG_NUMERICAL_MODEL"):
        config.numerical_computation_model = os.environ["JIUZHANG_NUMERICAL_MODEL"]
    
    return config


# Default configuration
MATH_CONFIG = get_optimal_math_config()