# Qwen-VL Output JSONL Contract

Status: frozen contract, model runtime not started.

## File Shape

- Format: JSONL
- One line equals one directed object-pair response.
- A row may contain zero predictions if the model sees no supported relation.
- Rows must preserve `scan_id`, `subgraph_id`, `subject_id`, `object_id`, and `record_id`.

## Required Identity Fields

- `record_id`
- `scan_id`
- `subgraph_id`
- `split`
- `subject_id`
- `object_id`
- `predicate_family`

## Required Runtime Fields

- `baseline_name`: fixed to `qwen_vl_semantic_source`
- `baseline_run_id`: stable id for one adapter run
- `model_id`: Hugging Face model id
- `model_revision`: fixed revision or checkpoint hash; `main` is not acceptable for paper runs
- `prompt_version`: frozen prompt template id
- `input_record_sha256`: hash of exact input JSONL line
- `decoding`: temperature, top_p, max_new_tokens, seed, and backend settings
- `raw_response`: raw model text before parsing
- `parser_status`: parsed, parsed_with_warning, unparseable, refused, or runtime_error
- `warnings`: non-fatal parser or contract warnings

## Prediction List

Each `predictions` item has:

- `predicate`: parsed candidate relation
- `rank`: semantic rank, 1-indexed
- `semantic_score`: model confidence proxy in [0, 1], or null if unavailable
- `answer_is_visible`: whether visual evidence appears sufficient
- `rationale_short`: short audit-only rationale, not used for scoring

## Scoring Rule

Use `semantic_score` only as a semantic-source score. If the model does not return a parseable confidence, use a rank-derived fallback such as `1/rank` and add a warning. Do not use geometry scores, verifier labels, GT labels, or `p_geom_valid` as `semantic_score`.

## Downstream Compatibility

The output rows are converted into the same H001 prediction/evaluation path as other baselines: semantic-only ranking first, then external geometry join and `qwen_vl_geometry_reranked`. Geometry evidence must be joined outside the Qwen semantic-only adapter.
