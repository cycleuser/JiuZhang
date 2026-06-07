"""Multi-provider API client for JiuZhang — sync wrapper (backward-compatible).

This module wraps the modern AsyncModelProvider with a synchronous interface,
so existing code that uses MultiProviderClient continues to work unchanged.

For new code, prefer using AsyncModelProvider directly:
    from jiuzhang.core.async_provider import AsyncModelProvider
    provider = AsyncModelProvider(config)
    response = await provider.send(messages)
"""

import asyncio
import json
import threading
from typing import Any, Iterator, Optional

import requests

from jiuzhang.core.config import Config, ProviderConfig
from jiuzhang.core.errors import ModelError, ToolResult
from jiuzhang.core.provider_factory import ProviderFactory, ProviderHealth


class MultiProviderClient:
    """Unified client for multiple AI model providers.

    This class maintains the original synchronous API for backward compatibility.
    Internally uses AsyncModelProvider via a dedicated event loop when possible,
    falling back to direct sync requests for simple cases.

    Usage (same as before):
        client = MultiProviderClient(config)
        result = client.send_message(messages)
        for chunk in client.stream_message(messages):
            print(chunk)
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._session = requests.Session()
        self._factory = ProviderFactory(self.config)
        self._async_provider = None  # Lazy init
        self._loop = None
        self._thread = None

    def _get_async(self):
        """Lazy-init the async provider and event loop."""
        if self._async_provider is None:
            from jiuzhang.core.async_provider import AsyncModelProvider
            self._async_provider = AsyncModelProvider(self.config)
        return self._async_provider

    def _run_async(self, coro):
        """Run an async coroutine in a sync context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a new loop in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result(timeout=300)
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    # ── Provider Management ───────────────────────────────────────────

    def _get_provider(self, provider_name: Optional[str] = None) -> ProviderConfig:
        return self.config.get_provider(provider_name)

    def get_health_report(self) -> str:
        return self._factory.get_health_report()

    def get_best_provider(self) -> str:
        return self._factory.get_best_provider_name()

    # ── HTTP Helpers ──────────────────────────────────────────────────

    def _build_headers(self, provider: ProviderConfig) -> dict:
        if provider.provider_type == "anthropic":
            return {
                "x-api-key": provider.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        if provider.is_local and not provider.api_key:
            return {"content-type": "application/json"}
        return {
            "Authorization": f"Bearer {provider.api_key}",
            "content-type": "application/json",
        }

    def _build_body(
        self, provider: ProviderConfig, messages: list, model: Optional[str] = None,
        max_tokens: Optional[int] = None, temperature: Optional[float] = None,
        stream: bool = False,
    ) -> dict:
        model_name = model or self.config.active_model
        max_tok = max_tokens or self.config.max_tokens
        temp = temperature if temperature is not None else self.config.temperature

        if provider.provider_type == "anthropic":
            system_msg = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            body = {
                "model": model_name, "messages": user_messages,
                "max_tokens": max_tok, "temperature": temp, "stream": stream,
            }
            if system_msg:
                body["system"] = system_msg
            return body
        return {
            "model": model_name, "messages": messages,
            "max_tokens": max_tok, "temperature": temp, "stream": stream,
        }

    def _get_endpoint(self, provider: ProviderConfig) -> str:
        base = provider.base_url.rstrip("/")
        if provider.provider_type == "anthropic":
            return f"{base}/v1/messages"
        return f"{base}/chat/completions"

    def _parse_response(self, provider: ProviderConfig, response: dict) -> ToolResult:
        try:
            if provider.provider_type == "anthropic":
                content = response.get("content", [])
                text = "".join(
                    block["text"] for block in content if block.get("type") == "text"
                )
                usage = response.get("usage", {})
                return ToolResult.ok(data=text, metadata={"usage": usage, "model": response.get("model", "")})

            choices = response.get("choices", [])
            if not choices:
                return ToolResult.fail("No choices in response")
            message = choices[0].get("message", {})
            text = message.get("content", "")
            usage = response.get("usage", {})
            return ToolResult.ok(data=text, metadata={"usage": usage, "model": response.get("model", "")})
        except Exception as e:
            return ToolResult.fail(f"Failed to parse response: {e}")

    # ── Core Send Message ─────────────────────────────────────────────

    def send_message(
        self, messages: list, provider: Optional[str] = None,
        model: Optional[str] = None, max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ToolResult:
        """Send messages and get a complete response (synchronous).

        Uses AsyncModelProvider internally with fallback to direct requests.
        """
        # Try async path first (with provider health awareness and fallback)
        try:
            async_provider = self._get_async()
            response = self._run_async(
                async_provider.send(messages, provider, model, max_tokens, temperature)
            )
            return ToolResult.ok(
                data=response.text,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                    "tokens_used": response.tokens_used,
                    "latency_ms": response.latency_ms,
                },
            )
        except Exception:
            # Fall back to direct sync request
            pass

        # Direct sync fallback
        provider_config = self._get_provider(provider)
        endpoint = self._get_endpoint(provider_config)
        headers = self._build_headers(provider_config)
        body = self._build_body(provider_config, messages, model, max_tokens, temperature)

        try:
            response = self._session.post(endpoint, headers=headers, json=body, timeout=300)
            response.raise_for_status()
            result = self._parse_response(provider_config, response.json())
            self._factory.record_success(
                provider or self.config.active_provider, 0, 0
            )
            return result
        except requests.RequestException as e:
            self._factory.record_error(provider or self.config.active_provider)
            return ToolResult.fail(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            return ToolResult.fail(f"Invalid JSON response: {e}")

    # ── Streaming ─────────────────────────────────────────────────────

    def stream_message(
        self, messages: list, provider: Optional[str] = None,
        model: Optional[str] = None, max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]:
        """Stream a response chunk by chunk (synchronous iterator).

        Uses sync streaming with aiohttp via run_async when possible,
        falls back to requests-based streaming.
        """
        provider_config = self._get_provider(provider)
        endpoint = self._get_endpoint(provider_config)
        headers = self._build_headers(provider_config)
        body = self._build_body(provider_config, messages, model, max_tokens, temperature, stream=True)

        try:
            response = self._session.post(
                endpoint, headers=headers, json=body, timeout=300, stream=True,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    line_str = line_str[6:]
                if line_str == "[DONE]":
                    break
                try:
                    data = json.loads(line_str)
                    if provider_config.provider_type == "anthropic":
                        if data.get("type") == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    else:
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                except json.JSONDecodeError:
                    continue
        except requests.RequestException as e:
            raise ModelError(f"Stream request failed: {e}")

    # ── Convenience Methods ───────────────────────────────────────────

    def explain_concept(
        self, concept: str, level: str = "beginner",
        language: Optional[str] = None, provider: Optional[str] = None,
    ) -> ToolResult:
        lang = language or self.config.language
        prompt = f"""请用{"中文" if lang == "zh" else "English"}讲解数学概念：{concept}

目标水平：{level}
要求：
1. 从基础开始，循序渐进
2. 用具体的例子说明
3. 给出代码实现示例
4. 解释可视化方法

请详细讲解："""
        messages = [{"role": "user", "content": prompt}]
        return self.send_message(messages, provider=provider)

    def generate_exercise(
        self, topic: str, difficulty: str = "medium", count: int = 5,
        provider: Optional[str] = None,
    ) -> ToolResult:
        prompt = f"""请生成 {count} 道关于 {topic} 的练习题。

难度：{difficulty}
要求：
1. 每道题后附上答案
2. 难度循序渐进
3. 包含解题思路提示

练习题："""
        messages = [{"role": "user", "content": prompt}]
        return self.send_message(messages, provider=provider)

    def list_models(self, provider: Optional[str] = None) -> ToolResult:
        provider_config = self._get_provider(provider)
        if provider_config.is_local and "ollama" in provider_config.base_url:
            try:
                response = self._session.get(
                    f"{provider_config.base_url.rstrip('/v1')}/api/tags", timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return ToolResult.ok(data=models)
            except Exception as e:
                return ToolResult.fail(f"Failed to list Ollama models: {e}")
        return ToolResult.ok(data=[provider_config.default_model])
