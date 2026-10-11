"""Reasoning module for JiuZhang.

Hybrid symbolic + LLM reasoning engine for mathematical problem solving.
Combines SymPy's exact computation with LLM's conceptual understanding.
"""

from jiuzhang.reasoning.hybrid_engine import HybridReasoningEngine, ReasoningResult
from jiuzhang.reasoning.proof_generator import ProofGenerator, Proof, ProofStep
from jiuzhang.reasoning.method_chain import MethodChain, ChainResult

__all__ = [
    "HybridReasoningEngine",
    "ReasoningResult",
    "ProofGenerator",
    "Proof",
    "ProofStep",
    "MethodChain",
    "ChainResult",
]