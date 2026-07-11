#!/usr/bin/env python3
"""Draft blinded Codex-proxy labels from public H001 audit evidence only.

This is a review aid, never independent human evidence.  The script consumes
only public_queue.jsonl and the public pair PLY files.  It does not read the
private source/rank/verifier sidecar or either human annotator sheet.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "h001_codex_blinded_proxy_draft_v1"
LABELS = ("physically_valid", "physically_invalid", "ambiguous", "unobservable")
CONFIDENCE = ("high", "medium", "low")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--public-queue",
        type=Path,
        default=Path("experiments/H001_geom_reliability/physical_validity_audit/frozen_v1/public_queue.jsonl"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/physical_validity_audit/codex_proxy_v1"),
    )
    return parser.parse_args()


def resolve(root: Path, path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_pair_ply(path: Path) -> tuple[np.ndarray, np.ndarray]:
    properties: list[str] = []
    vertex_count = 0
    in_vertex = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        if handle.readline().strip() != "ply":
            raise ValueError(f"invalid_ply:{path}")
        for line in handle:
            value = line.strip()
            if value.startswith("element vertex"):
                vertex_count = int(value.split()[-1])
                in_vertex = True
            elif value.startswith("element "):
                in_vertex = False
            elif value.startswith("property") and in_vertex:
                properties.append(value.split()[-1])
            elif value == "end_header":
                break
        indices = {name: properties.index(name) for name in ("x", "y", "z", "roleId")}
        subject: list[list[float]] = []
        obj: list[list[float]] = []
        for _ in range(vertex_count):
            values = handle.readline().split()
            if not values:
                break
            point = [float(values[indices[axis]]) for axis in ("x", "y", "z")]
            role = int(values[indices["roleId"]])
            if role == 1:
                subject.append(point)
            elif role == 2:
                obj.append(point)
    return np.asarray(subject, dtype=np.float64), np.asarray(obj, dtype=np.float64)


def robust_box(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return np.percentile(points, 5, axis=0), np.percentile(points, 95, axis=0)


def evidence_features(subject: np.ndarray, obj: np.ndarray) -> dict[str, float | int | bool | None]:
    if len(subject) < 20 or len(obj) < 20:
        return {"sufficient": False, "subject_points": len(subject), "object_points": len(obj)}
    sub_low, sub_high = robust_box(subject)
    obj_low, obj_high = robust_box(obj)
    sub_extent = np.maximum(sub_high - sub_low, 1e-6)
    obj_extent = np.maximum(obj_high - obj_low, 1e-6)
    scale = max(0.25, 0.5 * (float(np.linalg.norm(sub_extent)) + float(np.linalg.norm(obj_extent))))
    sub_center = np.median(subject, axis=0)
    obj_center = np.median(obj, axis=0)
    axis_gap = np.maximum(np.maximum(sub_low - obj_high, obj_low - sub_high), 0.0)
    bbox_gap = float(np.linalg.norm(axis_gap))
    intersection_xy = np.maximum(np.minimum(sub_high[:2], obj_high[:2]) - np.maximum(sub_low[:2], obj_low[:2]), 0.0)
    intersection_area = float(np.prod(intersection_xy))
    smaller_area = max(min(float(np.prod(sub_extent[:2])), float(np.prod(obj_extent[:2]))), 1e-8)
    xy_overlap = intersection_area / smaller_area
    expansion = 0.08 * scale
    local_mask = (
        (obj[:, 0] >= sub_low[0] - expansion)
        & (obj[:, 0] <= sub_high[0] + expansion)
        & (obj[:, 1] >= sub_low[1] - expansion)
        & (obj[:, 1] <= sub_high[1] + expansion)
    )
    local_obj = obj[local_mask]
    local_top = float(np.percentile(local_obj[:, 2], 95)) if len(local_obj) >= 10 else None
    subject_bottom = float(np.percentile(subject[:, 2], 5))
    local_vertical_gap = subject_bottom - local_top if local_top is not None else None
    return {
        "sufficient": True,
        "subject_points": len(subject),
        "object_points": len(obj),
        "scale_m": scale,
        "center_dz_m": float(sub_center[2] - obj_center[2]),
        "center_dz_norm": float((sub_center[2] - obj_center[2]) / scale),
        "bbox_gap_m": bbox_gap,
        "bbox_gap_norm": bbox_gap / scale,
        "xy_overlap_ratio": xy_overlap,
        "local_object_points": int(len(local_obj)),
        "local_vertical_gap_m": local_vertical_gap,
        "local_vertical_gap_norm": local_vertical_gap / scale if local_vertical_gap is not None else None,
        "subject_vertical_aspect": float(sub_extent[2] / max(sub_extent[0], sub_extent[1], 1e-6)),
    }


def result(label: str, confidence: str, reason: str, rule: str) -> dict[str, str]:
    return {"proxy_label": label, "proxy_confidence": confidence, "proxy_reason_code": reason, "proxy_rule": rule}


def classify(predicate: str, features: dict[str, Any]) -> dict[str, str]:
    if not features.get("sufficient"):
        return result("unobservable", "low", "occlusion_or_insufficient_evidence", "insufficient_public_pair_points")
    dz = float(features["center_dz_norm"])
    gap = float(features["bbox_gap_norm"])
    local_gap = features.get("local_vertical_gap_norm")
    overlap = float(features["xy_overlap_ratio"])
    aspect = float(features["subject_vertical_aspect"])

    if predicate in {"higher than", "lower than"}:
        aligned = dz if predicate == "higher than" else -dz
        if aligned >= 0.50:
            return result("physically_valid", "high", "vertical_order_consistent", "directed_center_height_margin_ge_0.50")
        if aligned >= 0.18:
            return result("physically_valid", "medium", "vertical_order_consistent", "directed_center_height_margin_ge_0.18")
        if aligned <= -0.40:
            return result("physically_invalid", "high", "vertical_order_inconsistent", "directed_center_height_reversed_le_-0.40")
        if aligned <= -0.12:
            return result("physically_invalid", "medium", "vertical_order_inconsistent", "directed_center_height_reversed_le_-0.12")
        return result("ambiguous", "low", "vertical_order_near_tie", "directed_center_height_margin_near_zero")

    if predicate == "close by":
        if gap <= 0.15:
            return result("physically_valid", "high", "distance_consistent", "robust_bbox_gap_norm_le_0.15")
        if gap <= 0.45:
            return result("physically_valid", "medium", "distance_consistent", "robust_bbox_gap_norm_le_0.45")
        if gap >= 1.00:
            return result("physically_invalid", "high", "distance_inconsistent", "robust_bbox_gap_norm_ge_1.00")
        if gap >= 0.65:
            return result("physically_invalid", "medium", "distance_inconsistent", "robust_bbox_gap_norm_ge_0.65")
        return result("ambiguous", "low", "distance_context_dependent", "robust_bbox_gap_norm_mid_band")

    local_contact = local_gap is not None and -0.18 <= float(local_gap) <= 0.22
    footprint_support = overlap >= 0.08 or int(features["local_object_points"]) >= 25
    support_plausible = local_contact and footprint_support and gap <= 0.35
    clearly_separated = (
        gap >= 0.55
        or (local_gap is not None and float(local_gap) >= 0.45)
        or (int(features["local_object_points"]) < 10 and gap >= 0.25)
    )

    if predicate == "supported by":
        if support_plausible:
            confidence = "high" if abs(float(local_gap)) <= 0.10 and overlap >= 0.20 else "medium"
            return result("physically_valid", confidence, "contact_or_support_consistent", "local_support_surface_contact")
        if clearly_separated:
            return result("physically_invalid", "high" if gap >= 0.90 else "medium", "contact_or_support_missing", "pair_or_vertical_separation")
        return result("ambiguous", "low", "support_configuration_uncertain", "contact_band_or_footprint_uncertain")

    if predicate == "standing on":
        if support_plausible and aspect >= 0.25:
            confidence = "high" if aspect >= 0.55 and abs(float(local_gap)) <= 0.10 else "medium"
            return result("physically_valid", confidence, "standing_support_consistent", "support_contact_plus_vertical_pose")
        if clearly_separated:
            return result("physically_invalid", "high" if gap >= 0.90 else "medium", "contact_or_support_missing", "standing_support_separated")
        if support_plausible and aspect < 0.14:
            return result("ambiguous", "low", "pose_subtype_uncertain", "support_contact_but_flat_subject")
        return result("ambiguous", "low", "support_configuration_uncertain", "standing_contact_or_pose_uncertain")

    if predicate == "lying on":
        if support_plausible and aspect <= 0.65:
            confidence = "high" if aspect <= 0.35 and abs(float(local_gap)) <= 0.10 else "medium"
            return result("physically_valid", confidence, "lying_support_consistent", "support_contact_plus_flat_pose")
        if clearly_separated:
            return result("physically_invalid", "high" if gap >= 0.90 else "medium", "contact_or_support_missing", "lying_support_separated")
        if support_plausible and aspect >= 1.20:
            return result("physically_invalid", "medium", "pose_subtype_inconsistent", "support_contact_but_vertical_subject")
        return result("ambiguous", "low", "pose_subtype_uncertain", "lying_contact_or_pose_uncertain")

    return result("unobservable", "low", "unsupported_predicate", "predicate_not_in_frozen_rubric")


def compact_features(features: dict[str, Any]) -> str:
    keys = (
        "center_dz_norm",
        "bbox_gap_norm",
        "xy_overlap_ratio",
        "local_vertical_gap_norm",
        "subject_vertical_aspect",
        "local_object_points",
    )
    values = []
    for key in keys:
        value = features.get(key)
        if isinstance(value, float):
            values.append(f"{key}={value:.4f}")
        else:
            values.append(f"{key}={value}")
    return ";".join(values)


def html_page(rows: list[dict[str, Any]]) -> str:
    safe_rows = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>H001 blinded proxy review</title>
<style>
body{{font-family:Arial,sans-serif;margin:18px;background:#f5f5f5;color:#222}} .warn{{background:#fff3cd;padding:12px;border:1px solid #d9b650}}
.toolbar{{position:sticky;top:0;background:#fff;padding:10px;border:1px solid #ccc;z-index:2}} .card{{background:#fff;margin:14px 0;padding:12px;border:1px solid #bbb}}
.evidence{{display:flex;gap:12px;flex-wrap:wrap}} .evidence img{{max-width:560px;max-height:430px;border:1px solid #aaa}} label{{margin-right:12px}} select,input,textarea{{margin:5px}}
.proxy{{padding:8px;background:#eef}} .small{{font-size:12px;color:#555}}
</style></head><body>
<h1>H001 Codex-blinded proxy review</h1>
<div class="warn"><b>Provenance:</b> These are Codex-proxy suggestions generated only from public relation text and public pair geometry. Reviewing/accepting them yields one human-confirmed, proxy-assisted audit—not two independent human annotations. Do not open the private sidecar while reviewing.</div>
<div class="toolbar">Filter <select id="filter"><option value="all">all</option><option>physically_valid</option><option>physically_invalid</option><option>ambiguous</option><option>unobservable</option></select>
<button onclick="acceptVisible()">Accept visible proxy labels</button><button onclick="exportCsv()">Export human_review_completed.csv</button><span id="progress"></span></div>
<div id="cards"></div>
<script>
const rows={safe_rows}; const labels={json.dumps(list(LABELS))}; const confidence={json.dumps(list(CONFIDENCE))};
const state=JSON.parse(localStorage.getItem('h001_proxy_review')||'{{}}');
function repoSrc(path){{return path?'../../../../'+path:''}}
function save(id,key,value){{state[id]=state[id]||{{}};state[id][key]=value;localStorage.setItem('h001_proxy_review',JSON.stringify(state));progress()}}
function esc(s){{return String(s??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]))}}
function opts(values,selected){{return '<option value=""></option>'+values.map(v=>`<option ${{v===selected?'selected':''}}>${{v}}</option>`).join('')}}
function render(){{const f=document.getElementById('filter').value;const box=document.getElementById('cards');box.innerHTML='';rows.filter(r=>f==='all'||r.proxy_label===f).forEach(r=>{{const s=state[r.audit_id]||{{}};const c=document.createElement('div');c.className='card';c.innerHTML=`<h3>${{esc(r.audit_id)}} · ${{esc(r.relation)}}</h3><div class="proxy"><b>Proxy:</b> ${{esc(r.proxy_label)}} / ${{esc(r.proxy_confidence)}} / ${{esc(r.proxy_reason_code)}}<br><span class="small">${{esc(r.proxy_rule)}} · ${{esc(r.visible_geometry_cues)}}</span></div><div class="evidence"><img src="${{repoSrc(r.geometry_projection_path)}}">${{r.rgb_pair_crop_path?`<img src="${{repoSrc(r.rgb_pair_crop_path)}}">`:''}}</div><div><label>Human final label <select onchange="save('${{r.audit_id}}','label',this.value)">${{opts(labels,s.label||'')}}</select></label><label>Confidence <select onchange="save('${{r.audit_id}}','confidence',this.value)">${{opts(confidence,s.confidence||'')}}</select></label><button onclick="save('${{r.audit_id}}','label','${{r.proxy_label}}');save('${{r.audit_id}}','confidence','${{r.proxy_confidence}}');render()">Accept proxy</button></div><textarea rows="2" cols="100" placeholder="human notes" onchange="save('${{r.audit_id}}','notes',this.value)">${{esc(s.notes||'')}}</textarea>`;box.appendChild(c)}});progress()}}
function acceptVisible(){{const f=document.getElementById('filter').value;rows.filter(r=>f==='all'||r.proxy_label===f).forEach(r=>{{state[r.audit_id]=state[r.audit_id]||{{}};state[r.audit_id].label=r.proxy_label;state[r.audit_id].confidence=r.proxy_confidence}});localStorage.setItem('h001_proxy_review',JSON.stringify(state));render()}}
function progress(){{const n=rows.filter(r=>state[r.audit_id]&&state[r.audit_id].label).length;document.getElementById('progress').textContent=` ${{n}}/${{rows.length}} human-final labels`}}
function q(v){{return '"'+String(v??'').replace(/"/g,'""')+'"'}}
function exportCsv(){{const h=['audit_id','relation','proxy_label','proxy_confidence','human_final_label','human_confidence','human_notes','reviewer_id','reviewed_at'];const lines=[h.join(',')];rows.forEach(r=>{{const s=state[r.audit_id]||{{}};lines.push([r.audit_id,r.relation,r.proxy_label,r.proxy_confidence,s.label||'',s.confidence||'',s.notes||'','',new Date().toISOString()].map(q).join(','))}});const blob=new Blob([lines.join('\n')+'\n'],{{type:'text/csv'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='human_review_completed.csv';a.click()}}
document.getElementById('filter').onchange=render;render();
</script></body></html>"""


