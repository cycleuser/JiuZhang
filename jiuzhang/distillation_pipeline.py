"""Comprehensive Distillation Pipeline for JiuZhang Math Model Training.

This pipeline combines online models (teachers) with local verification (SymPy)
to create high-quality training data for fine-tuning small local models.

Workflow:
1. Problem Collection: Gather math problems from benchmarks and curriculum
2. Teacher Generation: Send problems to online models (GPT-4, Claude, etc.)
3. Solution Verification: Verify each solution with SymPy ground truth
4. Quality Filtering: Keep only verified, high-quality solutions
5. Data Formatting: Format into ChatML/Alpaca for training
6. Training Script Generation: Generate complete Unsloth/QLoRA training scripts
7. Evaluation: Compare before/after performance

This is the same approach used by DeepSeek-Math, Qwen-Math, and other
state-of-the-art math models.
"""

import json
import os
import time
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.core.config import Config
from jiuzhang.math_benchmark import MathBenchmark, BenchmarkProblem
from jiuzhang.curriculum_pipeline import CurriculumDataPipeline
from jiuzhang.symbolic_verify import (
    verify_equation, verify_derivative, verify_integral,
    verify_solution, verify_limit, VerificationResult,
)
from jiuzhang.rejection_sampling import RejectionSampler


@dataclass
class DistilledSample:
    problem_id: str
    problem_zh: str
    problem_en: str
    teacher_model: str
    teacher_response: str
    verified: bool
    verification_method: str
    verification_detail: str
    final_answer: str
    category: str
    difficulty: str
    quality_score: float


@dataclass
class DistillationResult:
    total_problems: int
    teacher_responses: int
    verified_solutions: int
    failed_verifications: int
    samples: List[DistilledSample] = field(default_factory=list)
    teacher_stats: Dict[str, int] = field(default_factory=dict)
    category_stats: Dict[str, int] = field(default_factory=dict)


