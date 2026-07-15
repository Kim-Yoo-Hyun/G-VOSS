# RelCompat3D Non-Submission Analysis Manuscript

This workspace builds a review-only variant of the active AAAI manuscript.
It reuses the canonical submission sections from `paper/aaai/` and appends the
two-pass Codex blind proxy audit, complete 154-row visual adjudication, and
verifier--proxy construct comparison. The proxy analysis is intentionally
excluded from the submission PDF and must never be described as human
annotation or an independent physical-validity reference. Reviewers A, B, and
C confirmed all 488 completed labels without revision. Their completed sheets
live under
`experiments/H001_geom_reliability/physical_validity_audit/external_reviews_completed_v1/`,
and the validated reference is under `external_proxy_review_validation_v1/`.
This is reviewer-verified LLM annotation rather than blank first-pass human
annotation.

Build from this directory with the existing AAAI-27 image:

```bash
docker run --rm -e TEXINPUTS=../aaai: -v "$PWD/..:/work" -w /work/paper_nonsub \
  h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
cp main.pdf main_nonsub.pdf
```

Canonical output: `main_nonsub.pdf`.
