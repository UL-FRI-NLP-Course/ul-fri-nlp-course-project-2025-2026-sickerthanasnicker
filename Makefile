PYTHON ?= python
REPORT_TEX := report/report.tex

.PHONY: help setup json-check compile source-monitor corpus retrieval offline-eval report verify clean-report clean-pyc

help:
	@printf '%s\n' \
		'Targets:' \
		'  setup          Install Python dependencies' \
		'  verify         Run JSON checks, Python compile check, retrieval, offline eval, and report build' \
		'  source-monitor Check official source availability' \
		'  corpus         Rebuild report/code/data/chunk.jsonl from official sources' \
		'  retrieval      Re-run retrieval metrics on the committed corpus' \
		'  offline-eval   Re-run deterministic offline answer/judge/charts pipeline' \
		'  report         Build report/.out/report.pdf' \
		'  clean-report   Remove LaTeX output directory' \
		'  clean-pyc      Remove Python bytecode caches'

setup:
	$(PYTHON) -m pip install -r requirements.txt

json-check:
	$(PYTHON) -m json.tool evaluation/config.json >/tmp/ul_fri_eval_config.json
	$(PYTHON) -m json.tool evaluation/optimizations/config.json >/tmp/ul_fri_optimization_config.json
	$(PYTHON) -m json.tool evaluation/optimizations/official_sources.json >/tmp/ul_fri_official_sources.json

compile:
	$(PYTHON) -m compileall -q evaluation report/code

source-monitor:
	$(PYTHON) evaluation/optimizations/monitor_official_sources.py

corpus:
	$(PYTHON) evaluation/optimizations/build_official_corpus.py \
		--output report/code/data/chunk.jsonl \
		--include-case-law \
		--max-case-law-chunks 30

retrieval:
	$(PYTHON) evaluation/retrieval_eval.py --quiet

offline-eval:
	$(PYTHON) evaluation/run_eval.py --provider offline
	$(PYTHON) evaluation/judge_eval.py --provider offline
	$(PYTHON) evaluation/visualize_results.py

report:
	mkdir -p report/.out
	cd report/.out && TEXINPUTS=..: pdflatex -interaction=nonstopmode -halt-on-error ../report.tex
	cd report/.out && BIBINPUTS=..: bibtex report
	cd report/.out && TEXINPUTS=..: pdflatex -interaction=nonstopmode -halt-on-error ../report.tex
	cd report/.out && TEXINPUTS=..: pdflatex -interaction=nonstopmode -halt-on-error ../report.tex

verify: json-check compile retrieval offline-eval report

clean-report:
	rm -rf report/.out

clean-pyc:
	find evaluation report/code -type d -name __pycache__ -prune -exec rm -rf {} +
