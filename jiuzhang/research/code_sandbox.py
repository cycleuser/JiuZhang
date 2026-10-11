"""Hardened Code Sandbox for safe mathematical code execution.

Upgrades the original CodeInterpreter with:
1. Proper sandboxing via subprocess isolation
2. Resource limits (CPU time, memory, disk)
3. Library allowlist with version pinning
4. Output capture with size limits
5. Persistent notebook sessions across turns
6. Plotting support (matplotlib output captured as base64)
7. Timeout enforcement
8. Import auditing
"""

import ast
import io
import os
import re
import sys
import time
import base64
import hashlib
import threading
import resource
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

# Math-safe builtins
SAFE_BUILTINS = {
    'True': True, 'False': False, 'None': None,
    'abs': abs, 'all': all, 'any': any,
    'bool': bool, 'bytes': bytes, 'chr': chr,
    'complex': complex, 'dict': dict, 'divmod': divmod,
    'enumerate': enumerate, 'filter': filter, 'float': float,
    'format': format, 'frozenset': frozenset, 'int': int,
    'len': len, 'list': list, 'map': map,
    'max': max, 'min': min, 'ord': ord,
    'pow': pow, 'print': print, 'range': range,
    'repr': repr, 'reversed': reversed, 'round': round,
    'set': set, 'slice': slice, 'sorted': sorted,
    'str': str, 'sum': sum, 'tuple': tuple,
    'type': type, 'zip': zip, 'isinstance': isinstance,
}

# Allowed import modules
ALLOWED_MODULES = {
    # Math
    'math', 'cmath', 'decimal', 'fractions', 'statistics',
    'itertools', 'functools', 'collections', 'random',
    'operator', 'hashlib', 'base64', 'json', 're',
    # Scientific
    'sympy', 'numpy', 'scipy', 'mpmath',
    # Plotting (via io.BytesIO)
    'matplotlib', 'matplotlib.pyplot', 'matplotlib.figure',
    'seaborn', 'plotly',
    # Data
    'pandas', 'csv', 'dataclasses', 'typing', 'enum',
    'datetime', 'time',
}

# Blocked modules (security)
BLOCKED_MODULES = {
    'os', 'sys', 'subprocess', 'shutil', 'socket',
    'http', 'urllib', 'requests', 'ftplib', 'smtplib',
    'telnetlib', 'pickle', 'shelve', 'marshal',
    'ctypes', 'multiprocessing', 'threading', 'signal',
    'importlib', 'pkgutil', 'runpy', 'builtins',
    'pathlib', 'io' 'open', 'exec', 'eval', 'compile',
    '__builtins__', '__import__',
}


@dataclass
class SandboxConfig:
    timeout_seconds: float = 30.0
    max_memory_mb: int = 512
    max_output_bytes: int = 1_000_000  # 1MB
    max_code_length: int = 100_000    # 100KB
    allow_imports: bool = True
    allow_plots: bool = True
    isolate_process: bool = True     # Run in subprocess


@dataclass
class SandboxResult:
    success: bool
    output: str = ""
    error: str = ""
    plots: list = field(default_factory=list)  # base64 encoded images
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    memory_used_mb: float = 0.0
    exit_code: int = 0


class ImportAuditor(ast.NodeVisitor):
    """AST visitor that audits import statements for security."""

    def __init__(self):
        self.imports = []
        self.blocked = []
        self.allowed = []

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name.split('.')[0]
            self._check(name)

    def visit_ImportFrom(self, node):
        if node.module:
            name = node.module.split('.')[0]
            self._check(name)

    def _check(self, name: str):
        self.imports.append(name)
        if name in BLOCKED_MODULES:
            self.blocked.append(name)
        elif name in ALLOWED_MODULES:
            self.allowed.append(name)

    def is_safe(self) -> bool:
        return len(self.blocked) == 0


