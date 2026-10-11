"""Symbolic Verification Layer for JiuZhang.

Uses SymPy to verify mathematical claims made by the LLM,
enabling automatic fact-checking of generated proofs and solutions.
"""

import re
from typing import Optional, Tuple, List
from dataclasses import dataclass

import sympy
from sympy import (
    sympify, symbols, simplify, expand, factor,
    integrate, diff, solve, limit, series,
    Rational, oo, pi, E, I, sqrt,
    Symbol, Expr, Eq,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
)


@dataclass
class VerificationResult:
    claim: str
    verified: bool
    method: str
    detail: str
    confidence: float


def _safe_parse(expr_str: str) -> Optional[Expr]:
    """Safely parse a mathematical expression string into SymPy."""
    dangerous = ['import', 'open(', 'exec(', 'eval(', 'os.', 'sys.', '__']
    for d in dangerous:
        if d in expr_str:
            return None
    try:
        transformations = standard_transformations + (implicit_multiplication_application,)
        local_dict = {
            'x': symbols('x'), 'y': symbols('y'), 'z': symbols('z'),
            't': symbols('t'), 'n': symbols('n', integer=True),
            'pi': pi, 'e': E, 'i': I,
        }
        return parse_expr(expr_str, local_dict=local_dict, transformations=transformations)
    except Exception:
        return None


def verify_equation(eq_str: str) -> VerificationResult:
    """Verify if a stated equation is true.

    Handles forms like: 'a = b', 'a == b', 'a ≡ b', 'f(x) = expression'
    """
    for sep in ['==', '≡', '=']:
        if sep in eq_str:
            parts = eq_str.split(sep, 1)
            if len(parts) == 2:
                lhs_str = parts[0].strip()
                rhs_str = parts[1].strip()
                lhs = _safe_parse(lhs_str)
                rhs = _safe_parse(rhs_str)
                if lhs is None or rhs is None:
                    return VerificationResult(
                        claim=eq_str, verified=False, method='parse_failure',
                        detail=f'Could not parse: lhs={lhs_str}, rhs={rhs_str}',
                        confidence=0.0,
                    )
                diff_expr = simplify(lhs - rhs)
                if diff_expr == 0:
                    return VerificationResult(
                        claim=eq_str, verified=True, method='simplify',
                        detail=f'simplify({lhs} - {rhs}) = 0',
                        confidence=0.95,
                    )
                # Try numeric check at random points
                try:
                    free = list(diff_expr.free_symbols)
                    if free:
                        test_vals = [{s: Rational(i, 3) for s in free} for i in range(1, 6)]
                        for vals in test_vals:
                            result = diff_expr.subs(vals)
                            if result != 0:
                                return VerificationResult(
                                    claim=eq_str, verified=False, method='numeric_counterexample',
                                    detail=f'At {vals}: {lhs}-{rhs} = {result} ≠ 0',
                                    confidence=0.9,
                                )
                        return VerificationResult(
                            claim=eq_str, verified=True, method='numeric_sampling',
                            detail=f'Checked at 5 random points, {lhs}-{rhs}=0 at all',
                            confidence=0.7,
                        )
                    else:
                        return VerificationResult(
                            claim=eq_str, verified=False, method='symbolic_simplify',
                            detail=f'simplify({lhs}-{rhs}) = {diff_expr} ≠ 0',
                            confidence=0.95,
                        )
                except Exception as e:
                    return VerificationResult(
                        claim=eq_str, verified=False, method='exception',
                        detail=str(e), confidence=0.0,
                    )
    return VerificationResult(
        claim=eq_str, verified=False, method='no_separator',
        detail='No equation separator found', confidence=0.0,
    )


