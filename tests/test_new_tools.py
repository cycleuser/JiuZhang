"""Tests for Code Interpreter and Rejection Sampling."""

import pytest
import json
import os

from jiuzhang.code_interpreter import CodeInterpreter, CodeExecutionResult, SafeMathEnvironment
from jiuzhang.rejection_sampling import RejectionSampler, RejectionSamplingResult
from jiuzhang.math_benchmark import MathBenchmark


class TestCodeInterpreter:
    def test_execute_simple_code(self):
        interpreter = CodeInterpreter()
        code = "print(2 + 2)"
        result = interpreter.execute_code(code)
        assert result.success is True
        assert "4" in result.output

    def test_execute_sympy_code(self):
        interpreter = CodeInterpreter()
        code = """
x = symbols('x')
f = x**2
f_prime = diff(f, x)
print(f_prime)
"""
        result = interpreter.execute_code(code)
        assert result.success is True
        assert "2*x" in result.output

    def test_execute_unsafe_code(self):
        interpreter = CodeInterpreter()
        code = "import os; os.system('echo hacked')"
        result = interpreter.execute_code(code)
        assert result.success is False
        assert "Security violation" in result.error

    def test_extract_code_blocks(self):
        interpreter = CodeInterpreter()
        text = """
Here is the solution:
```python
x = 5
print(x)
```
And another one:
```
y = 10
print(y)
```
"""
        blocks = interpreter.extract_code_blocks(text)
        assert len(blocks) == 2
        assert "x = 5" in blocks[0]
        assert "y = 10" in blocks[1]

    def test_solve_with_code(self):
        interpreter = CodeInterpreter()
        problem = "Find the derivative of x^2"
        response = """
To find the derivative, we can use SymPy:
```python
x = symbols('x')
f = x**2
print(diff(f, x))
```
"""
        success, output, code = interpreter.solve_with_code(problem, response)
        assert success is True
        assert "2*x" in output

    def test_execute_error_handling(self):
        interpreter = CodeInterpreter()
        code = "print(1/0)"
        result = interpreter.execute_code(code)
        assert result.success is False
        assert "division by zero" in result.error


class TestRejectionSampler:
    def test_generate_candidates(self):
        sampler = RejectionSampler(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        problem = problems[0]
        
        candidates = sampler.generate_candidates_heuristic(problem, n=5)
        assert len(candidates) == 5
        assert any(problem.answer in c for c in candidates)

    def test_verify_candidate_correct(self):
        sampler = RejectionSampler(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        problem = problems[0]
        
        is_correct, verification = sampler.verify_candidate(problem, f"Solution: {problem.answer}")
        assert is_correct is True

    def test_verify_candidate_incorrect(self):
        sampler = RejectionSampler(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        problem = problems[0]
        
        is_correct, verification = sampler.verify_candidate(problem, "Solution: wrong answer")
        assert is_correct is False

    def test_run_sampling(self):
        sampler = RejectionSampler(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        
        result = sampler.run_sampling(problems[:5], n_candidates=3)
        assert result.total_problems == 5
        assert result.total_candidates == 15
        assert result.accepted_solutions > 0
        assert 0 <= result.rejection_rate < 1.0

    def test_export_training_data(self, tmp_path):
        sampler = RejectionSampler(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        
        result = sampler.run_sampling(problems[:5], n_candidates=3)
        output_path = str(tmp_path / "test_rejection.jsonl")
        
        sampler.export_training_data(result, output_path, format="chatml")
        
        assert os.path.exists(output_path)
        with open(output_path) as f:
            lines = f.readlines()
        assert len(lines) == result.accepted_solutions
        for line in lines:
            entry = json.loads(line)
            assert "messages" in entry
            assert len(entry["messages"]) == 3

    def test_print_report(self, capsys):
        sampler = RejectionSampler(seed=42)
        benchmark = MathBenchmark()
        problems = benchmark.get_problems(difficulties=["elementary"])
        
        result = sampler.run_sampling(problems[:2], n_candidates=2)
        sampler.print_report(result)
        
        captured = capsys.readouterr()
        assert "Rejection Sampling Report" in captured.out
        assert "Rejection Rate" in captured.out