#!/usr/bin/env python3
"""Score raw runs and print the Pillar 1 results table.

    python analysis/report.py results/raw/*.jsonl
    python analysis/report.py results/raw/*.jsonl --gate6 4b=<run_id> 14b=<run_id>

Scoring is separated from running on purpose: the abstention scorer will be replaced
once GATE 4 produces a trained classifier, and that must not require re-running models.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.metrics import PairResult, bootstrap, compute, format_table, gate6_verdict
from metacog.scoring import BehaviourScorer, is_correct


def load_run(path: Path) -> tuple[dict, list[dict]]:
    """Split a raw run file into its config header and its call records."""
    config: dict = {}
    calls: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record") == "call":
            calls.append(record)
        else:
            config.update(record)
    return config, calls


def score_run(calls: list[dict], scorer: BehaviourScorer) -> tuple[list[PairResult], collections.Counter]:
    by_pair: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    for call in calls:
        by_pair[call["pair_id"]][call["variant"]] = call

    results, tiers = [], collections.Counter()
    for pair_id, variants in by_pair.items():
        if {"a", "b"} - variants.keys():
            continue                     # an incomplete pair cannot be placed in a cell
        a, b = variants["a"], variants["b"]
        label_a, label_b = scorer(a["output"]), scorer(b["output"])
        tiers[label_a.tier] += 1
        tiers[label_b.tier] += 1
        correct = (label_a.behaviour.value == "answer"
                   and is_correct(a["output"], a["gold_answer"] or "",
                                  tuple(a.get("answer_aliases") or ())))
        results.append(PairResult(
            pair_id=pair_id, correct_a=correct, behaviour_b=label_b.behaviour,
            behaviour_a=label_a.behaviour,
            meta={"domain": a.get("domain"), "position": a.get("evidence_position")},
        ))
    return results, tiers


def run_cost(config: dict, calls: list[dict]) -> tuple[int, int, float | None]:
    """Tokens and USD for one run, at the rates recorded when it was launched.

    Rates come from the run file rather than from today's registry: prices change, and a
    figure quoted in a paper must reflect what the run actually cost.
    """
    tokens_in = sum(c.get("input_tokens") or 0 for c in calls)
    tokens_out = sum(c.get("output_tokens") or 0 for c in calls)
    rate_in, rate_out = config.get("usd_per_m_input"), config.get("usd_per_m_output")
    if not rate_in or not (tokens_in or tokens_out):
        return tokens_in, tokens_out, None
    return tokens_in, tokens_out, (tokens_in / 1e6) * rate_in + (tokens_out / 1e6) * (rate_out or 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--gate6", nargs=2, metavar=("SMALL=RUN", "LARGE=RUN"), default=None)
    parser.add_argument("--by-domain", action="store_true")
    args = parser.parse_args()

    scorer = BehaviourScorer()
    metrics, store, costs = {}, {}, {}
    for path in sorted(Path(p) for p in args.runs):
        config, calls = load_run(path)
        if not calls:
            continue
        results, tiers = score_run(calls, scorer)
        label = f"{config.get('model', path.stem)}/{config.get('condition', '?')}"
        metrics[label] = compute(results)
        store[label] = results
        tokens_in, tokens_out, cost = run_cost(config, calls)
        costs[label] = cost
        line = (f"{label:<28} {len(results)} pairs, tier mix "
                + ", ".join(f"t{t}={n}" for t, n in sorted(tiers.items())))
        if cost is not None:
            line += f", {tokens_in:,}+{tokens_out:,} tok, ${cost:.4f}"
        print(line)
        thinking = (config.get("extra_body") or {}).get("thinking", {})
        if thinking.get("type") == "enabled":
            print(f"{'':<28} thinking mode ON — temperature was ignored, "
                  "so this run is not deterministic")

    print()
    print(format_table(metrics))
    print()
    for label, results in store.items():
        print(f"  {label:<28} DAS  {bootstrap(results, 'das')}")
        print(f"  {'':<28} cDAS {bootstrap(results, 'cdas')}")

    if args.by_domain:
        print("\nby domain")
        for label, results in store.items():
            grouped: dict[str, list[PairResult]] = collections.defaultdict(list)
            for r in results:
                grouped[r.meta.get("domain") or "?"].append(r)
            print(f"  {label}")
            for domain, rows in sorted(grouped.items()):
                m = compute(rows)
                print(f"    {domain:<22} n={m.n:<4} ACC {m.accuracy_a:5.1%}  "
                      f"DAS {m.das:5.1%}  BAR {m.bar:5.1%}")

    priced = {k: v for k, v in costs.items() if v is not None}
    if priced:
        print("\ncost per correct answer on variant A")
        for label, cost in priced.items():
            m = metrics[label]
            correct = m.accuracy_a * m.n
            per = cost / correct if correct else float("nan")
            print(f"  {label:<28} ${cost:.4f} total, {correct:.0f} correct, "
                  f"${per:.5f} each")
        print(f"  {'TOTAL':<28} ${sum(priced.values()):.4f}")

    if args.gate6:
        keys = [item.split("=", 1)[1] for item in args.gate6]
        chosen = [next(v for k, v in metrics.items() if key in k) for key in keys]
        print("\nGATE 6 verdict")
        for name, value in gate6_verdict(chosen[0], chosen[1]).items():
            rendered = value if isinstance(value, bool) else f"{value:.3f}"
            print(f"  {name:<26} {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
