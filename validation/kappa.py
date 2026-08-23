#!/usr/bin/env python3
"""GATE 4, tier 3 — agreement between the behaviour scorer and human labellers.

    # draw a blind labelling sheet from one or more raw runs
    python validation/kappa.py sample results/raw/*.jsonl --n 200 --out labels/round1

    # after two people have filled in labels/round1.annotatorA.tsv and .annotatorB.tsv
    python validation/kappa.py score labels/round1

The sheet is **blind**: it carries the model output and nothing else. Showing the
machine label first would anchor the annotator and inflate the very agreement the gate
is meant to measure.

Two figures come out and both matter:

* kappa between the two humans — if this is below 0.75 the label definitions are
  unclear, and fixing the scorer would be fixing the wrong thing
* kappa between the scorer and each human — this is the gate, threshold 0.75

Sampling is stratified over the machine's own predicted classes, because `hedge` is
rare and a uniform sample would barely contain any.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.scoring import KAPPA_THRESHOLD, Behaviour, BehaviourScorer, cohens_kappa, confusion

LABELS = [b.value for b in Behaviour]


def read_calls(paths: list[str]) -> list[dict]:
    calls = []
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("record") == "call":
                calls.append(json.loads(line))
    return calls


def cmd_sample(args) -> int:
    calls = read_calls(args.runs)
    if not calls:
        raise SystemExit("no call records found")

    scorer = BehaviourScorer()
    buckets: dict[str, list[dict]] = collections.defaultdict(list)
    for call in calls:
        buckets[scorer(call["output"]).behaviour.value].append(call)

    rng = random.Random(args.seed)
    per_class = max(1, args.n // len(buckets))
    chosen: list[dict] = []
    for label, bucket in sorted(buckets.items()):
        take = min(per_class, len(bucket))
        chosen += rng.sample(bucket, take)
        print(f"  {label:8s} available {len(bucket):5d}  sampled {take}")
    # top up from the largest bucket if a rare class was short
    if len(chosen) < args.n:
        remainder = [c for c in calls if c not in chosen]
        chosen += rng.sample(remainder, min(args.n - len(chosen), len(remainder)))
    rng.shuffle(chosen)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    key = [{"item": i, "pair_id": c["pair_id"], "variant": c["variant"],
            "machine": scorer(c["output"]).behaviour.value,
            "tier": scorer(c["output"]).tier, "output": c["output"]}
           for i, c in enumerate(chosen, 1)]
    out.with_suffix(".key.jsonl").write_text(
        "".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key), encoding="utf-8")

    for annotator in ("annotatorA", "annotatorB"):
        path = out.with_suffix(f".{annotator}.tsv")
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(["item", "label", "model_output"])
            for entry in key:
                writer.writerow([entry["item"], "",
                                 entry["output"].replace("\t", " ").replace("\n", " ")])
        print(f"  wrote {path}")

    print(f"\n  label each row with one of: {', '.join(LABELS)}")
    print("  abstain = declines outright | answer = commits to a value | "
          "hedge = neither")
    print(f"  key kept separately at {out.with_suffix('.key.jsonl')} — do not open it "
          "while labelling")
    return 0


def read_labels(path: Path) -> dict[int, str]:
    labels = {}
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            value = (row.get("label") or "").strip().lower()
            if value:
                labels[int(row["item"])] = value
    return labels


def cmd_score(args) -> int:
    base = Path(args.base)
    key = {json.loads(l)["item"]: json.loads(l)
           for l in base.with_suffix(".key.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    annotations = {name: read_labels(base.with_suffix(f".{name}.tsv"))
                   for name in ("annotatorA", "annotatorB")}

    for name, labels in annotations.items():
        unknown = {v for v in labels.values()} - set(LABELS)
        if unknown:
            raise SystemExit(f"{name}: unrecognised labels {sorted(unknown)}")

    shared = sorted(set(annotations["annotatorA"]) & set(annotations["annotatorB"]))
    if not shared:
        raise SystemExit("no items labelled by both annotators yet")

    a = [annotations["annotatorA"][i] for i in shared]
    b = [annotations["annotatorB"][i] for i in shared]
    machine = [key[i]["machine"] for i in shared]

    human_kappa = cohens_kappa(a, b)
    kappa_a = cohens_kappa(machine, a)
    kappa_b = cohens_kappa(machine, b)
    gate = min(kappa_a, kappa_b) >= KAPPA_THRESHOLD

    print(f"GATE 4 tier 3 — {base}")
    print(f"  items labelled by both : {len(shared)}")
    print(f"  annotator A vs B       : kappa {human_kappa:.3f}"
          + ("" if human_kappa >= KAPPA_THRESHOLD
             else "   <- below 0.75: the label definitions are unclear, fix those first"))
    print(f"  scorer vs annotator A  : kappa {kappa_a:.3f}")
    print(f"  scorer vs annotator B  : kappa {kappa_b:.3f}")
    print(f"  verdict                : {'PASS' if gate else 'FAIL'} "
          f"(threshold {KAPPA_THRESHOLD})")

    print("\n  confusion, scorer (rows) vs annotator A (columns)")
    matrix = confusion(machine, a)
    print("           " + "".join(f"{label:>10}" for label in LABELS))
    for row_label in LABELS:
        cells = "".join(f"{matrix.get((row_label, col), 0):>10}" for col in LABELS)
        print(f"  {row_label:<9}{cells}")

    disagreements = [i for i in shared if key[i]["machine"] != a[shared.index(i)]]
    if disagreements:
        print(f"\n  {len(disagreements)} disagreements against annotator A; first 5:")
        for item in disagreements[:5]:
            print(f"    item {item}: scorer={key[item]['machine']} "
                  f"human={annotations['annotatorA'][item]}")
            print(f"      {key[item]['output'][:110]!r}")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "n": len(shared), "human_kappa": human_kappa,
            "kappa_scorer_vs_a": kappa_a, "kappa_scorer_vs_b": kappa_b,
            "threshold": KAPPA_THRESHOLD, "pass": gate,
        }, indent=2), encoding="utf-8")
        print(f"\n  written: {args.out}")
    return 0 if gate else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sampler = sub.add_parser("sample", help="draw a blind labelling sheet")
    sampler.add_argument("runs", nargs="+")
    sampler.add_argument("--n", type=int, default=200)
    sampler.add_argument("--seed", type=int, default=13)
    sampler.add_argument("--out", default="labels/round1")
    sampler.set_defaults(func=cmd_sample)

    scorer = sub.add_parser("score", help="compute kappa from filled-in sheets")
    scorer.add_argument("base")
    scorer.add_argument("--out", default=None)
    scorer.set_defaults(func=cmd_score)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
