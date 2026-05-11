#!/usr/bin/env python3
"""Apply H001 Open3DSG source compatibility patches before Docker execution."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_source_patch_v3"

LOAD_BLOCK_ORIGINAL = """        self.scene_data = []
        manager = Manager()
        shared_list = manager.list()

        if self.relationships_R3SCAN:
            self.obj_vis_crit -= 0.1  # r3scan images are smaller than scannet lets adjust
            self.obj_mask_crit -= 0.1
            self.rel_vis_crit -= 0.1
            # Load all data into ram for faster training
            process_map(partial(_load_data_tqdm, shared_list), self.relationships_R3SCAN, max_workers=8, chunksize=1)

        if self.relationships_scannet:
            # Load all data into ram for faster training
            process_map(partial(_load_data_scannet_tqdm, shared_list), self.relationships_scannet, max_workers=8, chunksize=1)

        self.scene_data = shared_list
"""

LOAD_BLOCK_WORKER_LIMITED = """        self.scene_data = []
        dataset_load_workers = int(os.environ.get("OPEN3DSG_DATASET_LOAD_WORKERS", "1"))
        manager = Manager() if dataset_load_workers > 1 else None
        shared_list = manager.list() if manager is not None else self.scene_data

        if self.relationships_R3SCAN:
            self.obj_vis_crit -= 0.1  # r3scan images are smaller than scannet lets adjust
            self.obj_mask_crit -= 0.1
            self.rel_vis_crit -= 0.1
            # Load all data into ram for faster training
            if dataset_load_workers > 1:
                process_map(partial(_load_data_tqdm, shared_list), self.relationships_R3SCAN, max_workers=dataset_load_workers, chunksize=1)
            else:
                for relationship in tqdm(self.relationships_R3SCAN):
                    _load_data_tqdm(shared_list, relationship)

        if self.relationships_scannet:
            # Load all data into ram for faster training
            if dataset_load_workers > 1:
                process_map(partial(_load_data_scannet_tqdm, shared_list), self.relationships_scannet, max_workers=dataset_load_workers, chunksize=1)
            else:
                for relationship in tqdm(self.relationships_scannet):
                    _load_data_scannet_tqdm(shared_list, relationship)

        self.scene_data = list(shared_list)
"""

LOAD_BLOCK_LAZY = """        self.lazy_data = os.environ.get("OPEN3DSG_LAZY_DATASET", "0") == "1"
        self.scene_data = []
        dataset_load_workers = int(os.environ.get("OPEN3DSG_DATASET_LOAD_WORKERS", "1"))
        manager = Manager() if dataset_load_workers > 1 and not self.lazy_data else None
        shared_list = manager.list() if manager is not None else self.scene_data

        if self.relationships_R3SCAN:
            self.obj_vis_crit -= 0.1  # r3scan images are smaller than scannet lets adjust
            self.obj_mask_crit -= 0.1
            self.rel_vis_crit -= 0.1
            if self.lazy_data:
                self.scene_data.extend(("r3scan", relationship) for relationship in self.relationships_R3SCAN)
            elif dataset_load_workers > 1:
                process_map(partial(_load_data_tqdm, shared_list), self.relationships_R3SCAN, max_workers=dataset_load_workers, chunksize=1)
            else:
                for relationship in tqdm(self.relationships_R3SCAN):
                    _load_data_tqdm(shared_list, relationship)

        if self.relationships_scannet:
            if self.lazy_data:
                self.scene_data.extend(("scannet", relationship) for relationship in self.relationships_scannet)
            elif dataset_load_workers > 1:
                process_map(partial(_load_data_scannet_tqdm, shared_list), self.relationships_scannet, max_workers=dataset_load_workers, chunksize=1)
            else:
                for relationship in tqdm(self.relationships_scannet):
                    _load_data_scannet_tqdm(shared_list, relationship)

        if not self.lazy_data:
            self.scene_data = list(shared_list)
"""

GETITEM_BLOCK_ORIGINAL = """    def __getitem__(self, idx):
        # start = time.time()

        data_dict = vars(self.scene_data[idx])
"""

GETITEM_BLOCK_LAZY_R3SCAN_TYPO = """    def __getitem__(self, idx):
        # start = time.time()

        if getattr(self, "lazy_data", False):
            dataset_name, relationship = self.scene_data[idx]
            loaded_data = []
            if dataset_name == "3rscan":
                _load_data_tqdm(loaded_data, relationship)
            else:
                _load_data_scannet_tqdm(loaded_data, relationship)
            if not loaded_data:
                raise RuntimeError(f"Failed to lazy-load Open3DSG sample: {relationship}")
            data_dict = vars(loaded_data[0])
        else:
            data_dict = vars(self.scene_data[idx])
