import httpx
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AdvisoryResponse:
    provider: str
    model: str
    summary: str
    suggestions: list[str]
    confidence: float
    advisory: bool = True


class LLMProvider(ABC):
    @abstractmethod
    async def analyze(self, prompt: str) -> AdvisoryResponse:
        pass


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str, timeout: float):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def analyze(self, prompt: str) -> AdvisoryResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an iOS build failure analyst. Provide concise, actionable diagnostics."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1000,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)

    def _parse_response(self, content: str) -> AdvisoryResponse:
        return AdvisoryResponse(
            provider="openai-compatible",
            model=self.model,
            summary=content[:200] + "..." if len(content) > 200 else content,
            suggestions=[content],
            confidence=0.7,
        )


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str | None, model: str, timeout: float):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")
        self.model = model
        self.timeout = timeout

    async def analyze(self, prompt: str) -> AdvisoryResponse:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]
            return AdvisoryResponse(
                provider="anthropic",
                model=self.model,
                summary=content[:200] + "..." if len(content) > 200 else content,
                suggestions=[content],
                confidence=0.7,
            )


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str | None, model: str, timeout: float):
        self.api_key = api_key
        self.base_url = (base_url or "https://generativelanguage.googleapis.com").rstrip("/")
        self.model = model
        self.timeout = timeout

    async def analyze(self, prompt: str) -> AdvisoryResponse:
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return AdvisoryResponse(
                provider="gemini",
                model=self.model,
                summary=content[:200] + "..." if len(content) > 200 else content,
                suggestions=[content],
                confidence=0.7,
            )


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def analyze(self, prompt: str) -> AdvisoryResponse:
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("response", "")
            return AdvisoryResponse(
                provider="ollama",
                model=self.model,
                summary=content[:200] + "..." if len(content) > 200 else content,
                suggestions=[content],
                confidence=0.6,
            )


def get_llm_provider() -> Optional[LLMProvider]:
    if not settings.llm_api_key:
        return None

    provider = settings.llm_provider.lower()
    if provider == "openai-compatible":
        return OpenAICompatibleProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or "https://api.openai.com/v1",
            model=settings.llm_model,
            timeout=settings.llm_timeout,
        )
    elif provider == "anthropic":
        return AnthropicProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout=settings.llm_timeout,
        )
    elif provider == "gemini":
        return GeminiProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout=settings.llm_timeout,
        )
    elif provider == "ollama":
        return OllamaProvider(
            base_url=settings.llm_base_url or "http://localhost:11434",
            model=settings.llm_model,
            timeout=settings.llm_timeout,
        )
    return None


def build_failure_prompt(build_log: str, error_message: str) -> str:
    return f"""Analyze this iOS SwiftPM build failure and provide diagnostic suggestions.

Build Log (truncated):
```
{build_log[-3000:]}
```

Error: {error_message}

Provide:
1. Likely root cause
2. Specific fix suggestions
3. Whether this is a known toolchain issue

Keep response concise and actionable."""


async def get_build_failure_advisory(build_log: str, error_message: str) -> Optional[AdvisoryResponse]:
    provider = get_llm_provider()
    if not provider:
        return None

    try:
        prompt = build_failure_prompt(build_log, error_message)
        response = await provider.analyze(prompt)
        logger.info(f"LLM advisory generated via {provider.__class__.__name__}")
        return response
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API error: {e.response.status_code}")
        return AdvisoryResponse(
            provider=settings.llm_provider,
            model=settings.llm_model,
            summary=f"Provider error: {e.response.status_code}",
            suggestions=["Check LLM API credentials and endpoint configuration"],
            confidence=0.0,
        )
    except Exception as e:
        logger.error(f"LLM advisory failed: {type(e).__name__}")
        return AdvisoryResponse(
            provider=settings.llm_provider,
            model=settings.llm_model,
            summary=f"Advisory unavailable: {type(e).__name__}",
            suggestions=["LLM service temporarily unavailable"],
            confidence=0.0,
        )