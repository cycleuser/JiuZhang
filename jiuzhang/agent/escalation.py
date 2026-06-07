"""Escalation Engine — model tiering for autonomous research.

Inspired by smallcode: when the local model is stuck (3+ verification failures,
contradiction loops, or timeout), escalate to a stronger cloud model.

The escalation engine:
1. Auto-detects available cloud API keys (Anthropic first, then OpenAI, then DeepSeek)
2. Converts conversation history into provider-native format
3. Frames the escalation with a system message: "A smaller local model failed..."
4. Session cap to prevent runaway API costs (default 5 escalations)
5. Graceful degradation if no cloud keys are configured
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable
import os
import time


class EscalationReason(Enum):
    VERIFICATION_FAILURE = "verification_failure"     # 3+ SymPy verifications failed
    CONTRADICTION_LOOP = "contradiction_loop"         # Model contradicts itself repeatedly
    TIMEOUT = "timeout"                               # Experiment exceeded time budget
    PROOF_STUCK = "proof_stuck"                       # Can't complete proof after N attempts
    OUT_OF_SCOPE = "out_of_scope"                     # Topic beyond local model capability
    CRASH = "crash"                                   # Code execution failure


@dataclass
class EscalationConfig:
    max_escalations_per_session: int = 5
    verification_failure_threshold: int = 3
    contradiction_threshold: int = 3
    proof_attempt_threshold: int = 5
    timeout_seconds: int = 600
    cooldown_seconds: int = 300  # Minimum time between escalations


@dataclass
class EscalationEvent:
    reason: EscalationReason
    timestamp: float = field(default_factory=time.time)
    context: str = ""
    local_model: str = ""
    escalated_to: str = ""
    success: bool = False
    cost_estimate_usd: float = 0.0


class EscalationEngine:
    """Smart escalation from local to cloud models.

    Detects when the local model is stuck and automatically escalates
    to a stronger cloud model, with cost controls and session limits.
    """

    def __init__(self, config: Optional[EscalationConfig] = None):
        self.config = config or EscalationConfig()
        self._events: list = []
        self._verification_failures: int = 0
        self._contradictions: int = 0
        self._proof_attempts: int = 0
        self._last_escalation_time: float = 0
        self._available_providers: list = []
        self._detect_providers()

    def _detect_providers(self):
        """Auto-detect available cloud API keys."""
        providers = []
        if os.environ.get("ANTHROPIC_API_KEY"):
            providers.append("anthropic")
        if os.environ.get("OPENAI_API_KEY"):
            providers.append("openai")
        if os.environ.get("DEEPSEEK_API_KEY"):
            providers.append("deepseek")
        self._available_providers = providers

    @property
    def can_escalate(self) -> bool:
        """Check if escalation is available (has API keys + under session cap)."""
        if not self._available_providers:
            return False
        if len(self._events) >= self.config.max_escalations_per_session:
            return False
        if time.time() - self._last_escalation_time < self.config.cooldown_seconds:
            return False
        return True

    @property
    def next_provider(self) -> Optional[str]:
        """Get the next available provider in preference order."""
        if not self._available_providers:
            return None
        return self._available_providers[0]  # Anthropic preferred, then OpenAI, then DeepSeek

    def should_escalate(self, reason: EscalationReason) -> bool:
        """Determine if conditions warrant escalation."""
        if not self.can_escalate:
            return False

        if reason == EscalationReason.VERIFICATION_FAILURE:
            return self._verification_failures >= self.config.verification_failure_threshold
        elif reason == EscalationReason.CONTRADICTION_LOOP:
            return self._contradictions >= self.config.contradiction_threshold
        elif reason == EscalationReason.PROOF_STUCK:
            return self._proof_attempts >= self.config.proof_attempt_threshold
        elif reason in (EscalationReason.TIMEOUT, EscalationReason.CRASH, EscalationReason.OUT_OF_SCOPE):
            return True

        return False

    def escalate(
        self,
        reason: EscalationReason,
        conversation_history: list,
        client,
        context: str = "",
    ) -> Optional[str]:
        """Execute an escalation to the cloud model.

        Args:
            reason: Why we're escalating
            conversation_history: Full message history from local model
            client: MultiProviderClient instance
            context: Additional context about what went wrong

        Returns:
            Cloud model's response text, or None if escalation failed
        """
        if not self.should_escalate(reason):
            return None

        provider = self.next_provider
        if not provider:
            return None

        # Build escalation prompt (smallcode pattern)
        frame_messages = [
            {
                "role": "system",
                "content": (
                    "A smaller local model attempted to solve this mathematical research "
                    f"task and failed. Reason: {reason.value}. Context: {context}\n\n"
                    "Your task: Fix the issue in as few tool calls as possible. "
                    "Provide a correct, verified solution. Be precise about mathematical reasoning."
                ),
            }
        ]

        # Convert and compress history
        history_summary = self._summarize_history(conversation_history)
        frame_messages.append({"role": "user", "content": history_summary})

        # Send to cloud provider
        event = EscalationEvent(
            reason=reason, context=context, local_model="local", escalated_to=provider
        )

        try:
            result = client.send_message(
                messages=frame_messages,
                provider=provider,
                max_tokens=4096,
                temperature=0.7,
            )
            if result.success:
                event.success = True
                event.cost_estimate_usd = self._estimate_cost(result.data)
                self._events.append(event)
                self._last_escalation_time = time.time()
                self._reset_counters()
                return result.data
        except Exception:
            pass

        self._events.append(event)
        return None

    def record_verification_failure(self):
        self._verification_failures += 1

    def record_contradiction(self):
        self._contradictions += 1

    def record_proof_attempt(self):
        self._proof_attempts += 1

    def record_success(self):
        """Reset counters on success."""
        self._reset_counters()

    def _reset_counters(self):
        self._verification_failures = 0
        self._contradictions = 0
        self._proof_attempts = 0

    def _summarize_history(self, messages: list, max_chars: int = 4000) -> str:
        """Summarize conversation history for the escalation prompt."""
        parts = []
        total = 0
        for msg in reversed(messages):
            content = msg.get("content", "")
            role = msg.get("role", "unknown")
            line = f"[{role}]: {content[:300]}"
            if total + len(line) > max_chars:
                parts.append("... [earlier context truncated]")
                break
            parts.append(line)
            total += len(line)
        return "\n".join(reversed(parts))

    def _estimate_cost(self, response_text: str) -> float:
        """Rough cost estimate in USD."""
        tokens = len(response_text) / 4  # Rough
        # Anthropic Claude: ~$15/M input, $75/M output
        # Use a blended rate of ~$30/M tokens as rough estimate
        return (tokens / 1_000_000) * 30.0

    @property
    def total_cost(self) -> float:
        return sum(e.cost_estimate_usd for e in self._events)

    @property
    def escalation_count(self) -> int:
        return len(self._events)

    def get_report(self) -> str:
        """Get a summary report of all escalations."""
        if not self._events:
            return "No escalations this session."

        lines = ["Escalation Report:", f"Total escalations: {len(self._events)}"]
        for i, e in enumerate(self._events, 1):
            lines.append(
                f"  {i}. {e.reason.value} → {e.escalated_to} "
                f"({'OK' if e.success else 'FAIL'}) "
                f"${e.cost_estimate_usd:.4f}"
            )
        lines.append(f"Total estimated cost: ${self.total_cost:.4f}")
        return "\n".join(lines)
