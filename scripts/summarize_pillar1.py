#!/usr/bin/env python3
"""Summarise a scored Pillar 1 run into one committed JSON per model.

    # write / update results/pillar1/en/<model>.json from raw runs
    python scripts/summarize_pillar1.py results/raw/p1_v4-flash_*.jsonl \
        results/raw/p1_v4-pro_*.jsonl

    # print a comparison table across every summarised model
    python scripts/summarize_pillar1.py --compare

``results/raw/`` is gitignored and large; the per-model summary here is the small,
comparable artifact that is committed. Scoring is redone from the raw outputs (never
from a stored label) so a future trained classifier (GATE 4) re-summarises without a
re-run. One file per model, keyed inside by ``<condition>/<prompt>`` so adding the
neutral condition or a new seed later extends the file rather than overwriting it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.report import load_run, run_cost, score_run
from metacog.metrics import bootstrap, compute
from metacog.scoring import BehaviourScorer

SUMMARY_ROOT = Path("results/pillar1")


def _lang_of(config: dict) -> str:
    """Language segment of the dataset path: data/p1_paired/<lang>/pairs.jsonl."""
    parts = Path(config.get("dataset", "")).parts
    return parts[parts.index("p1_paired") + 1] if "p1_paired" in parts else "en"


def summarise_run(path: Path, scorer: BehaviourScorer) -> tuple[str, str, dict] | None:
    """Score one raw run file and return (model, run_key, entry) for the summary."""
    config, calls = load_run(path)
    if not calls:
        return None
    results, tiers = score_run(calls, scorer)
    metrics = compute(results)
    tokens_in, tokens_out, cost = run_cost(config, calls)
    thinking = (config.get("extra_body") or {}).get("thinking", {}).get("type")

    das, cdas = bootstrap(results, "das"), bootstrap(results, "cdas")
    entry = {
        "run_id": config.get("run_id"),
        "source": str(path),
        "model_version": next((c.get("model_version") for c in calls), None),
        "condition": config.get("condition"),
        "prompt": config.get("prompt"),
        "seed": config.get("seed"),
        "temperature": config.get("temperature"),
        # The whole point of the no-thinking control (nguyên tắc 13); record its state so
        # a summary can never be misread as deterministic when thinking was on.
        "thinking": thinking or "default",
        "n_pairs": metrics.n,
        "tier_mix": {str(t): n for t, n in sorted(tiers.items())},
        "outcome_counts": {o.value: metrics.counts[o] for o in metrics.counts},
        "metrics": {k: round(v, 4) if isinstance(v, float) else v
                    for k, v in metrics.as_row().items()},
        "bootstrap95": {
            "das": [round(das.point, 4), round(das.low, 4), round(das.high, 4)],
            "cdas": [round(cdas.point, 4), round(cdas.low, 4), round(cdas.high, 4)],
        },
        "tokens": {"in": tokens_in, "out": tokens_out},
        "cost_usd": round(cost, 4) if cost is not None else None,
        # Warning in the artifact itself: tier 2 is the unvalidated lexical baseline
        # until GATE 4 confirms kappa >= 0.75, so any t2 labels make this provisional.
        "scorer_validated": False,
        "scored_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return config.get("model", path.stem), f"{entry['condition']}/{entry['prompt']}", entry


def write_summaries(paths: list[Path]) -> None:
    scorer = BehaviourScorer()
    for path in sorted(paths):
        summarised = summarise_run(path, scorer)
        if summarised is None:
            print(f"  skip (no calls): {path}")
            continue
        model, run_key, entry = summarised
        lang = _lang_of(load_run(path)[0])
        out = SUMMARY_ROOT / lang / f"{model}.json"
        out.parent.mkdir(parents=True, exist_ok=True)

        doc = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {
            "model": model, "pillar": 1, "lang": lang, "runs": {}
        }
        doc["runs"][run_key] = entry
        out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        m = entry["metrics"]
        print(f"  {model:<10} {run_key:<12} ACC {m['ACC_A']:.1%}  DAS {m['DAS']:.1%}  "
              f"cDAS {m['cDAS']:.1%}  -> {out}")


def compare(lang: str) -> int:
    """Print one row per (model, condition) across every summary file."""
    files = sorted((SUMMARY_ROOT / lang).glob("*.json"))
    if not files:
        print(f"no summaries under {SUMMARY_ROOT / lang} yet")
        return 1
    header = (f"{'model':<12}{'cond':<10}{'n':>5}{'ACC_A':>8}{'NAR':>8}{'DAS':>8}"
              f"{'BAR':>8}{'OCR':>8}{'HR':>8}{'cDAS':>8}  thinking")
    print(header)
    print("-" * len(header))
    provisional = False
    for file in files:
        doc = json.loads(file.read_text(encoding="utf-8"))
        for run_key, e in sorted(doc["runs"].items()):
            m = e["metrics"]
            if any(t != "1" for t in e["tier_mix"]):
                provisional = True
            print(f"{doc['model']:<12}{e['condition'] or '?':<10}{m['n']:>5}"
                  f"{m['ACC_A']:>7.1%}{m['NAR']:>8.1%}{m['DAS']:>8.1%}{m['BAR']:>8.1%}"
                  f"{m['OCR']:>8.1%}{m['HR']:>8.1%}{m['cDAS']:>8.1%}  {e['thinking']}")
    if provisional:
        print("\n* some labels came from the tier-2 lexical baseline (GATE 4 not yet "
              "passed): treat DAS/cDAS as provisional.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="*", help="raw run JSONL files to summarise")
    parser.add_argument("--compare", action="store_true",
                        help="print a comparison table instead of writing summaries")
    parser.add_argument("--lang", default="en", help="language for --compare")
    args = parser.parse_args()

    if args.compare:
        return compare(args.lang)
    if not args.runs:
        parser.error("give raw run files to summarise, or pass --compare")
    write_summaries([Path(p) for p in args.runs])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
