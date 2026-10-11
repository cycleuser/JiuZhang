"""Phase 1 unit tests for JiuZhang V3 core modules."""
import os, subprocess, sys

PYTHON = "/Users/fred/miniconda3/bin/python"
ROOT = "/Users/fred/Documents/GitHub/cycleuser/JiuZhang"
ENV = {**os.environ, "PYTHONPATH": ROOT}


def run_test(name, script):
    r = subprocess.run(
        [PYTHON, "-c", script],
        capture_output=True, text=True, timeout=60, cwd=ROOT, env=ENV,
    )
    ok = r.returncode == 0
    print(f"{'OK' if ok else 'FAIL'} {name}")
    if not ok:
        out = (r.stdout + "\n" + r.stderr).strip()
        for line in out.split("\n")[-5:]:
            print(f"   {line}")
    return ok


ok = 0
total = 0


def T(name, script):
    global ok, total
    total += 1
    if run_test(name, script):
        ok += 1


# ── 1. ProviderFactory ────────────────────────────────────────────────
T("ProviderFactory init + pick_provider", """
from jiuzhang.core.config import Config
from jiuzhang.core.provider_factory import ProviderFactory, ProviderHealth, FallbackChain

config = Config()
factory = ProviderFactory(config)

snaps = factory.get_all_snapshots()
assert len(snaps) == 5, f"Expected 5, got {len(snaps)}"
assert "ollama" in snaps

snap, model = factory.pick_provider()
assert snap is not None
assert snap.name == "ollama", f"Expected ollama, got {snap.name}"
assert model == "qwen2.5:7b"

factory.record_success("ollama", 150.0, 500)
m = factory.get_metrics("ollama")
assert m.total_successes == 1, f"Got {m.total_successes}"
assert m.avg_latency_ms == 150.0, f"Got {m.avg_latency_ms}"
assert m.health == ProviderHealth.HEALTHY

factory.record_error("openai")
factory.record_error("openai")
m2 = factory.get_metrics("openai")
assert m2.consecutive_errors == 2, f"Got {m2.consecutive_errors}"
assert m2.health == ProviderHealth.UNSTABLE, f"Got {m2.health}"

chain = FallbackChain.auto_build(config, {})
assert len(chain.providers) >= 2, f"Got {len(chain.providers)}"

snap2, _ = factory.pick_provider(exclude={"ollama"})
assert snap2 is not None

report = factory.get_health_report()
assert "ollama" in report
best = factory.get_best_provider_name()
assert best in snaps
print("PASS")
""")

# ── 2. ProviderMetrics circuit breaker ───────────────────────────────
T("ProviderMetrics circuit breaker", """
from jiuzhang.core.provider_factory import ProviderMetrics, ProviderHealth

m = ProviderMetrics(name="test")
assert m.health == ProviderHealth.HEALTHY
assert m.can_use()

for _ in range(5):
    m.record_error()

assert m.health == ProviderHealth.CIRCUIT_OPEN, f"Got {m.health}"
assert m.consecutive_errors == 5

m.record_success(50.0, 100)
assert m.health == ProviderHealth.HEALTHY
assert m.consecutive_errors == 0
assert m.can_use()
print("PASS")
""")

# ── 3. ProviderSnapshot ──────────────────────────────────────────────
T("ProviderSnapshot frozen + from_config", """
from jiuzhang.core.config import Config
from jiuzhang.core.provider_factory import ProviderSnapshot

config = Config()
snap = ProviderSnapshot.from_provider_config("ollama", config.providers["ollama"], config)
assert snap.name == "ollama"
assert snap.is_local == True
assert snap.provider_type == "ollama"
assert snap.base_url == "http://localhost:11434/v1"
assert snap.default_model == "qwen2.5:7b"

openai_snap = ProviderSnapshot.from_provider_config("openai", config.providers["openai"], config)
assert openai_snap.provider_type == "openai"
assert not openai_snap.is_local

try:
    snap.name = "changed"
    assert False, "Should have raised"
except Exception:
    pass
print("PASS")
""")

