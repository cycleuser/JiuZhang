"""Unified Async Model Provider — streaming-first, multi-provider AI model client.

Upgrades from the original synchronous multi_provider_api.py with:
- Full async/await support (asyncio + aiohttp)
- True streaming with async generators (token-by-token yield)
- Built-in retry with exponential backoff + jitter
- Token usage tracking with tiktoken (fallback to character-based estimate)
- Provider health monitoring via ProviderFactory
- Automatic fallback to next healthiest provider on failure
- Response caching for repeated queries
- Concurrency control with in-flight request slots
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional

from jiuzhang.core.config import Config, ProviderConfig
from jiuzhang.core.errors import ToolResult, ModelError
from jiuzhang.core.provider_factory import (
    ProviderFactory, ProviderSnapshot, ProviderMetrics, ProviderHealth,
)

# Lazy import: aiohttp may not be available on all platforms
_aiohttp = None


def _get_aiohttp():
    global _aiohttp
    if _aiohttp is None:
        import aiohttp as _mod
        _aiohttp = _mod
    return _aiohttp

# Try tiktoken for accurate token counting, fall back to heuristic
try:
    import tiktoken
    _TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
    def _count_tokens(text: str) -> int:
        return len(_TIKTOKEN_ENC.encode(text))
except ImportError:
    def _count_tokens(text: str) -> int:
        # Rough: ~4 chars per token for English, ~1.5 chars per token for CJK
        return max(len(text.encode("utf-8")) // 3, 1)


# ── Public Data Types ─────────────────────────────────────────────────

@dataclass
class ModelResponse:
    """Complete model response with metadata."""
    text: str
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    cached: bool = False


class StreamEventType(Enum):
    TEXT = "text"              # Regular text chunk
    THINKING = "thinking"      # Chain-of-thought / reasoning
    TOOL_CALL = "tool_call"    # Tool call requested
    DONE = "done"              # Stream complete
    ERROR = "error"            # Stream error


@dataclass
class StreamEvent:
    """Single event in a streaming response."""
    type: StreamEventType
    content: str = ""
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.type in (StreamEventType.DONE, StreamEventType.ERROR)


# ── Async Model Provider ─────────────────────────────────────────────

class AsyncModelProvider:
    """Unified async client for multiple AI model providers.

    Features:
    - True token-by-token streaming via async generators
    - Retry with jittered exponential backoff
    - ProviderFactory for health-aware routing and fallback
    - Token budget tracking (tiktoken when available)
    - Response caching
    - Concurrency control per provider

    Usage:
        provider = AsyncModelProvider(config)
        async for event in provider.stream_events(messages):
            if event.type == StreamEventType.TEXT:
                print(event.content, end="")

        response = await provider.send(messages)
        print(response.text)
    """

    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._session: Optional[aiohttp.ClientSession] = None
        self._factory = ProviderFactory(self.config)
        self._cache: dict[str, ModelResponse] = {}
        self._token_budget_used: int = 0
        self._token_budget_limit: int = 1_000_000

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            aiohttp = _get_aiohttp()
            timeout = aiohttp.ClientTimeout(total=300, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    # ── Token Budget ──────────────────────────────────────────────────

    @property
    def token_budget_used(self) -> int:
        return self._token_budget_used

    @property
    def token_budget_remaining(self) -> int:
        return max(0, self._token_budget_limit - self._token_budget_used)

    def set_token_budget(self, limit: int):
        self._token_budget_limit = limit

    def reset_budget(self):
        self._token_budget_used = 0

    # ── Caching ───────────────────────────────────────────────────────

    def _cache_key(self, messages: list, model: str, **kwargs) -> str:
        content = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        content += model + str(kwargs.get("temperature", ""))
        return hashlib.sha256(content.encode()).hexdigest()

    def clear_cache(self):
        self._cache.clear()

    # ── Core Send (non-streaming) ─────────────────────────────────────

    async def send(
        self,
        messages: list,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = False,
    ) -> ModelResponse:
        """Send messages and get a complete response.

        Uses ProviderFactory for health-aware routing and automatic fallback.
        """
        await self._ensure_session()

        model_name = model or self.config.active_model
        max_tok = max_tokens or self.config.max_tokens
        temp = temperature if temperature is not None else self.config.temperature
        provider_name = provider or self.config.active_provider

        # Check cache
        if use_cache:
            key = self._cache_key(messages, model_name, temperature=temp)
            if key in self._cache:
                cached = self._cache[key]
                return ModelResponse(
                    text=cached.text, model=model_name, provider=provider_name,
                    tokens_used=0, latency_ms=0, cached=True,
                )

        # Try providers with fallback
        tried: set[str] = set()
        current_provider = provider_name

        for attempt in range(self.MAX_RETRIES * 2):  # More attempts across fallbacks
            # Get provider config
            if current_provider not in self.config.providers:
                snap, _ = self._factory.pick_provider(exclude=tried)
                if snap is None:
                    raise ModelError(f"No usable providers available. Tried: {tried}")
                current_provider = snap.name

            provider_config = self.config.get_provider(current_provider)
            tried.add(current_provider)

            # Acquire concurrency slot
            slot_acquired = await self._factory.acquire_slot(current_provider)
            if not slot_acquired:
                # Try next provider
                snap, _ = self._factory.next_fallback(current_provider, exclude=tried)
                if snap:
                    current_provider = snap.name
                    continue
                # Wait and retry same provider
                await asyncio.sleep(0.5)

            start = time.perf_counter()
            try:
                result = await self._send_request(
                    provider_config, messages, model_name, max_tok, temp, stream=False,
                )
                latency = (time.perf_counter() - start) * 1000

                if result.success:
                    text = result.data if isinstance(result.data, str) else str(result.data)
                    tokens = _count_tokens(text)
                    self._token_budget_used += tokens
                    self._factory.record_success(current_provider, latency, tokens)

                    response = ModelResponse(
                        text=text, model=model_name, provider=current_provider,
                        tokens_used=tokens, latency_ms=latency,
                    )
                    if use_cache:
                        key = self._cache_key(messages, model_name, temperature=temp)
                        self._cache[key] = response
                    return response
                else:
                    self._factory.record_error(current_provider)

            except (Exception, asyncio.TimeoutError, ModelError) as e:
                self._factory.record_error(current_provider)
            finally:
                await self._factory.release_slot(current_provider)

            # Try fallback
            snap, fallback_model = self._factory.next_fallback(current_provider, exclude=tried)
            if snap:
                current_provider = snap.name
                if not model:
                    model_name = fallback_model
                await self._backoff(attempt)
            elif attempt < self.MAX_RETRIES - 1:
                await self._backoff(attempt)
            else:
                break

        raise ModelError(f"All providers exhausted. Tried: {tried}")

    async def _send_request(
        self,
        provider_config: ProviderConfig,
        messages: list,
        model: str,
        max_tokens: int,
        temperature: float,
        stream: bool = False,
    ) -> ToolResult:
        """Send a single HTTP request and return the parsed result."""
        endpoint = self._get_endpoint(provider_config)
        headers = self._build_headers(provider_config)
        body = self._build_body(provider_config, messages, model, max_tokens, temperature, stream)

        async with self._session.post(endpoint, headers=headers, json=body) as resp:
            if resp.status == 429:
                # Rate limited — extract Retry-After
                retry_after = resp.headers.get("Retry-After", "5")
                try:
                    wait_s = float(retry_after)
                except ValueError:
                    wait_s = 5.0
                return ToolResult.fail(f"Rate limited (retry after {wait_s}s)", metadata={"retry_after": wait_s})

            if resp.status != 200:
                text = await resp.text()
                return ToolResult.fail(f"HTTP {resp.status}: {text[:300]}")

            if stream:
                # Collect all chunks for non-streaming use case
                chunks = []
                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    if line_str == "[DONE]":
                        break
                    try:
                        data = json.loads(line_str)
                        chunk = self._extract_chunk(provider_config, data)
                        if chunk:
                            chunks.append(chunk)
                    except json.JSONDecodeError:
                        continue
                return ToolResult.ok(data="".join(chunks))
            else:
                data = await resp.json()
                return self._parse_response(provider_config, data)

    # ── Streaming ─────────────────────────────────────────────────────

    async def stream(
        self,
        messages: list,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """Stream a response as raw text chunks (compatible legacy interface).

        For richer events (thinking/tool_calls/etc.), use stream_events().
        """
        async for event in self.stream_events(messages, provider, model, max_tokens, temperature):
            if event.type == StreamEventType.TEXT or event.type == StreamEventType.THINKING:
                yield event.content

    async def stream_events(
        self,
        messages: list,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a response as typed events.

        Yields StreamEvent objects with type (TEXT, THINKING, TOOL_CALL, DONE, ERROR).
        This is the primary streaming interface — it supports reasoning content,
        tool calls, and proper error propagation.
        """
        await self._ensure_session()

        model_name = model or self.config.active_model
        max_tok = max_tokens or self.config.max_tokens
        temp = temperature if temperature is not None else self.config.temperature

        provider_config = self.config.get_provider(provider)
        provider_name = provider or self.config.active_provider

        slot_acquired = await self._factory.acquire_slot(provider_name)
        if not slot_acquired:
            yield StreamEvent(type=StreamEventType.ERROR, content="Provider at capacity")
            return

        start = time.perf_counter()
        try:
            endpoint = self._get_endpoint(provider_config)
            headers = self._build_headers(provider_config)
            body = self._build_body(provider_config, messages, model_name, max_tok, temp, stream=True)

            async with self._session.post(endpoint, headers=headers, json=body) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    yield StreamEvent(type=StreamEventType.ERROR, content=f"HTTP {resp.status}: {text[:200]}")
                    self._factory.record_error(provider_name)
                    return

                total_text = []
                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    if line_str == "[DONE]":
                        break
                    try:
                        data = json.loads(line_str)
                        chunk_text = self._extract_chunk(provider_config, data)
                        if chunk_text:
                            total_text.append(chunk_text)
                            yield StreamEvent(type=StreamEventType.TEXT, content=chunk_text)

                        # Extract reasoning/thinking content (if available)
                        reasoning = self._extract_reasoning(data)
                        if reasoning:
                            yield StreamEvent(type=StreamEventType.THINKING, content=reasoning)

                        # Extract tool calls (if available)
                        tool_calls = self._extract_tool_calls(data)
                        for tc in tool_calls:
                            yield StreamEvent(
                                type=StreamEventType.TOOL_CALL,
                                tool_name=tc.get("name", ""),
                                tool_args=tc.get("arguments", {}),
                            )
                    except json.JSONDecodeError:
                        continue

                latency = (time.perf_counter() - start) * 1000
                tokens = _count_tokens("".join(total_text))
                self._token_budget_used += tokens
                self._factory.record_success(provider_name, latency, tokens)

                yield StreamEvent(type=StreamEventType.DONE)

        except (Exception, asyncio.TimeoutError) as e:
            self._factory.record_error(provider_name)
            yield StreamEvent(type=StreamEventType.ERROR, content=str(e))
        finally:
            await self._factory.release_slot(provider_name)

    # ── Chunk Extraction ──────────────────────────────────────────────

    @staticmethod
    def _extract_chunk(provider_config: ProviderConfig, data: dict) -> str:
        """Extract text chunk from streaming response data."""
        if provider_config.provider_type == "anthropic":
            if data.get("type") == "content_block_delta":
                return data.get("delta", {}).get("text", "")
        else:
            choices = data.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content", "")
        return ""

    @staticmethod
    def _extract_reasoning(data: dict) -> str:
        """Extract reasoning/thinking content if present (e.g., DeepSeek-R1, o1)."""
        choices = data.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            # Some providers put reasoning in a separate field
            return delta.get("reasoning_content", "") or delta.get("thinking", "")
        return ""

    @staticmethod
    def _extract_tool_calls(data: dict) -> list[dict]:
        """Extract tool calls from streaming data if present."""
        choices = data.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            tool_calls = delta.get("tool_calls", [])
            results = []
            for tc in tool_calls:
                func = tc.get("function", {})
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                results.append({"name": func.get("name", ""), "arguments": args})
            return results
        return []

    # ── Helpers ────────────────────────────────────────────────────────

    async def _backoff(self, attempt: int):
        delay = self.BASE_DELAY * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.5)
        await asyncio.sleep(delay + jitter)

    def _get_endpoint(self, provider: ProviderConfig) -> str:
        base = provider.base_url.rstrip("/")
        if provider.provider_type == "anthropic":
            return f"{base}/v1/messages"
        if "/chat/completions" in base:
            return base
        return f"{base}/chat/completions"

    def _build_headers(self, provider: ProviderConfig) -> dict:
        headers = {"content-type": "application/json"}
        if provider.provider_type == "anthropic":
            headers["x-api-key"] = provider.api_key
            headers["anthropic-version"] = "2023-06-01"
        elif provider.is_local and not provider.api_key:
            pass
        elif provider.api_key:
            headers["Authorization"] = f"Bearer {provider.api_key}"
        return headers

    def _build_body(
        self, provider: ProviderConfig, messages: list,
        model: str, max_tokens: int, temperature: float, stream: bool = False,
    ) -> dict:
        if provider.provider_type == "anthropic":
            system_msg = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            body = {
                "model": model, "messages": user_messages,
                "max_tokens": max_tokens, "temperature": temperature, "stream": stream,
            }
            if system_msg:
                body["system"] = system_msg
            return body
        return {
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature, "stream": stream,
        }

    def _parse_response(self, provider: ProviderConfig, response: dict) -> ToolResult:
        try:
            if provider.provider_type == "anthropic":
                content = response.get("content", [])
                text = "".join(b["text"] for b in content if b.get("type") == "text")
                return ToolResult.ok(data=text)
            choices = response.get("choices", [])
            if not choices:
                return ToolResult.fail("No choices in response")
            text = choices[0].get("message", {}).get("content", "")
            return ToolResult.ok(data=text)
        except (KeyError, IndexError, TypeError) as e:
            return ToolResult.fail(f"Parse error: {e}")

    # ── Convenience Methods ───────────────────────────────────────────

    async def chat(
        self, prompt: str, system: str = "",
        provider: Optional[str] = None, model: Optional[str] = None,
    ) -> ModelResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.send(messages, provider=provider, model=model)

    async def stream_chat(
        self, prompt: str, system: str = "",
        provider: Optional[str] = None, model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        async for chunk in self.stream(messages, provider=provider, model=model):
            yield chunk

    # ── Health & Diagnostics ──────────────────────────────────────────

    def get_health_report(self) -> str:
        return self._factory.get_health_report()

    def get_best_provider(self) -> str:
        return self._factory.get_best_provider_name()

    def get_factory(self) -> ProviderFactory:
        """Expose the ProviderFactory for advanced use."""
        return self._factory
