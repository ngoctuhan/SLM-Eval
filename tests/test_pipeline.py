"""Runner and report: the plumbing must survive without a model server."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.report import load_run, score_run
from metacog.metrics import compute
from metacog.scoring import BehaviourScorer


def test_dry_run_produces_a_scorable_file(tmp_path):
    out = tmp_path / "run.jsonl"
    result = subprocess.run(
        [sys.executable, "runners/run_paired.py", "--dry-run", "--limit", "20",
         "--out", str(out)],
        capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr

    config, calls = load_run(out)
    assert config["record"] == "config"
    assert len(calls) == 40                      # two variants per pair
    assert {c["variant"] for c in calls} == {"a", "b"}
    assert all(c["model_version"] for c in calls)
    assert all(c["output"] is not None for c in calls)

    results, tiers = score_run(calls, BehaviourScorer())
    assert len(results) == 20
    assert sum(tiers.values()) == 40

    metrics = compute(results)
    assert metrics.n == 20
    # A dry run must exercise more than one cell, otherwise it would hide join and
    # aggregation bugs behind a degenerate table.
    assert sum(1 for count in metrics.counts.values() if count) >= 3


def test_incomplete_pairs_are_dropped_not_miscounted():
    calls = [{"pair_id": "p1", "variant": "a", "output": "60 days",
              "gold_answer": "60 days", "answer_aliases": []}]
    results, _ = score_run(calls, BehaviourScorer())
    assert results == []


def test_prompt_templates_all_have_both_placeholders():
    for path in sorted((ROOT / "prompts/p1").rglob("*.txt")):
        text = path.read_text(encoding="utf-8")
        assert "{context}" in text, path
        assert "{question}" in text, path


def test_explicit_prompts_name_the_refusal_string():
    from metacog.scoring import REFUSAL_STRING
    for path in sorted((ROOT / "prompts/p1/explicit").glob("*.txt")):
        assert REFUSAL_STRING in path.read_text(encoding="utf-8"), path
    for path in sorted((ROOT / "prompts/p1/neutral").glob("*.txt")):
        assert REFUSAL_STRING not in path.read_text(encoding="utf-8"), path