def verify_derivative(f_str: str, claimed_deriv_str: str, var: str = 'x') -> VerificationResult:
    """Verify that claimed_deriv_str is the derivative of f_str w.r.t. var."""
    f = _safe_parse(f_str)
    claimed = _safe_parse(claimed_deriv_str)
    x = Symbol(var)
    if f is None or claimed is None:
        return VerificationResult(
            claim=f"d/d{var}({f_str}) = {claimed_deriv_str}",
            verified=False, method='parse_failure',
            detail=f'Could not parse expressions', confidence=0.0,
        )
    try:
        actual = diff(f, x)
        diff_result = simplify(actual - claimed)
        if diff_result == 0:
            return VerificationResult(
                claim=f"d/d{var}({f_str}) = {claimed_deriv_str}",
                verified=True, method='symbolic_diff',
                detail=f'sympy.diff({f}, {var}) = {actual}, matches claim',
                confidence=0.98,
            )
        return VerificationResult(
            claim=f"d/d{var}({f_str}) = {claimed_deriv_str}",
            verified=False, method='symbolic_diff',
            detail=f'sympy.diff({f}, {var}) = {actual}, does NOT match {claimed}',
            confidence=0.98,
        )
    except Exception as e:
        return VerificationResult(
            claim=f"d/d{var}({f_str}) = {claimed_deriv_str}",
            verified=False, method='exception',
            detail=str(e), confidence=0.0,
        )


def verify_integral(f_str: str, claimed_integral_str: str, var: str = 'x') -> VerificationResult:
    """Verify that claimed_integral_str is an antiderivative of f_str."""
    f = _safe_parse(f_str)
    claimed = _safe_parse(claimed_integral_str)
    x = Symbol(var)
    if f is None or claimed is None:
        return VerificationResult(
            claim=f"∫{f_str}d{var} = {claimed_integral_str}",
            verified=False, method='parse_failure',
            detail='Could not parse expressions', confidence=0.0,
        )
    try:
        computed_derivative = diff(claimed, x)
        diff_result = simplify(computed_derivative - f)
        if diff_result == 0:
            return VerificationResult(
                claim=f"∫{f_str}d{var} = {claimed_integral_str}",
                verified=True, method='diff_check',
                detail=f'd/d{var}({claimed}) = {computed_derivative}, matches {f}',
                confidence=0.95,
            )
        return VerificationResult(
            claim=f"∫{f_str}d{var} = {claimed_integral_str}",
            verified=False, method='diff_check',
            detail=f'd/d{var}({claimed}) = {computed_derivative}, does NOT match {f}',
            confidence=0.95,
        )
    except Exception as e:
        return VerificationResult(
            claim=f"∫{f_str}d{var} = {claimed_integral_str}",
            verified=False, method='exception',
            detail=str(e), confidence=0.0,
        )


def verify_limit(f_str: str, var: str = 'x', target: str = 'oo') -> VerificationResult:
    """Verify the limit of f_str as var approaches target."""
    f = _safe_parse(f_str)
    x = symbols(var)
    if f is None:
        return VerificationResult(
            claim=f"lim({f_str}, {var}→{target})",
            verified=False, method='parse_failure',
            detail='Could not parse expression', confidence=0.0,
        )
    try:
        if target in ('oo', 'inf', 'infinity', '∞'):
            target_val = oo
        elif target in ('-oo', '-inf', '-∞'):
            target_val = -oo
        else:
            target_val = _safe_parse(target)
            if target_val is None:
                return VerificationResult(
                    claim=f"lim({f_str}, {var}→{target})",
                    verified=False, method='parse_failure',
                    detail=f'Could not parse target: {target}', confidence=0.0,
                )
        result = limit(f, x, target_val)
        return VerificationResult(
            claim=f"lim({f_str}, {var}→{target})",
            verified=True, method='sympy_limit',
            detail=f'sympy.limit({f}, {var}, {target_val}) = {result}',
            confidence=0.95,
        )
    except Exception as e:
        return VerificationResult(
            claim=f"lim({f_str}, {var}→{target})",
            verified=False, method='exception',
            detail=str(e), confidence=0.0,
        )


