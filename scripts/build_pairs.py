#!/usr/bin/env python3
"""Compile hand-authored items into the release-form paired-twin dataset.

    python scripts/build_pairs.py --lang en

Reads  data/authoring/<lang>/*.jsonl
Writes data/p1_paired/<lang>/pairs.jsonl
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.schema import compile_item, read_authored, write_pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", default="en")
    parser.add_argument("--authoring", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    authoring = Path(args.authoring or f"data/authoring/{args.lang}")
    out = Path(args.out or f"data/p1_paired/{args.lang}/pairs.jsonl")

    items = read_authored(authoring)
    if not items:
        print(f"no authored items found under {authoring}", file=sys.stderr)
        return 2

    ids = [item.id for item in items]
    duplicates = [i for i, n in collections.Counter(ids).items() if n > 1]
    if duplicates:
        print(f"duplicate ids: {', '.join(duplicates)}", file=sys.stderr)
        return 2

    written = write_pairs(out, (compile_item(item, args.lang) for item in items))

    by_domain = collections.Counter(item.domain for item in items)
    by_position = collections.Counter(item.position for item in items)
    print(f"built {written} pairs -> {out}")
    print(f"  domains   : {len(by_domain)}  " + ", ".join(f"{k}={v}" for k, v in sorted(by_domain.items())))
    print(f"  positions : " + ", ".join(f"{k}={by_position.get(k, 0)}" for k in ("head", "middle", "tail")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