# ── 4. MultiProviderClient ────────────────────────────────────────────
T("MultiProviderClient sync API", """
from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient

config = Config()
client = MultiProviderClient(config)
assert client.get_best_provider() is not None
report = client.get_health_report()
assert "Provider Factory" in report

r = client.explain_concept("addition", level="elementary")
assert r is not None
r2 = client.generate_exercise("fractions", count=3)
assert r2 is not None
r3 = client.list_models()
assert r3 is not None
print("PASS")
""")

# ── 5. AsyncModelProvider ────────────────────────────────────────────
T("AsyncModelProvider construct + types", """
from jiuzhang.core.config import Config
from jiuzhang.core.async_provider import AsyncModelProvider, ModelResponse, StreamEvent, StreamEventType

config = Config()
provider = AsyncModelProvider(config)
factory = provider.get_factory()
assert factory is not None
assert provider.get_best_provider() in config.providers
assert provider.token_budget_remaining > 0
provider.set_token_budget(50000)
assert provider.token_budget_remaining == 50000

resp = ModelResponse(text="hello", model="test", provider="test", tokens_used=10, latency_ms=100.0)
assert resp.text == "hello"

e1 = StreamEvent(type=StreamEventType.TEXT, content="hi")
assert not e1.is_terminal
e2 = StreamEvent(type=StreamEventType.DONE)
assert e2.is_terminal
e3 = StreamEvent(type=StreamEventType.ERROR, content="fail")
assert e3.is_terminal

report = provider.get_health_report()
assert report
provider.clear_cache()
provider.reset_budget()
print("PASS")
""")

# ── 6. Config ────────────────────────────────────────────────────────
T("Config to_dict/from_dict", """
from jiuzhang.core.config import Config

config = Config()
d = config.to_dict()
config2 = Config.from_dict(d)
assert config2.active_provider == "ollama"
assert config2.language == "zh"
assert config2.max_tokens == 8192

p = config.get_provider("ollama")
assert p.is_local == True
assert "11434" in p.base_url

p2 = config.get_provider("openai")
assert not p2.is_local
print("PASS")
""")

# ── 7. Config save/load ──────────────────────────────────────────────
T("Config save and load from file", """
import tempfile, os
from jiuzhang.core.config import Config

config = Config()
config.language = "en"
config.active_provider = "openai"

tmp = tempfile.mktemp(suffix=".json")
try:
    config.save(tmp)
    loaded = Config.load(tmp)
    assert loaded.language == "en", f"Got {loaded.language}"
    assert loaded.active_provider == "openai", f"Got {loaded.active_provider}"
finally:
    if os.path.exists(tmp):
        os.remove(tmp)
print("PASS")
""")

# ── 8. ToolResult ────────────────────────────────────────────────────
T("ToolResult ok/fail", """
from jiuzhang.core.errors import ToolResult

r1 = ToolResult.ok("hello", {"meta": 1})
assert r1.success
assert r1.data == "hello"
assert r1.metadata == {"meta": 1}

r2 = ToolResult.fail("bad")
assert not r2.success
assert r2.error == "bad"

from jiuzhang.core.errors import JiuZhangError, ConfigError, ModelError
try:
    raise ConfigError("test")
except JiuZhangError:
    pass
else:
    assert False

print("PASS")
""")

# ── 9. Core __init__ exports ─────────────────────────────────────────
T("core.__init__ exports all V3 modules", """
from jiuzhang.core import (
    Config, ProviderConfig,
    ToolResult, JiuZhangError, ConfigError, ModelError,
    MultiProviderClient,
    AsyncModelProvider, ModelResponse, StreamEvent, StreamEventType,
    ProviderFactory, ProviderSnapshot, ProviderMetrics, ProviderHealth, FallbackChain,
)
# All should be non-None
assert AsyncModelProvider is not None
assert ProviderFactory is not None
assert ProviderSnapshot is not None
assert StreamEvent is not None
print("PASS")
""")

# ── Summary ──────────────────────────────────────────────────────────
print(f"\\n{'='*60}")
print(f"Phase 1: {ok}/{total} passed")
if ok == total:
    print("ALL PHASE 1 TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({total - ok} failures)")
    sys.exit(1)
