"""Provider Factory — nanobot-style provider lifecycle management.

Key concepts adapted from nanobot's provider architecture:
- **ProviderSnapshot**: Frozen snapshot of provider config at init time — prevents
  runtime mutations from destabilizing the agent loop.
- **FallbackChain**: Ordered list of fallback providers with health-aware routing.
- **ProviderFactory**: Creates and manages provider instances with lifecycle hooks,
  health monitoring, and automatic fallback on failure.

Also adds:
- Circuit breaker pattern: after N consecutive failures, pause a provider temporarily
- Rate limit awareness: track rate-limit headers (Retry-After, X-RateLimit-*)
- Concurrency control: limit simultaneous in-flight requests per provider
"""

from __future__ import annotations

import asyncio
import time
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from jiuzhang.core.config import Config, ProviderConfig
from jiuzhang.core.errors import ModelError


# ── Snapshot ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProviderSnapshot:
    """Immutable snapshot of a provider's configuration at a point in time.

    Inspired by nanobot's ProviderSnapshot: captures the provider state when the
    agent loop starts. All subsequent routing decisions use this snapshot, not
    the live config, so runtime config changes can't destabilize running loops.
    """

    name: str
    provider_type: str
    base_url: str
    api_key: str = ""
    default_model: str = ""
    is_local: bool = True
    max_tokens: int = 8192
    temperature: float = 1.0
    enabled: bool = True

    @classmethod
    def from_provider_config(cls, name: str, config: ProviderConfig, global_config: Config) -> "ProviderSnapshot":
        return cls(
            name=name,
            provider_type=config.provider_type,
            base_url=config.base_url,
            api_key=config.api_key,
            default_model=config.default_model,
            is_local=config.is_local,
            max_tokens=global_config.max_tokens,
            temperature=global_config.temperature,
            enabled=config.enabled,
        )


# ── Health ────────────────────────────────────────────────────────────

class ProviderHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"     # High latency but still usable
    UNSTABLE = "unstable"     # Frequent errors, use only as last resort
    DOWN = "down"             # Unreachable, skip entirely
    CIRCUIT_OPEN = "circuit_open"  # Circuit breaker tripped


@dataclass
class ProviderMetrics:
    """Per-provider health and performance metrics with circuit breaker."""
    name: str
    total_requests: int = 0
    total_successes: int = 0
    total_errors: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float = 0.0
    consecutive_errors: int = 0
    health: ProviderHealth = ProviderHealth.HEALTHY

    # Circuit breaker
    circuit_open_until: float = 0.0
    circuit_half_open: bool = False

    # Rate limit tracking
    rate_limit_remaining: int = 1000
    rate_limit_reset_at: float = 0.0

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.total_successes / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    def record_success(self, latency_ms: float, tokens: int = 0):
        self.total_requests += 1
        self.total_successes += 1
        self.total_latency_ms += latency_ms
        self.last_latency_ms = latency_ms
        self.total_tokens += tokens
        self.consecutive_errors = 0
        self.circuit_half_open = False
        self._update_health()

    def record_error(self):
        self.total_requests += 1
        self.total_errors += 1
        self.consecutive_errors += 1
        self._update_health()

    def record_rate_limit(self, remaining: int, reset_at: float):
        self.rate_limit_remaining = remaining
        self.rate_limit_reset_at = reset_at

    def _update_health(self):
        if self.consecutive_errors >= 5:
            self.health = ProviderHealth.CIRCUIT_OPEN
            self.circuit_open_until = time.time() + min(30 * (2 ** min(self.consecutive_errors - 5, 4)), 300)
        elif self.consecutive_errors >= 3:
            self.health = ProviderHealth.DOWN
        elif self.consecutive_errors >= 2:
            self.health = ProviderHealth.UNSTABLE
        elif self.avg_latency_ms > 30000 and self.total_requests > 3:
            self.health = ProviderHealth.DEGRADED
        else:
            self.health = ProviderHealth.HEALTHY

    def can_use(self) -> bool:
        """Check if this provider is currently usable."""
        if not self.health or self.health == ProviderHealth.CIRCUIT_OPEN:
            if time.time() > self.circuit_open_until:
                self.circuit_half_open = True
                return True  # Allow one probe request
            return False
        if self.health == ProviderHealth.DOWN:
            return False
        return True

    def is_rate_limited(self) -> bool:
        if self.rate_limit_remaining <= 0 and time.time() < self.rate_limit_reset_at:
            return True
        return False


# ── Fallback Chain ────────────────────────────────────────────────────

@dataclass
class FallbackChain:
    """Ordered list of providers to try on failure with health-aware routing.

    Key behaviors:
    - Providers tried in order (primary → first fallback → second → ...)
    - Unhealthy providers skipped
    - If all providers fail, raises ModelError with accumulated diagnostics
    - Each provider may use a different model (configured per provider)
    """

    providers: list[str] = field(default_factory=list)
    max_total_retries: int = 5  # Total retries across all providers

    def get_usable(self, metrics: dict[str, ProviderMetrics]) -> list[str]:
        """Get list of currently usable providers in fallback order."""
        result = []
        for name in self.providers:
            if name in metrics and not metrics[name].can_use():
                continue
            result.append(name)
        return result

    @classmethod
    def auto_build(cls, config: Config, metrics: dict[str, ProviderMetrics]) -> "FallbackChain":
        """Auto-build fallback chain from config.

        Priority: local providers first (fast/cheap), then cloud providers (powerful/expensive).
        Within each tier, prefer healthy providers with lower latency.
        """
        locals_list = []
        clouds = []

        for name, pcfg in config.providers.items():
            if not pcfg.enabled:
                continue
            snap = ProviderSnapshot.from_provider_config(name, pcfg, config)
            if snap.is_local:
                locals_list.append(name)
            else:
                clouds.append(name)

        # Sort locals by health/performance
        def sort_key(name: str) -> float:
            if name in metrics:
                m = metrics[name]
                return m.avg_latency_ms + m.error_rate * 50000
            return 0.0

        locals_list.sort(key=sort_key)
        clouds.sort(key=sort_key)

        chain = locals_list + clouds
        return cls(providers=chain)