"""

GETITEM_BLOCK_LAZY = """    def __getitem__(self, idx):
        # start = time.time()

        if getattr(self, "lazy_data", False):
            dataset_name, relationship = self.scene_data[idx]
            loaded_data = []
            if dataset_name in {"r3scan", "3rscan"}:
                _load_data_tqdm(loaded_data, relationship)
            else:
                _load_data_scannet_tqdm(loaded_data, relationship)
            if not loaded_data:
                raise RuntimeError(f"Failed to lazy-load Open3DSG sample: {relationship}")
            data_dict = vars(loaded_data[0])
        else:
            data_dict = vars(self.scene_data[idx])
"""

TRAINING_STEP_ORIGINAL = """    def training_step(self, data_dict, *_, **__):

        data_dict = self._forward(data_dict)
        if self.hparams.get('dump_features'):
            self._dump_features(data_dict, data_dict["objects_id"].size(0), path=self.clip_path)
            return
        data_dict = self._compute_loss(data_dict)
"""

TRAINING_STEP_NO_GRAD = """    def training_step(self, data_dict, *_, **__):

        if self.hparams.get('dump_features'):
            with torch.no_grad():
                data_dict = self._forward(data_dict)
                self._dump_features(data_dict, data_dict["objects_id"].size(0), path=self.clip_path)
            return
        data_dict = self._forward(data_dict)
        data_dict = self._compute_loss(data_dict)
"""

TRAINING_STEP_RESUMABLE = """    def training_step(self, data_dict, *_, **__):

        if self.hparams.get('dump_features'):
            if self._feature_outputs_exist(data_dict, data_dict["objects_id"].size(0), path=self.clip_path):
                return
            with torch.no_grad():
                data_dict = self._forward(data_dict)
                self._dump_features(data_dict, data_dict["objects_id"].size(0), path=self.clip_path)
            return
        data_dict = self._forward(data_dict)
        data_dict = self._compute_loss(data_dict)
"""

VALIDATION_STEP_ORIGINAL = """        data_dict = self._forward(data_dict)
        if self.hparams.get('dump_features'):
            self._dump_features(data_dict, data_dict["objects_id"].size(0), path=self.clip_path)
            return
        data_dict = self._compute_loss(data_dict)
"""

VALIDATION_STEP_RESUMABLE = """        if self.hparams.get('dump_features') and self._feature_outputs_exist(data_dict, data_dict["objects_id"].size(0), path=self.clip_path):
            return

        data_dict = self._forward(data_dict)
        if self.hparams.get('dump_features'):
            self._dump_features(data_dict, data_dict["objects_id"].size(0), path=self.clip_path)
            return
        data_dict = self._compute_loss(data_dict)
"""

FEATURE_HELPERS = """    def _feature_output_paths(self, feature_id, path=CONF.PATH.FEATURES):
        obj_clip_model = self.hparams['node_model'] if self.hparams['node_model'] and self.hparams['clip_model'] != "OpenSeg" else self.hparams['clip_model']
        rel_clip_model = self.hparams['edge_model'] if self.hparams['edge_model'] else self.hparams['clip_model']
        if self.hparams['blip']:
            rel_clip_model = "BLIP"
        elif self.hparams['llava']:
            rel_clip_model = "LLaVa"

        obj_path = os.path.join(path, 'export_obj_clip_emb_clip_' + obj_clip_model.replace('/', '-')+'_Topk_' + str(self.hparams['top_k_frames'])+'_scales_'+str(
            self.hparams['scales'])+'_vis_crit_' + str(self.val_dataset.obj_vis_crit)+'_vis_crit_mask_' + str(self.val_dataset.obj_mask_crit))
        obj_valid_path = os.path.join(path, 'export_obj_clip_valids')
        rel_path = os.path.join(path, 'export_rel_clip_emb_clip_' + rel_clip_model.replace('/', '-')+'_Topk_' + str(
            self.hparams['top_k_frames'])+'_scales_'+str(self.hparams['scales'])+'_vis_crit_' + str(self.val_dataset.rel_vis_crit))
        return (
            os.path.join(obj_path, feature_id),
            os.path.join(obj_valid_path, feature_id),
            os.path.join(rel_path, feature_id),
        )

    def _feature_outputs_exist(self, data_dict, batch_size, path=CONF.PATH.FEATURES):
        if os.environ.get("OPEN3DSG_FEATURE_SKIP_EXISTING", "0") != "1":
            return False
        for bidx in range(batch_size):
            feature_id = data_dict['scan_id'][bidx] + '.pt'
            if not all(os.path.exists(pth) for pth in self._feature_output_paths(feature_id, path=path)):
                return False
        return True

