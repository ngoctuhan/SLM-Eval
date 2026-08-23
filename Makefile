.PHONY: help setup build gate2 gate3 gates review dryrun check pilot report kappa test clean

help:
	@echo "setup   install dependencies into .venv"
	@echo "build   compile authored items into the release dataset"
	@echo "gates   run GATE 2 and GATE 3"
	@echo "review  generate the GATE 2 manual review sheet"
	@echo "dryrun  run the full pipeline with no server, to check plumbing"
	@echo "check   one live call per model, to verify keys and provider quirks"
	@echo "pilot   run both DeepSeek V4 models over the full dataset, then report"
	@echo "report  score raw runs and print the results table"
	@echo "test    run the test suite"
	@echo ""
	@echo "override the language with LANGCODE=<code> (LANG is a shell variable, do not use it)"

PY := .venv/bin/python
LANGCODE ?= en

setup:
	python3 -m venv .venv && $(PY) -m pip install -q -r requirements.txt

build:
	$(PY) scripts/build_pairs.py --lang $(LANGCODE)

gate2:
	$(PY) validation/invariants.py data/p1_paired/$(LANGCODE)/pairs.jsonl --out results/gates/gate2_$(LANGCODE).json

gate3:
	$(PY) validation/shortcut_audit.py data/p1_paired/$(LANGCODE)/pairs.jsonl --out results/gates/gate3_$(LANGCODE).json

review:
	$(PY) validation/review_sheet.py data/p1_paired/$(LANGCODE)/pairs.jsonl --out results/gates/gate2_manual_review_$(LANGCODE).md

dryrun:
	$(PY) runners/run_paired.py --dry-run --out results/raw/dryrun.jsonl
	$(PY) analysis/report.py results/raw/dryrun.jsonl

check:
	$(PY) runners/run_paired.py --model v4-flash --check
	$(PY) runners/run_paired.py --model v4-pro --check

# Both abstention conditions on both models: the neutral-vs-explicit gap is the
# "how much hand-holding does this model need" figure.
pilot:
	$(PY) runners/run_paired.py --model v4-flash --condition explicit --prompt v1
	$(PY) runners/run_paired.py --model v4-pro   --condition explicit --prompt v1
	$(PY) runners/run_paired.py --model v4-flash --condition neutral  --prompt v1
	$(PY) runners/run_paired.py --model v4-pro   --condition neutral  --prompt v1
	$(PY) analysis/report.py results/raw/p1_v4-*.jsonl --by-domain \
	    --gate6 small=v4-flash_explicit large=v4-pro_explicit

report:
	$(PY) analysis/report.py results/raw/*.jsonl --by-domain

kappa:
	$(PY) validation/kappa.py sample results/raw/*.jsonl --n 200 --out labels/round1

gates: build gate2 gate3

test:
	$(PY) -m pytest tests -q

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache
