#!/usr/bin/env python3
"""GATE 3 — shortcut audit (design spec §2.2). The single largest risk to Pillar 1.

The question this answers: can A be told apart from B using surface features alone —
without reading the question, without understanding anything?

If yes, a model can score well on the paired design by pattern-matching, and every
downstream metric measures the wrong thing.

Four layers:
  L1  TF-IDF (1-2 grams) + logistic regression over the context only   threshold AUC <= 0.60
  L2  length-only baseline                                             threshold AUC <= 0.55
  L3  top weighted tokens per class                                    eyeball for marker phrases
  L4  two annotators, 10 s per sample, question hidden (run offline)   accuracy in 0.45-0.60

Cross-validation MUST group by pair_id. Without it the A and B halves of one pair land
in both train and test, and the AUC is inflated to the point of meaninglessness.

    python validation/shortcut_audit.py data/p1_paired/en/pairs.jsonl --out results/gates/gate3_en.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.schema import read_pairs
from metacog.text import digit_density

TFIDF_AUC_MAX = 0.60
LENGTH_AUC_MAX = 0.55
TOP_TOKENS = 25


def audit(texts: list[str], labels: np.ndarray, groups: list[str], folds: int = 5) -> dict:
    n_groups = len(set(groups))
    folds = min(folds, max(2, n_groups // 2))

    pipeline = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
        LogisticRegression(max_iter=2000),
    )
    probs = cross_val_predict(pipeline, texts, labels, cv=GroupKFold(folds),
                              groups=groups, method="predict_proba")[:, 1]
    tfidf_auc = roc_auc_score(labels, probs)

    lengths = np.array([len(t) for t in texts]).reshape(-1, 1)
    length_probs = cross_val_predict(LogisticRegression(), lengths, labels,
                                     cv=GroupKFold(folds), groups=groups,
                                     method="predict_proba")[:, 1]
    length_auc = roc_auc_score(labels, length_probs)

    vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=2, sublinear_tf=True)
    classifier = LogisticRegression(max_iter=3000).fit(vectorizer.fit_transform(texts), labels)
    features = np.array(vectorizer.get_feature_names_out())
    weights = classifier.coef_[0]

    return {
        "n_pairs": n_groups,
        "folds": folds,
        "tfidf_auc": float(tfidf_auc),
        "length_only_auc": float(length_auc),
        "top_tokens_toward_b": features[np.argsort(-weights)[:TOP_TOKENS]].tolist(),
        "top_tokens_toward_a": features[np.argsort(weights)[:TOP_TOKENS]].tolist(),
        "mean_length_a": float(lengths[labels == 0].mean()),
        "mean_length_b": float(lengths[labels == 1].mean()),
        "digit_density_a": float(np.mean([digit_density(t) for t, y in zip(texts, labels) if y == 0])),
        "digit_density_b": float(np.mean([digit_density(t) for t, y in zip(texts, labels) if y == 1])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    pairs = read_pairs(args.path)
    texts, labels, groups = [], [], []
    for pair in pairs:
        texts += [pair.context_a, pair.context_b]
        labels += [0, 1]
        groups += [pair.pair_id] * 2

    if not texts:
        print(f"no pairs in {args.path}", file=sys.stderr)
        return 2

    report = audit(texts, np.array(labels), groups)
    tfidf_ok = report["tfidf_auc"] <= TFIDF_AUC_MAX
    length_ok = report["length_only_auc"] <= LENGTH_AUC_MAX
    report["pass"] = bool(tfidf_ok and length_ok)

    print(f"GATE 3 — shortcut audit — {args.path}")
    print(f"  pairs                : {report['n_pairs']}  ({report['folds']} folds, grouped by pair_id)")
    print(f"  L1 TF-IDF AUC        : {report['tfidf_auc']:.3f}   (threshold <= {TFIDF_AUC_MAX})  "
          f"{'PASS' if tfidf_ok else 'FAIL'}")
    print(f"  L2 length-only AUC   : {report['length_only_auc']:.3f}   (threshold <= {LENGTH_AUC_MAX})  "
          f"{'PASS' if length_ok else 'FAIL'}")
    print(f"     mean length       : A={report['mean_length_a']:.0f}  B={report['mean_length_b']:.0f} chars")
    print(f"     digit density     : A={report['digit_density_a']:.4f}  B={report['digit_density_b']:.4f}")
    print(f"  L3 tokens toward B   : {', '.join(report['top_tokens_toward_b'])}")
    print(f"     tokens toward A   : {', '.join(report['top_tokens_toward_a'])}")
    print(f"  verdict              : {'PASS' if report['pass'] else 'FAIL — rewrite the leaking pairs'}")
    print("  L4 offline           : 2 annotators, 10 s per sample, question hidden; accuracy must land in 0.45-0.60")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  written              : {args.out}")

    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
