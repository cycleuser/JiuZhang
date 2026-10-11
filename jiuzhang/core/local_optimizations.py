"""Local Model Optimizations for JiuZhang.

Provides specialized support for running math research on local models:
- llama.cpp server integration (better math performance than Ollama)
- MLX support for Apple Silicon (M1/M2/M3/M4)
- Grammar-constrained sampling for structured math output
- Speculative decoding hints for math reasoning chains
- Quantization-aware model loading
- Batch inference for multiple conjectures
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
import json
import os
import re
import subprocess
import time


class LocalBackend(Enum):
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    MLX = "mlx"          # Apple Silicon
    TRANSFORMERS = "transformers"  # HuggingFace
    VLLM = "vllm"        # High-throughput


@dataclass
class LocalModelConfig:
    backend: LocalBackend = LocalBackend.OLLAMA
    model_path: str = ""
    model_name: str = "qwen2.5:7b"
    endpoint_url: str = "http://localhost:11434/v1"

    # Quantization
    quantization: str = ""  # "q4_K_M", "q8_0", "f16"
    n_gpu_layers: int = -1  # -1 = all
    context_length: int = 8192

    # Performance
    n_threads: int = 8
    batch_size: int = 512
    flash_attention: bool = True

    # Sampling
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.1


# ── Math Grammar Definitions ──────────────────────────────────────────

# JSON schema for structured mathematical output
MATH_PROOF_GRAMMAR = {
    "type": "object",
    "properties": {
        "theorem_statement": {"type": "string"},
        "proof_type": {"type": "string", "enum": [
            "direct", "contradiction", "induction", "contrapositive", "construction"
        ]},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "statement": {"type": "string"},
                    "justification": {"type": "string"},
                    "latex": {"type": "string"},
                },
                "required": ["step_number", "statement"],
            },
        },
        "conclusion": {"type": "string"},
        "qed": {"type": "boolean"},
    },
}

MATH_SOLUTION_GRAMMAR = {
    "type": "object",
    "properties": {
        "problem": {"type": "string"},
        "domain": {"type": "string"},
        "solution_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "integer"},
                    "action": {"type": "string"},
                    "expression": {"type": "string"},
                    "latex": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
        },
        "final_answer": {"type": "string"},
        "verification": {"type": "string"},
    },
}


def build_grammar_constraint(grammar: dict) -> str:
    """Convert a JSON schema to a GBNF grammar string for llama.cpp.

    GBNF (GGML BNF) constrains the model's output to follow a specific grammar,
    ensuring structured, parseable mathematical outputs.
    """
    # Simplified GBNF generator — for production, use llama.cpp's built-in
    # json_schema_to_grammar or the full GBNF specification.

    if "proof_type" in str(grammar):
        # Proof grammar
        return r"""
