#!/usr/bin/env python3
"""Run Pillar 1 over a paired-twin dataset and write raw model outputs.

    # exercise the whole pipeline with no server and no key
    python runners/run_paired.py --dry-run

    # a real run against an OpenAI-compatible endpoint
    python runners/run_paired.py --model qwen2.5-7b-instruct \
        --base-url http://localhost:8000/v1 --condition explicit --prompt v1 --seed 1

Writes one JSONL line per model call to results/raw/. Raw text is always kept, never
just the label: the error taxonomy planned for later depends on it, and re-running the
whole matrix to recover it is expensive.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.adapters import (Adapter, Completion, OpenAICompatible,
                               build_payload_preview)
from metacog.config import load_dotenv, require_key, resolve, REGISTRY
from metacog.schema import Pair, read_pairs


class DryRunAdapter:
    """Simulates a model so the pipeline can be exercised without a server.

    It answers variant A correctly at ``accuracy`` and abstains on variant B at
    ``abstention``, with an occasional hedge, which produces a non-degenerate outcome
    table. That matters: an adapter that refuses everything would put every pair in one
    cell and hide join, scoring and aggregation bugs.

    Deterministic given the seed. It has privileged access to the pair, so it is a
    plumbing fixture and nothing else — never a baseline.
    """

    name = "dry-run"

    def __init__(self, seed: int = 1, accuracy: float = 0.7, abstention: float = 0.6,
                 hedge: float = 0.05) -> None:
        self.rng = random.Random(seed)
        self.accuracy, self.abstention, self.hedge = accuracy, abstention, hedge
        self.pair: Pair | None = None
        self.variant: str = "a"

    def complete(self, prompt: str, **_) -> Completion:
        pair, roll = self.pair, self.rng.random()
        if self.variant == "a":
            if roll < self.hedge:
                text = "The document mentions this but may not state it precisely."
            elif roll < self.hedge + self.accuracy:
                text = f"{pair.gold_answer}."
            else:
                text = "NO INFORMATION"
        else:
            if roll < self.hedge:
                text = "It is unclear from the document."
            elif roll < self.hedge + self.abstention:
                text = "NO INFORMATION"
            else:
                text = "The document states 30 days."
        return Completion(text, "dry-run-v0", 0)


def load_prompt(condition: str, version: str) -> str:
    path = Path("prompts/p1") / condition / f"{version}.txt"
    if not path.exists():
        raise SystemExit(f"no prompt template at {path}")
    return path.read_text(encoding="utf-8")


def build_adapter(args) -> tuple[Adapter, object | None]:
    if args.dry_run:
        return DryRunAdapter(seed=args.seed), None
    spec = resolve(args.model)
    require_key(spec)
    overrides = {}
    if args.base_url:
        overrides["base_url"] = args.base_url
    adapter = OpenAICompatible.from_spec(spec, **overrides)
    if args.model_id:
        adapter.model = args.model_id
    return adapter, spec


def preflight(adapter, spec, template: str, pair: Pair, args) -> int:
    """Show the exact request body, send one call, and stop.

    A 300-call run that fails on call one because a provider rejected a parameter has
    wasted the run. This costs a single call to rule that out.
    """
    prompt = template.format(context=pair.context_a, question=pair.question)
    body = build_payload_preview(adapter, prompt, temperature=args.temperature,
                                 max_tokens=args.max_tokens, seed=args.seed,
                                 logprobs=args.logprobs)
    preview = dict(body, messages=f"<{len(prompt)} chars>")
    print(f"model    : {args.model} -> {adapter.model}")
    print(f"endpoint : {adapter.base_url}/chat/completions")
    print(f"body     : {json.dumps(preview)}")
    if spec is not None and spec.notes:
        print(f"note     : {spec.notes}")
    print("\nsending one call ...")
    completion = adapter.complete(prompt, temperature=args.temperature,
                                  max_tokens=args.max_tokens, seed=args.seed,
                                  logprobs=args.logprobs)
    print(f"  model_version : {completion.model_version}")
    print(f"  finish_reason : {completion.finish_reason}")
    print(f"  tokens        : {completion.input_tokens} in / {completion.output_tokens} out")
    print(f"  latency       : {completion.latency_ms} ms")
    if completion.reasoning:
        print(f"  reasoning     : {len(completion.reasoning)} chars returned "
              "(thinking mode is on; temperature is ignored)")
    print(f"  question      : {pair.question}")
    print(f"  gold          : {pair.gold_answer}")
    print(f"  output        : {completion.text!r}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default="data/p1_paired/en/pairs.jsonl")
    parser.add_argument("--model", default="dry-run",
                        help="registry alias: " + ", ".join(sorted(REGISTRY)))
    parser.add_argument("--model-id", default=None,
                        help="override the served model name (self-hosted)")
    parser.add_argument("--base-url", default=None, help="override the registry base URL")
    parser.add_argument("--check", action="store_true",
                        help="print the request body, make one live call, and stop")
    parser.add_argument("--condition", default="explicit", choices=["neutral", "explicit"])
    parser.add_argument("--prompt", default="v1")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--logprobs", action="store_true",
                        help="request token logprobs (self-hosted models only)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    load_dotenv()

    pairs = read_pairs(args.dataset)
    if args.limit:
        pairs = pairs[: args.limit]
    template = load_prompt(args.condition, args.prompt)
    adapter, spec = build_adapter(args)

    if args.check:
        return preflight(adapter, spec, template, pairs[0], args)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"p1_{args.model}_{args.condition}_{args.prompt}_s{args.seed}_{stamp}"
    out = Path(args.out or f"results/raw/{run_id}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "run_id": run_id, "dataset": args.dataset, "model": args.model,
        "model_id": getattr(adapter, "model", args.model),
        "base_url": getattr(adapter, "base_url", None),
        "condition": args.condition, "prompt": args.prompt,
        "temperature": args.temperature, "seed": args.seed,
        "max_tokens": args.max_tokens, "started_utc": stamp,
        "extra_body": getattr(adapter, "extra_body", {}),
        "usd_per_m_input": getattr(spec, "usd_per_m_input", None),
        "usd_per_m_output": getattr(spec, "usd_per_m_output", None),
    }

    written = 0
    tokens_in = tokens_out = 0
    with out.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"record": "config", **config}, ensure_ascii=False) + "\n")
        for index, pair in enumerate(pairs, 1):
            for variant in ("a", "b"):
                if isinstance(adapter, DryRunAdapter):
                    adapter.pair, adapter.variant = pair, variant
                context = pair.context_a if variant == "a" else pair.context_b
                prompt = template.format(context=context, question=pair.question)
                completion = adapter.complete(
                    prompt, temperature=args.temperature, max_tokens=args.max_tokens,
                    seed=args.seed, logprobs=args.logprobs,
                )
                handle.write(json.dumps({
                    "record": "call",
                    "run_id": run_id,
                    "pair_id": pair.pair_id,
                    "variant": variant,
                    "domain": pair.meta.get("domain"),
                    "evidence_position": pair.meta.get("evidence_position"),
                    "gold_answer": pair.gold_answer if variant == "a" else None,
                    "answer_aliases": pair.variant_a.get("answer_aliases", []) if variant == "a" else [],
                    "output": completion.text,
                    "model_version": completion.model_version,
                    "finish_reason": completion.finish_reason,
                    "mean_logprob": completion.mean_logprob,
                    "reasoning": completion.reasoning,
                    "input_tokens": completion.input_tokens,
                    "output_tokens": completion.output_tokens,
                    "latency_ms": completion.latency_ms,
                    "called_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                }, ensure_ascii=False) + "\n")
                written += 1
                tokens_in += completion.input_tokens
                tokens_out += completion.output_tokens
            if index % 25 == 0:
                print(f"  {index}/{len(pairs)} pairs", flush=True)

    print(f"{written} calls over {len(pairs)} pairs -> {out}")
    if tokens_in or tokens_out:
        print(f"  tokens: {tokens_in:,} in / {tokens_out:,} out")
        if spec is not None and spec.usd_per_m_input:
            cost = (tokens_in / 1e6) * spec.usd_per_m_input + \
                   (tokens_out / 1e6) * spec.usd_per_m_output
            print(f"  cost:   ${cost:.4f} at peak rates (half that off-peak)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
