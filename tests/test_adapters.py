"""Provider quirks. "OpenAI-compatible" is a claim, not a contract."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from metacog.adapters import OpenAICompatible, build_payload_preview
from metacog.config import REGISTRY, load_dotenv, require_key, resolve


def payload(alias: str, **kwargs) -> dict:
    adapter = OpenAICompatible.from_spec(resolve(alias))
    return build_payload_preview(adapter, "PROMPT", **kwargs)


def test_deepseek_disables_thinking_by_default():
    """Thinking mode is ON by default on V4 and silently ignores temperature. The spec
    requires temperature=0 on tasks with a gold answer, so it must be switched off."""
    for alias in ("v4-flash", "v4-pro"):
        assert payload(alias)["thinking"] == {"type": "disabled"}


def test_thinking_variants_enable_it_explicitly():
    body = payload("v4-pro-thinking")
    assert body["thinking"] == {"type": "enabled"}
    assert body["reasoning_effort"] == "high"


def test_unsupported_parameters_are_never_sent():
    """DeepSeek is not documented as accepting seed or logprobs. Sending them risks a
    400 that would only surface partway through a 300-call run."""
    body = payload("v4-flash", seed=1, logprobs=True)
    assert "seed" not in body
    assert "logprobs" not in body


def test_local_gets_the_full_openai_surface():
    body = payload("local", seed=7, logprobs=True)
    assert body["seed"] == 7
    assert body["logprobs"] is True
    assert "thinking" not in body


def test_from_spec_override_replaces_rather_than_duplicates():
    """Regression: passing base_url as an override raised TypeError for multiple values."""
    adapter = OpenAICompatible.from_spec(resolve("v4-flash"),
                                         base_url="http://127.0.0.1:8899/v1")
    assert adapter.base_url == "http://127.0.0.1:8899/v1"
    assert adapter.model == "deepseek-v4-flash"


def test_from_spec_ignores_none_overrides():
    adapter = OpenAICompatible.from_spec(resolve("v4-pro"), base_url=None)
    assert adapter.base_url == resolve("v4-pro").base_url


def test_every_registry_entry_is_self_consistent():
    for alias, spec in REGISTRY.items():
        assert spec.alias == alias
        assert spec.base_url.endswith("/v1")
        assert spec.api_key_env.isupper()
        priced = spec.usd_per_m_input is not None
        assert priced == (spec.usd_per_m_output is not None), alias


def test_unknown_alias_fails_loudly():
    with pytest.raises(SystemExit):
        resolve("gpt-9")


def test_missing_key_explains_how_to_set_it():
    spec = resolve("v4-flash")
    saved = os.environ.pop(spec.api_key_env, None)
    try:
        with pytest.raises(SystemExit) as caught:
            require_key(spec)
        assert spec.api_key_env in str(caught.value)
        assert ".env" in str(caught.value)
    finally:
        if saved is not None:
            os.environ[spec.api_key_env] = saved


def test_dotenv_parses_comments_quotes_and_blanks(tmp_path):
    path = tmp_path / ".env"
    path.write_text('# comment\n\nA=1\nB="two"\nC=\'three\'\nBAD_LINE\n', encoding="utf-8")
    loaded = load_dotenv(path)
    assert loaded == {"A": "1", "B": "two", "C": "three"}


def test_real_environment_wins_over_dotenv(tmp_path):
    """A shell export must override the file, so a one-off run needs no file edit."""
    path = tmp_path / ".env"
    path.write_text("METACOG_TEST_KEY=from_file\n", encoding="utf-8")
    os.environ["METACOG_TEST_KEY"] = "from_shell"
    try:
        load_dotenv(path)
        assert os.environ["METACOG_TEST_KEY"] == "from_shell"
        load_dotenv(path, override=True)
        assert os.environ["METACOG_TEST_KEY"] == "from_file"
    finally:
        os.environ.pop("METACOG_TEST_KEY", None)
