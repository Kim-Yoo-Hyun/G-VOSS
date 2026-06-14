#!/usr/bin/env python3
"""Generate VL-SAT style CLIP multi_view features for selected scans."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT

DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_STAGED_ROOT = DEFAULT_DATASET_ROOT / "VLSAT_staged" / "CVPR2023-VLSAT"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_mini" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "layout" / "vlsat"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate per-instance origin_view_mean CLIP features for VL-SAT."
    )
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scan-id", action="append", default=None, help="Restrict generation to one or more scan ids.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--topk", type=int, default=10)
    parser.add_argument("--save-debug-images", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_scene_objects(relationships_path: Path) -> dict[str, dict[str, str]]:
    data = load_json(relationships_path)
    scene_objects: dict[str, dict[str, str]] = {}
    for entry in data.get("scans", []):
        scan_id = str(entry.get("scan"))
        scene_objects.setdefault(scan_id, {})
        scene_objects[scan_id].update({str(k): str(v) for k, v in entry.get("objects", {}).items()})
    return scene_objects


def read_intrinsic(info_path: Path) -> dict[str, Any]:
    lines = info_path.read_text(encoding="utf-8", errors="replace").splitlines()
    intrinsic = [float(x) for x in lines[7].strip().split(" ")[2:]]
    return {
        "width": int(lines[2].strip().split(" ")[-1]),
        "height": int(lines[3].strip().split(" ")[-1]),
        "intrinsic": intrinsic,
        "frames": int(lines[11].strip().split(" ")[-1]),
    }


def read_pose(path: Path) -> list[list[float]]:
    return [[float(x) for x in line.strip().split(" ")] for line in path.read_text(encoding="utf-8").splitlines()]


def dependency_imports() -> dict[str, Any]:
    missing: list[str] = []
    modules: dict[str, Any] = {}
    for name in ("clip", "torch", "trimesh", "numpy", "PIL"):
        try:
            if name == "PIL":
                import PIL.Image as pil_image  # type: ignore

                modules["Image"] = pil_image
            else:
                modules[name] = __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        raise RuntimeError(f"missing required modules: {', '.join(sorted(missing))}")
    return modules


def choose_device(torch: Any, requested: str) -> str:
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
        return "cuda"
    if requested == "cpu":
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def normalize(features: Any) -> Any:
    return features / features.norm(dim=-1, keepdim=True)


def encode_images(
    image_paths: list[Path],
    *,
    model: Any,
    preprocess: Any,
    torch: Any,
    image_mod: Any,
    device: str,
    batch_size: int,
) -> Any:
    batches = []
    rotate = getattr(image_mod, "Transpose", image_mod).ROTATE_270
    with torch.no_grad():
        for start in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[start : start + batch_size]
            images = [
                preprocess(image_mod.open(path).convert("RGB").transpose(rotate))
                for path in batch_paths
            ]
            image_input = torch.stack(images, dim=0).to(device)
            encoded = model.encode_image(image_input)
            batches.append(encoded.cpu())
    return normalize(torch.cat(batches, dim=0)).to(device)


def encode_one_image(
    image: Any,
    *,
    model: Any,
    preprocess: Any,
    torch: Any,
    image_mod: Any,
    device: str,
) -> Any:
    rotate = getattr(image_mod, "Transpose", image_mod).ROTATE_270
    with torch.no_grad():
        image_input = preprocess(image.convert("RGB").transpose(rotate)).unsqueeze(0).to(device)
        return model.encode_image(image_input).cpu().numpy()


def image_array(image: Any, np: Any) -> Any:
    return np.asarray(image.convert("RGB"))


def save_debug_image(path: Path, array: Any, image_mod: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image_mod.fromarray(array).save(path)


def ply_vertex_property(ply: Any, property_name: str) -> Any:
    raw = ply.metadata.get("ply_raw") or ply.metadata.get("_ply_raw")
    if raw is None:
        raise RuntimeError(f"PLY metadata does not contain raw vertex data for {property_name}")
    return raw["vertex"]["data"][property_name]


def generate_scan(
    scan_id: str,
    *,
    scan_root: Path,
    instance_names: dict[str, str],
    class_list: list[str],
    class_weight: Any,
    model: Any,
    preprocess: Any,
    torch: Any,
    np: Any,
    trimesh: Any,
    image_mod: Any,
    device: str,
    batch_size: int,
    base_topk: int,
    save_debug_images: bool,
    overwrite: bool,
) -> dict[str, Any]:
    scan_dir = scan_root / scan_id
    sequence_dir = scan_dir / "sequence"
    multi_view_dir = scan_dir / "multi_view"
    multi_view_dir.mkdir(parents=True, exist_ok=True)

    ply = trimesh.load(scan_dir / "labels.instances.annotated.v2.ply", process=False)
    points = np.asarray(ply.vertices)
    instances = np.asarray(ply_vertex_property(ply, "objectId"))

    info = read_intrinsic(sequence_dir / "_info.txt")
    intrinsic = np.asarray(info["intrinsic"], dtype=np.float64).reshape((4, 4))
    image_paths = [sequence_dir / f"frame-{idx:06d}.color.jpg" for idx in range(info["frames"])]
    pose_paths = [sequence_dir / f"frame-{idx:06d}.pose.txt" for idx in range(info["frames"])]
    missing_inputs = [str(path) for path in image_paths + pose_paths if not path.exists()]
    if missing_inputs:
        raise RuntimeError(f"{scan_id}: missing sequence files: {missing_inputs[:5]}")

    extrinsics = np.asarray([np.linalg.inv(np.asarray(read_pose(path), dtype=np.float64)) for path in pose_paths])
    image_features = encode_images(
        image_paths,
        model=model,
        preprocess=preprocess,
        torch=torch,
        image_mod=image_mod,
        device=device,
        batch_size=batch_size,
    )
    similarity = (image_features @ class_weight.T).softmax(dim=-1)

    instance_ids = sorted(instance_names.keys(), key=lambda x: int(x))
    name_count: dict[str, int] = {}
    for instance_id in instance_ids:
        name_count[instance_names[instance_id]] = name_count.get(instance_names[instance_id], 0) + 1
    max_num = max(name_count.values()) if name_count else 1
    topk = min(
        30,
        max(base_topk, max_num * int(math.ceil(image_features.shape[0] / max(len(instance_ids), 1)))),
        max(1, int(image_features.shape[0] / 10)),
    )

    quality_counts: dict[str, int] = {}
    generated = 0
    skipped_existing = 0
    no_points = 0
    fin_all = (scan_dir / "multi_view_quality.txt").open("a", encoding="utf-8")
    try:
        for instance_id in instance_ids:
            instance_name = instance_names[instance_id]
            origin_out = multi_view_dir / f"instance_{instance_id}_class_{instance_name}_origin_view_mean.npy"
            crop_out = multi_view_dir / f"instance_{instance_id}_class_{instance_name}_croped_view_mean.npy"
            if origin_out.exists() and crop_out.exists() and not overwrite:
                skipped_existing += 1
                continue
            if instance_name not in class_list:
                raise RuntimeError(f"{scan_id}: class not found in classes.txt: {instance_name}")

            points_i = points[(instances == int(instance_id)).flatten()]
            if points_i.shape[0] == 0:
                no_points += 1
                continue
            points_h = np.concatenate((points_i, np.ones((points_i.shape[0], 1))), axis=-1)
            world_to_camera = extrinsics @ points_h.T
            camera_to_image = intrinsic[:3, :] @ world_to_camera
            camera_to_image = camera_to_image.transpose(0, 2, 1)
            camera_to_image = camera_to_image[..., :2] / camera_to_image[..., 2:]
            in_image = (
                (camera_to_image[..., 0] < info["width"])
                & (camera_to_image[..., 0] > 0)
                & (camera_to_image[..., 1] < info["height"])
                & (camera_to_image[..., 1] > 0)
            )

            class_idx = class_list.index(instance_name)
            topk_by_clip = (-similarity[:, class_idx]).argsort()[:topk].detach().cpu().numpy().tolist()
            crop_feats = []
            origin_feats = []
            quality = None
            view_idx = 0

            def add_view(frame_idx: int, quality_label: str, crop_array: Any | None = None) -> None:
                nonlocal view_idx
                image = image_mod.open(image_paths[frame_idx]).convert("RGB")
                image_np = image_array(image, np)
                if crop_array is None:
                    crop_array = image_np
                if save_debug_images:
                    save_debug_image(
                        multi_view_dir
                        / f"instance_{instance_id}_class_{instance_name}_croped_view{view_idx}_{quality_label}.jpg",
                        crop_array,
                        image_mod,
                    )
                    save_debug_image(
                        multi_view_dir
                        / f"instance_{instance_id}_class_{instance_name}_view{view_idx}_{frame_idx}_{quality_label}.jpg",
                        image_np,
                        image_mod,
                    )
                crop_feats.append(
                    encode_one_image(
                        image_mod.fromarray(crop_array),
                        model=model,
                        preprocess=preprocess,
                        torch=torch,
                        image_mod=image_mod,
                        device=device,
                    )
                )
                origin_feats.append(
                    encode_one_image(
                        image,
                        model=model,
                        preprocess=preprocess,
                        torch=torch,
                        image_mod=image_mod,
                        device=device,
                    )
                )
                view_idx += 1

            for frame_idx in topk_by_clip:
                projected = camera_to_image[frame_idx][in_image[frame_idx].reshape(-1)]
                if len(projected) == 0:
                    continue
                image = image_mod.open(image_paths[frame_idx]).convert("RGB")
                image_np = image_array(image, np)
                padding_x = min(info["height"] * 0.3, 20)
                padding_y = min(info["width"] * 0.3, 20)
                x1 = max(0, int(projected[..., 1].min()) - int(padding_x))
                y1 = max(0, int(projected[..., 0].min()) - int(padding_y))
                x2 = min(int(projected[..., 1].max()) + int(padding_x), info["height"])
                y2 = min(int(projected[..., 0].max()) + int(padding_y), info["width"])
                crop = image_np[x1:x2, y1:y2]
                if crop.size == 0:
                    continue
                add_view(frame_idx, "A", crop)
                quality = "A"
                if view_idx >= 5:
                    break

            if view_idx == 0:
                topk_by_projection = np.argsort(-in_image.mean(-1)).tolist()
                for frame_idx in topk_by_projection:
                    projected = camera_to_image[frame_idx][in_image[frame_idx].reshape(-1)]
                    if len(projected) == 0:
                        continue
                    image = image_mod.open(image_paths[frame_idx]).convert("RGB")
                    image_np = image_array(image, np)
                    padding_x = min(info["height"] * 0.3, 20)
                    padding_y = min(info["width"] * 0.3, 20)
                    x1 = max(0, int(projected[..., 1].min()) - int(padding_x))
                    y1 = max(0, int(projected[..., 0].min()) - int(padding_y))
                    x2 = min(int(projected[..., 1].max()) + int(padding_x), info["height"])
                    y2 = min(int(projected[..., 0].max()) + int(padding_y), info["width"])
                    crop = image_np[x1:x2, y1:y2]
                    if crop.size == 0:
                        continue
                    add_view(frame_idx, "B", crop)
                    quality = "B"
                    if view_idx >= 5:
                        break

            if view_idx == 0:
                topk_by_clip_all = (-similarity[:, class_idx]).argsort()[:3].detach().cpu().numpy().tolist()
                for frame_idx in topk_by_clip_all:
                    add_view(frame_idx, "C", None)
                    quality = "C"
                    if view_idx >= 3:
                        break

            if quality is None:
                raise RuntimeError(f"{scan_id}: no view found for instance {instance_id}")

            crop_mean = np.concatenate(crop_feats, axis=0).mean(axis=0, keepdims=True)
            origin_mean = np.concatenate(origin_feats, axis=0).mean(axis=0, keepdims=True)
            np.save(crop_out, crop_mean)
            np.save(origin_out, origin_mean)
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            generated += 1
            fin_all.write(f"Scene:{scan_id} Instance:{instance_id} Label:{instance_name} Quality:{quality}\n")
            fin_all.flush()
    finally:
        fin_all.close()

    return {
        "scan_id": scan_id,
        "frame_count": info["frames"],
        "instance_count": len(instance_ids),
        "generated_instances": generated,
        "skipped_existing_instances": skipped_existing,
        "no_point_instances": no_points,
        "quality_counts": quality_counts,
        "multi_view_file_count": sum(1 for _ in multi_view_dir.glob("*.npy")),
        "multi_view_dir": rel(multi_view_dir),
    }


def build_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Multi-View Generation",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- status: `{manifest['status']}`",
        f"- device: `{manifest['device']}`",
        f"- scans requested: `{manifest['counts']['scans_requested']}`",
        f"- scans completed: `{manifest['counts']['scans_completed']}`",
        f"- instances generated: `{manifest['counts']['instances_generated']}`",
        f"- instances skipped existing: `{manifest['counts']['instances_skipped_existing']}`",
        "",
        "## Scan Results",
        "",
    ]
    for record in manifest["scan_records"]:
        lines.append(
            "- `{scan_id}`: frames=`{frames}`, instances=`{instances}`, generated=`{generated}`, npy=`{npy}`".format(
                scan_id=record["scan_id"],
                frames=record["frame_count"],
                instances=record["instance_count"],
                generated=record["generated_instances"],
                npy=record["multi_view_file_count"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    modules = dependency_imports()
    clip = modules["clip"]
    torch = modules["torch"]
    trimesh = modules["trimesh"]
    np = modules["numpy"]
    image_mod = modules["Image"]
    device = choose_device(torch, args.device)

    staged_root = args.staged_root.resolve()
    scan_root = staged_root / "data" / "3RScan"
    subset_root = staged_root / "data" / "3DSSG_subset"
    selected_scans = args.scan_id if args.scan_id else read_lines(args.selected_scans.resolve())

    print(f"loading CLIP ViT-B/32 on {device}")
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()

    class_list = read_lines(subset_root / "classes.txt")
    text = torch.cat([clip.tokenize(f"a photo of a {label}") for label in class_list]).to(device)
    with torch.no_grad():
        class_weight = normalize(model.encode_text(text))

    scene_objects = load_scene_objects(subset_root / "relationships_validation.json")
    scan_records = []
    for scan_id in selected_scans:
        print(f"generating multi_view: {scan_id}")
        if scan_id not in scene_objects:
            raise RuntimeError(f"{scan_id}: not found in relationships_validation.json")
        scan_records.append(
            generate_scan(
                scan_id,
                scan_root=scan_root,
                instance_names=scene_objects[scan_id],
                class_list=class_list,
                class_weight=class_weight,
                model=model,
                preprocess=preprocess,
                torch=torch,
                np=np,
                trimesh=trimesh,
                image_mod=image_mod,
                device=device,
                batch_size=args.batch_size,
                base_topk=args.topk,
                save_debug_images=args.save_debug_images,
                overwrite=args.overwrite,
            )
        )

    counts = {
        "scans_requested": len(selected_scans),
        "scans_completed": len(scan_records),
        "instances_generated": sum(record["generated_instances"] for record in scan_records),
        "instances_skipped_existing": sum(record["skipped_existing_instances"] for record in scan_records),
    }
    manifest = {
        "generated_at": now_iso(),
        "generator_version": "vlsat-multiview-generator-v1",
        "status": "completed",
        "staged_root": str(staged_root),
        "scan_root": str(scan_root),
        "selected_scans": selected_scans,
        "device": device,
        "model": "CLIP ViT-B/32",
        "save_debug_images": args.save_debug_images,
        "counts": counts,
        "scan_records": scan_records,
    }
    output_dir = args.output_dir.resolve()
    write_json(output_dir / "multiview_generation.json", manifest)
    write_text(output_dir / "multiview_generation.md", build_report(manifest))
    print(f"report={rel(output_dir / 'multiview_generation.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
