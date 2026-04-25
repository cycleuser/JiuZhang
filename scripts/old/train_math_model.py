#!/usr/bin/env python3
"""JiuZhang Math Model Builder — automated Ollama model creation + evaluation.

Workflow:
  1. Generate (or reuse) training data via jiuzhang.train_math_model
  2. Create an Ollama Modelfile with math-optimised parameters
  3. Call ``ollama create`` to build the model
  4. Optionally run a quick evaluation against test prompts
  5. Print instructions for wiring the model into JiuZhang

Requirements:
  - Ollama must be installed and running (``ollama serve``)
  - The base model must already be pulled (e.g. ``ollama pull mistral:7b``)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_BASE_MODEL = "qwen3.5:0.8b"
DEFAULT_DATASET = "jiuzhang_math_training.jsonl"
MODEL_NAME_PREFIX = "jiu-math"

EVAL_PROMPTS = [
    {
        "prompt": "Prove that the sum of the first n positive integers equals n(n+1)/2.",
        "keywords": ["induction", "n(n+1)/2", "Q.E.D", "base case"],
        "category": "proof",
    },
    {
        "prompt": "Solve for x: 3x + 7 = 22",
        "keywords": ["x = 5", "5"],
        "category": "algebra",
    },
    {
        "prompt": "Find the derivative of f(x) = x^3 + 2x^2 - 5x + 1.",
        "keywords": ["3x^2", "4x", "3x²"],
        "category": "calculus",
    },
    {
        "prompt": "Simplify: (a+b)^2 - (a-b)^2",
        "keywords": ["4ab", "4*a*b"],
        "category": "algebra",
    },
    {
        "prompt": "What is the integral of 2x dx?",
        "keywords": ["x^2", "x²", "C"],
        "category": "calculus",
    },
]


def _run(cmd, check=True, capture=True):
    r = subprocess.run(
        cmd, shell=isinstance(cmd, str),
        capture_output=capture, text=True, check=check,
    )
    return r


def _slug(model_name: str) -> str:
    return model_name.replace(":", "-").replace("/", "-")


def generate_dataset(path: str, force: bool = False) -> int:
    if Path(path).exists() and not force:
        count = sum(1 for line in Path(path).read_text().splitlines() if line.strip())
        print(f"Dataset already exists at {path} ({count} samples). Use --force to regenerate.")
        return count
    print(f"Generating training dataset → {path}")
    from jiuzhang.train_math_model import MathTrainingDataGenerator
    gen = MathTrainingDataGenerator()
    gen.generate_formatted_dataset(path)
    count = sum(1 for line in Path(path).read_text().splitlines() if line.strip())
    print(f"Generated {count} samples.")
    return count


def create_modelfile(base_model: str, dataset_path: str, output_path: str) -> str:
    abs_dataset = str(Path(dataset_path).resolve())
    content = f"""FROM {base_model}

PARAMETER temperature 0.1
PARAMETER top_p 0.8
PARAMETER num_ctx 4096
PARAMETER presence_penalty 0.3
PARAMETER frequency_penalty 0.3
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_header_id|>"

SYSTEM \"\"\"You are JiuZhang-Math, a specialized mathematical reasoning assistant. You:
- Provide step-by-step mathematical proofs with clear logical flow
- Solve complex mathematical problems showing all work
- Perform symbolic computations accurately
- Analyze mathematical conjectures with rigor
- Verify your own solutions when possible
- Use formal mathematical notation appropriately
- Express the same concept in both Chinese and English when helpful
\"\"\"
"""
    Path(output_path).write_text(content, encoding="utf-8")
    print(f"Modelfile written → {output_path}")
    return output_path


def build_ollama_model(modelfile_path: str, model_name: str) -> bool:
    if not shutil.which("ollama"):
        print("ERROR: 'ollama' not found in PATH. Install from https://ollama.com")
        return False
    print(f"Building Ollama model '{model_name}' from {modelfile_path} ...")
    try:
        r = _run(["ollama", "create", model_name, "-f", modelfile_path], check=False)
        if r.returncode != 0:
            print(f"ollama create failed:\n{r.stderr}")
            return False
        print(f"Model '{model_name}' created successfully.")
        return True
    except FileNotFoundError:
        print("ERROR: 'ollama' CLI not found. Is Ollama installed?")
        return False


def evaluate_model(model_name: str, prompts=None, timeout_per=60) -> dict:
    if prompts is None:
        prompts = EVAL_PROMPTS
    if not shutil.which("ollama"):
        print("ERROR: 'ollama' not found — skipping evaluation.")
        return {"error": "ollama not found"}

    results = []
    print(f"\nEvaluating model '{model_name}' on {len(prompts)} test prompts ...")
    for item in prompts:
        prompt = item["prompt"]
        try:
            r = _run(
                ["ollama", "run", model_name, prompt],
                check=False, capture=True,
            )
            response = r.stdout.strip() if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"
        except Exception as e:
            response = f"ERROR: {e}"

        matched = sum(1 for kw in item["keywords"] if kw.lower() in response.lower())
        total = len(item["keywords"])
        results.append({
            "category": item["category"],
            "prompt": prompt[:80],
            "keyword_hits": f"{matched}/{total}",
            "response_preview": response[:200],
            "pass": matched >= max(1, total // 2),
        })
        status = "PASS" if results[-1]["pass"] else "FAIL"
        print(f"  [{status}] {item['category']}: {matched}/{total} keywords matched")

    passed = sum(1 for r in results if r["pass"])
    summary = {
        "model": model_name,
        "total_prompts": len(prompts),
        "passed": passed,
        "failed": len(prompts) - passed,
        "pass_rate": f"{passed}/{len(prompts)}",
        "details": results,
    }
    print(f"\nEvaluation summary: {passed}/{len(prompts)} prompts passed")
    return summary


def print_config_instructions(model_name: str):
    print(f"""
{'='*60}
NEXT STEPS — Wire the model into JiuZhang
{'='*60}

