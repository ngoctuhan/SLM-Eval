#!/usr/bin/env python3
"""GATE 2 — triage sheet for the two rules a machine cannot decide.

R4  variant B stays in the same domain and keeps the same principal entity
R6  variant B is "close but missing" — neither off-topic nor still answerable

Neither is decidable mechanically, but the *risk* of breaking one is measurable, so
this ranks the corpus and hands a reviewer the suspicious pairs instead of all of them.

Three signals, each gated to remove the noise that made a naive version useless:

    topic_fit       replacement vs the rest of the document.
                    LOW -> the replacement reads as off-topic filler, and the task
                    degenerates into topic detection (R6).

    question_pull   replacement vs the question, entity name removed.
                    HIGH -> the replacement sits so close to the question that a
                    reader could mistake its figure for the answer. Some of this is
                    wanted: a hard negative is the point. Too much of it makes the
                    item ambiguous rather than unanswerable, and only a human can
                    draw that line (R6).

    residual_answer best *other* sentence vs the question, counting only sentences
                    that carry a figure or a time expression.
                    HIGH -> some sentence other than the evidence may still answer
                    the question, so variant B is not truly unanswerable (R6).

The entity name is stripped from the question before scoring; every question ends with
"at <Company>?" and every sentence names the company, so leaving it in makes all three
signals measure the company name. The numeric gate on residual_answer matters for the
same reason: a sentence can restate the topic at length and still answer nothing,
because every question in this corpus asks for a quantity, a duration or a date.

Thresholds are percentile-based, so the review budget stays bounded as the corpus grows.

    python validation/review_sheet.py data/p1_paired/en/pairs.jsonl \
        --out results/gates/gate2_manual_review_en.md
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.schema import Pair, read_pairs
from metacog.text import split_sentences

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "of", "to",
    "in", "on", "at", "for", "from", "by", "with", "and", "or", "not", "no", "any",
    "as", "that", "this", "these", "those", "it", "its", "may", "must", "shall",
    "will", "which", "who", "what", "when", "how", "long", "much", "many", "does",
    "do", "did", "has", "have", "had", "than", "then", "there", "their", "they",
    "each", "every", "all", "before", "after", "within", "up", "per", "into", "out",
}
# A sentence can only answer a question in this corpus if it carries a quantity.
QUANTITY = re.compile(r"\d|\bone\b|\btwo\b|\bthree\b|\bfour\b|\bfive\b|\bsix\b|"
                      r"\bseven\b|\beight\b|\bnine\b|\bten\b", re.I)

PRIORITY_BUDGET = 30         # pairs to review first, ranked by composite risk
SIGNAL_PERCENTILE = 0.90     # a signal is "elevated" above its own 90th percentile
SAMPLE_SIZE = 20             # unflagged pairs to spot-check, for an honest denominator
STOP_RULE = 10               # stop reading the ranked list after this many clean in a row


def tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def coverage(source: set[str], target: set[str]) -> float:
    """Fraction of `target` covered by `source`."""
    return len(source & target) / len(target) if target else 0.0


def score(pair: Pair) -> dict:
    entity = tokens(pair.meta["company"])
    question = tokens(pair.question) - entity
    replacement = tokens(pair.variant_b["replacement_proposition"]) - entity

    sentences = split_sentences(pair.context_a)
    evidence_index = pair.meta["evidence_sentence_index"]
    others = [s for i, s in enumerate(sentences) if i != evidence_index]
    rest = set().union(*(tokens(s) for s in others)) - entity if others else set()

    residual, residual_sentence = 0.0, ""
    for sentence in others:
        if not QUANTITY.search(sentence):
            continue                          # cannot answer a quantity question
        value = coverage(tokens(sentence) - entity, question)
        if value > residual:
            residual, residual_sentence = value, sentence

    return {
        "pair": pair,
        "topic": coverage(rest, replacement),
        "pull": coverage(replacement, question),
        "residual": residual,
        "residual_sentence": residual_sentence,
        "flags": [],
    }


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[int(p * (len(ordered) - 1))]


def zscore(values: list[float]) -> list[float]:
    mean = sum(values) / len(values)
    spread = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5 or 1.0
    return [(v - mean) / spread for v in values]


def rank(rows: list[dict]) -> None:
    """Rank by composite risk and label which signal put each pair near the top.

    A hard per-signal cut flags 43 percent of the corpus, which is not triage. The
    signals are weak proxies, so the honest use is an ordering plus a review budget:
    work down the list and stop once it goes quiet (see STOP_RULE).
    """
    topic = zscore([r["topic"] for r in rows])
    pull = zscore([r["pull"] for r in rows])
    residual = zscore([r["residual"] for r in rows])
    cuts = {
        "R6 off-topic": percentile([r["topic"] for r in rows], 1 - SIGNAL_PERCENTILE),
        "R6 question-pull": percentile([r["pull"] for r in rows], SIGNAL_PERCENTILE),
        "R6 residual-answer": percentile([r["residual"] for r in rows], SIGNAL_PERCENTILE),
    }
    for row, t, p_, res in zip(rows, topic, pull, residual):
        row["risk"] = p_ + res - t
        if row["topic"] <= cuts["R6 off-topic"]:
            row["flags"].append("R6 off-topic")
        if row["pull"] >= cuts["R6 question-pull"]:
            row["flags"].append("R6 question-pull")
        if row["residual"] >= cuts["R6 residual-answer"]:
            row["flags"].append("R6 residual-answer")
    rows.sort(key=lambda r: -r["risk"])
    for position, row in enumerate(rows):
        row["priority"] = position < PRIORITY_BUDGET


QUESTIONS = {
    "R6 off-topic": "Is B still recognisably about this policy, or has it become filler "
                    "the model can dismiss on topic alone?",
    "R6 question-pull": "Is B a fair hard negative, or is it close enough that answering "
                        "with its figure would be reasonable? If reasonable, rewrite.",
    "R6 residual-answer": "Does the sentence below still answer the question once the "
                          "evidence is gone? If it does, B is not unanswerable.",
}


def render(rows: list[dict], sample: list[dict]) -> str:
    flagged = [r for r in rows if r["priority"]]
    out = [
        "# GATE 2 — manual review sheet",
        "",
        f"{len(rows)} pairs scored. Review the **{len(flagged)} priority pairs** in the "
        f"order given, then the **{len(sample)} control pairs**.",
        "",
        f"**Stop rule.** The priority list is ranked by risk, not thresholded. If you reach "
        f"{STOP_RULE} consecutive pairs needing no rewrite, stop and record where you "
        f"stopped. If the last pairs are still producing rewrites, extend past the budget.",
        "",
        "Two rules are under review. Neither can be checked by machine.",
        "",
        "| Rule | Question to answer on every pair |",
        "| --- | --- |",
        "| **R4** | Does variant B keep the same domain and the same principal entity? |",
        "| **R6** | Is variant B *close but missing* — not off-topic, and not still answerable? |",
        "",
        "Mark each row `ok` or `rewrite`. Rewrite in `data/authoring/en/<domain>.jsonl`, "
        "then run `make gates`: a rewrite can move the GATE 3 numbers, so both gates must "
        "be re-run and the new figures recorded.",
        "",
        "---",
        "",
        "## Priority pairs, highest risk first",
        "",
    ]
    for position, row in enumerate(flagged, 1):
        pair = row["pair"]
        out += [
            f"### {position}. {pair.pair_id}" + (f" · {', '.join(row['flags'])}" if row["flags"] else ""),
            "",
            f"`{pair.meta['domain']}` · **{pair.meta['company']}** · {pair.meta['doc_title']}  ",
            f"field `{pair.meta['evidence_field']}` -> `{pair.meta['replacement_field']}` · "
            f"topic-fit {row['topic']:.2f} · question-pull {row['pull']:.2f} · "
            f"residual {row['residual']:.2f}",
            "",
            f"**Q** {pair.question}",
            "",
            f"**A** *{pair.variant_b['removed_proposition']}* → `{pair.gold_answer}`",
            "",
            f"**B** *{pair.variant_b['replacement_proposition']}*",
            "",
        ]
        if "R6 residual-answer" in row["flags"] and row["residual_sentence"]:
            out += [f"**surviving sentence** *{row['residual_sentence']}*", ""]
        for flag in row["flags"]:
            out.append(f"> {QUESTIONS[flag]}")
        out += ["", "verdict: `___`", "", "---", ""]

    out += ["## Control pairs (below the priority cut)", "",
            "Drawn at random from outside the priority list. Reviewing them is what lets "
            "you report a defect rate rather than an impression: if the control sample is "
            "clean and the priority list is not, the ranking is working.", ""]
    for row in sample:
        pair = row["pair"]
        out += [
            f"### {pair.pair_id}",
            "",
            f"**Q** {pair.question}",
            "",
            f"**A** *{pair.variant_b['removed_proposition']}* → `{pair.gold_answer}`",
            "",
            f"**B** *{pair.variant_b['replacement_proposition']}*",
            "",
            "verdict: `___`",
            "",
        ]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--out", default=None)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    rows = [score(p) for p in read_pairs(args.path)]
    rank(rows)
    flagged = [r for r in rows if r["priority"]]
    clean = [r for r in rows if not r["priority"]]
    sample = random.Random(args.seed).sample(clean, min(SAMPLE_SIZE, len(clean)))

    print(f"GATE 2 — manual review triage — {args.path}")
    print(f"  pairs scored : {len(rows)}")
    print(f"  priority     : {len(flagged)}  ({len(flagged) / len(rows):.0%}), ranked by composite risk")
    counts: dict[str, int] = {}
    for row in flagged:
        for flag in row["flags"]:
            counts[flag] = counts.get(flag, 0) + 1
    for flag, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"    {flag:22s} {n}")
    print(f"  control sample: {len(sample)} unflagged pairs")
    print(f"  review load   : {len(flagged) + len(sample)} of {len(rows)} pairs")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(render(rows, sample), encoding="utf-8")
        print(f"  written       : {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
