#!/usr/bin/env python3
"""Prepare the H001 Qwen-VL semantic-source adapter contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_qwen_vl_adapter_contract_v2"


MODEL_CANDIDATES: list[dict[str, Any]] = [
    {
        "name": "qwen3_vl_4b_instruct",
        "model_id": "Qwen/Qwen3-VL-4B-Instruct",
        "family": "Qwen3-VL",
        "size_b": 4,
        "role": "recommended_small_modern_main",
        "priority": 1,
        "rationale": (
            "Small dense Qwen3-VL model; best first target for a modern trend-aligned "
            "semantic-source adapter on a single 32GB GPU."
        ),
        "official_source": "https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct",
        "paper_or_report": "https://arxiv.org/abs/2511.21631",
    },
    {
        "name": "qwen2_5_vl_3b_instruct",
        "model_id": "Qwen/Qwen2.5-VL-3B-Instruct",
        "family": "Qwen2.5-VL",
        "size_b": 3,
        "role": "stable_small_fallback",
        "priority": 2,
        "rationale": (
            "Small Qwen2.5-VL model with mature official model card and Transformers examples; "
            "use if Qwen3-VL package/runtime friction blocks progress."
        ),
        "official_source": "https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct",
        "paper_or_report": "https://arxiv.org/abs/2502.13923",
    },
    {
        "name": "qwen3_vl_2b_instruct",
        "model_id": "Qwen/Qwen3-VL-2B-Instruct",
        "family": "Qwen3-VL",
        "size_b": 2,
        "role": "lowest_cost_parser_smoke",
        "priority": 3,
        "rationale": (
            "Lowest-cost Qwen3-VL candidate for prompt/parser/runtime smoke tests; not the "
            "preferred paper-quality model unless 4B/8B are infeasible."
        ),
        "official_source": "https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct",
        "paper_or_report": "https://arxiv.org/abs/2511.21631",
    },
    {
        "name": "qwen3_vl_8b_instruct",
        "model_id": "Qwen/Qwen3-VL-8B-Instruct",
        "family": "Qwen3-VL",
        "size_b": 8,
        "role": "quality_small_followup",
        "priority": 4,
        "rationale": (
            "Higher-quality small dense Qwen3-VL follow-up if 4B smoke passes and runtime "
            "budget allows."
        ),
        "official_source": "https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct",
        "paper_or_report": "https://arxiv.org/abs/2511.21631",
    },
    {
        "name": "qwen2_5_vl_7b_instruct",
        "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "family": "Qwen2.5-VL",
        "size_b": 7,
        "role": "stable_quality_followup",
        "priority": 5,
        "rationale": (
            "Stable Qwen2.5-VL quality follow-up; useful for checking whether observed gains "
            "depend on the Qwen3-VL family."
        ),
        "official_source": "https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct",
        "paper_or_report": "https://arxiv.org/abs/2502.13923",
    },
]


PREDICATE_FAMILY_MAP: dict[str, list[str]] = {
    "support_contact": [
        "supported by",
        "standing on",
        "lying on",
        "attached to",
        "hanging on",
        "part of",
    ],
    "proximity": [
        "close by",
        "next to",
        "near",
        "far from",
    ],
    "relative_vertical": [
        "higher than",
        "lower than",
        "above",
        "under",
    ],
}


INPUT_SCHEMA: dict[str, Any] = {
    "schema_version": "h001_qwen_vl_input_v2",
    "record_type": "one directed object-pair visual relation query",
    "jsonl_policy": "one JSON object per line",
    "required_fields": [
        "schema_version",
        "record_id",
        "scan_id",
        "subgraph_id",
        "split",
        "subject_id",
        "object_id",
        "subject_label",
        "object_label",
        "predicate_family",
        "candidate_predicates",
        "view_set_id",
        "crop_paths",
    ],
    "fields": {
        "record_id": "Stable unique id for one directed object-pair query.",
        "scan_id": "3RScan scan id.",
        "subgraph_id": "3DSSG subgraph/split id.",
        "split": "Dataset split for provenance, e.g. train, validation, or held_out.",
        "subject_id": "Subject object instance id.",
        "object_id": "Object object instance id.",
        "subject_label": "Subject object semantic label.",
        "object_label": "Object object semantic label.",
        "predicate_family": "One of support_contact, proximity, relative_vertical.",
        "candidate_predicates": "Allowed predicates for this family. Must match the frozen family map.",
        "view_set_id": "Stable id for selected multi-view crop set.",
        "crop_paths": "List of crop records, preferably pair crop plus subject/object highlights.",
        "crop_record": {
            "path": "Path to image crop relative to repo root or mounted dataset root.",
            "role": "pair, subject, object, context, or auxiliary.",
            "view_id": "Stable camera/view id.",
            "frame_id": "Optional source frame id.",
            "subject_bbox_xyxy": "Optional subject 2D bbox in crop coordinates.",
            "object_bbox_xyxy": "Optional object 2D bbox in crop coordinates.",
        },
        "geometry_summary": "Optional; excluded from semantic-only prompt and reserved for diagnostic prompts.",
    },
    "predicate_family_map": PREDICATE_FAMILY_MAP,
    "non_leakage_rules": [
        "Do not include ground-truth predicate labels in Qwen-VL prompts.",
        "Do not include H001 verifier decision, p_geom_valid, or violation label in semantic-only prompts.",
        "Use geometry_summary only for explicitly labeled diagnostic prompts, not for the main semantic-only condition.",
    ],
    "freeze_rules": [
        "Do not change record_id construction after held-out generation starts.",
        "Do not change crop selection policy after parser-smoke succeeds without creating a new prompt/input schema version.",
        "Do not include geometry_summary in semantic_only_v1 prompt payloads.",
    ],
}


OUTPUT_SCHEMA: dict[str, Any] = {
    "schema_version": "h001_qwen_vl_prediction_v2",
    "record_type": "one directed object-pair parsed Qwen-VL response",
    "jsonl_policy": "one JSON object per line; each line may contain zero or more parsed predicate candidates",
    "required_fields": [
        "schema_version",
        "record_id",
        "scan_id",
        "subgraph_id",
        "split",
        "subject_id",
        "object_id",
        "predicate_family",
        "baseline_name",
        "baseline_run_id",
        "model_id",
        "model_revision",
        "prompt_version",
        "input_record_sha256",
        "decoding",
        "raw_response",
        "parser_status",
        "predictions",
        "warnings",
    ],
    "fields": {
        "input_record_sha256": "SHA-256 hash of the exact input JSON record line.",
        "raw_response": "Raw model text before parser normalization.",
        "parser_status": "One of parser_status_values.",
        "predictions": "List sorted by semantic rank; empty list allowed when no relation is supported.",
        "warnings": "List of non-fatal contract or parser warnings.",
    },
    "prediction_fields": {
        "predicate": "Parsed predicate candidate.",
        "rank": "1-indexed semantic rank from the parsed model output.",
        "semantic_score": "Optional model self-confidence proxy in [0, 1]; null if unavailable.",
        "answer_is_visible": "Boolean parser field for whether relation evidence is visible.",
        "rationale_short": "Short raw rationale for auditing only; not used in ranking.",
    },
    "parser_status_values": ["parsed", "parsed_with_warning", "unparseable", "refused", "runtime_error"],
    "baseline_name": "qwen_vl_semantic_source",
    "compatible_metric_conditions": ["qwen_vl_semantic_only", "qwen_vl_geometry_reranked"],
    "score_policy": {
        "primary": "Use semantic_score only as a semantic ranking proxy when the model returns a parseable confidence.",
        "fallback": "If semantic_score is unavailable, use rank-derived score 1/rank and record a parser warning.",
        "not_allowed": "Do not use geometry scores, verifier labels, GT labels, or p_geom_valid as semantic_score.",
    },
}


INPUT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "h001_qwen_vl_input_v2.schema.json",
    "title": "H001 Qwen-VL input record",
    "type": "object",
    "additionalProperties": False,
    "required": INPUT_SCHEMA["required_fields"],
    "properties": {
        "schema_version": {"const": INPUT_SCHEMA["schema_version"]},
        "record_id": {"type": "string", "minLength": 1},
        "scan_id": {"type": "string", "minLength": 1},
        "subgraph_id": {"type": "string", "minLength": 1},
        "split": {"type": "string", "enum": ["train", "validation", "held_out", "pilot", "smoke"]},
        "subject_id": {"type": ["integer", "string"]},
        "object_id": {"type": ["integer", "string"]},
        "subject_label": {"type": "string", "minLength": 1},
        "object_label": {"type": "string", "minLength": 1},
        "predicate_family": {"type": "string", "enum": sorted(PREDICATE_FAMILY_MAP)},
        "candidate_predicates": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "uniqueItems": True,
        },
        "view_set_id": {"type": "string", "minLength": 1},
        "crop_paths": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "role", "view_id"],
                "properties": {
                    "path": {"type": "string", "minLength": 1},
                    "role": {"type": "string", "enum": ["pair", "subject", "object", "context", "auxiliary"]},
                    "view_id": {"type": "string", "minLength": 1},
                    "frame_id": {"type": ["string", "integer", "null"]},
                    "subject_bbox_xyxy": {
                        "type": ["array", "null"],
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "object_bbox_xyxy": {
                        "type": ["array", "null"],
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                },
            },
        },
        "geometry_summary": {"type": ["object", "null"]},
    },
}


OUTPUT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "h001_qwen_vl_prediction_v2.schema.json",
    "title": "H001 Qwen-VL output JSONL row",
    "type": "object",
    "additionalProperties": False,
    "required": OUTPUT_SCHEMA["required_fields"],
    "properties": {
        "schema_version": {"const": OUTPUT_SCHEMA["schema_version"]},
        "record_id": {"type": "string", "minLength": 1},
        "scan_id": {"type": "string", "minLength": 1},
        "subgraph_id": {"type": "string", "minLength": 1},
        "split": {"type": "string", "enum": ["train", "validation", "held_out", "pilot", "smoke"]},
        "subject_id": {"type": ["integer", "string"]},
        "object_id": {"type": ["integer", "string"]},
        "predicate_family": {"type": "string", "enum": sorted(PREDICATE_FAMILY_MAP)},
        "baseline_name": {"const": OUTPUT_SCHEMA["baseline_name"]},
        "baseline_run_id": {"type": "string", "minLength": 1},
        "model_id": {"type": "string", "minLength": 1},
        "model_revision": {"type": "string", "minLength": 1},
        "prompt_version": {"type": "string", "minLength": 1},
        "input_record_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "decoding": {
            "type": "object",
            "additionalProperties": True,
            "required": ["temperature", "top_p", "max_new_tokens", "seed"],
            "properties": {
                "temperature": {"type": "number"},
                "top_p": {"type": "number"},
                "max_new_tokens": {"type": "integer"},
                "seed": {"type": "integer"},
            },
        },
        "raw_response": {"type": "string"},
        "parser_status": {"type": "string", "enum": OUTPUT_SCHEMA["parser_status_values"]},
        "predictions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["predicate", "rank", "semantic_score", "answer_is_visible", "rationale_short"],
                "properties": {
                    "predicate": {"type": "string", "minLength": 1},
                    "rank": {"type": "integer", "minimum": 1},
                    "semantic_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                    "answer_is_visible": {"type": "boolean"},
                    "rationale_short": {"type": "string"},
                },
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
}


PROMPTS: dict[str, str] = {
    "semantic_only_v1": """You are given one or more image crops from the same indoor 3D scene.
