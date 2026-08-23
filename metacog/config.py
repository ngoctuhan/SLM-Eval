"""Environment loading and the model registry.

Two jobs:

* read ``.env`` without a third-party dependency
* record, in one place, what each provider actually accepts

The registry exists because "OpenAI-compatible" is a claim, not a contract. DeepSeek V4
rejects some OpenAI parameters and requires one of its own, and discovering that inside
a 300-call run costs the run. Capability flags per model keep the quirk in the registry
instead of scattering provider branches through the adapter.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def load_dotenv(path: str | Path = ".env", override: bool = False) -> dict[str, str]:
    """Minimal ``.env`` reader: ``KEY=value`` per line, ``#`` comments, optional quotes.

    Real environment variables win by default, so a shell export can override the file
    without editing it.
    """
    loaded: dict[str, str] = {}
    file = Path(path)
    if not file.exists():
        return loaded
    for raw in file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value
        loaded[key] = value
    return loaded


@dataclass(frozen=True)
class ModelSpec:
    """One evaluable model, plus what its API will and will not accept."""

    alias: str                       # what we call it in results
    model: str                       # what the provider calls it
    base_url: str
    api_key_env: str
    supports_seed: bool = True
    supports_logprobs: bool = False
    # Provider-specific fields merged into the request body.
    extra_body: dict[str, Any] = field(default_factory=dict)
    # Cost in USD per million tokens, for the cost-per-correct figure in Pillar 3.
    usd_per_m_input: float | None = None
    usd_per_m_output: float | None = None
    notes: str = ""


DEEPSEEK_BASE = "https://api.deepseek.com/v1"

# Prices below are DeepSeek's PEAK rates (01:00-04:00 and 06:00-10:00 UTC). Off-peak is
# half. Using peak keeps the cost-per-correct figure an upper bound rather than a
# best case that depends on when the run happened.

# Thinking mode is ON by default on V4 and it silently ignores temperature, top_p and
# the penalty parameters. Design spec section 7.1 requires temperature=0 for tasks with
# a gold answer, so the pilot must disable thinking or the control is not in force.
# Thinking on/off is worth measuring later as its own variable: AbstentionBench reports
# that reasoning fine-tuning degrades abstention by 24 percent on average.
DEEPSEEK_NO_THINKING = {"thinking": {"type": "disabled"}}
DEEPSEEK_THINKING = {"thinking": {"type": "enabled"}, "reasoning_effort": "high"}

REGISTRY: dict[str, ModelSpec] = {
    "v4-flash": ModelSpec(
        alias="v4-flash",
        model="deepseek-v4-flash",
        base_url=DEEPSEEK_BASE,
        api_key_env="DEEPSEEK_API_KEY",
        supports_seed=False,       # not documented as supported; omit rather than risk a 400
        extra_body=dict(DEEPSEEK_NO_THINKING),
        usd_per_m_input=0.44, usd_per_m_output=1.32,
        notes="284B total / 13B active. The small model in the pair.",
    ),
    "v4-pro": ModelSpec(
        alias="v4-pro",
        model="deepseek-v4-pro",
        base_url=DEEPSEEK_BASE,
        api_key_env="DEEPSEEK_API_KEY",
        supports_seed=False,
        extra_body=dict(DEEPSEEK_NO_THINKING),
        usd_per_m_input=1.32, usd_per_m_output=3.96,
        notes="1.6T total / 49B active. The large model in the pair.",
    ),
    # Same two models with thinking left on, for the reasoning-mode comparison.
    "v4-flash-thinking": ModelSpec(
        alias="v4-flash-thinking", model="deepseek-v4-flash", base_url=DEEPSEEK_BASE,
        api_key_env="DEEPSEEK_API_KEY", supports_seed=False,
        extra_body=dict(DEEPSEEK_THINKING),
        usd_per_m_input=0.44, usd_per_m_output=1.32,
        notes="Thinking mode ignores temperature; runs are not deterministic.",
    ),
    "v4-pro-thinking": ModelSpec(
        alias="v4-pro-thinking", model="deepseek-v4-pro", base_url=DEEPSEEK_BASE,
        api_key_env="DEEPSEEK_API_KEY", supports_seed=False,
        extra_body=dict(DEEPSEEK_THINKING),
        usd_per_m_input=1.32, usd_per_m_output=3.96,
        notes="Thinking mode ignores temperature; runs are not deterministic.",
    ),
    # Local vLLM or llama.cpp: full OpenAI surface including logprobs, which Pillar 3
    # needs and no hosted API exposes.
    "local": ModelSpec(
        alias="local", model="local-model", base_url="http://localhost:8000/v1",
        api_key_env="LOCAL_API_KEY", supports_seed=True, supports_logprobs=True,
        notes="Self-hosted. Override the served name with --model-id.",
    ),
}


def resolve(alias: str) -> ModelSpec:
    if alias not in REGISTRY:
        raise SystemExit(
            f"unknown model '{alias}'. Known: {', '.join(sorted(REGISTRY))}")
    return REGISTRY[alias]


def require_key(spec: ModelSpec) -> str:
    key = os.environ.get(spec.api_key_env, "").strip()
    if not key:
        raise SystemExit(
            f"{spec.api_key_env} is not set.\n"
            f"  Put it in .env:   {spec.api_key_env}=sk-...\n"
            f"  or export it:     export {spec.api_key_env}=sk-...\n"
            f"  .env is gitignored; copy .env.example if you have not made one yet."
        )
    return key