root ::= proof
proof ::= "{\n  \"theorem_statement\": \"" statement "\",\n  \"proof_type\": \"" prooftype "\",\n  \"assumptions\": [" assumptions "],\n  \"steps\": [" steps "],\n  \"conclusion\": \"" conclusion "\",\n  \"qed\": " qed "\n}"
statement ::= [^\"]+
prooftype ::= "direct" | "contradiction" | "induction" | "contrapositive" | "construction"
assumptions ::= string ("," string)*
steps ::= step ("," step)*
step ::= "{\n    \"step_number\": " [0-9]+ ",\n    \"statement\": \"" [^\"]+ "\",\n    \"justification\": \"" [^\"]+ "\",\n    \"latex\": \"" [^\"]+ "\"\n  }"
conclusion ::= [^\"]+
qed ::= "true" | "false"
string ::= "\"" [^\"]* "\""
"""
    return ""


# ── Speculative Decoding Hints ───────────────────────────────────────

MATH_REASONING_PREFIXES = {
    "theorem_proof": (
        "I will prove this theorem step by step.\n\n"
        "**Proof:**\n\n"
    ),
    "problem_solving": (
        "Let me solve this problem systematically.\n\n"
        "**Solution:**\n\n"
        "Step 1: Understand the problem.\n"
    ),
    "conjecture_analysis": (
        "I will analyze this conjecture by:\n"
        "1. Examining known results\n"
        "2. Testing small cases\n"
        "3. Attempting a proof or finding counterexamples\n\n"
    ),
    "symbolic_computation": (
        "Let me compute this using SymPy.\n\n"
        "```python\n"
        "import sympy as sp\n"
    ),
    "derivation": (
        "I will derive this step by step:\n\n"
        "Starting from:\n"
    ),
}


def get_reasoning_hint(task_type: str) -> str:
    """Get a speculative decoding prefix to jump-start reasoning chains.

    By providing the first few tokens of a reasoning chain, we help local models
    get into the right "mode" faster, reducing the chance of rambling or confusion.
    """
    return MATH_REASONING_PREFIXES.get(task_type, "")


# ── LLM Output Cleaning ───────────────────────────────────────────────

def clean_math_output(text: str) -> str:
    """Clean up common issues in local model math output.

    Local models often produce slightly malformed LaTeX, incomplete proofs,
    or mixed formatting. This function cleans common issues.
    """
    # Fix unclosed LaTeX delimiters
    dollar_count = text.count("$") - text.count("$$") * 2
    if dollar_count % 2 != 0:
        text += "$"

    # Fix unclosed code blocks
    code_open = text.count("```")
    if code_open % 2 != 0:
        text += "\n```"

    # Remove trailing incomplete lines
    lines = text.split("\n")
    if lines and len(lines[-1]) < 5 and not lines[-1].endswith((".", "?", "!")):
        lines = lines[:-1]
        text = "\n".join(lines)

    # Fix common LaTeX errors
    text = text.replace("\\begin{align}", "\\begin{aligned}")
    text = text.replace("\\end{align}", "\\end{aligned}")

    # Ensure proper spacing around operators
    for op in ["+", "-", "=", "×", "÷"]:
        text = re.sub(rf'(?<=\w){re.escape(op)}(?=\w)', f' {op} ', text)

    return text.strip()


# ── MLX Integration (Apple Silicon) ──────────────────────────────────

class MLXModelLoader:
    """Load and run models on Apple Silicon via MLX.

    Provides optimized inference for Mac users with M1/M2/M3/M4 chips.
    Uses the mlx-lm package for model loading and inference.
    """

    def __init__(self, config: Optional[LocalModelConfig] = None):
        self.config = config or LocalModelConfig(backend=LocalBackend.MLX)
        self._model = None
        self._tokenizer = None

    @property
    def is_available(self) -> bool:
        """Check if MLX is available on this system."""
        try:
            import mlx.core  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self, model_path: str):
        """Load a model via MLX."""
        if not self.is_available:
            raise RuntimeError("MLX is not available. Install with: pip install mlx-lm")

        try:
            from mlx_lm import load
            self._model, self._tokenizer = load(model_path)
        except ImportError:
            raise RuntimeError("mlx-lm not installed. Install with: pip install mlx-lm")

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text using the loaded MLX model."""
        if not self._model:
            raise RuntimeError("Model not loaded. Call load() first.")

        try:
            from mlx_lm import generate
            return generate(
                self._model, self._tokenizer,
                prompt=prompt, max_tokens=max_tokens,
                temp=self.config.temperature,
            )
        except ImportError:
            raise RuntimeError("mlx-lm not installed")


# ── Batch Inference ──────────────────────────────────────────────────

@dataclass
class BatchResult:
    prompt: str
    response: str
    latency_ms: float
    success: bool
    error: Optional[str] = None


class BatchInferenceRunner:
    """Run multiple prompts in batch for efficiency.

    Used for testing multiple conjectures or running parallel verifications.
    Supports both sequential (Ollama) and batched (vLLM/llama.cpp) execution.
    """

    def __init__(self, backend: LocalBackend = LocalBackend.OLLAMA, endpoint: str = "http://localhost:11434/v1"):
        self.backend = backend
        self.endpoint = endpoint

    def run_sequential(
        self, prompts: list, model: str = "qwen2.5:7b", max_tokens: int = 256
    ) -> list:
        """Run prompts sequentially (compatible with any backend)."""
        import requests

        results = []
        for prompt in prompts:
            start = time.perf_counter()
            try:
                resp = requests.post(
                    f"{self.endpoint}/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                latency = (time.perf_counter() - start) * 1000
                results.append(BatchResult(
                    prompt=prompt, response=text, latency_ms=latency, success=True,
                ))
            except Exception as e:
                results.append(BatchResult(
                    prompt=prompt, response="", latency_ms=time.perf_counter() * 1000,
                    success=False, error=str(e),
                ))

        return results

    def run_batched_vllm(
        self, prompts: list, model: str = "qwen2.5:7b", max_tokens: int = 256
    ) -> list:
        """Run prompts in batch using vLLM server (much faster for many prompts)."""
        import requests

        try:
            resp = requests.post(
                f"{self.endpoint}/chat/completions",
                json={
                    "model": model,
                    "messages": [[{"role": "user", "content": p}] for p in prompts],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            # vLLM returns list of responses
            choices = data.get("choices", [])
            for i, choice in enumerate(choices):
                results.append(BatchResult(
                    prompt=prompts[i] if i < len(prompts) else "",
                    response=choice.get("message", {}).get("content", ""),
                    latency_ms=0, success=True,
                ))
            return results
        except Exception as e:
            return [
                BatchResult(prompt=p, response="", latency_ms=0, success=False, error=str(e))
                for p in prompts
            ]


# ── Local Model Quality Checks ───────────────────────────────────────

def check_model_math_capability(model_name: str, endpoint: str = "http://localhost:11434/v1") -> dict:
    """Quick benchmark of a local model's math capabilities.

    Runs a few test prompts and scores the model.
    """
    import requests

    test_prompts = [
        {
            "prompt": "What is 123 * 456? Answer with just the number.",
            "expected": ["56088"],
            "type": "arithmetic",
        },
        {
            "prompt": "Solve: x^2 - 5x + 6 = 0. Give the roots.",
            "expected": ["2", "3", "2,3", "2 and 3"],
            "type": "algebra",
        },
        {
            "prompt": "What is the derivative of sin(x)? Answer concisely.",
            "expected": ["cos(x)", "cos x"],
            "type": "calculus",
        },
        {
            "prompt": "Is 97 prime? Answer yes or no.",
            "expected": ["yes", "Yes"],
            "type": "number_theory",
        },
    ]

    results = []
    for test in test_prompts:
        try:
            resp = requests.post(
                f"{endpoint}/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": test["prompt"]}],
                    "max_tokens": 50,
                    "temperature": 0.1,
                },
                timeout=30,
            )
            resp.raise_for_status()
            answer = resp.json()["choices"][0]["message"]["content"].strip().lower()

            passed = any(exp.lower() in answer for exp in test["expected"])
            results.append({
                "type": test["type"],
                "passed": passed,
                "answer": answer[:100],
            })
        except Exception as e:
            results.append({
                "type": test["type"],
                "passed": False,
                "error": str(e),
            })

    passed = sum(1 for r in results if r.get("passed"))
    return {
        "model": model_name,
        "score": f"{passed}/{len(results)}",
        "passed": passed,
        "total": len(results),
        "details": results,
    }