class DistillationPipeline:
    """Orchestrates the full distillation pipeline from teacher models to local model training."""

    def __init__(self, config: Optional[Config] = None, seed: int = 42):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)
        self.benchmark = MathBenchmark()
        self.curriculum = CurriculumDataPipeline(seed=seed)
        self.rejection_sampler = RejectionSampler(seed=seed)
        self.rng = random.Random(seed)
        self.samples: List[DistilledSample] = []

    def collect_problems(self, categories: Optional[List[str]] = None,
                         difficulties: Optional[List[str]] = None,
                         count: int = 100) -> List[BenchmarkProblem]:
        """Collect math problems for distillation."""
        problems = self.benchmark.get_problems(categories, difficulties)
        if len(problems) > count:
            problems = self.rng.sample(problems, count)
        return problems

    def generate_teacher_response(self, problem: BenchmarkProblem,
                                   teacher_model: str = None,
                                   max_retries: int = 2) -> Optional[str]:
        """Generate a solution using an online teacher model."""
        if teacher_model is None:
            teacher_model = self.config.active_model

        prompt = f"Please solve the following math problem step by step. Show all your work and provide a clear final answer.\n\nProblem: {problem.problem_en}\n\nSolution:"

        for attempt in range(max_retries):
            try:
                result = self.client.send_message(
                    [{"role": "user", "content": prompt}],
                    model=teacher_model,
                    max_tokens=2048,
                    temperature=0.1,
                )
                if result.success:
                    return result.data
            except Exception as e:
                print(f"  Teacher attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        
        return None

    def verify_solution(self, problem: BenchmarkProblem, solution: str) -> Tuple[bool, str, str]:
        """Verify a teacher's solution against SymPy ground truth."""
        score, detail = self.benchmark.score_response(problem, solution)
        
        symbolic_verified = False
        symbolic_detail = ""
        
        try:
            if problem.sympy_check:
                if "derivative" in problem.category:
                    parts = solution.split("=")
                    if len(parts) == 2:
                        result = verify_derivative(parts[0].strip(), parts[1].strip())
                        symbolic_verified = result.verified
                        symbolic_detail = result.detail
                elif "integral" in problem.category:
                    parts = solution.split("=")
                    if len(parts) == 2:
                        result = verify_integral(parts[0].strip().replace("∫", "").replace("dx", ""), parts[1].strip())
                        symbolic_verified = result.verified
                        symbolic_detail = result.detail
                elif "equation" in problem.category or "=" in problem.problem_en:
                    result = verify_solution(problem.problem_en, solution)
                    symbolic_verified = result.verified
                    symbolic_detail = result.detail
                elif "limit" in problem.category:
                    result = verify_limit(solution, "x", "0")
                    symbolic_verified = result.verified
                    symbolic_detail = result.detail
        except Exception as e:
            symbolic_detail = f"Symbolic verification error: {e}"

        is_verified = (score >= 0.8) or symbolic_verified
        
        if is_verified:
            method = "symbolic" if symbolic_verified else "keyword_match"
            detail = symbolic_detail if symbolic_verified else f"Score: {score:.2f}"
        else:
            method = "failed"
            detail = f"Score: {score:.2f}, Symbolic: {symbolic_detail}"

        return is_verified, method, detail

    def calculate_quality_score(self, problem: BenchmarkProblem, solution: str,
                                 is_verified: bool, verification_method: str) -> float:
        """Calculate a quality score for a distilled sample."""
        score = 0.0
        
        if is_verified:
            score += 0.5
            if verification_method == "symbolic":
                score += 0.3
            else:
                score += 0.1
        
        length_score = min(len(solution) / 500, 0.2)
        score += length_score
        
        step_indicators = ["step", "first", "second", "third", "therefore", "thus", "hence"]
        step_count = sum(1 for indicator in step_indicators if indicator in solution.lower())
        step_score = min(step_count * 0.05, 0.2)
        score += step_score
        
        return min(score, 1.0)

    def run_distillation(self, teacher_model: str = None,
                          categories: Optional[List[str]] = None,
                          difficulties: Optional[List[str]] = None,
                          problem_count: int = 50,
                          output_path: str = "jiuzhang_distilled.jsonl") -> DistillationResult:
        """Run the full distillation pipeline."""
        result = DistillationResult(
            total_problems=0,
            teacher_responses=0,
            verified_solutions=0,
            failed_verifications=0,
        )

        print(f"Step 1: Collecting {problem_count} math problems...")
        problems = self.collect_problems(categories, difficulties, problem_count)
        result.total_problems = len(problems)
        print(f"  Collected {len(problems)} problems")

        print(f"Step 2: Generating teacher responses with {teacher_model or self.config.active_model}...")
        for i, problem in enumerate(problems):
            print(f"  Processing problem {i+1}/{len(problems)}: {problem.id}")
            
            teacher_response = self.generate_teacher_response(problem, teacher_model)
            if teacher_response is None:
                print(f"    Teacher failed to respond")
                result.failed_verifications += 1
                continue
            
            result.teacher_responses += 1
            result.teacher_stats[teacher_model or self.config.active_model] = \
                result.teacher_stats.get(teacher_model or self.config.active_model, 0) + 1

            print(f"    Verifying solution...")
            is_verified, method, detail = self.verify_solution(problem, teacher_response)
            
            if is_verified:
                result.verified_solutions += 1
                result.category_stats[problem.category] = \
                    result.category_stats.get(problem.category, 0) + 1
                
                quality_score = self.calculate_quality_score(problem, teacher_response, is_verified, method)
                
                sample = DistilledSample(
                    problem_id=problem.id,
                    problem_zh=problem.problem_zh,
                    problem_en=problem.problem_en,
                    teacher_model=teacher_model or self.config.active_model,
                    teacher_response=teacher_response,
                    verified=True,
                    verification_method=method,
                    verification_detail=detail,
                    final_answer=problem.answer,
                    category=problem.category,
                    difficulty=problem.difficulty,
                    quality_score=quality_score,
                )
                self.samples.append(sample)
                print(f"    Verified (method: {method}, quality: {quality_score:.2f})")
            else:
                result.failed_verifications += 1
                print(f"    Verification failed: {detail}")

        print(f"Step 3: Exporting {len(self.samples)} verified samples...")
        self.export_training_data(output_path)
        
        print(f"\nDistillation complete!")
        print(f"  Total problems: {result.total_problems}")
        print(f"  Teacher responses: {result.teacher_responses}")
        print(f"  Verified solutions: {result.verified_solutions}")
        print(f"  Failed verifications: {result.failed_verifications}")
        print(f"  Success rate: {result.verified_solutions / max(result.teacher_responses, 1):.1%}")
        
        return result

    def export_training_data(self, output_path: str, format: str = "chatml",
                              min_quality: float = 0.5):
        """Export verified samples to training data format."""
        filtered = [s for s in self.samples if s.quality_score >= min_quality]
        
        if not filtered:
            print("No samples meet the quality threshold.")
            return
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in filtered:
                if format == "chatml":
                    entry = {
                        "messages": [
                            {"role": "system", "content": "You are JiuZhang-Math, a mathematical reasoning expert. Provide clear, step-by-step solutions with verification."},
                            {"role": "user", "content": f"{sample.problem_zh}\n/\n{sample.problem_en}"},
                            {"role": "assistant", "content": sample.teacher_response},
                        ],
                        "problem_id": sample.problem_id,
                        "category": sample.category,
                        "difficulty": sample.difficulty,
                        "verification_method": sample.verification_method,
                        "quality_score": sample.quality_score,
                        "teacher_model": sample.teacher_model,
                    }
                else:
                    entry = {
                        "instruction": f"Solve: {sample.problem_en}",
                        "input": sample.problem_zh,
                        "output": sample.teacher_response,
                        "problem_id": sample.problem_id,
                        "category": sample.category,
                        "quality_score": sample.quality_score,
                    }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        print(f"Exported {len(filtered)} high-quality samples to {output_path}")

    def generate_training_script(self, output_dir: str = "jiuzhang-math-model",
                                  base_model: str = "Qwen/Qwen3.5-0.8B",
                                  method: str = "qlora") -> str:
        """Generate a complete training script for the distilled data."""
        if method == "qlora":
            script = self._generate_unsloth_script(output_dir, base_model)
        elif method == "full":
            script = self._generate_hf_script(output_dir, base_model)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        model_tag = base_model.split('/')[-1].replace(':', '_')
        script_path = f"train_{method}_{model_tag}.py"
        Path(script_path).write_text(script, encoding="utf-8")
        print(f"Training script generated: {script_path}")
        return script_path

    def _generate_unsloth_script(self, output_dir: str, base_model: str) -> str:
        """Generate Unsloth QLoRA training script."""
        lines = [
            '#!/usr/bin/env python3',
            '"""JiuZhang Math Model Training Script (Unsloth QLoRA)"""',
            '',
            'import os',
            'os.environ["WANDB_DISABLED"] = "true"',
            '',
            'from unsloth import FastLanguageModel',
            'import torch',
            'from trl import SFTTrainer',
            'from transformers import TrainingArguments',
            'from datasets import load_dataset',
            '',
            f'MODEL_NAME = "{base_model}"',
            'DATA_PATH = "jiuzhang_distilled.jsonl"',
            f'OUTPUT_DIR = "{output_dir}"',
            'MAX_SEQ_LENGTH = 2048',
            'BATCH_SIZE = 4',
            'GRADIENT_ACCUMULATION = 8',
            'EPOCHS = 3',
            'LEARNING_RATE = 2e-4',
            '',
            '# Resolve ModelScope model path',
            'MODEL_PATH = MODEL_NAME',
            'try:',
            '    from modelscope import snapshot_download',
            '    MODEL_PATH = snapshot_download(MODEL_NAME)',
            '    print(f"ModelScope model resolved to: {MODEL_PATH}")',
            'except ImportError:',
            '    print("modelscope not installed, falling back to HuggingFace path")',
            'except Exception as e:',
            '    print(f"ModelScope download failed: {e}, trying HuggingFace path")',
            '',
            'model, tokenizer = FastLanguageModel.from_pretrained(',
            '    model_name=MODEL_PATH,',
            '    max_seq_length=MAX_SEQ_LENGTH,',
            '    dtype=None,',
            '    load_in_4bit=True,',
            ')',
            '',
            'model = FastLanguageModel.get_peft_model(',
            '    model,',
            '    r=64,',
            '    lora_alpha=16,',
            '    lora_dropout=0.05,',
            '    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],',
            '    bias="none",',
            '    use_gradient_checkpointing=True,',
            '    random_state=42,',
            ')',
            '',
            'dataset = load_dataset("json", data_files=DATA_PATH, split="train")',
            '',
            'def format_chatml(example):',
            '    return {"text": tokenizer.apply_chat_template(example["messages"], tokenize=False)}',
            '',
            'dataset = dataset.map(format_chatml)',
            '',
            'trainer = SFTTrainer(',
            '    model=model,',
            '    tokenizer=tokenizer,',
            '    train_dataset=dataset,',
            '    args=TrainingArguments(',
            '        per_device_train_batch_size=BATCH_SIZE,',
            '        gradient_accumulation_steps=GRADIENT_ACCUMULATION,',
            '        warmup_ratio=0.03,',
            '        max_steps=-1,',
            '        num_train_epochs=EPOCHS,',
            '        learning_rate=LEARNING_RATE,',
            '        weight_decay=0.01,',
            '        lr_scheduler_type="cosine",',
            '        logging_steps=10,',
            '        save_steps=200,',
            '        output_dir=OUTPUT_DIR,',
            '        seed=42,',
            '        bf16=torch.cuda.is_bf16_supported(),',
            '        fp16=not torch.cuda.is_bf16_supported(),',
            '        optim="adamw_8bit",',
            '    ),',
            ')',
            '',
            'print("Starting training...")',
            'trainer.train()',
            '',
            'model.save_pretrained(OUTPUT_DIR)',
            'tokenizer.save_pretrained(OUTPUT_DIR)',
            'print(f"Model saved to {OUTPUT_DIR}")',
            '',
            'model.save_pretrained_gguf(OUTPUT_DIR, tokenizer)',
            'print(f"GGUF model exported to {OUTPUT_DIR}")',
        ]
        return "\n".join(lines)

    def _generate_hf_script(self, output_dir: str, base_model: str) -> str:
        """Generate HuggingFace Transformers training script."""
        lines = [
            '#!/usr/bin/env python3',
            '"""JiuZhang Math Model Training Script (HuggingFace Full Fine-tuning)"""',
            '',
            'import os',
            'os.environ["WANDB_DISABLED"] = "true"',
            '',
            'from transformers import (',
            '    AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForSeq2Seq',
            ')',
            'from datasets import load_dataset',
            'import torch',
            '',
            f'MODEL_NAME = "{base_model}"',
            'DATA_PATH = "jiuzhang_distilled.jsonl"',
            f'OUTPUT_DIR = "{output_dir}"',
            'MAX_SEQ_LENGTH = 2048',
            'BATCH_SIZE = 4',
            'GRADIENT_ACCUMULATION = 8',
            'EPOCHS = 3',
            'LEARNING_RATE = 5e-5',
            '',
            '# Resolve ModelScope model path',
            'MODEL_PATH = MODEL_NAME',
            'try:',
            '    from modelscope import snapshot_download',
            '    MODEL_PATH = snapshot_download(MODEL_NAME)',
            '    print(f"ModelScope model resolved to: {MODEL_PATH}")',
            'except ImportError:',
            '    print("modelscope not installed, falling back to HuggingFace path")',
            'except Exception as e:',
            '    print(f"ModelScope download failed: {e}, trying HuggingFace path")',
            '',
            'tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)',
            'if tokenizer.pad_token is None:',
            '    tokenizer.pad_token = tokenizer.eos_token',
            '',
            'model = AutoModelForCausalLM.from_pretrained(',
            '    MODEL_PATH,',
            '    torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,',
            '    device_map="auto",',
            ')',
            '',
            'dataset = load_dataset("json", data_files=DATA_PATH, split="train")',
            '',
            'def tokenize(example):',
            '    text = tokenizer.apply_chat_template(example["messages"], tokenize=False)',
            '    return tokenizer(text, truncation=True, max_length=MAX_SEQ_LENGTH)',
            '',
            'tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)',
            '',
            'trainer = Trainer(',
            '    model=model,',
            '    args=TrainingArguments(',
            '        output_dir=OUTPUT_DIR,',
            '        per_device_train_batch_size=BATCH_SIZE,',
            '        gradient_accumulation_steps=GRADIENT_ACCUMULATION,',
            '        num_train_epochs=EPOCHS,',
            '        learning_rate=LEARNING_RATE,',
            '        weight_decay=0.01,',
            '        warmup_ratio=0.06,',
            '        lr_scheduler_type="cosine",',
            '        logging_steps=10,',
            '        save_steps=200,',
            '        seed=42,',
            '        fp16=True,',
            '        gradient_checkpointing=True,',
            '    ),',
            '    train_dataset=tokenized,',
            '    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),',
            ')',
            '',
            'print("Starting training...")',
            'trainer.train()',
            '',
            'model.save_pretrained(OUTPUT_DIR)',
            'tokenizer.save_pretrained(OUTPUT_DIR)',
            'print(f"Model saved to {OUTPUT_DIR}")',
        ]
        return "\n".join(lines)

    def generate_ollama_modelfile(self, model_name: str = "jiuzhang-math") -> str:
        """Generate Ollama Modelfile for the trained model."""
        content = f"""FROM {model_name}

# JiuZhang Math Model configuration
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER presence_penalty 0.2
PARAMETER frequency_penalty 0.2
PARAMETER stop "."

SYSTEM \"\"\"You are JiuZhang-Math, a specialized mathematical reasoning model.
You excel at:
- Step-by-step mathematical proofs
- Symbolic computation and verification
- Problem solving with clear explanations
- Conjecture analysis and counterexample search
Always show your reasoning process and verify your answers when possible.\"\"\"
"""
        path = f"Modelfile.{model_name.replace(':', '_')}"
        Path(path).write_text(content, encoding="utf-8")
        print(f"Ollama Modelfile generated: {path}")
        return path

    def print_full_report(self, result: DistillationResult):
        """Print a comprehensive report of the distillation run."""
        print("\n" + "=" * 70)
        print("JiuZhang Distillation Pipeline - Full Report")
        print("=" * 70)
        print(f"\nTeacher Model: {list(result.teacher_stats.keys())[0] if result.teacher_stats else 'N/A'}")
        print(f"Total Problems: {result.total_problems}")
        print(f"Teacher Responses: {result.teacher_responses}")
        print(f"Verified Solutions: {result.verified_solutions}")
        print(f"Failed Verifications: {result.failed_verifications}")
        print(f"Success Rate: {result.verified_solutions / max(result.teacher_responses, 1):.1%}")
        
        if result.category_stats:
            print(f"\nBy Category:")
            for cat, count in sorted(result.category_stats.items()):
                print(f"  {cat:20s}: {count}")
        
        print(f"\nNext Steps:")
        print(f"  1. Review distilled data: jiuzhang_distilled.jsonl")
        print(f"  2. Generate training script: pipeline.generate_training_script()")
        print(f"  3. Run training: python train_qlora_*.py")
        print(f"  4. Export to Ollama: ollama create jiu-math -f Modelfile.*")
        print(f"  5. Evaluate: python -m jiuzhang.small_math_model eval jiu-math")
        print("=" * 70 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JiuZhang Distillation Pipeline")
    parser.add_argument("--teacher", default=None, help="Teacher model name")
    parser.add_argument("--problems", type=int, default=50, help="Number of problems")
    parser.add_argument("--categories", nargs="*", help="Categories to include")
    parser.add_argument("--difficulties", nargs="*", help="Difficulties to include")
    parser.add_argument("--output", default="jiuzhang_distilled.jsonl")
    parser.add_argument("--format", choices=["chatml", "alpaca"], default="chatml")
    parser.add_argument("--generate-script", action="store_true", help="Generate training script")
    parser.add_argument("--method", choices=["qlora", "full"], default="qlora")
    parser.add_argument("--base-model", default="Qwen/Qwen3.5-0.8B")
    parser.add_argument("--stats", action="store_true", help="Print stats only")
    args = parser.parse_args()

    pipeline = DistillationPipeline(seed=42)
    
    if args.stats:
        print("Distillation Pipeline ready.")
        print(f"Teacher: {args.teacher or 'default'}")
        print(f"Problems: {args.problems}")
        print(f"Categories: {args.categories or 'all'}")
        print(f"Difficulties: {args.difficulties or 'all'}")
        return

    result = pipeline.run_distillation(
        teacher_model=args.teacher,
        categories=args.categories,
        difficulties=args.difficulties,
        problem_count=args.problems,
        output_path=args.output,
    )
    
    pipeline.export_training_data(args.output, format=args.format)
    
    if args.generate_script:
        pipeline.generate_training_script(
            base_model=args.base_model,
            method=args.method,
        )
    
    pipeline.print_full_report(result)


if __name__ == "__main__":
    main()
