"""MathExtractor - Extract math capabilities from local GGUF models into compact 1B models.

This module integrates FanFu's GGUF→HF conversion with JiuZhang's distillation pipeline
to extract mathematical reasoning abilities from large local models into efficient 1B models.

Workflow:
1. Locate local GGUF models (Ollama storage, custom paths)
2. Convert GGUF → HuggingFace format using FanFu (enables fine-tuning)
3. Use converted model as teacher for knowledge distillation
4. Generate verified math training data via JiuZhang's pipeline
5. Fine-tune onto 1B student model (Qwen3.5-0.8B, etc.)
6. Export to GGUF/Ollama for deployment

Supported teacher models:
- Local GGUF files (any format: Q4_0, Q8_0, F16, BF16, F32)
- Ollama models (deepseek-math:7b, qwen2.5:7b, etc.)

Supported student models (1B以内):
- Qwen/Qwen3.5-0.8B (recommended)
- Qwen/Qwen2.5-1.5B-Instruct
- microsoft/Phi-3-mini-4k-instruct (2.3B, slightly over 1B)

Example usage:
    from jiuzhang.math_extractor import MathKnowledgeExtractor

    extractor = MathKnowledgeExtractor()
    extractor.run_full_pipeline(
        teacher_model="deepseek-math:7b",  # or path to GGUF
        student_model="Qwen/Qwen3.5-0.8B",
        categories=["algebra", "calculus"],
        problem_count=200,
    )
"""

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.distillation_pipeline import DistillationPipeline, DistilledSample
from jiuzhang.symbolic_verify import VerificationResult


SUPPORTED_1B_MODELS = {
    "qwen3.5-0.8b": "Qwen/Qwen3.5-0.8B",
    "qwen2.5-1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
    "phi3-mini": "microsoft/Phi-3-mini-4k-instruct",
}


@dataclass
class GGUFModelInfo:
    path: str
    name: str
    size_gb: float
    quantization: str
    is_ollama: bool = False


@dataclass
class ExtractionResult:
    teacher_model: str
    student_model: str
    training_samples: int
    verified_samples: int
    hf_model_path: Optional[str]
    output_dir: str
    ollama_model_name: Optional[str] = None


