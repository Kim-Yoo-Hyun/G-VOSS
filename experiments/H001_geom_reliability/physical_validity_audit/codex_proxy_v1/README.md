# Codex-Blinded Proxy Draft

Status: `codex_blinded_proxy_ready_for_user_review`  
Rows: `488`

This folder is a review aid. The proxy read only `public_queue.jsonl` and the
public pair PLY files. It did not read source identity, semantic/geometry scores,
ranks, verifier outputs, sampling strata, GT, or the private sidecar.

Files:

- `codex_proxy_draft.csv`: filled proxy suggestions.
- `user_review.csv`: proxy fields plus blank human-final fields.
- `review.html`: local review UI with geometry/RGB evidence and CSV export.
- `manifest.json`: rubric thresholds, counts, and provenance boundary.

Open `review.html`, inspect the raw evidence, and enter the human-final label.
Accepting the proxy suggestions does not create an independent second human
annotator. The result must be described as a single human-confirmed,
proxy-assisted audit unless another human completes a separate blinded pass.
