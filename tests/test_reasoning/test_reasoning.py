"""Tests for reasoning module."""

import pytest
import sys
import os

# Add parent directory to path to avoid importing full jiuzhang package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from jiuzhang.reasoning.proof_generator import ProofGenerator, Proof, ProofStep, ProofStrategy
from jiuzhang.reasoning.method_chain import MethodChain, ChainResult
from jiuzhang.solver.method_registry import MethodRegistry


class TestProofGenerator:
    @pytest.fixture
    def generator(self):
        return ProofGenerator()

    def test_generate_direct_proof(self, generator):
        proof = generator.generate("两个偶数之和是偶数", ProofStrategy.DIRECT)
        assert proof.theorem == "两个偶数之和是偶数"
        assert proof.strategy == ProofStrategy.DIRECT
        assert len(proof.steps) > 0

    def test_generate_contradiction_proof(self, generator):
        proof = generator.generate("√2是无理数", ProofStrategy.CONTRADICTION)
        assert proof.strategy == ProofStrategy.CONTRADICTION
        assert len(proof.steps) >= 3

    def test_generate_induction_proof(self, generator):
        proof = generator.generate("1+2+...+n = n(n+1)/2", ProofStrategy.INDUCTION)
        assert proof.strategy == ProofStrategy.INDUCTION
        assert len(proof.steps) >= 3

    def test_generate_construction_proof(self, generator):
        proof = generator.generate("存在一个连续但处处不可导的函数", ProofStrategy.CONSTRUCTION)
        assert proof.strategy == ProofStrategy.CONSTRUCTION

    def test_generate_cases_proof(self, generator):
        proof = generator.generate("分情况讨论", ProofStrategy.CASES)
        assert proof.strategy == ProofStrategy.CASES

    def test_auto_detect_strategy(self, generator):
        proof = generator.generate("对所有自然数n")
        assert proof.strategy == ProofStrategy.INDUCTION

    def test_auto_detect_contradiction(self, generator):
        proof = generator.generate("不存在最大的素数")
        assert proof.strategy == ProofStrategy.CONTRADICTION

    def test_proof_latex(self, generator):
        proof = generator.generate("两个偶数之和是偶数")
        assert proof.latex != ""
        assert r"\begin{proof}" in proof.latex

    def test_proof_explanation_chinese(self, generator):
        proof = generator.generate("两个偶数之和是偶数", language="zh")
        assert "证明" in proof.explanation

    def test_proof_explanation_english(self, generator):
        proof = generator.generate("Sum of two evens is even", language="en")
        assert "Proof" in proof.explanation

    def test_proof_templates(self, generator):
        templates = generator.list_templates()
        assert len(templates) > 0

    def test_get_template(self, generator):
        proof = generator.get_template("sum_of_naturals")
        assert proof is not None
        assert proof.strategy == ProofStrategy.INDUCTION

    def test_proof_steps_verified(self, generator):
        proof = generator.generate("两个偶数之和是偶数")
        for step in proof.steps:
            assert isinstance(step, ProofStep)
            assert step.number > 0
            assert step.statement != ""
            assert step.justification != ""


class TestMethodChain:
    @pytest.fixture
    def registry(self):
        return MethodRegistry()

    @pytest.fixture
    def chain(self, registry):
        return MethodChain(registry)

    def test_chain_creation(self, chain):
        result = chain.chain(["addition", "multiplication"]).execute()
        assert result.success is True
        assert result.step_count == 2

    def test_chain_with_invalid_method(self, chain):
        result = chain.chain(["addition", "nonexistent_method"]).execute()
        assert result.success is False

    def test_chain_for_problem(self, registry):
        chain = MethodChain.for_problem("2 加 3 等于多少", registry)
        # May or may not have chain_ids depending on method matching
        assert isinstance(chain, MethodChain)

    def test_chain_for_domain(self, registry):
        chain = MethodChain.for_domain("arithmetic", registry)
        assert hasattr(chain, "_chain_ids")
        assert len(chain._chain_ids) > 0

    def test_chain_result_properties(self, chain):
        result = chain.chain(["addition"]).execute()
        assert result.step_count == 1
        assert result.all_successful is True

    def test_register_executor(self, chain):
        chain.register_executor("test_method", lambda ctx: "test_result")
        assert "test_method" in chain._executors