class LocalModelExtractor:
    """Locate and convert local GGUF models using FanFu."""

    def __init__(self, fanfu_path: Optional[str] = None):
        self.fanfu_path = Path(fanfu_path) if fanfu_path else None
        self._setup_fanfu_import()

    def _setup_fanfu_import(self):
        if self.fanfu_path:
            if str(self.fanfu_path) not in sys.path:
                sys.path.insert(0, str(self.fanfu_path))
        try:
            from fanfu import api as fanfu_api
            self.fanfu = fanfu_api
        except ImportError:
            self.fanfu = None

    def find_ollama_models(self) -> List[GGUFModelInfo]:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = []
                for m in data.get("models", []):
                    size_gb = m.get("size", 0) / (1024**3)
                    models.append(GGUFModelInfo(
                        path=m["name"],
                        name=m["name"],
                        size_gb=size_gb,
                        quantization=self._detect_quantization(m["name"]),
                        is_ollama=True,
                    ))
                return models
        except Exception:
            pass
        return []

    def find_local_gguf(self, search_paths: Optional[List[str]] = None) -> List[GGUFModelInfo]:
        if search_paths is None:
            search_paths = [
                str(Path.cwd()),
                str(Path.home() / "Models"),
                str(Path.home() / "Downloads"),
                "/opt/homebrew/opt/llama.cpp/bin" if Path("/opt/homebrew/opt/llama.cpp/bin").exists() else "",
                "/usr/local/opt/llama.cpp/bin" if Path("/usr/local/opt/llama.cpp/bin").exists() else "",
            ]
            search_paths = [p for p in search_paths if p]

        models = []
        for search_path in search_paths:
            path = Path(search_path)
            if not path.exists():
                continue
            for gguf_file in path.rglob("*.gguf"):
                size_gb = gguf_file.stat().st_size / (1024**3)
                models.append(GGUFModelInfo(
                    path=str(gguf_file),
                    name=gguf_file.stem,
                    size_gb=size_gb,
                    quantization=self._detect_quantization(gguf_file.name),
                    is_ollama=False,
                ))
        return models

    def _detect_quantization(self, filename: str) -> str:
        filename_lower = filename.lower()
        if "q8_0" in filename_lower or "q8.0" in filename_lower:
            return "Q8_0"
        if "q6_k" in filename_lower or "q6k" in filename_lower:
            return "Q6_K"
        if "q5_0" in filename_lower or "q5.0" in filename_lower:
            return "Q5_0"
        if "q5_1" in filename_lower or "q5.1" in filename_lower:
            return "Q5_1"
        if "q4_1" in filename_lower or "q4.1" in filename_lower:
            return "Q4_1"
        if "q4_0" in filename_lower or "q4.0" in filename_lower:
            return "Q4_0"
        if "q3_k" in filename_lower or "q3k" in filename_lower:
            return "Q3_K"
        if "q2_k" in filename_lower or "q2k" in filename_lower:
            return "Q2_K"
        if "f16" in filename_lower or "fp16" in filename_lower:
            return "F16"
        if "bf16" in filename_lower:
            return "BF16"
        if "f32" in filename_lower or "fp32" in filename_lower:
            return "F32"
        return "UNKNOWN"

    def convert_gguf_to_hf(
        self,
        gguf_path: str,
        output_dir: str,
        outtype: str = "f16",
    ) -> Tuple[bool, str]:
        if self.fanfu is None:
            return False, "FanFu not available. Install from /Users/fred/Documents/GitHub/CodeOfMe/FanFu"

        result = self.fanfu.convert_gguf_to_hf(
            gguf_path=gguf_path,
            output_dir=output_dir,
            outtype=outtype,
            extract_tokenizer=True,
        )
        if result.success:
            return True, result.data.get("output_dir", output_dir)
        return False, result.error or "Conversion failed"

    def get_ollama_model_path(self, model_name: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["ollama", "show", "--modelfile", model_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            for line in result.stdout.split("\n"):
                if line.strip() and not line.startswith("PARAMETER") and not line.startswith("FROM"):
                    path = line.strip()
                    if Path(path).exists():
                        return path
        except Exception:
            pass

        manifest_path = Path.home() / ".ollama" / "manifests" / "registry.ollama.ai" / "library" / model_name.replace(":", "/")
        if not manifest_path.exists():
            manifest_path = Path.home() / ".ollama" / "manifests" / model_name.replace(":", "/")
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                if "blob" in manifest:
                    blob_path = Path.home() / ".ollama" / "models" / "blobs" / manifest["blob"]
                    if blob_path.exists():
                        return str(blob_path)
            except Exception:
                pass
        return None

    def list_ollama_math_models(self) -> List[str]:
        math_keywords = ["math", "deepseek", "qwen", "gemma", "phi", "lfm", "omnicoder"]
        models = self.find_ollama_models()
        return [m.name for m in models if any(k in m.name.lower() for k in math_keywords)]

    def pull_ollama_model(self, model_name: str, timeout: int = 1800) -> Tuple[bool, str]:
        print(f"Pulling Ollama model: {model_name}")
        print("This may take several minutes...")
        try:
            proc = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in iter(proc.stdout.readline, ""):
                if line:
                    print(f"  {line.rstrip()}")
            proc.wait(timeout=timeout)
            if proc.returncode == 0:
                return True, f"Successfully pulled {model_name}"
            return False, f"Failed to pull {model_name}"
        except subprocess.TimeoutExpired:
            proc.kill()
            return False, f"Timeout while pulling {model_name}"
        except Exception as e:
            return False, f"Error pulling model: {e}"

    def get_teacher_candidates(self) -> List[GGUFModelInfo]:
        models = self.find_ollama_models()
        return [m for m in models if m.size_gb > 2.0 and "embedding" not in m.name.lower()]

    def get_student_candidates(self) -> List[GGUFModelInfo]:
        models = self.find_ollama_models()
        return [m for m in models if m.size_gb <= 1.5 and "embedding" not in m.name.lower()]


class MathKnowledgeExtractor:
    """Extract math capabilities from teacher model into compact 1B student model."""

    def __init__(
        self,
        config: Optional[Config] = None,
        fanfu_path: Optional[str] = None,
    ):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)
        self.local_extractor = LocalModelExtractor(fanfu_path=fanfu_path)
        self.distillation = DistillationPipeline(config=self.config)
        self.samples: List[DistilledSample] = []

    def list_available_teachers(self) -> Dict[str, List[GGUFModelInfo]]:
        return {
            "ollama_gguf": self.local_extractor.find_ollama_models(),
            "local_gguf": self.local_extractor.find_local_gguf(),
        }

    def prepare_teacher_model(
        self,
        teacher_model: str,
        output_dir: str = "teacher_model_hf",
    ) -> Tuple[bool, str]:
        if teacher_model.endswith(".gguf") and Path(teacher_model).exists():
            success, path = self.local_extractor.convert_gguf_to_hf(
                teacher_model, output_dir, outtype="f16"
            )
            if success:
                return True, path
            return False, path

        if ":" in teacher_model and not teacher_model.startswith("/"):
            ollama_models = self.local_extractor.find_ollama_models()
            model_exists = any(m.name == teacher_model for m in ollama_models)
            if not model_exists:
                success, msg = self.local_extractor.pull_ollama_model(teacher_model)
                if not success:
                    return False, f"Need to pull {teacher_model} first: {msg}"
            return True, teacher_model

        if Path(teacher_model).exists() and teacher_model.endswith(".gguf"):
            success, path = self.local_extractor.convert_gguf_to_hf(
                teacher_model, output_dir, outtype="f16"
            )
            if success:
                return True, path
            return False, path

        return True, teacher_model

    def generate_distillation_data(
        self,
        teacher_model: str,
        categories: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        problem_count: int = 100,
        output_path: str = "jiuzhang_distilled.jsonl",
    ) -> Tuple[int, int]:
        result = self.distillation.run_distillation(
            teacher_model=teacher_model,
            categories=categories,
            difficulties=difficulties,
            problem_count=problem_count,
            output_path=output_path,
        )
        self.samples = self.distillation.samples
        return result.verified_solutions, result.teacher_responses

    def run_full_pipeline(
        self,
        teacher_model: str,
        student_model: str = "Qwen/Qwen3.5-0.8B",
        categories: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        problem_count: int = 200,
        output_dir: str = "jiuzhang-math-extracted",
        use_curriculum: bool = True,
    ) -> ExtractionResult:
        print("=" * 70)
        print("MathKnowledgeExtractor - Full Pipeline")
        print("=" * 70)
        print(f"Teacher: {teacher_model}")
        print(f"Student: {student_model}")
        print(f"Problems: {problem_count}")
        print(f"Output: {output_dir}")
        print("=" * 70)

        os.makedirs(output_dir, exist_ok=True)

        print("\n[Step 1/4] Preparing teacher model...")
        hf_path = None
        teacher_path = teacher_model

        if teacher_model.endswith(".gguf") or (
            ":" in teacher_model and not teacher_model.startswith("/")
        ):
            success, path = self.prepare_teacher_model(teacher_model, f"{output_dir}/teacher_hf")
            if not success:
                print(f"  Warning: {path}")
                print("  Will attempt to use Ollama API directly...")
            elif path != teacher_model:
                hf_path = path
                print(f"  Converted to HF: {hf_path}")
            else:
                print(f"  Using teacher via Ollama API: {teacher_model}")

        print("\n[Step 2/4] Generating distillation data...")
        distillation_path = f"{output_dir}/distilled_data.jsonl"
        verified, total = self.generate_distillation_data(
            teacher_model=teacher_model,
            categories=categories,
            difficulties=difficulties,
            problem_count=problem_count,
            output_path=distillation_path,
        )
        print(f"  Generated {verified}/{total} verified samples")

        print("\n[Step 3/4] Generating training script...")
        from jiuzhang.small_math_model import SmallMathModelConfig, SmallMathModelTrainer

        cfg = SmallMathModelConfig(
            base_model=student_model,
            model_size="0.8B" if "0.8B" in student_model else "1.5B" if "1.5B" in student_model else "unknown",
            output_dir=output_dir,
            data_path=distillation_path,
            num_epochs=3,
            use_curriculum=use_curriculum,
        )
        trainer = SmallMathModelTrainer(cfg)

        model_tag = student_model.split("/")[-1].replace(":", "_")
        script_path = f"train_extracted_{model_tag}.py"

        with open(script_path, "w") as f:
            f.write(trainer.build_unsloth_script(distillation_path))
        print(f"  Training script: {script_path}")

        print("\n[Step 4/4] Generating Ollama export...")
        modelfile_path = trainer.build_ollama_modelfile()
        print(f"  Modelfile: {modelfile_path}")

        print("\n" + "=" * 70)
        print("Pipeline complete!")
        print("=" * 70)
        print("\nNext steps:")
        print(f"  1. python {script_path}")
        print(f"  2. ollama create jiu-math-extracted -f {modelfile_path}")
        print(f"  3. ollama run jiu-math-extracted 'Solve: x^2 - 5x + 6 = 0'")
        print("=" * 70)

        return ExtractionResult(
            teacher_model=teacher_model,
            student_model=student_model,
            training_samples=total,
            verified_samples=verified,
            hf_model_path=hf_path,
            output_dir=output_dir,
        )

    def extract_from_ollama(
        self,
        teacher_model: str,
        student_model: str = "Qwen/Qwen3.5-0.8B",
        categories: Optional[List[str]] = None,
        problem_count: int = 200,
        output_dir: str = "jiuzhang-math-ollama",
    ) -> ExtractionResult:
        return self.run_full_pipeline(
            teacher_model=teacher_model,
            student_model=student_model,
            categories=categories,
            problem_count=problem_count,
            output_dir=output_dir,
        )

    def extract_from_gguf(
        self,
        gguf_path: str,
        student_model: str = "Qwen/Qwen3.5-0.8B",
        categories: Optional[List[str]] = None,
        problem_count: int = 200,
        output_dir: str = "jiuzhang-math-gguf",
    ) -> ExtractionResult:
        return self.run_full_pipeline(
            teacher_model=gguf_path,
            student_model=student_model,
            categories=categories,
            problem_count=problem_count,
            output_dir=output_dir,
        )

    def quick_extract(
        self,
        teacher_model: str = "deepseek-math:7b",
        student_model: str = "Qwen/Qwen3.5-0.8B",
        problem_count: int = 100,
    ) -> str:
        result = self.run_full_pipeline(
            teacher_model=teacher_model,
            student_model=student_model,
            categories=["algebra", "arithmetic"],
            problem_count=problem_count,
            output_dir="jiuzhang-math-quick",
        )
        return f"{result.output_dir}/distilled_data.jsonl"


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MathExtractor - Extract math capabilities into 1B models"
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    p_list = sub.add_parser("list", help="List available local GGUF models")
    p_list.add_argument("--search", nargs="*", help="Additional paths to search")

    p_ollama = sub.add_parser("from-ollama", help="Extract from Ollama model")
    p_ollama.add_argument("--teacher", required=True, help="Ollama model name")
    p_ollama.add_argument("--student", default="Qwen/Qwen3.5-0.8B")
    p_ollama.add_argument("--problems", type=int, default=200)
    p_ollama.add_argument("--output", default="jiuzhang-math-ollama")
    p_ollama.add_argument("--categories", nargs="*")

    p_gguf = sub.add_parser("from-gguf", help="Extract from GGUF file")
    p_gguf.add_argument("--gguf", required=True, help="Path to GGUF file")
    p_gguf.add_argument("--student", default="Qwen/Qwen3.5-0.8B")
    p_gguf.add_argument("--problems", type=int, default=200)
    p_gguf.add_argument("--output", default="jiuzhang-math-gguf")
    p_gguf.add_argument("--categories", nargs="*")

    p_quick = sub.add_parser("quick", help="Quick extraction with defaults")
    p_quick.add_argument("--teacher", default="deepseek-math:7b")
    p_quick.add_argument("--student", default="Qwen/Qwen3.5-0.8B")
    p_quick.add_argument("--problems", type=int, default=100)

    p_info = sub.add_parser("info", help="Show supported models")
    p_info.add_argument(
        "--fanfu-path",
        default="/Users/fred/Documents/GitHub/CodeOfMe/FanFu",
        help="Path to FanFu installation",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "list":
        extractor = LocalModelExtractor()
        print("Ollama GGUF models:")
        for m in extractor.find_ollama_models():
            print(f"  {m.name} ({m.size_gb:.1f}GB, {m.quantization})")
        print("\nLocal GGUF models:")
        for m in extractor.find_local_gguf(args.search or []):
            print(f"  {m.path} ({m.size_gb:.1f}GB, {m.quantization})")

    elif args.command == "info":
        print("Supported 1B student models:")
        for name, model in SUPPORTED_1B_MODELS.items():
            print(f"  {name}: {model}")

    elif args.command == "from-ollama":
        extractor = MathKnowledgeExtractor(fanfu_path="/Users/fred/Documents/GitHub/CodeOfMe/FanFu")
        extractor.run_full_pipeline(
            teacher_model=args.teacher,
            student_model=args.student,
            categories=args.categories,
            problem_count=args.problems,
            output_dir=args.output,
        )

    elif args.command == "from-gguf":
        extractor = MathKnowledgeExtractor(fanfu_path="/Users/fred/Documents/GitHub/CodeOfMe/FanFu")
        extractor.extract_from_gguf(
            gguf_path=args.gguf,
            student_model=args.student,
            categories=args.categories,
            problem_count=args.problems,
            output_dir=args.output,
        )

    elif args.command == "quick":
        extractor = MathKnowledgeExtractor(fanfu_path="/Users/fred/Documents/GitHub/CodeOfMe/FanFu")
        extractor.quick_extract(
            teacher_model=args.teacher,
            student_model=args.student,
            problem_count=args.problems,
        )


if __name__ == "__main__":
    main()