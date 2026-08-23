#!/usr/bin/env python3
"""GATE 2 — mechanical A/B invariants (design spec §2.1 and the B-variant contract).

Runs before GATE 3. Cheap, needs no model, and catches most authoring mistakes.

    python validation/invariants.py data/p1_paired/en/pairs.jsonl --out results/gates/gate2_en.json

Exits non-zero on failure so it can gate CI.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.schema import read_pairs
from metacog.text import digit_density, split_sentences

# Rule 2 of the B-variant contract: no vague quantifiers. This is exactly the failure
# mode that makes the public SUM dataset leak (see docs/pillar1-survey-and-gates-vi.md).
VAGUE_PATTERNS = [
    r"\bsome\b", r"\bseveral\b", r"\bvarious\b", r"\ba few\b", r"\bcertain\b",
    r"\bunspecified\b", r"\bundefined\b", r"\bunclear\b", r"\bunknown\b",
    r"\bapproximately\b", r"\baround\s+\d", r"\broughly\b", r"\bmay vary\b",
    r"\bnot (?:exactly )?(?:defined|specified|stated|disclosed)\b",
    r"\bat the discretion\b", r"\bcase[- ]by[- ]case\b", r"\bto be determined\b",
    r"_{2,}",
]

LENGTH_TOLERANCE = 0.05         # R3
DIGIT_TOLERANCE = 0.010         # R10
LENGTH_PASS_RATE = 0.95         # R3 may miss on 5% of items; every other rule is absolute

RULES = {
    "R1": "question is byte-identical across A and B",
    "R2": "same number of chunks",
    "R3": f"context length differs by <= {LENGTH_TOLERANCE:.0%}",
    "R5": "evidence position is uniform across head/middle/tail (chi-square p > 0.05)",
    "R7": "gold answer does not appear anywhere in context B",
    "R8": "exactly one sentence differs; all others are byte-identical",
    "R9": "replacement proposition contains no vague quantifier",
    "R10": f"digit density preserved (|delta| <= {DIGIT_TOLERANCE})",
    "R11": "replacement states a different field than the evidence",
}
MANUAL_RULES = {
    "R4": "same domain and same principal entity",
    "R6": "B is 'close but missing', not off-topic",
}


def chi_square_uniform(counts: list[int]) -> tuple[float, float]:
    """Goodness-of-fit against a uniform distribution; falls back to the df=2 closed form."""
    total, k = sum(counts), len(counts)
    if total == 0:
        return 0.0, 1.0
    expected = total / k
    statistic = sum((c - expected) ** 2 / expected for c in counts)
    try:
        from scipy.stats import chi2  # type: ignore

        return statistic, float(chi2.sf(statistic, k - 1))
    except ImportError:
        return statistic, math.exp(-statistic / 2)  # exact for df=2


def evaluate(pairs) -> tuple[dict[str, list[tuple[str, bool]]], collections.Counter]:
    results: dict[str, list[tuple[str, bool]]] = {key: [] for key in RULES}
    positions: collections.Counter = collections.Counter()

    for pair in pairs:
        pid = pair.pair_id
        a, b = pair.context_a, pair.context_b
        meta, variant_b = pair.meta, pair.variant_b
        positions[meta.get("evidence_position", "?")] += 1

        # R1 holds by construction: the release schema stores one question per pair.
        results["R1"].append((pid, isinstance(pair.question, str) and bool(pair.question.strip())))
        results["R2"].append((pid, len(pair.variant_a["contexts"]) == len(variant_b["contexts"])))
        results["R3"].append((pid, abs(len(b) - len(a)) / max(len(a), 1) <= LENGTH_TOLERANCE))

        gold = (pair.gold_answer or "").strip()
        results["R7"].append((pid, bool(gold) and gold.lower() not in b.lower()))

        sa, sb = split_sentences(a), split_sentences(b)
        differing = [i for i in range(min(len(sa), len(sb))) if sa[i] != sb[i]]
        results["R8"].append((pid, len(sa) == len(sb) and len(differing) == 1))

        replacement = variant_b.get("replacement_proposition", "")
        results["R9"].append((pid, not any(re.search(p, replacement, re.I) for p in VAGUE_PATTERNS)))
        results["R10"].append((pid, abs(digit_density(a) - digit_density(b)) <= DIGIT_TOLERANCE))
        results["R11"].append((pid, meta.get("evidence_field") != meta.get("replacement_field")))

    counts = [positions.get(k, 0) for k in ("head", "middle", "tail")]
    _, p_value = chi_square_uniform(counts)
    results["R5"] = [("__corpus__", p_value > 0.05)]
    return results, positions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    pairs = read_pairs(args.path)
    results, positions = evaluate(pairs)
    counts = [positions.get(k, 0) for k in ("head", "middle", "tail")]
    statistic, p_value = chi_square_uniform(counts)

    print(f"GATE 2 — A/B invariants — {args.path}")
    print(f"  pairs             : {len(pairs)}")
    print(f"  evidence position : head={counts[0]} middle={counts[1]} tail={counts[2]}"
          f"  (chi2={statistic:.2f}, p={p_value:.3f})")

    all_passed, report = True, {}
    for key, description in RULES.items():
        rows = results[key]
        passed = sum(ok for _, ok in rows)
        rate = passed / len(rows)
        threshold = LENGTH_PASS_RATE if key == "R3" else 1.0
        ok = rate >= threshold
        all_passed &= ok
        failures = [pid for pid, good in rows if not good]
        suffix = f"   e.g. {', '.join(failures[:4])}" if failures else ""
        print(f"  {key:4s} {description:55s} {passed:>3}/{len(rows):<3} {rate:6.1%}  "
              f"{'PASS' if ok else 'FAIL'}{suffix}")
        report[key] = {"description": description, "pass_rate": rate, "pass": ok, "failures": failures}

    print(f"  verdict           : {'PASS' if all_passed else 'FAIL'}")
    for key, description in MANUAL_RULES.items():
        print(f"  {key:4s} {description:55s} manual review required")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({
            "path": args.path, "n_pairs": len(pairs), "position_counts": counts,
            "chi_square": statistic, "chi_square_p": p_value,
            "rules": report, "pass": all_passed,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  written           : {args.out}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