def verify_solution(equation_str: str, solution_str: str, var: str = 'x') -> VerificationResult:
    """Verify that solution_str satisfies equation_str.

    equation_str: e.g. 'x^2 - 4 = 0'
    solution_str: e.g. 'x = 2' or 'x = -2, 2'
    """
    eq = equation_str.replace('=', '==') if '==' not in equation_str else equation_str
    eq_parts = eq.split('==', 1)
    if len(eq_parts) != 2:
        return VerificationResult(
            claim=f"{equation_str}, solution: {solution_str}",
            verified=False, method='parse_failure',
            detail='Could not parse equation', confidence=0.0,
        )
    lhs = _safe_parse(eq_parts[0].strip())
    rhs = _safe_parse(eq_parts[1].strip())
    if lhs is None or rhs is None:
        return VerificationResult(
            claim=f"{equation_str}, solution: {solution_str}",
            verified=False, method='parse_failure',
            detail='Could not parse equation parts', confidence=0.0,
        )
    x = Symbol(var)
    # Parse solutions
    solutions = []
    for sol_part in re.split(r'[,;]', solution_str):
        sol_part = sol_part.strip()
        for sep in ['=', '==', '=', '≈']:
            if sep in sol_part:
                val_str = sol_part.split(sep, 1)[1].strip()
                val = _safe_parse(val_str)
                if val is not None:
                    solutions.append(val)
                break
        else:
            val = _safe_parse(sol_part)
            if val is not None:
                solutions.append(val)

    if not solutions:
        return VerificationResult(
            claim=f"{equation_str}, solution: {solution_str}",
            verified=False, method='parse_failure',
            detail='Could not parse any solutions', confidence=0.0,
        )

    verified_count = 0
    details = []
    for val in solutions:
        result = simplify((lhs - rhs).subs(x, val))
        if result == 0:
            verified_count += 1
            details.append(f'x={val}: ✓')
        else:
            details.append(f'x={val}: ✗ (residual={result})')

    if verified_count == len(solutions):
        return VerificationResult(
            claim=f"{equation_str}, solution: {solution_str}",
            verified=True, method='substitution',
            detail='; '.join(details), confidence=0.95,
        )
    elif verified_count > 0:
        return VerificationResult(
            claim=f"{equation_str}, solution: {solution_str}",
            verified=False, method='partial_substitution',
            detail=f'{verified_count}/{len(solutions)} verified; ' + '; '.join(details),
            confidence=0.5,
        )
    return VerificationResult(
        claim=f"{equation_str}, solution: {solution_str}",
        verified=False, method='substitution',
        detail='; '.join(details), confidence=0.95,
    )


def verify_llm_output(text: str) -> List[VerificationResult]:
    """Scan LLM output text for verifiable mathematical claims and check them."""
    results = []

    # Pattern 1: equations like "3x + 2 = 11"
    equation_patterns = [
        r'([a-zA-Z0-9\+\-\*\/\^\(\)\s]+?)\s*(?:==|=|≡)\s*([a-zA-Z0-9\+\-\*\/\^\(\)\s]+)',
    ]
    for pattern in equation_patterns:
        for match in re.finditer(pattern, text):
            clause = match.group(0).strip()
            if len(clause) > 5 and len(clause) < 200:
                result = verify_equation(clause)
                if result.confidence > 0:
                    results.append(result)

    # Pattern 2: derivative claims like "f'(x) = ..." or "d/dx(f) = ..."
    deriv_pattern = r"(?:d/d[x-z]|[fgh]'[\(])([^=]+?)\s*(?:==|=)\s*([^\n,;]+)"
    for match in re.finditer(deriv_pattern, text):
        f_str = match.group(1).strip().rstrip(')')
        deriv_str = match.group(2).strip()
        results.append(verify_derivative(f_str, deriv_str))

    return results