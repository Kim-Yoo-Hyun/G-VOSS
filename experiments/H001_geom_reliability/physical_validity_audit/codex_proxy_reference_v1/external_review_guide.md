# External Verification Guide

This is verification of a completed Codex proxy reference, not an independent
first-pass annotation task. Each reviewer receives one `external_reviewer_N.csv`
file and checks all 488 rows using the relation text, geometry projection,
optional RGB crop, and pair PLY.

For every row:

- use `verdict=confirm` and leave `corrected_label` empty when the proxy label is
  acceptable;
- use `verdict=revise`, enter one of `physically_valid`, `physically_invalid`,
  `ambiguous`, or `unobservable`, and provide a nonempty `comment` when changing
  the label;
- use one pseudonymous `reviewer_id` throughout the sheet and an ISO-8601
  `reviewed_at` timestamp on every row;
- do not edit, delete, add, or reorder immutable columns or rows.

The three sheets must use distinct reviewer IDs. After all sheets are returned,
run `external_proxy_review_validate`. A row is accepted only when at least two
reviewers agree; the validator writes the reviewer-verified proxy reference.
The resulting evidence must be described as reviewer-verified LLM annotation,
not as independent human first-pass annotation or human ground truth.
