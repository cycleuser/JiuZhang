"""Multi-provider API client for JiuZhang.

Supports Ollama, OpenAI, Anthropic, Alibaba CodingPlan, and any OpenAI-compatible API.
"""

import asyncio
import json
from typing import Any, Iterator, Optional

import requests

from jiuzhang.core.config import Config, ProviderConfig
from jiuzhang.core.errors import ModelError, ToolResult


class MultiProviderClient:
    """Unified client for multiple AI model providers."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._session = requests.Session()

    def _get_provider(self, provider_name: Optional[str] = None) -> ProviderConfig:
        return self.config.get_provider(provider_name)

    def _build_headers(self, provider: ProviderConfig) -> dict:
        if provider.provider_type == "anthropic":
            return {
                "x-api-key": provider.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        if provider.provider_type == "openai_compatible" and not provider.api_key:
            return {"content-type": "application/json"}
        if provider.is_local:
            return {"content-type": "application/json"}
        return {
            "Authorization": f"Bearer {provider.api_key}",
            "content-type": "application/json",
        }

    def _build_body(
        self,
        provider: ProviderConfig,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
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
                "model": model_name,
                "messages": user_messages,
                "max_tokens": max_tok,
                "temperature": temp,
                "stream": stream,
            }
            if system_msg:
                body["system"] = system_msg
            return body

        return {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tok,
            "temperature": temp,
            "stream": stream,
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
                text = ""
                for block in content:
                    if block.get("type") == "text":
                        text += block["text"]
                usage = response.get("usage", {})
                return ToolResult.ok(
                    data=text,
                    metadata={
                        "usage": usage,
                        "model": response.get("model", ""),
                    },
                )

            choices = response.get("choices", [])
            if not choices:
                return ToolResult.fail("No choices in response")

            message = choices[0].get("message", {})
            text = message.get("content", "")
            usage = response.get("usage", {})

            return ToolResult.ok(
                data=text,
                metadata={
                    "usage": usage,
                    "model": response.get("model", ""),
                },
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to parse response: {e}")

    def send_message(
        self,
        messages: list[dict],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ToolResult:
        provider_config = self._get_provider(provider)
        endpoint = self._get_endpoint(provider_config)
        headers = self._build_headers(provider_config)
        body = self._build_body(
            provider_config, messages, model, max_tokens, temperature
        )

        try:
            response = self._session.post(
                endpoint, headers=headers, json=body, timeout=120
            )
            response.raise_for_status()
            return self._parse_response(provider_config, response.json())
        except requests.RequestException as e:
            return ToolResult.fail(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            return ToolResult.fail(f"Invalid JSON response: {e}")

    def stream_message(
        self,
        messages: list[dict],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]:
        provider_config = self._get_provider(provider)
        endpoint = self._get_endpoint(provider_config)
        headers = self._build_headers(provider_config)
        body = self._build_body(
            provider_config, messages, model, max_tokens, temperature, stream=True
        )

        try:
            response = self._session.post(
                endpoint, headers=headers, json=body, timeout=120, stream=True
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
                            yield data.get("delta", {}).get("text", "")
                    else:
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            yield delta.get("content", "")
                except json.JSONDecodeError:
                    continue
        except requests.RequestException as e:
            raise ModelError(f"Stream request failed: {e}")

    def explain_concept(
        self,
        concept: str,
        level: str = "beginner",
        language: Optional[str] = None,
        provider: Optional[str] = None,
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
        self,
        topic: str,
        difficulty: str = "medium",
        count: int = 5,
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
                    f"{provider_config.base_url.rstrip('/v1')}/api/tags",
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return ToolResult.ok(data=models)
            except Exception as e:
                return ToolResult.fail(f"Failed to list Ollama models: {e}")

        return ToolResult.ok(data=[provider_config.default_model])