"""

REPLACEMENTS = (
    (
        "open3dsg/models/sgpn.py",
        "torch.load(os.path.join(CONF.PATH.CHECKPOINTS, 'blip2_positional_embedding.pt'))",
        "torch.load(os.path.join(CONF.PATH.CHECKPOINTS, 'blip2_positional_embedding.pt'), weights_only=False)",
    ),
    (
        "open3dsg/models/sgpn.py",
        "torch.load(pth, map_location=torch.device(torch.distributed.get_rank()))[\"state_dict\"]",
        "torch.load(pth, map_location=torch.device(torch.distributed.get_rank()), weights_only=False)[\"state_dict\"]",
    ),
    (
        "open3dsg/models/sgpn.py",
        "torch.load(pth)[\"state_dict\"]",
        "torch.load(pth, weights_only=False)[\"state_dict\"]",
    ),
    (
        "open3dsg/models/sgpn.py",
        "torch.load(pth, map_location=torch.device(torch.distributed.get_rank()))[\"model_state_dict\"]",
        "torch.load(pth, map_location=torch.device(torch.distributed.get_rank()), weights_only=False)[\"model_state_dict\"]",
    ),
    (
        "open3dsg/models/sgpn.py",
        "torch.load(pth)[\"model_state_dict\"]",
        "torch.load(pth, weights_only=False)[\"model_state_dict\"]",
    ),
    (
        "open3dsg/scripts/run.py",
        "torch.load(checkpoint)['global_step']",
        "torch.load(checkpoint, weights_only=False)['global_step']",
    ),
    (
        "open3dsg/data/open_dataset.py",
        "torch.load(obj_feature_pth)",
        "torch.load(obj_feature_pth, weights_only=False)",
    ),
    (
        "open3dsg/data/open_dataset.py",
        "torch.load(obj_valid_feature_pth)",
        "torch.load(obj_valid_feature_pth, weights_only=False)",
    ),
    (
        "open3dsg/data/open_dataset.py",
        "torch.load(rel_feature_pth)",
        "torch.load(rel_feature_pth, weights_only=False)",
    ),
    (
        "open3dsg/scripts/trainer.py",
        "DataLoader(self.train_dataset, batch_size=self.hparams['batch_size'], shuffle=True,",
        "DataLoader(self.train_dataset, batch_size=self.hparams['batch_size'], shuffle=not self.hparams.get('dump_features'),",
    ),
    (
        "open3dsg/scripts/trainer.py",
        """        self.clip_path = os.path.join(CONF.PATH.FEATURES, f"clip_features_{datetime.now().strftime('%Y-%m-%d-%H-%M')}")
""",
        """        self.clip_path = os.environ.get(
            "OPEN3DSG_FEATURE_RUN_DIR",
            os.path.join(CONF.PATH.FEATURES, f"clip_features_{datetime.now().strftime('%Y-%m-%d-%H-%M')}")
        )
""",
    ),
    (
        "open3dsg/scripts/trainer.py",
        """            torch.save(clip_obj_emb.detach().cpu(), os.path.join(obj_path, data_dict['scan_id'][bidx]+'.pt'))
            torch.save(obj_valids.detach().cpu(), os.path.join(obj_valid_path, data_dict['scan_id'][bidx]+'.pt'))
            torch.save(clip_rel_emb_masked.detach().cpu(), os.path.join(rel_path, data_dict['scan_id'][bidx]+'.pt'))
""",
        """            feature_id = data_dict['scan_id'][bidx] + '.pt'
            obj_out = os.path.join(obj_path, feature_id)
            obj_valid_out = os.path.join(obj_valid_path, feature_id)
            rel_out = os.path.join(rel_path, feature_id)
            if os.environ.get("OPEN3DSG_FEATURE_SKIP_EXISTING", "0") == "1" and all(
                os.path.exists(pth) for pth in (obj_out, obj_valid_out, rel_out)
            ):
                continue

            torch.save(clip_obj_emb.detach().cpu(), obj_out)
            torch.save(obj_valids.detach().cpu(), obj_valid_out)
            torch.save(clip_rel_emb_masked.detach().cpu(), rel_out)