The subject object is: {subject_label} (id {subject_id}).
The object object is: {object_label} (id {object_id}).
Pair crops may mark the subject with a red box and the object with a blue box. Use these boxes only to identify the target pair.

Use only the visual evidence and object labels. Do not assume hidden 3D geometry.
Choose relations only from this allowed list: {candidate_predicates}.

Return strict JSON with this schema:
{
  "answer_is_visible": true or false,
  "predictions": [
    {"predicate": "<allowed predicate>", "confidence": 0.0-1.0, "rationale_short": "<brief reason>"}
  ]
}
If no relation is visually supported, return an empty predictions list.""",
    "geometry_aware_diagnostic_v1": """Diagnostic-only prompt. You are given image crops and a frozen 3D geometry summary.
Subject: {subject_label} (id {subject_id}); Object: {object_label} (id {object_id}).
Allowed predicates: {candidate_predicates}.
Geometry summary: {geometry_summary}

Return strict JSON with predicted predicates and a short note about whether the geometry summary supports or contradicts the visual relation.
This prompt is not used for the main semantic-only condition.""",
}


PILOT_PLAN: list[dict[str, Any]] = [
    {
        "stage": "contract_only",
        "goal": "Freeze model candidates, input schema, output schema, prompt templates, parser status values, and metric compatibility.",
        "blocking_for_paper": False,
    },
    {
        "stage": "tiny_pilot_scope",
        "goal": "Freeze 20-50 non-held-out object-pair input records before model download or inference.",
        "blocking_for_paper": False,
    },
    {
        "stage": "cache_preflight",
        "goal": "Verify selected model id/revision can be downloaded into local_dataset/model_cache/huggingface with a fixed local-dir.",
        "blocking_for_paper": True,
    },
    {
        "stage": "parser_smoke",
        "goal": "Run 20-50 non-held-out object-pair queries with Qwen3-VL-2B or Qwen2.5-VL-3B to validate prompt and parser robustness.",
        "blocking_for_paper": False,
    },
    {
        "stage": "small_pilot",
        "goal": "Run 100-500 object-pair queries with Qwen3-VL-4B; require stable row counts and parser success before any held-out metrics.",
        "blocking_for_paper": True,
    },
    {
        "stage": "held_out_adapter_export",
        "goal": "Export identity-preserving prediction JSONL, join geometry, and evaluate qwen_vl_semantic_only vs qwen_vl_geometry_reranked.",
        "blocking_for_paper": True,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl"),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_prompt_templates() -> str:
    lines = [
        "# Qwen-VL Prompt Templates",
        "",
        "These prompts are contract templates. They are frozen before held-out metric inspection.",
        "",
    ]
    for name, prompt in PROMPTS.items():
        lines.extend([f"## `{name}`", "", "```text", prompt, "```", ""])
    return "\n".join(lines)


def render_output_contract() -> str:
    lines = [
        "# Qwen-VL Output JSONL Contract",
        "",
        "Status: frozen contract; model runtime status is tracked by `runtime_smoke/` and `full_source_plan/`.",
        "",
        "## File Shape",
        "",
        "- Format: JSONL",
        "- One line equals one directed object-pair response.",
        "- A row may contain zero predictions if the model sees no supported relation.",
        "- Rows must preserve `scan_id`, `subgraph_id`, `subject_id`, `object_id`, and `record_id`.",
        "",
        "## Required Identity Fields",
        "",
    ]
    for field in [
        "record_id",
        "scan_id",
        "subgraph_id",
        "split",
        "subject_id",
        "object_id",
        "predicate_family",
    ]:
        lines.append(f"- `{field}`")
    lines.extend(
        [
            "",
            "## Required Runtime Fields",
            "",
            "- `baseline_name`: fixed to `qwen_vl_semantic_source`",
            "- `baseline_run_id`: stable id for one adapter run",
            "- `model_id`: Hugging Face model id",
            "- `model_revision`: fixed revision or checkpoint hash; `main` is not acceptable for paper runs",
            "- `prompt_version`: frozen prompt template id",
            "- `input_record_sha256`: hash of exact input JSONL line",
            "- `decoding`: temperature, top_p, max_new_tokens, seed, and backend settings",
            "- `raw_response`: raw model text before parsing",
            "- `parser_status`: parsed, parsed_with_warning, unparseable, refused, or runtime_error",
            "- `warnings`: non-fatal parser or contract warnings",
            "",
            "## Prediction List",
            "",
            "Each `predictions` item has:",
            "",
            "- `predicate`: parsed candidate relation",
            "- `rank`: semantic rank, 1-indexed",
            "- `semantic_score`: model confidence proxy in [0, 1], or null if unavailable",
            "- `answer_is_visible`: whether visual evidence appears sufficient",
            "- `rationale_short`: short audit-only rationale, not used for scoring",
            "",
            "## Scoring Rule",
            "",
            "Use `semantic_score` only as a semantic-source score. If the model does not return a parseable confidence, use a rank-derived fallback such as `1/rank` and add a warning. Do not use geometry scores, verifier labels, GT labels, or `p_geom_valid` as `semantic_score`.",
            "",
            "## Downstream Compatibility",
            "",
            "The output rows are converted into the same H001 prediction/evaluation path as other baselines: semantic-only ranking first, then external geometry join and `qwen_vl_geometry_reranked`. Geometry evidence must be joined outside the Qwen semantic-only adapter.",
            "",
        ]
    )
    return "\n".join(lines)


def render_commands() -> str:
    return """# Qwen-VL Adapter Commands

