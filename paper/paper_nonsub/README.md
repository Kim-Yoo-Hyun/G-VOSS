# GeoCalib Non-Submission Analysis Manuscript

This workspace builds a review-only variant of the active AAAI manuscript.
It reuses the canonical submission sections from `paper/aaai/` and appends the
two-pass Codex blind proxy audit. The proxy analysis is intentionally excluded
from the submission PDF and must never be described as human annotation or an
independent physical-validity reference.

Build from this directory with the existing AAAI-27 image:

```bash
docker run --rm -e TEXINPUTS=../aaai: -v "$PWD/..:/work" -w /work/paper_nonsub \
  h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Canonical output: `main_nonsub.pdf`.