""",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/source_patch"),
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


def apply_replacement(source_root: Path, rel_file: str, old: str, new: str) -> dict[str, Any]:
    path = source_root / rel_file
    record: dict[str, Any] = {"file": rel_file}
    if not path.is_file():
        record["status"] = "missing_file"
        return record
    text = path.read_text(encoding="utf-8")
    if new in text:
        record["status"] = "already_patched"
        return record
    if old not in text:
        record["status"] = "pattern_missing"
        return record
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    record["status"] = "patched"
    return record


def apply_open_dataset_lazy_patch(source_root: Path) -> dict[str, Any]:
    rel_file = "open3dsg/data/open_dataset.py"
    path = source_root / rel_file
    record: dict[str, Any] = {"file": rel_file, "patch": "lazy_dataset"}
    if not path.is_file():
        record["status"] = "missing_file"
        return record

    text = path.read_text(encoding="utf-8")
    changed = False

    if LOAD_BLOCK_LAZY not in text:
        if LOAD_BLOCK_WORKER_LIMITED in text:
            text = text.replace(LOAD_BLOCK_WORKER_LIMITED, LOAD_BLOCK_LAZY, 1)
            changed = True
        elif LOAD_BLOCK_ORIGINAL in text:
            text = text.replace(LOAD_BLOCK_ORIGINAL, LOAD_BLOCK_LAZY, 1)
            changed = True
        else:
            record["status"] = "pattern_missing"
            record["missing_pattern"] = "dataset_load_block"
            return record

    if GETITEM_BLOCK_LAZY not in text:
        if GETITEM_BLOCK_LAZY_R3SCAN_TYPO in text:
            text = text.replace(GETITEM_BLOCK_LAZY_R3SCAN_TYPO, GETITEM_BLOCK_LAZY, 1)
            changed = True
        elif GETITEM_BLOCK_ORIGINAL in text:
            text = text.replace(GETITEM_BLOCK_ORIGINAL, GETITEM_BLOCK_LAZY, 1)
            changed = True
        else:
            record["status"] = "pattern_missing"
            record["missing_pattern"] = "getitem_block"
            return record

    if changed:
        path.write_text(text, encoding="utf-8")
        record["status"] = "patched"
    else:
        record["status"] = "already_patched"
    return record


def apply_trainer_feature_dump_patch(source_root: Path) -> dict[str, Any]:
    rel_file = "open3dsg/scripts/trainer.py"
    path = source_root / rel_file
    record: dict[str, Any] = {"file": rel_file, "patch": "resumable_feature_dump"}
    if not path.is_file():
        record["status"] = "missing_file"
        return record

    text = path.read_text(encoding="utf-8")
    changed = False
    missing_patterns: list[str] = []

    if FEATURE_HELPERS not in text:
        marker = "    def _dump_features(self, data_dict, batch_size, path=CONF.PATH.FEATURES):\n"
        if marker in text:
            text = text.replace(marker, FEATURE_HELPERS + marker, 1)
            changed = True
        else:
            missing_patterns.append("dump_feature_helper_marker")

    if TRAINING_STEP_RESUMABLE not in text:
        if TRAINING_STEP_NO_GRAD in text:
            text = text.replace(TRAINING_STEP_NO_GRAD, TRAINING_STEP_RESUMABLE, 1)
            changed = True
        elif TRAINING_STEP_ORIGINAL in text:
            text = text.replace(TRAINING_STEP_ORIGINAL, TRAINING_STEP_RESUMABLE, 1)
            changed = True
        else:
            missing_patterns.append("training_step")

    if VALIDATION_STEP_RESUMABLE not in text:
        if VALIDATION_STEP_ORIGINAL in text:
            text = text.replace(VALIDATION_STEP_ORIGINAL, VALIDATION_STEP_RESUMABLE, 1)
            changed = True
        else:
            missing_patterns.append("validation_step")

    if missing_patterns:
        record["status"] = "pattern_missing"
        record["missing_patterns"] = missing_patterns
        return record

    if changed:
        path.write_text(text, encoding="utf-8")
        record["status"] = "patched"
    else:
        record["status"] = "already_patched"
    return record


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Source Patch",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Status: `{payload['status']}`",
        f"Source root: `{payload['source_root']}`",
        "",
        "## Purpose",
        "",
        "Apply explicit `weights_only=False` to trusted local Open3DSG checkpoint/feature loads required by PyTorch 2.6+, enable env-controlled lazy dataset loading to avoid full-train preload OOM, and make feature dumping resumable before expensive forward passes.",
        "",
        "## Records",
        "",
    ]
    for record in payload["records"]:
        lines.append(f"- `{record['file']}`: `{record['status']}`")
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    source_root = resolve(repo_root, args.source_root).resolve()
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = [apply_replacement(source_root, *replacement) for replacement in REPLACEMENTS]
    records.append(apply_trainer_feature_dump_patch(source_root))
    records.append(apply_open_dataset_lazy_patch(source_root))
    blockers = [
        f"{record['file']}:{record['status']}"
        for record in records
        if record["status"] in {"missing_file", "pattern_missing"}
    ]
    status = "ready" if not blockers else "blocked"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_root": relpath(repo_root, source_root),
        "records": records,
        "blockers": blockers,
        "trust_boundary": "The patched loads target local Open3DSG model checkpoints/features staged for this Docker reproduction.",
    }
    write_json(out_dir / "manifest.json", payload)
    (out_dir / "report.md").write_text(render_report(payload), encoding="utf-8")
    print(json.dumps({"status": status, "blockers": blockers}, sort_keys=True))
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