Run from the repository root.

Generate the contract artifacts:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_adapter_contract'
```

Future Docker services should use fixed model/cache roots:

```text
HF_HOME=/workspace/local_dataset/model_cache/huggingface
QWEN_VL_MODEL_ID=Qwen/Qwen3-VL-4B-Instruct
QWEN_VL_LOCAL_DIR=/workspace/local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct
```

Long model downloads must run in `tmux` or another background process and write timestamped logs under `logs/`.

Before any model download or inference, validate the frozen input/output JSONL contract and parser skeleton:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_contract_validator'
```

Select and validate the non-held-out tiny pilot scope without model download or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_scope'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
```

Plan tiny-pilot crop rendering and model runtime lock without download or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_runtime_plan'
```

Render tiny-pilot pair crops without model download or inference, then revalidate:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_pair_crop_render'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
```
"""


def render_readme(payload: dict[str, Any]) -> str:
    recommended = next(item for item in payload["model_candidates"] if item["priority"] == 1)
    fallback = next(item for item in payload["model_candidates"] if item["priority"] == 2)
    low_cost = next(item for item in payload["model_candidates"] if item["role"] == "lowest_cost_parser_smoke")
    lines = [
        "# Qwen-VL Semantic-Source Adapter",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Role",
        "",
        "Qwen-VL is a modern open-vocabulary VLM semantic-source extension for H001.",
        "It is not a replacement for the Open3DSG reproduction anchor and is not an end-to-end 3DSSG training result.",
        "",
        "## Model Ladder",
        "",
        f"- recommended small modern main: `{recommended['model_id']}`",
        f"- stable small fallback: `{fallback['model_id']}`",
        f"- lowest-cost parser smoke: `{low_cost['model_id']}`",
        "- optional quality follow-ups: `Qwen/Qwen3-VL-8B-Instruct`, `Qwen/Qwen2.5-VL-7B-Instruct`",
        "",
        "## Contract Files",
        "",
        "- `adapter_contract.json`: model candidates, schemas, pilot plan, and claim boundary",
        "- `input_schema.json`: frozen input JSON Schema",
        "- `input_schema_example.json`: example input JSONL row",
        "- `output_schema.json`: frozen output JSONL row JSON Schema",
        "- `output_jsonl_contract.md`: human-readable output JSONL contract",
        "- `model_candidates.json`: candidate model ladder including 2B/3B/4B options",
        "- `prediction_schema_example.json`: example identity-preserving output row",
        "- `prompt_templates.md`: semantic-only and diagnostic prompt templates",
        "- `commands.qwen_vl.md`: Docker command entrypoint for this contract",
        "- `report.md`: human-readable summary",
        "- `validation/`: contract-only validator/parser skeleton outputs after running `qwen_vl_contract_validator`",
        "- `tiny_pilot/`: non-held-out 30-row pilot input scope and validator outputs",
        "- `runtime_plan/`: crop-rendering preflight and recommended model id/revision/local-dir",
        "- `crops/`: pair-crop rendering records/manifest/report; crop images stay under ignored `local_dataset/qwen_vl_crops/`",
        "",
        "## Next Gate",
        "",
        "Before any model download or inference, render and validate tiny-pilot pair crops, then run the input/output JSONL validator and parser skeleton against these frozen contracts.",
        "Docker cache/runtime smoke is a later optional gate after an explicit model choice; prefer `Qwen/Qwen3-VL-4B-Instruct` and fall back to `Qwen/Qwen2.5-VL-3B-Instruct` if Qwen3-VL runtime friction blocks progress.",
        "",
    ]
    return "\n".join(lines)


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Qwen-VL Adapter Contract Report",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Decision",
        "",
        "Use Qwen-VL as the third semantic source / modern VLM extension after recording the VL-SAT controlled anchor and Open3DSG reproduction anchor.",
        "Start with small models: `Qwen3-VL-4B-Instruct` as the recommended modern target, `Qwen2.5-VL-3B-Instruct` as stable fallback, and `Qwen3-VL-2B-Instruct` for lowest-cost parser smoke.",
        "",
        "## Claim Boundary",
        "",
        "- allowed: modern VLM semantic-source reliability with H001 geometry reranking",
        "- not allowed: end-to-end 3DSSG generation claim",
        "- not allowed: replacement of Open3DSG reproduction evidence",
        "- not allowed: replacement of the VL-SAT controlled anchor",
        "",
        "## Acceptance Gates",
        "",
        "- frozen `input_schema.json` and `output_schema.json` before model downloads or inference",
        "- contract-only validator/parser skeleton before model downloads or inference",
        "- non-held-out tiny pilot scope before model downloads or inference",
        "- fixed model id and revision/local-dir before held-out metrics",
        "- frozen prompt templates and parser",
        "- identity-preserving prediction JSONL",
        "- semantic-only prompt must not receive verifier labels or geometry scores",
        "- Docker-generated outputs only for paper-result promotion",
        "",
    ]
    return "\n".join(lines)


def prediction_example() -> dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA["schema_version"],
        "record_id": "scan001::subgraph_a::obj_3->obj_7::support_contact",
        "scan_id": "scan001",
        "subgraph_id": "subgraph_a",
        "split": "held_out",
        "subject_id": 3,
        "object_id": 7,
        "predicate_family": "support_contact",
        "baseline_name": "qwen_vl_semantic_source",
        "baseline_run_id": "qwen3_vl_4b_semantic_only_v1",
        "model_id": "Qwen/Qwen3-VL-4B-Instruct",
        "model_revision": "REQUIRED_FIXED_REVISION",
        "prompt_version": "semantic_only_v1",
        "input_record_sha256": "0" * 64,
        "decoding": {
            "temperature": 0.0,
            "top_p": 1.0,
            "max_new_tokens": 256,
            "seed": 42,
        },
        "raw_response": "{\"answer_is_visible\": true, \"predictions\": [{\"predicate\": \"supported by\", \"confidence\": 0.73, \"rationale_short\": \"subject appears on object\"}]}",
        "parser_status": "parsed",
        "predictions": [
            {
                "predicate": "supported by",
                "rank": 1,
                "semantic_score": 0.73,
                "answer_is_visible": True,
                "rationale_short": "subject appears on object",
            }
        ],
        "warnings": [],
    }


def input_example() -> dict[str, Any]:
    return {
        "schema_version": INPUT_SCHEMA["schema_version"],
        "record_id": "scan001::subgraph_a::obj_3->obj_7::support_contact",
        "scan_id": "scan001",
        "subgraph_id": "subgraph_a",
        "split": "held_out",
        "subject_id": 3,
        "object_id": 7,
        "subject_label": "chair",
        "object_label": "floor",
        "predicate_family": "support_contact",
        "candidate_predicates": PREDICATE_FAMILY_MAP["support_contact"],
        "view_set_id": "scan001::subgraph_a::obj_3->obj_7::top3",
        "crop_paths": [
            {
                "path": "local_dataset/qwen_vl_crops/scan001/subgraph_a/obj_3_obj_7/pair_view_000.png",
                "role": "pair",
                "view_id": "view_000",
                "frame_id": "frame-000000.color.jpg",
                "subject_bbox_xyxy": [12.0, 18.0, 124.0, 160.0],
                "object_bbox_xyxy": [0.0, 150.0, 224.0, 224.0],
            }
        ],
        "geometry_summary": None,
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "io_contract_frozen_model_runtime_not_started",
        "repo_root": str(repo_root),
        "out_dir": relpath(repo_root, out_dir),
        "verification_date": "2026-05-08",
        "model_candidates": MODEL_CANDIDATES,
        "recommended_first_model": "Qwen/Qwen3-VL-4B-Instruct",
        "stable_small_fallback": "Qwen/Qwen2.5-VL-3B-Instruct",
        "lowest_cost_smoke": "Qwen/Qwen3-VL-2B-Instruct",
        "input_schema": INPUT_SCHEMA,
        "input_json_schema": INPUT_JSON_SCHEMA,
        "output_schema": OUTPUT_SCHEMA,
        "output_json_schema": OUTPUT_JSON_SCHEMA,
        "prompt_versions": sorted(PROMPTS),
        "pilot_plan": PILOT_PLAN,
        "claim_boundary": {
            "allowed": "modern VLM semantic-source reliability extension",
            "not_allowed": [
                "Open3DSG reproduction replacement",
                "end-to-end 3DSSG training result",
                "baseline-agnostic final claim before measured cross-source evidence",
            ],
        },
    }

    write_json(out_dir / "adapter_contract.json", payload)
    write_json(out_dir / "input_schema.json", INPUT_JSON_SCHEMA)
    write_json(out_dir / "input_schema_example.json", input_example())
    write_json(out_dir / "output_schema.json", OUTPUT_JSON_SCHEMA)
    write_json(out_dir / "model_candidates.json", MODEL_CANDIDATES)
    write_json(out_dir / "prediction_schema_example.json", prediction_example())
    (out_dir / "output_jsonl_contract.md").write_text(render_output_contract(), encoding="utf-8")
    (out_dir / "prompt_templates.md").write_text(render_prompt_templates(), encoding="utf-8")
    (out_dir / "commands.qwen_vl.md").write_text(render_commands(), encoding="utf-8")
    (out_dir / "README.md").write_text(render_readme(payload), encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(payload), encoding="utf-8")
    write_json(out_dir / "status.json", {"status": payload["status"], "created_at": payload["created_at"]})

    print(json.dumps({"status": payload["status"], "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
