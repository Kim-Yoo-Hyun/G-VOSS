#!/usr/bin/env python3
"""Run a H001-Mini VL-SAT validation pass and dump raw relation scores.

The script keeps the official VL-SAT source tree unmodified. It builds a
runtime config and a mini validation selection, imports the official dataset
and model, then calls the model forward pass at the same point where relation
scores still retain scan/subgraph/object-pair identity.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import types
from datetime import date
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT
DEFAULT_VLSAT_CODE_ROOT = REPO_ROOT / "local_dataset" / "VLSAT_code" / "CVPR2023-VLSAT"
DEFAULT_STAGED_ROOT = REPO_ROOT / "local_dataset" / "VLSAT_staged" / "CVPR2023-VLSAT"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_mini" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "vlsat_closed_set" / "mini" / "raw"
DEFAULT_BASELINE_RUN_ID = f"vlsat_eval_{date.today().strftime('%Y%m%d')}_h001_mini"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Faithful VL-SAT H001-Mini raw relation score dump."
    )
    parser.add_argument("--vlsat-code-root", type=Path, default=DEFAULT_VLSAT_CODE_ROOT)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--exp", default="3dssg")
    parser.add_argument("--baseline-run-id", default=DEFAULT_BASELINE_RUN_ID)
    parser.add_argument("--limit-subgraphs", type=int)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--append", action="store_true")
    parser.add_argument(
        "--allow-no-checkpoint",
        action="store_true",
        help="Run with random weights for adapter plumbing only. Not reportable.",
    )
    parser.add_argument(
        "--force-pyg-shim",
        action="store_true",
        help="Use the minimal local torch_geometric MessagePassing shim even if PyG is installed.",
    )
    return parser.parse_args()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def make_report(summary: dict[str, Any]) -> str:
    validation = summary["validation"]
    counts = summary["counts"]
    lines = [
        "# VL-SAT Raw Dump",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Status: `{summary['status']}`",
        f"Baseline run id: `{summary['baseline_run_id']}`",
        "",
        "## Inputs",
        "",
        f"- VL-SAT code root: `{summary['vlsat_code_root']}`",
        f"- Staged root: `{summary['staged_root']}`",
        f"- Selection file: `{summary['selected_scans_file']}`",
        f"- Checkpoint root: `{summary['checkpoint_root']}`",
        "",
        "## Outputs",
        "",
        f"- Raw dump: `{summary['raw_dump_file']}`",
        f"- Runtime config: `{summary['runtime_config_file']}`",
        f"- Summary: `summary.json`",
        "",
        "## Counts",
        "",
        f"- Selected scans: `{counts['selected_scans']}`",
        f"- Dumped subgraphs: `{counts['dumped_subgraphs']}`",
        f"- Directed pairs: `{counts['directed_pairs']}`",
        "",
        "## Validation",
        "",
        f"- Passed: `{validation['passed']}`",
        f"- Errors: `{len(validation['errors'])}`",
        f"- Warnings: `{len(validation['warnings'])}`",
    ]
    if validation["errors"]:
        lines.extend(["", "### Errors", ""])
        for error in validation["errors"][:30]:
            lines.append(f"- `{error}`")
    if validation["warnings"]:
        lines.extend(["", "### Warnings", ""])
        for warning in validation["warnings"][:30]:
            lines.append(f"- `{warning}`")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This raw dump is source-run data for the selected scan split named by the command.",
            "- It must not be used to fit `p_geom_valid`.",
            "- Raw scores alone are not metric evidence until prediction export, ground-truth JSONL, geometry join, calibrator/verifier outputs, metrics, controls, and bootstrap outputs exist.",
            "",
        ]
    )
    return "\n".join(lines)


def install_minimal_pyg_message_passing() -> bool:
    """Install a tiny MessagePassing-compatible shim for the VL-SAT code path.

    VL-SAT uses only PyG's gather and aggregate behavior in the Mmgnet path.
    This shim is intentionally narrow and exists so the raw-dump runner can use
    the existing local venv without mutating the official source checkout.
    """

    import torch

    class _Inspector:
        def distribute(self, fn_name: str, coll_dict: dict[str, Any]) -> dict[str, Any]:
            if fn_name == "message":
                return {"x_i": coll_dict["x_i"], "x_j": coll_dict["x_j"]}
            if fn_name == "aggregate":
                return {"index": coll_dict["index"], "dim_size": coll_dict["dim_size"]}
            return {}

    class MessagePassing(torch.nn.Module):
        def __init__(
            self,
            aggr: str = "add",
            node_dim: int = -2,
            flow: str = "source_to_target",
            **_: Any,
        ) -> None:
            super().__init__()
            self.aggr = aggr
            self.node_dim = node_dim
            self.flow = flow
            self.__user_args__ = []
            self.inspector = _Inspector()

        def __check_input__(self, edge_index: Any, size: Any) -> Any:
            return size

        def __collect__(
            self,
            user_args: Any,
            edge_index: Any,
            size: Any,
            kwargs: dict[str, Any],
        ) -> dict[str, Any]:
            del user_args, size
            if self.flow == "source_to_target":
                i, j = 1, 0
            elif self.flow == "target_to_source":
                i, j = 0, 1
            else:
                raise ValueError(f"unsupported flow: {self.flow}")

            out: dict[str, Any] = {"index": edge_index[i]}
            if kwargs and "x" in kwargs:
                x = kwargs["x"]
                out["x_i"] = x[edge_index[i]]
                out["x_j"] = x[edge_index[j]]
            return out

        def aggregate(self, inputs: Any, index: Any, dim_size: int | None = None) -> Any:
            if dim_size is None:
                dim_size = int(index.max().item()) + 1 if index.numel() else 0
            out_shape = (dim_size,) + tuple(inputs.shape[1:])
            if self.aggr in {"add", "mean"}:
                out = inputs.new_zeros(out_shape)
                for row_idx in range(inputs.shape[0]):
                    out[int(index[row_idx])] += inputs[row_idx]
                if self.aggr == "mean":
                    counts = inputs.new_zeros((dim_size,) + (1,) * (inputs.dim() - 1))
                    for row_idx in range(inputs.shape[0]):
                        counts[int(index[row_idx])] += 1
                    out = out / counts.clamp_min(1)
                return out
            if self.aggr == "max":
                out = inputs.new_full(out_shape, -float("inf"))
                seen = inputs.new_zeros((dim_size,), dtype=torch.bool)
                for row_idx in range(inputs.shape[0]):
                    target = int(index[row_idx])
                    out[target] = torch.maximum(out[target], inputs[row_idx])
                    seen[target] = True
                if seen.numel():
                    out[~seen] = 0
                return out
            raise ValueError(f"unsupported aggregation: {self.aggr}")

    torch_geometric = types.ModuleType("torch_geometric")
    nn_mod = types.ModuleType("torch_geometric.nn")
    conv_mod = types.ModuleType("torch_geometric.nn.conv")
    conv_mod.MessagePassing = MessagePassing
    nn_mod.conv = conv_mod
    nn_mod.MessagePassing = MessagePassing
    torch_geometric.nn = nn_mod
    sys.modules["torch_geometric"] = torch_geometric
    sys.modules["torch_geometric.nn"] = nn_mod
    sys.modules["torch_geometric.nn.conv"] = conv_mod
    return True


def maybe_install_pyg_shim(force: bool) -> bool:
    if not force:
        try:
            from torch_geometric.nn.conv import MessagePassing  # noqa: F401

            return False
        except Exception:
            pass
    return install_minimal_pyg_message_passing()


def install_tkinter_shim_if_missing() -> bool:
    try:
        import tkinter  # noqa: F401

        return False
    except Exception:
        tkinter_mod = types.ModuleType("tkinter")
        tkinter_mod.N = "n"
        sys.modules["tkinter"] = tkinter_mod
        return True


def install_pointnet_graph_shim() -> bool:
    """Provide the unused legacy GraphTripleConvNet import if the repo omits it."""

    if "src.lib.pointnet.graph" in sys.modules:
        return False

    class GraphTripleConvNet:  # pragma: no cover - only used if legacy path is called
        def __init__(self, *_: Any, **__: Any) -> None:
            raise RuntimeError("GraphTripleConvNet shim is import-only for H001 VL-SAT dump")

    lib_mod = types.ModuleType("src.lib")
    pointnet_mod = types.ModuleType("src.lib.pointnet")
    graph_mod = types.ModuleType("src.lib.pointnet.graph")
    graph_mod.GraphTripleConvNet = GraphTripleConvNet
    sys.modules.setdefault("src.lib", lib_mod)
    sys.modules.setdefault("src.lib.pointnet", pointnet_mod)
    sys.modules["src.lib.pointnet.graph"] = graph_mod
    return True


def patch_torch_load_for_legacy_vlsat(torch_mod: Any) -> None:
    """Make official 2022 VL-SAT checkpoints load under PyTorch 2.6+.

    The checkpoint was obtained from the official VL-SAT README link. PyTorch
    2.6 changed torch.load's default to weights_only=True, but the official
    config checkpoint stores numpy scalar metadata. Keep this patch local to
    this runner process.
    """

    original_load = torch_mod.load

    def trusted_legacy_load(*args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("weights_only", False)
        return original_load(*args, **kwargs)

    torch_mod.load = trusted_legacy_load


def patch_util_ply_for_current_trimesh(util_ply_mod: Any) -> None:
    def read_labels_compat(plydata: Any) -> Any:
        raw = plydata.metadata.get("ply_raw") or plydata.metadata.get("_ply_raw")
        if raw is None:
            raise KeyError("ply_raw")
        data = raw["vertex"]["data"]
        try:
            return data["objectId"]
        except Exception:
            return data["label"]

    util_ply_mod.read_labels = read_labels_compat


def checkpoint_files(checkpoint_root: Path, exp: str) -> list[Path]:
    ckp_dir = checkpoint_root / "ckp" / "Mmgnet" / exp
    return sorted(ckp_dir.glob("*_best.pth")) + sorted(ckp_dir.glob("config_best.pth"))


def make_selection_dir(output_dir: Path, staged_root: Path, selected_scans: Path) -> Path:
    selection_dir = output_dir / "selection"
    selection_dir.mkdir(parents=True, exist_ok=True)
    subset_dir = staged_root / "data" / "3DSSG_subset"
    for name in ["classes.txt", "relationships.txt", "relations.txt"]:
        shutil.copy2(subset_dir / name, selection_dir / name)
    shutil.copy2(subset_dir / "train_scans.txt", selection_dir / "train_scans.txt")
    (selection_dir / "validation_scans.txt").write_text(
        "\n".join(read_lines(selected_scans)) + "\n", encoding="utf-8"
    )
    return selection_dir


def make_runtime_config(
    *,
    args: argparse.Namespace,
    output_root: Path,
    selection_dir: Path,
) -> Path:
    template = args.vlsat_code_root / "config" / "mmgnet.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    data["PATH"] = str(output_root)
    data["multi_view_root"] = str(args.staged_root)
    data["WORKERS"] = 0
    data["Batch_Size"] = 1
    data["EVAL"] = True
    data["VERBOSE"] = False
    data["GPU"] = [0]
    data["MODEL"]["obj_label_path"] = str(args.staged_root / "data" / "3DSSG_subset" / "classes.txt")
    data["MODEL"]["rel_label_path"] = str(args.staged_root / "data" / "3DSSG_subset" / "relations.txt")
    data["MODEL"]["adapter_path"] = str(
        args.vlsat_code_root / "clip_adapter" / "checkpoint" / "origin_mean.pth"
    )
    data["dataset"]["root"] = str(args.staged_root / "data" / "3DSSG_subset")
    data["dataset"]["selection"] = str(selection_dir)
    data["dataset"]["use_data_augmentation"] = False
    data["dataset"]["data_augmentation"] = False
    runtime_config = args.output_dir / "config.json"
    write_json(runtime_config, data)
    return runtime_config


def preflight(args: argparse.Namespace, output_root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required_paths = {
        "vlsat_code_root": args.vlsat_code_root,
        "staged_root": args.staged_root,
        "selected_scans": args.selected_scans,
        "vlsat_config": args.vlsat_code_root / "config" / "mmgnet.json",
        "clip_adapter": args.vlsat_code_root / "clip_adapter" / "checkpoint" / "origin_mean.pth",
        "staged_subset": args.staged_root / "data" / "3DSSG_subset",
        "staged_3rscan": args.staged_root / "data" / "3RScan",
    }
    for name, path in required_paths.items():
        if not path.exists():
            errors.append(f"missing_input:{name}:{relpath(path)}")

    selected: list[str] = []
    if args.selected_scans.exists():
        selected = read_lines(args.selected_scans)
        if not selected:
            errors.append(f"empty_selected_scans:{relpath(args.selected_scans)}")
    for scan_id in selected:
        scan_dir = args.staged_root / "data" / "3RScan" / scan_id
        for name in [
            "labels.instances.align.annotated.v2.ply",
            "semseg.v2.json",
            "mesh.refined.0.010000.segs.v2.json",
        ]:
            if not (scan_dir / name).exists():
                errors.append(f"missing_scan_payload:{scan_id}:{name}")
        multi_view = scan_dir / "multi_view"
        if not multi_view.exists() or not list(multi_view.glob("*_origin_view_mean.npy")):
            errors.append(f"missing_multiview:{scan_id}")

    checkpoint_hits = checkpoint_files(output_root, args.exp)
    if not checkpoint_hits and not args.allow_no_checkpoint:
        errors.append(
            "missing_vlsat_checkpoint:"
            f"{relpath(output_root / 'ckp' / 'Mmgnet' / args.exp)}"
        )
    if args.allow_no_checkpoint:
        warnings.append("allow_no_checkpoint_random_weights_not_reportable")

    try:
        import torch

        if not torch.cuda.is_available():
            errors.append("cuda_unavailable:official_vlsat_clip_path_uses_cuda")
    except Exception as exc:
        errors.append(f"missing_dependency:torch:{type(exc).__name__}:{exc}")

    for module_name in ["numpy", "trimesh", "clip"]:
        try:
            __import__(module_name)
        except Exception as exc:
            errors.append(f"missing_dependency:{module_name}:{type(exc).__name__}:{exc}")

    if not args.force_pyg_shim:
        try:
            __import__("torch_geometric")
        except Exception:
            warnings.append("torch_geometric_missing_using_local_messagepassing_shim")
    try:
        __import__("tkinter")
    except Exception:
        warnings.append("tkinter_missing_using_unused_import_shim")
    if not (args.vlsat_code_root / "src" / "lib" / "pointnet" / "graph.py").exists():
        warnings.append("src_lib_pointnet_graph_missing_using_unused_import_shim")

    return errors, warnings


def run_dump(args: argparse.Namespace, output_root: Path) -> dict[str, Any]:
    import numpy as np
    import torch

    patch_torch_load_for_legacy_vlsat(torch)
    maybe_install_pyg_shim(args.force_pyg_shim)
    install_tkinter_shim_if_missing()
    install_pointnet_graph_shim()

    sys.path.insert(0, str(args.vlsat_code_root))
    sys.path.insert(0, str(args.vlsat_code_root / "src"))

    from src.dataset.DataLoader import CustomDataLoader, collate_fn_mmg
    from src.dataset.dataset_builder import build_dataset
    from src.model.SGFN_MMG.model import Mmgnet
    from src.utils.config import Config
    from utils import define, util, util_ply

    import vlsat_dump_hook

    patch_util_ply_for_current_trimesh(util_ply)

    define.ROOT_PATH = str(args.staged_root) + os.sep
    define.DATA_PATH = str(args.staged_root / "data" / "3RScan") + os.sep
    define.FILE_PATH = str(args.staged_root / "files") + os.sep
    define.Scan3RJson_PATH = str(args.staged_root / "files" / "3RScan.json")

    selection_dir = make_selection_dir(args.output_dir, args.staged_root, args.selected_scans)
    runtime_config = make_runtime_config(args=args, output_root=output_root, selection_dir=selection_dir)

    config = Config(str(runtime_config))
    config.PATH = str(output_root)
    config.MODE = "trace"
    config.exp = args.exp
    config.EVAL = True
    config.VERBOSE = False
    config.WORKERS = 0
    config.Batch_Size = 1
    config.GPU = [0]
    config.DEVICE = torch.device("cuda")
    config.total = 1
    config.max_iteration = 1
    config.max_iteration_scheduler = 1
    util.set_random_seed(config.SEED)
    np.random.seed(int(config.SEED))

    dataset_valid = build_dataset(
        config,
        split_type="validation_scans",
        shuffle_objs=False,
        multi_rel_outputs=config.MODEL.multi_rel_outputs,
        use_rgb=config.MODEL.USE_RGB,
        use_normal=config.MODEL.USE_NORMAL,
    )
    model = Mmgnet(config, len(dataset_valid.classNames), len(dataset_valid.relationNames)).to(config.DEVICE)
    loaded = model.load(best=True)
    if not loaded and not args.allow_no_checkpoint:
        raise RuntimeError("VL-SAT checkpoint load failed")
    model.eval()

    val_loader = CustomDataLoader(
        config=config,
        dataset=dataset_valid,
        batch_size=1,
        num_workers=0,
        drop_last=False,
        shuffle=False,
        collate_fn=collate_fn_mmg,
    )

    raw_path = args.output_dir / "raw.jsonl"
    if raw_path.exists() and not args.append:
        raw_path.unlink()

    dumped_subgraphs = 0
    directed_pairs = 0
    with torch.no_grad():
        for i, items in enumerate(val_loader):
            if args.limit_subgraphs is not None and i >= args.limit_subgraphs:
                break
            (
                obj_points,
                obj_2d_feats,
                gt_class,
                gt_rel_cls,
                edge_indices,
                descriptor,
                batch_ids,
            ) = items
            obj_points = obj_points.permute(0, 2, 1).contiguous().to(config.DEVICE)
            obj_2d_feats = obj_2d_feats.to(config.DEVICE)
            gt_class = gt_class.to(config.DEVICE)
            edge_indices = edge_indices.to(config.DEVICE)
            descriptor = descriptor.to(config.DEVICE)
            batch_ids = batch_ids.to(config.DEVICE)

            obj_logits_3d, obj_logits_2d, rel_cls_3d, rel_cls_2d = model(
                obj_points,
                obj_2d_feats,
                edge_indices.t().contiguous(),
                descriptor,
                batch_ids,
                istrain=False,
            )
            record = vlsat_dump_hook.make_raw_record(
                dataset=dataset_valid,
                dataset_index=i,
                edge_indices=edge_indices.detach().cpu(),
                rel_scores_3d=rel_cls_3d.detach().cpu(),
                baseline_run_id=args.baseline_run_id,
                rel_scores_2d=rel_cls_2d.detach().cpu(),
                obj_scores_3d=torch.softmax(obj_logits_3d.detach().cpu(), dim=-1),
                obj_scores_2d=torch.softmax(obj_logits_2d.detach().cpu(), dim=-1),
            )
            vlsat_dump_hook.append_raw_record(raw_path, record)
            dumped_subgraphs += 1
            directed_pairs += len(record["edge_indices"])

    return {
        "raw_path": raw_path,
        "runtime_config": runtime_config,
        "dumped_subgraphs": dumped_subgraphs,
        "directed_pairs": directed_pairs,
    }


def main() -> int:
    args = parse_args()
    args.vlsat_code_root = args.vlsat_code_root.resolve()
    args.staged_root = args.staged_root.resolve()
    args.selected_scans = args.selected_scans.resolve()
    args.output_dir = args.output_dir.resolve()
    output_root = (args.output_root or (args.vlsat_code_root / "output")).resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    selected_count = len(read_lines(args.selected_scans)) if args.selected_scans.exists() else 0
    raw_path = args.output_dir / "raw.jsonl"
    runtime_config = args.output_dir / "config.json"

    errors, warnings = preflight(args, output_root)
    run_result: dict[str, Any] | None = None
    status = "ready_to_run" if not errors else "blocked"
    if not errors and not args.preflight_only:
        try:
            run_result = run_dump(args, output_root)
            raw_path = run_result["raw_path"]
            runtime_config = run_result["runtime_config"]
            status = "raw_dump_ready"
        except Exception as exc:
            status = "blocked"
            errors.append(f"run_failed:{type(exc).__name__}:{exc}")

    dumped_subgraphs = run_result["dumped_subgraphs"] if run_result else 0
    directed_pairs = run_result["directed_pairs"] if run_result else 0
    summary = {
        "schema_version": "h001_vlsat_raw_dump_summary_v1",
        "created_at": date.today().isoformat(),
        "status": status,
        "baseline_name": "vlsat_closed_set",
        "baseline_run_id": args.baseline_run_id,
        "vlsat_code_root": relpath(args.vlsat_code_root),
        "staged_root": relpath(args.staged_root),
        "selected_scans_file": relpath(args.selected_scans),
        "checkpoint_root": relpath(output_root),
        "exp": args.exp,
        "raw_dump_file": relpath(raw_path),
        "runtime_config_file": relpath(runtime_config),
        "counts": {
            "selected_scans": selected_count,
            "dumped_subgraphs": dumped_subgraphs,
            "directed_pairs": directed_pairs,
        },
        "validation": {
            "passed": not errors,
            "errors": errors,
            "warnings": warnings,
        },
        "notes": [
            "The selected scan split is fixed by the command; do not use this raw dump to fit calibration.",
            "This runner preserves raw VL-SAT relation scores before aggregate metric files lose join identity.",
        ],
    }
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(make_report(summary), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "output_dir": relpath(args.output_dir),
                "raw_dump_file": relpath(raw_path),
                "dumped_subgraphs": dumped_subgraphs,
                "directed_pairs": directed_pairs,
                "errors": len(errors),
                "warnings": len(warnings),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