# ── ProviderFactory ───────────────────────────────────────────────────

class ProviderFactory:
    """Central provider lifecycle manager.

    Responsibilities:
    1. Create/maintain ProviderSnapshots from configuration
    2. Build and update fallback chains
    3. Track per-provider health metrics
    4. Implement circuit breaker pattern
    5. Route requests to the best available provider

    Usage:
        factory = ProviderFactory(config)
        snapshot, model = factory.pick_provider(task_type="reasoning")
        # ... make request ...
        factory.record_success("ollama", 150, 500)
        # On failure:
        next_provider = factory.next_fallback("ollama")
    """

    def __init__(self, config: Config):
        self.config = config
        self._snapshots: dict[str, ProviderSnapshot] = {}
        self._metrics: dict[str, ProviderMetrics] = {}
        self._fallback_configs: dict[str, FallbackChain] = {}
        self._lock = asyncio.Lock()

        # In-flight request tracking (per provider)
        self._in_flight: dict[str, int] = {}
        self._max_in_flight: dict[str, int] = {
            "ollama": 4,
            "openai_compatible": 4,
            "openai": 8,
            "anthropic": 8,
            "aliyun_coding_plan": 4,
        }

        # Initialize snapshots
        self._refresh_snapshots()

    def _refresh_snapshots(self):
        """Refresh all provider snapshots from config."""
        for name, pcfg in self.config.providers.items():
            if pcfg.enabled:
                self._snapshots[name] = ProviderSnapshot.from_provider_config(
                    name, pcfg, self.config
                )

    def get_snapshot(self, name: str) -> Optional[ProviderSnapshot]:
        return self._snapshots.get(name)

    def get_all_snapshots(self) -> dict[str, ProviderSnapshot]:
        return dict(self._snapshots)

    def get_metrics(self, name: str) -> ProviderMetrics:
        if name not in self._metrics:
            self._metrics[name] = ProviderMetrics(name=name)
        return self._metrics[name]

    def pick_provider(
        self, exclude: Optional[set] = None, prefer_local: bool = True
    ) -> tuple[Optional[ProviderSnapshot], str]:
        """Pick the best available provider.

        Args:
            exclude: Set of provider names to skip
            prefer_local: Whether to prefer local providers

        Returns:
            (ProviderSnapshot, model_name) or (None, "") if none available
        """
        exclude = exclude or set()

        # Build candidates list sorted by preference
        candidates: list[tuple[float, str]] = []
        for name, snap in self._snapshots.items():
            if name in exclude or not snap.enabled:
                continue
            metrics = self.get_metrics(name)
            if not metrics.can_use():
                continue
            if metrics.is_rate_limited():
                continue
            if self._in_flight.get(name, 0) >= self._max_in_flight.get(name, 10):
                continue

            # Score: prefer healthy, low-latency, local
            score = metrics.avg_latency_ms + metrics.error_rate * 50000
            if prefer_local and snap.is_local:
                score -= 100000  # Strong preference for local
            candidates.append((score, name))

        if not candidates:
            return None, ""

        candidates.sort(key=lambda x: x[0])
        best_name = candidates[0][1]
        snap = self._snapshots[best_name]
        return snap, snap.default_model

    def next_fallback(self, failed_provider: str, exclude: set | None = None) -> tuple[Optional[ProviderSnapshot], str]:
        """Get the next provider to try after a failure."""
        exclude = exclude or set()
        exclude.add(failed_provider)
        snap, model = self.pick_provider(exclude=exclude)
        return snap, model

    def record_success(self, provider_name: str, latency_ms: float, tokens: int = 0):
        metrics = self.get_metrics(provider_name)
        metrics.record_success(latency_ms, tokens)

    def record_error(self, provider_name: str):
        metrics = self.get_metrics(provider_name)
        metrics.record_error()

    def record_rate_limit(self, provider_name: str, remaining: int, reset_at: float):
        metrics = self.get_metrics(provider_name)
        metrics.record_rate_limit(remaining, reset_at)

    async def acquire_slot(self, provider_name: str) -> bool:
        """Try to acquire an in-flight request slot. Returns True if acquired."""
        async with self._lock:
            current = self._in_flight.get(provider_name, 0)
            max_slots = self._max_in_flight.get(provider_name, 4)
            if current >= max_slots:
                return False
            self._in_flight[provider_name] = current + 1
            return True

    async def release_slot(self, provider_name: str):
        async with self._lock:
            current = self._in_flight.get(provider_name, 0)
            if current > 0:
                self._in_flight[provider_name] = current - 1

    def get_health_report(self) -> str:
        lines = ["Provider Factory Health Report", "=" * 45]
        for name in self._snapshots:
            m = self.get_metrics(name)
            in_flight = self._in_flight.get(name, 0)
            lines.append(
                f"  {name:20s} | {m.health.value:14s} | "
                f"ok={m.success_rate:.1%} | lat={m.avg_latency_ms:.0f}ms | "
                f"err_consec={m.consecutive_errors} | flight={in_flight}"
            )
        return "\n".join(lines)

    def get_best_provider_name(self) -> str:
        """Return name of the best currently available provider."""
        snap, _ = self.pick_provider()
        return snap.name if snap else self.config.active_provider
