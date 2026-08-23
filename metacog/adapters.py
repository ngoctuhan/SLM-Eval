"""One interface for every model.

Design spec section 8, first technical principle: self-hosted and API models go through
a single OpenAI-compatible interface, and the calling code does not distinguish them.
vLLM, llama.cpp, OpenAI and DeepSeek all speak this protocol; anything that does not
needs a shim, not a second code path here.

Every call records the model version string the server reports and a timestamp, because
API models change under a fixed name and a run that cannot say which version produced
it is not reproducible.

No third-party HTTP dependency: the request is small and ``urllib`` is enough.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Completion:
    text: str
    model_version: str
    latency_ms: int
    finish_reason: str | None = None
    mean_logprob: float | None = None      # Pillar 3 confidence signal, self-host only
    # Returned separately by models in thinking mode. Kept apart from `text` so the
    # scorer never sees deliberation: a chain of thought that says "the document does
    # not state this" while the answer commits to a figure must score as an answer.
    reasoning: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


class Adapter(Protocol):
    name: str

    def complete(self, prompt: str, *, temperature: float = 0.0,
                 max_tokens: int = 256, seed: int | None = None,
                 logprobs: bool = False) -> Completion: ...


@dataclass
class OpenAICompatible:
    """Any server exposing POST /v1/chat/completions.

    "OpenAI-compatible" is a claim rather than a contract, so the differences live in
    fields here instead of provider branches in the request code: ``extra_body`` carries
    fields a provider requires, and the two ``supports_*`` flags stop us sending
    parameters a provider rejects.
    """

    name: str
    model: str
    base_url: str = "http://localhost:8000/v1"
    api_key_env: str = "OPENAI_API_KEY"
    system_prompt: str = "You are a careful assistant answering questions about documents."
    timeout: int = 120
    max_retries: int = 4
    extra_body: dict[str, Any] = field(default_factory=dict)
    supports_seed: bool = True
    supports_logprobs: bool = False

    @classmethod
    def from_spec(cls, spec, **overrides) -> "OpenAICompatible":
        fields = {
            "name": spec.alias, "model": spec.model, "base_url": spec.base_url,
            "api_key_env": spec.api_key_env, "extra_body": dict(spec.extra_body),
            "supports_seed": spec.supports_seed,
            "supports_logprobs": spec.supports_logprobs,
        }
        fields.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**fields)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        key = os.environ.get(self.api_key_env, "")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def complete(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256,
                 seed: int | None = None, logprobs: bool = False) -> Completion:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None and self.supports_seed:
            payload["seed"] = seed
        if logprobs and self.supports_logprobs:
            payload["logprobs"] = True
        payload.update(self.extra_body)

        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            started = time.monotonic()
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == self.max_retries - 1:
                    raise RuntimeError(
                        f"{self.name}: {self.max_retries} attempts failed: {exc}") from exc
                time.sleep(2 ** attempt)        # exponential backoff
        else:                                    # pragma: no cover
            raise RuntimeError(f"{self.name}: unreachable: {last_error}")

        choice = body["choices"][0]
        message = choice["message"]
        usage = body.get("usage") or {}
        return Completion(
            text=message.get("content") or "",
            model_version=body.get("model", self.model),
            latency_ms=int((time.monotonic() - started) * 1000),
            finish_reason=choice.get("finish_reason"),
            mean_logprob=_mean_logprob(choice),
            reasoning=message.get("reasoning_content") or None,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            raw={"id": body.get("id"), "usage": usage},
        )


def _mean_logprob(choice: dict[str, Any]) -> float | None:
    entries = (choice.get("logprobs") or {}).get("content") or []
    values = [e["logprob"] for e in entries if "logprob" in e]
    return sum(values) / len(values) if values else None


@dataclass
class ScriptedAdapter:
    """Deterministic stand-in used by the tests and by ``--dry-run``.

    Lets the whole pipeline be exercised — prompting, scoring, joining, metrics,
    reporting — with no server and no key, so plumbing bugs surface before GPU time
    is spent on them.
    """

    name: str = "scripted"
    responses: dict[str, str] = field(default_factory=dict)
    default: str = "NO INFORMATION"

    def complete(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256,
                 seed: int | None = None, logprobs: bool = False) -> Completion:
        for needle, response in self.responses.items():
            if needle in prompt:
                return Completion(response, f"{self.name}-v0", 0)
        return Completion(self.default, f"{self.name}-v0", 0)


def build_payload_preview(adapter: OpenAICompatible, prompt: str, **kwargs) -> dict[str, Any]:
    """The exact body that would be sent, without sending it.

    Lets ``--check`` verify provider quirks are wired correctly before spending a run
    on finding out they are not.
    """
    payload: dict[str, Any] = {
        "model": adapter.model,
        "messages": [{"role": "system", "content": adapter.system_prompt},
                     {"role": "user", "content": prompt}],
        "temperature": kwargs.get("temperature", 0.0),
        "max_tokens": kwargs.get("max_tokens", 256),
    }
    seed = kwargs.get("seed")
    if seed is not None and adapter.supports_seed:
        payload["seed"] = seed
    if kwargs.get("logprobs") and adapter.supports_logprobs:
        payload["logprobs"] = True
    payload.update(adapter.extra_body)
    return payload
