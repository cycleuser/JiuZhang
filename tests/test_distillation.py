"""Tests for Distillation Pipeline."""

import pytest
import json
import os

from jiuzhang.distillation_pipeline import DistillationPipeline, DistilledSample, DistillationResult
from jiuzhang.math_benchmark import MathBenchmark


class TestDistillationPipeline:
    def test_collect_problems(self):
        pipeline = DistillationPipeline(seed=42)
        problems = pipeline.collect_problems(count=10)
        assert len(problems) <= 10
        assert len(problems) > 0

    def test_collect_problems_by_category(self):
        pipeline = DistillationPipeline(seed=42)
        problems = pipeline.collect_problems(categories=["algebra"], count=10)
        assert all(p.category == "algebra" for p in problems)

    def test_verify_solution_correct(self):
        pipeline = DistillationPipeline(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        problem = problems[0]
        
        is_verified, method, detail = pipeline.verify_solution(problem, f"Solution: {problem.answer}")
        assert is_verified is True

    def test_verify_solution_incorrect(self):
        pipeline = DistillationPipeline(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        problem = problems[0]
        
        is_verified, method, detail = pipeline.verify_solution(problem, "Solution: wrong answer")
        assert is_verified is False

    def test_calculate_quality_score(self):
        pipeline = DistillationPipeline(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        problem = problems[0]
        
        score = pipeline.calculate_quality_score(problem, "Step 1: Analyze. Step 2: Solve. Result: correct.", True, "symbolic")
        assert 0.5 <= score <= 1.0

    def test_export_training_data(self, tmp_path):
        pipeline = DistillationPipeline(seed=42)
        
        sample = DistilledSample(
            problem_id="test_01",
            problem_zh="测试问题",
            problem_en="Test problem",
            teacher_model="test-model",
            teacher_response="Test solution",
            verified=True,
            verification_method="symbolic",
            verification_detail="Verified",
            final_answer="42",
            category="arithmetic",
            difficulty="elementary",
            quality_score=0.8,
        )
        pipeline.samples.append(sample)
        
        output_path = str(tmp_path / "test_distilled.jsonl")
        pipeline.export_training_data(output_path, min_quality=0.5)
        
        assert os.path.exists(output_path)
        with open(output_path) as f:
            lines = f.readlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert "messages" in entry

    def test_generate_training_script_qlora(self, tmp_path):
        pipeline = DistillationPipeline(seed=42)
        script_path = pipeline.generate_training_script(
            output_dir=str(tmp_path / "model"),
            base_model="Qwen/Qwen2.5-1.5B-Instruct",
            method="qlora",
        )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "unsloth" in content.lower()
        assert "SFTTrainer" in content

    def test_generate_training_script_hf(self, tmp_path):
        pipeline = DistillationPipeline(seed=42)
        script_path = pipeline.generate_training_script(
            output_dir=str(tmp_path / "model"),
            base_model="Qwen/Qwen2.5-1.5B-Instruct",
            method="full",
        )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "transformers" in content.lower()
        assert "Trainer" in content

    def test_generate_ollama_modelfile(self, tmp_path):
        pipeline = DistillationPipeline(seed=42)
        os.chdir(str(tmp_path))
        path = pipeline.generate_ollama_modelfile("jiuzhang-math")
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "PARAMETER temperature 0.1" in content
        assert "JiuZhang-Math" in content

    def test_print_full_report(self, capsys):
        pipeline = DistillationPipeline(seed=42)
        result = DistillationResult(
            total_problems=10,
            teacher_responses=8,
            verified_solutions=6,
            failed_verifications=2,
            teacher_stats={"test-model": 8},
            category_stats={"arithmetic": 3, "algebra": 3},
        )
        pipeline.print_full_report(result)
        captured = capsys.readouterr()
        assert "Distillation Pipeline" in captured.out
        assert "Success Rate" in captured.out