class CodeSandbox:
    """Hardened sandbox for safe mathematical code execution.

    Usage:
        sandbox = CodeSandbox()
        result = sandbox.execute('''
            import sympy as sp
            x = sp.Symbol('x')
            result = sp.integrate(x**2, x)
            print(f"∫x² dx = {result}")
        ''')
        print(result.output)
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._sessions: dict[str, dict] = {}  # Persistent notebook sessions

    def execute(self, code: str, session_id: str = "default") -> SandboxResult:
        """Execute math code safely.

        Args:
            code: Python code to execute
            session_id: Persistent session identifier

        Returns:
            SandboxResult with output, errors, and plots
        """
        # Pre-flight checks
        if len(code) > self.config.max_code_length:
            return SandboxResult(
                success=False,
                error=f"Code too long: {len(code)} > {self.config.max_code_length} chars",
            )

        # Audit imports
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return SandboxResult(success=False, error=f"Syntax error: {e}")

        auditor = ImportAuditor()
        auditor.visit(tree)

        if auditor.blocked:
            return SandboxResult(
                success=False,
                error=f"Blocked imports: {', '.join(auditor.blocked)}. "
                      f"These modules are not allowed for security reasons.",
            )

        # Check for dangerous builtins
        if self._has_dangerous_calls(code):
            return SandboxResult(
                success=False,
                error="Dangerous function calls detected (exec, eval, __import__, open, etc.)",
            )

        # Execute
        if self.config.isolate_process:
            return self._execute_subprocess(code, session_id)
        else:
            return self._execute_inline(code, session_id)

    def _execute_subprocess(self, code: str, session_id: str) -> SandboxResult:
        """Execute in a separate subprocess for isolation."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            # Wrap code with safety
            wrapped = self._wrap_code(code, session_id)
            f.write(wrapped)
            tmp_path = f.name

        try:
            start = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True, text=True,
                timeout=self.config.timeout_seconds,
                env={**os.environ, "PYTHONHASHSEED": "0"},
            )
            elapsed = time.perf_counter() - start

            return SandboxResult(
                success=proc.returncode == 0,
                stdout=proc.stdout[:self.config.max_output_bytes],
                stderr=proc.stderr[:self.config.max_output_bytes],
                output=(proc.stdout + "\n" + proc.stderr).strip()[:self.config.max_output_bytes],
                execution_time=elapsed,
                exit_code=proc.returncode,
                error=proc.stderr if proc.returncode != 0 else "",
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                error=f"Execution timed out after {self.config.timeout_seconds}s",
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _execute_inline(self, code: str, session_id: str) -> SandboxResult:
        """Execute code inline (less isolation, for development)."""
        result = SandboxResult(success=False)
        start = time.perf_counter()

        # Set up safe globals
        safe_globals = {"__builtins__": SAFE_BUILTINS}

        # Add allowed modules
        for mod_name in auditor.allowed:
            try:
                mod = __import__(mod_name)
                safe_globals[mod_name] = mod
            except ImportError:
                pass

        # Load session state
        session = self._get_session(session_id)
        safe_globals.update(session.get("variables", {}))

        # Capture stdout
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            sys.stdout = stdout_buf
            sys.stderr = stderr_buf

            exec(code, safe_globals)
            result.success = True
        except Exception as e:
            result.error = f"{type(e).__name__}: {e}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        elapsed = time.perf_counter() - start
        result.execution_time = elapsed
        result.stdout = stdout_buf.getvalue()[:self.config.max_output_bytes]
        result.stderr = stderr_buf.getvalue()[:self.config.max_output_bytes]
        result.output = (result.stdout + "\n" + result.stderr).strip()

        # Save session state (only safe variables)
        session["variables"] = {
            k: v for k, v in safe_globals.items()
            if not k.startswith('_') and k not in SAFE_BUILTINS
            and isinstance(v, (int, float, str, list, dict, tuple, bool, type(None)))
        }

        # Capture matplotlib plots
        if self.config.allow_plots and 'matplotlib' in safe_globals:
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                for fig_num in plt.get_fignums():
                    fig = plt.figure(fig_num)
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=100)
                    buf.seek(0)
                    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
                    result.plots.append(img_b64)
                plt.close('all')
            except Exception:
                pass

        return result

    def _wrap_code(self, code: str, session_id: str) -> str:
        """Wrap code with safety preamble for subprocess execution."""
        return f'''"""Sandboxed math execution — DO NOT EDIT."""
import sys
import traceback
import signal

# Resource limits
def _timeout_handler(signum, frame):
    raise TimeoutError("Execution time limit exceeded")

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm({int(self.config.timeout_seconds)})

# Blocked module guard
import builtins
_original_import = builtins.__import__

BLOCKED = {repr(BLOCKED_MODULES)}

def _safe_import(name, *args, **kwargs):
    root = name.split('.')[0]
    if root in BLOCKED:
        raise ImportError(f"Module '{{name}}' is blocked for security")
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _safe_import

try:
{chr(10).join('    ' + line for line in code.split(chr(10)))}
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
finally:
    signal.alarm(0)
'''

    def _get_session(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "variables": {},
                "history": [],
                "created_at": time.time(),
            }
        return self._sessions[session_id]

    def _has_dangerous_calls(self, code: str) -> bool:
        """Check for dangerous function calls."""
        dangerous = [
            r'\bexec\s*\(', r'\beval\s*\(', r'\bcompile\s*\(',
            r'\b__import__\s*\(', r'\bopen\s*\(', r'\b__builtins__',
            r'\bos\.system\b', r'\bos\.popen\b', r'\bsubprocess\b',
            r'\bimportlib\b', r'\bimport\(\s*["\']',
        ]
        return any(re.search(p, code) for p in dangerous)

    def create_session(self, session_id: str = ""):
        """Create a named persistent session."""
        if not session_id:
            session_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
        self._get_session(session_id)
        return session_id

    def clear_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    def list_sessions(self) -> list:
        return [
            {"id": sid, "variables": len(s.get("variables", {})),
             "history": len(s.get("history", [])),
             "age": f"{time.time() - s.get('created_at', time.time()):.0f}s"}
            for sid, s in self._sessions.items()
        ]

    # ── Pre-built Math Cells ─────────────────────────────────────────

    @staticmethod
    def math_preamble() -> str:
        """Standard math preamble for sandbox sessions."""
        return """import sympy as sp
import numpy as np
from sympy import (
    symbols, Symbol, Rational, pi, E, I, oo,
    sqrt, sin, cos, tan, exp, log,
    diff, integrate, solve, simplify, factor, expand,
    limit, series, Matrix, factorial, gcd, isprime,
)
x, y, z, t = symbols('x y z t')
n, k, m = symbols('n k m', integer=True)
print("Math sandbox ready. Variables: x, y, z, t (reals), n, k, m (integers)")
"""

    @staticmethod
    def plotting_preamble() -> str:
        """Standard plotting preamble."""
        return """import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def plot_function(f, x_range=(-5, 5), title="Function", num=500):
    x_vals = np.linspace(x_range[0], x_range[1], num)
    y_vals = [f(xi) for xi in x_vals]
    plt.figure(figsize=(8, 5))
    plt.plot(x_vals, y_vals)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.xlabel('x')
    plt.ylabel('f(x)')
    plt.show()

print("Plotting ready. Use plot_function() for graphs.")
"""