def make_readme(manifest: dict[str, Any]) -> str:
    return f"""# Codex-Blinded Proxy Draft

Status: `{manifest['status']}`  
Rows: `{manifest['counts']['rows']}`

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
"""


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    queue_path = resolve(root, args.public_queue)
    out = resolve(root, args.out)
    public_rows = read_jsonl(queue_path)
    proxy_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for row in public_rows:
        ply_path = resolve(root, row["pair_ply_path"])
        try:
            subject, obj = load_pair_ply(ply_path)
            features = evidence_features(subject, obj)
            decision = classify(row["predicate_label"], features)
        except Exception as exc:
            features = {"sufficient": False, "error": type(exc).__name__}
            decision = result("unobservable", "low", "evidence_load_error", "public_pair_ply_load_failed")
            errors.append(f"{row['audit_id']}:{type(exc).__name__}")
        cues = compact_features(features)
        proxy_rows.append(
            {
                "audit_id": row["audit_id"],
                "relation": row["relation"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "rgb_pair_crop_path": row["rgb_pair_crop_path"],
                "geometry_projection_path": row["geometry_projection_path"],
                "pair_ply_path": row["pair_ply_path"],
                "physical_validity_label": decision["proxy_label"],
                "confidence": decision["proxy_confidence"],
                "primary_reason_code": decision["proxy_reason_code"],
                "evidence_sufficient": bool(features.get("sufficient")),
                "notes": f"codex_blinded_proxy:{decision['proxy_rule']};{cues}",
                "reviewer_id": "codex_blinded_proxy_v1",
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        review_rows.append(
            {
                "audit_id": row["audit_id"],
                "relation": row["relation"],
                "predicate_family": row["predicate_family"],
                "geometry_projection_path": row["geometry_projection_path"],
                "rgb_pair_crop_path": row["rgb_pair_crop_path"],
                "proxy_label": decision["proxy_label"],
                "proxy_confidence": decision["proxy_confidence"],
                "proxy_reason_code": decision["proxy_reason_code"],
                "proxy_rule": decision["proxy_rule"],
                "visible_geometry_cues": cues,
                "human_final_label": "",
                "human_confidence": "",
                "human_reason_code": "",
                "human_notes": "",
                "reviewer_id": "",
                "reviewed_at": "",
            }
        )
        feature_rows.append({"audit_id": row["audit_id"], **features})

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "codex_proxy_draft.csv", proxy_rows)
    write_csv(out / "user_review.csv", review_rows)
    write_csv(out / "visible_geometry_features.csv", feature_rows)
    (out / "review.html").write_text(html_page(review_rows), encoding="utf-8")
    counts_label = Counter(row["physical_validity_label"] for row in proxy_rows)
    counts_confidence = Counter(row["confidence"] for row in proxy_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "codex_blinded_proxy_ready_for_user_review" if not errors else "proxy_ready_with_load_errors",
        "counts": {
            "rows": len(proxy_rows),
            "by_label": dict(sorted(counts_label.items())),
            "by_confidence": dict(sorted(counts_confidence.items())),
            "load_errors": len(errors),
        },
        "errors": errors,
        "input_contract": {
            "public_queue": relpath(root, queue_path),
            "public_queue_sha256": sha256_file(queue_path),
            "allowed_inputs": ["public_queue relation/evidence paths", "public pair PLY coordinates and role colors"],
            "forbidden_inputs_not_read": [
                "private_sidecar.jsonl",
                "annotator_a.csv",
                "annotator_b.csv",
                "source identity",
                "semantic or geometry scores",
                "ranks",
                "verifier status",
                "sampling strata",
                "ground truth",
            ],
        },
        "rubric": {
            "relative_vertical": "directed robust center-height margin normalized by pair scale",
            "proximity": "robust pair-bounding-box gap normalized by pair scale",
            "support_contact": "local support-surface gap, footprint support, pair gap, and subject pose aspect",
            "thresholds_are_proxy_triage_only": True,
        },
        "provenance_boundary": {
            "independent_human_evidence": False,
            "human_confirmed": False,
            "allowed_description_after_user_review": "single human-confirmed proxy-assisted audit",
            "two_independent_human_audit": False,
            "paper_metric_promotion": False,
        },
        "outputs": [
            relpath(root, out / "codex_proxy_draft.csv"),
            relpath(root, out / "user_review.csv"),
            relpath(root, out / "visible_geometry_features.csv"),
            relpath(root, out / "review.html"),
            relpath(root, out / "README.md"),
        ],
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_proxy",
    }
    write_json(out / "manifest.json", manifest)
    (out / "README.md").write_text(make_readme(manifest), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], **manifest["counts"], "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