1. Set environment variables:
   export JIUZHANG_THEOREM_MODEL={model_name}
   export JIUZHANG_SYMBOLIC_MODEL={model_name}
   export JIUZHANG_NUMERICAL_MODEL={model_name}

2. Or update jiuzhang/math_config.py defaults:
   theorem_proving_model: str = "{model_name}"
   symbolic_computation_model: str = "{model_name}"
   numerical_computation_model: str = "{model_name}"

3. Test from CLI:
   python -m jiuzhang --math-solve "Solve for x: 3x + 7 = 22"

4. Or via API:
   curl -X POST http://localhost:5000/api/math/solve \\
     -H 'Content-Type: application/json' \\
     -d '{{"problem": "Solve for x: 3x + 7 = 22"}}'
""")


def main():
    parser = argparse.ArgumentParser(
        description="JiuZhang Math Model Builder — generate data, create Modelfile, build & evaluate Ollama model"
    )
    sub = parser.add_subparsers(dest="command")

    p_all = sub.add_parser("all", help="End-to-end: generate data → create Modelfile → build → evaluate")
    p_all.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    p_all.add_argument("--dataset", default=DEFAULT_DATASET)
    p_all.add_argument("--force", action="store_true", help="Regenerate dataset even if it exists")
    p_all.add_argument("--no-eval", action="store_true", help="Skip evaluation after building")

    p_build = sub.add_parser("build", help="Build Ollama model from existing Modelfile")
    p_build.add_argument("modelfile", help="Path to Modelfile")
    p_build.add_argument("--name", help="Model name (default: jiu-math-<base>)")

    p_modelfile = sub.add_parser("modelfile", help="Create Modelfile only (no build)")
    p_modelfile.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    p_modelfile.add_argument("--dataset", default=DEFAULT_DATASET)
    p_modelfile.add_argument("--output", default=None)

    p_eval = sub.add_parser("eval", help="Evaluate an existing Ollama model")
    p_eval.add_argument("model_name", help="Ollama model name to evaluate")

    p_generate = sub.add_parser("generate", help="Generate training dataset only")
    p_generate.add_argument("--output", default=DEFAULT_DATASET)
    p_generate.add_argument("--force", action="store_true")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "generate":
        generate_dataset(args.output, force=args.force)

    elif args.command == "modelfile":
        out = args.output or f"Modelfile.{_slug(args.base_model)}"
        create_modelfile(args.base_model, args.dataset, out)

    elif args.command == "build":
        name = args.name or f"{MODEL_NAME_PREFIX}-{_slug(DEFAULT_BASE_MODEL)}"
        build_ollama_model(args.modelfile, name)

    elif args.command == "eval":
        evaluate_model(args.model_name)

    elif args.command == "all":
        slug = _slug(args.base_model)
        model_name = f"{MODEL_NAME_PREFIX}-{slug}"
        modelfile = f"Modelfile.{slug}"

        generate_dataset(args.dataset, force=args.force)
        create_modelfile(args.base_model, args.dataset, modelfile)

        if build_ollama_model(modelfile, model_name):
            if not args.no_eval:
                evaluate_model(model_name)
            print_config_instructions(model_name)
        else:
            print("\nBuild failed. Fix the errors above and retry.")
            sys.exit(1)


if __name__ == "__main__":
    main()