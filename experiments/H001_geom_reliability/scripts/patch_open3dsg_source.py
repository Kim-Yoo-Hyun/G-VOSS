#!/usr/bin/env python3
"""Apply H001 Open3DSG source compatibility patches before Docker execution."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_source_patch_v10"

OPEN_DATASET_NUMPY_IMPORT = "import numpy as np\n"

OPEN_DATASET_NUMPY_PICKLE_COMPAT = """import numpy as np
import importlib
import sys


def _h001_install_numpy_core_pickle_aliases():
    try:
        sys.modules.setdefault("numpy._core", importlib.import_module("numpy.core"))
        for name in ("multiarray", "numeric", "fromnumeric", "umath", "_multiarray_umath"):
            try:
                sys.modules.setdefault(f"numpy._core.{name}", importlib.import_module(f"numpy.core.{name}"))
            except Exception:
                pass
    except Exception:
        pass


_h001_install_numpy_core_pickle_aliases()
"""

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

FEATURE_SHARD_HELPERS = """    def _h001_feature_id_from_scene_item(self, scene_item):
        if isinstance(scene_item, tuple) and len(scene_item) == 2:
            _, relationship = scene_item
            scan = relationship.get("scan")
            split = relationship.get("split")
            if scan is None or split is None:
                return None
            return f"{scan}-{str(hex(int(split)))[-1]}"
        scan_id = getattr(scene_item, "scan_id", None)
        if scan_id is None and isinstance(scene_item, dict):
            scan_id = scene_item.get("scan_id")
        return None if scan_id is None else str(scan_id)

    def _h001_scene_item_preprocessed_exists(self, scene_item):
        if not isinstance(scene_item, tuple) or len(scene_item) != 2:
            return True
        dataset_name, relationship = scene_item
        scan = relationship.get("scan")
        split = relationship.get("split")
        if scan is None or split is None:
            return False
        base = CONF.PATH.R3SCAN if dataset_name in {"r3scan", "3rscan"} else CONF.PATH.SCANNET
        path = os.path.join(base, "preprocessed", str(scan), f"data_dict_{str(hex(int(split)))[-1]}.pkl")
        return os.path.exists(path)

    def _h001_feature_outputs_exist_by_id(self, feature_id):
        if not feature_id:
            return False
        return all(os.path.exists(pth) for pth in self._feature_output_paths(feature_id + ".pt", path=self.clip_path))

    def _h001_apply_feature_dump_shard(self, dataset, split_name):
        if not self.hparams.get('dump_features'):
            return
        if os.environ.get("OPEN3DSG_FEATURE_SHARD_ONLY_MISSING", "0") != "1":
            return
        scene_data = list(getattr(dataset, "scene_data", []))
        max_new = int(os.environ.get("OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS", "0"))
        kept = []
        complete = 0
        missing = 0
        skipped_missing_preprocessed = 0
        unparsable = 0
        for scene_item in scene_data:
            feature_id = self._h001_feature_id_from_scene_item(scene_item)
            if feature_id is None:
                unparsable += 1
                kept.append(scene_item)
                continue
            if not self._h001_scene_item_preprocessed_exists(scene_item):
                skipped_missing_preprocessed += 1
                continue
            if self._h001_feature_outputs_exist_by_id(feature_id):
                complete += 1
                continue
            missing += 1
            if max_new > 0 and len(kept) >= max_new:
                continue
            kept.append(scene_item)
        dataset.scene_data = kept
        print(
            "H001 feature shard "
            f"split={split_name} original={len(scene_data)} complete={complete} "
            f"missing={missing} selected={len(kept)} max_new={max_new} "
            f"skipped_missing_preprocessed={skipped_missing_preprocessed} "
            f"unparsable={unparsable} clip_path={self.clip_path}"
        )

"""

TEST_REL_MAPPER_ORIGINAL = """        elif stage == 'test':
            self.rel_mapper = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True).cuda()
            if self.hparams.get('test_scans_3rscan'):
"""

TEST_REL_MAPPER_FEATURE_DUMP_AWARE = """        elif stage == 'test':
            if self.hparams.get('dump_features'):
                self.rel_mapper = None
            else:
                self.rel_mapper = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True).cuda()
            if self.hparams.get('test_scans_3rscan'):
"""

TEST_DATASET_BLOCK_ORIGINAL = """            self.val_dataset = Open2D3DSGDataset(
                relationships_R3SCAN=D3SSG_VAL if not self.hparams.get('test_scans_3rscan') else D3SSG_TEST,
                relationships_scannet=SCANNET_VAL,
                openseg=self.hparams['clip_model'] == 'OpenSeg',
                img_dim=img_dim,
                rel_img_dim=rel_img_dim,
                top_k_frames=self.hparams['top_k_frames'],
                scales=self.hparams['scales'],
                mini=self.hparams['mini_dataset'],
                load_features=self.hparams.get('load_features', None),
                blip=self.hparams.get('blip', False),
                llava=self.hparams.get('llava', False),
                half=self.hparams.get('quick_eval', False)
            )
"""

TEST_DATASET_BLOCK_SHARDED = """            self.val_dataset = Open2D3DSGDataset(
                relationships_R3SCAN=D3SSG_VAL if not self.hparams.get('test_scans_3rscan') else D3SSG_TEST,
                relationships_scannet=SCANNET_VAL,
                openseg=self.hparams['clip_model'] == 'OpenSeg',
                img_dim=img_dim,
                rel_img_dim=rel_img_dim,
                top_k_frames=self.hparams['top_k_frames'],
                scales=self.hparams['scales'],
                mini=self.hparams['mini_dataset'],
                load_features=self.hparams.get('load_features', None),
                blip=self.hparams.get('blip', False),
                llava=self.hparams.get('llava', False),
                half=self.hparams.get('quick_eval', False)
            )
            self._h001_apply_feature_dump_shard(self.val_dataset, "test_val")
"""

ON_TEST_EPOCH_START_ORIGINAL_TAIL = """        self.start_t = time.time()

        self.rel_vocab = F.normalize(torch.from_numpy(self.rel_mapper.encode(self.pred_class_dict)), dim=-1).cuda()
        self.vis_dump_dir = CONF.PATH.BASE+'/vis_graphs/'+self.hparams['run_name'] + f"_{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
"""

ON_TEST_EPOCH_START_FEATURE_DUMP_RETURN = """        self.start_t = time.time()

        if self.hparams.get('dump_features'):
            return

        self.rel_vocab = F.normalize(torch.from_numpy(self.rel_mapper.encode(self.pred_class_dict)), dim=-1).cuda()
        self.vis_dump_dir = CONF.PATH.BASE+'/vis_graphs/'+self.hparams['run_name'] + f"_{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
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

TEST_STEP_ORIGINAL = """    def test_step(self, data_dict, batch_ixd):
        assert data_dict['objects_id'].shape[0] == 1

        pred_dict = self._forward(data_dict)
        if self.hparams.get('dump_features'):
            self._dump_features(pred_dict, data_dict["objects_id"].size(0), path=self.clip_path)
            return
"""

TEST_STEP_RESUMABLE = """    def test_step(self, data_dict, batch_ixd):
        assert data_dict['objects_id'].shape[0] == 1

        if self.hparams.get('dump_features') and self._feature_outputs_exist(data_dict, data_dict["objects_id"].size(0), path=self.clip_path):
            return

        pred_dict = self._forward(data_dict)
        if self.hparams.get('dump_features'):
            self._dump_features(pred_dict, data_dict["objects_id"].size(0), path=self.clip_path)
            return
"""

RAW_DUMP_HELPERS = """    def _h001_json_value(self, value):
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, np.generic):
            value = value.item()
        return value

    def _h001_int(self, value):
        return int(self._h001_json_value(value))

    def _h001_scan_parts(self, scan_value):
        if isinstance(scan_value, (list, tuple)) and scan_value:
            scan_value = scan_value[0]
        raw_scan_id = str(scan_value)
        if "-" in raw_scan_id:
            scan_id, split = raw_scan_id.rsplit("-", 1)
            if split.isdigit():
                return scan_id, int(split), raw_scan_id
        return raw_scan_id, None, raw_scan_id

    def _h001_label(self, id2name, object_id):
        source = id2name
        if isinstance(source, (list, tuple)) and len(source) == 1:
            source = source[0]
        if isinstance(source, dict):
            for key in (object_id, str(object_id)):
                if key not in source:
                    continue
                value = source[key]
                if isinstance(value, (list, tuple)):
                    value = value[0] if value else None
                return None if value is None else str(value)
        return None

    def _h001_export_raw_dump(self, outputs):
        raw_dump_jsonl = os.environ.get("OPEN3DSG_RAW_DUMP_JSONL")
        if not raw_dump_jsonl:
            return
        os.makedirs(os.path.dirname(raw_dump_jsonl), exist_ok=True)
        baseline_run_id = os.environ.get("OPEN3DSG_BASELINE_RUN_ID", self.hparams.get("run_name", "open3dsg"))
        checkpoint_path = os.environ.get("OPEN3DSG_CHECKPOINT")
        model_source_stage = os.environ.get("OPEN3DSG_MODEL_SOURCE_STAGE", "open3dsg")
        rows_written = 0
        with open(raw_dump_jsonl, "w", encoding="utf-8") as handle:
            for eval_dict in outputs:
                scan_values = eval_dict.get("scan_id", [])
                batch_size = len(scan_values) if isinstance(scan_values, (list, tuple)) else 1
                for bidx in range(batch_size):
                    scan_value = scan_values[bidx] if isinstance(scan_values, (list, tuple)) else scan_values
                    scan_id, subset_split_id, raw_scan_id = self._h001_scan_parts(scan_value)
                    subgraph_id = f"{scan_id}_{subset_split_id}" if subset_split_id is not None else raw_scan_id
                    object_count = self._h001_int(eval_dict["objects_count"][bidx])
                    relation_count = self._h001_int(eval_dict["predicate_count"][bidx])
                    object_ids = [self._h001_int(value) for value in eval_dict["objects_id"][bidx][:object_count].tolist()]
                    id2name = eval_dict.get("id2name")
                    if isinstance(id2name, (list, tuple)) and len(id2name) > bidx:
                        id2name = id2name[bidx]
                    edges = eval_dict["edges"][bidx][:relation_count].tolist()
                    score_tensor = eval_dict["predicates_mapped_probs"][bidx][:relation_count]
                    if hasattr(score_tensor, "detach"):
                        scores = score_tensor.detach().cpu().float().numpy()
                    else:
                        scores = np.array(score_tensor, dtype=float)
                    for edge_index, edge in enumerate(edges):
                        subject_node_index = int(edge[0])
                        object_node_index = int(edge[1])
                        if subject_node_index >= len(object_ids) or object_node_index >= len(object_ids):
                            continue
                        subject_id = object_ids[subject_node_index]
                        object_id = object_ids[object_node_index]
                        predicate_scores = []
                        score_count = min(len(self.pred_class_dict_orig), scores.shape[-1])
                        for predicate_index in range(score_count):
                            score = float(scores[edge_index][predicate_index])
                            if not np.isfinite(score):
                                continue
                            predicate_scores.append({
                                "predicate_label": self.pred_class_dict_orig[predicate_index],
                                "score": score,
                                "score_type": "open3dsg_relation_score",
                                "raw_3dssg_predicate_id": predicate_index,
                                "open3dsg_predicate_index": predicate_index,
                                "predicate_vocab": "3DSSG_subset_relationships",
                            })
                        record = {
                            "schema_version": "h001_open3dsg_raw_dump_v1",
                            "record_type": "open3dsg_raw_prediction",
                            "baseline_run_id": baseline_run_id,
                            "checkpoint_path": checkpoint_path,
                            "model_source_stage": model_source_stage,
                            "scan_id": scan_id,
                            "subset_split_id": subset_split_id,
                            "subgraph_id": subgraph_id,
                            "raw_scan_id": raw_scan_id,
                            "edge_index": rows_written,
                            "edge": {
                                "subject_id": subject_id,
                                "object_id": object_id,
                                "subject_node_index": subject_node_index,
                                "object_node_index": object_node_index,
                                "subject_label": self._h001_label(id2name, subject_id),
                                "object_label": self._h001_label(id2name, object_id),
                            },
                            "predicate_scores": predicate_scores,
                        }
                        handle.write(json.dumps(record, sort_keys=True))
                        handle.write("\\n")
                        rows_written += 1
        print(f"H001 raw dump wrote {rows_written} rows to {raw_dump_jsonl}")

"""

ON_TEST_EPOCH_END_MARKER = """    @torch.no_grad()
    def on_test_epoch_end(self,):
        if not self.hparams.get('dataset') == '3rscan':
            return
        outputs = self.test_step_outputs
"""

ON_TEST_EPOCH_END_RAW_DUMP = """    @torch.no_grad()
    def on_test_epoch_end(self,):
        if not self.hparams.get('dataset') == '3rscan':
            return
        outputs = self.test_step_outputs
        self._h001_export_raw_dump(outputs)
"""

ON_TEST_EPOCH_END_RAW_DUMP_FEATURE_RETURN = """    @torch.no_grad()
    def on_test_epoch_end(self,):
        if not self.hparams.get('dataset') == '3rscan':
            return
        outputs = self.test_step_outputs
        self._h001_export_raw_dump(outputs)
        if self.hparams.get('dump_features'):
            return
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

BLIP_ENCODE_ORIGINAL = """    @torch.no_grad()
    def blip_encode_images(self, rel_imgs):
        rel_images_tensor = np.array(rel_imgs)
        rel_images_tensor.shape
        with torch.no_grad():
            inputs = self.PROCESSOR(images=rel_images_tensor.flatten().tolist(), text=None, return_tensors="pt").to(self.clip_device)

            rel_embeds = self.BLIP.embedd_image(inputs['pixel_values']).view((*rel_images_tensor.shape, 257, 1408))
        return rel_embeds
"""

BLIP_ENCODE_CHUNKED = """    @torch.no_grad()
    def blip_encode_images(self, rel_imgs):
        rel_images_tensor = np.array(rel_imgs)
        rel_images_tensor.shape
        flat_images = rel_images_tensor.flatten().tolist()
        chunk_size = max(1, int(os.environ.get("OPEN3DSG_BLIP_EMBED_CHUNK_SIZE", "4")))
        rel_embeds = []
        with torch.no_grad():
            for start in range(0, len(flat_images), chunk_size):
                inputs = self.PROCESSOR(images=flat_images[start:start + chunk_size], text=None, return_tensors="pt").to(self.clip_device)
                rel_embeds.append(self.BLIP.embedd_image(inputs['pixel_values']).detach())
                torch.cuda.empty_cache()
            rel_embeds = torch.cat(rel_embeds, dim=0).view((*rel_images_tensor.shape, 257, 1408))
        return rel_embeds
"""

BLIP_PROJECTOR_ORIGINAL = """            pred_encoding_pos = pred_encoding.view(-1, 1408).unsqueeze(1)+self.blip_pos_encoding
            projector_outputs = self.blip_projector(inputs_embeds=pred_encoding_pos,
                                                    output_attentions=False,
                                                    output_hidden_states=False,
                                                    return_dict=False,)
            last_hidden_state = projector_outputs[0]
            last_hidden_state = self.blip_layernorm(last_hidden_state)
            pred_encoding = last_hidden_state.view((*pred_encoding.shape[:2], *last_hidden_state.shape[1:]))
"""

BLIP_PROJECTOR_CHUNKED = """            pred_encoding_pos = pred_encoding.view(-1, 1408).unsqueeze(1)+self.blip_pos_encoding
            projector_chunk_size = max(1, int(os.environ.get("OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE", "16")))
            projector_hidden_states = []
            for start in range(0, pred_encoding_pos.size(0), projector_chunk_size):
                projector_outputs = self.blip_projector(inputs_embeds=pred_encoding_pos[start:start + projector_chunk_size],
                                                        output_attentions=False,
                                                        output_hidden_states=False,
                                                        return_dict=False,)
                projector_hidden_states.append(projector_outputs[0])
            last_hidden_state = torch.cat(projector_hidden_states, dim=0)
            last_hidden_state = self.blip_layernorm(last_hidden_state)
            pred_encoding = last_hidden_state.view((*pred_encoding.shape[:2], *last_hidden_state.shape[1:]))
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


def apply_open_dataset_numpy_pickle_compat_patch(source_root: Path) -> dict[str, Any]:
    rel_file = "open3dsg/data/open_dataset.py"
    path = source_root / rel_file
    record: dict[str, Any] = {"file": rel_file, "patch": "numpy_core_pickle_compat"}
    if not path.is_file():
        record["status"] = "missing_file"
        return record

    text = path.read_text(encoding="utf-8")
    if "_h001_install_numpy_core_pickle_aliases" in text:
        record["status"] = "already_patched"
        return record
    if OPEN_DATASET_NUMPY_IMPORT not in text:
        record["status"] = "pattern_missing"
        record["missing_pattern"] = "numpy_import"
        return record

    path.write_text(text.replace(OPEN_DATASET_NUMPY_IMPORT, OPEN_DATASET_NUMPY_PICKLE_COMPAT, 1), encoding="utf-8")
    record["status"] = "patched"
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

    if FEATURE_SHARD_HELPERS not in text:
        marker = "    def setup(self, stage: str):\n"
        if marker in text:
            text = text.replace(marker, FEATURE_SHARD_HELPERS + marker, 1)
            changed = True
        else:
            missing_patterns.append("setup_marker_for_feature_shard_helpers")

    if TEST_REL_MAPPER_FEATURE_DUMP_AWARE not in text:
        if TEST_REL_MAPPER_ORIGINAL in text:
            text = text.replace(TEST_REL_MAPPER_ORIGINAL, TEST_REL_MAPPER_FEATURE_DUMP_AWARE, 1)
            changed = True
        else:
            missing_patterns.append("test_rel_mapper_block")

    if TEST_DATASET_BLOCK_SHARDED not in text:
        if TEST_DATASET_BLOCK_ORIGINAL in text:
            text = text.replace(TEST_DATASET_BLOCK_ORIGINAL, TEST_DATASET_BLOCK_SHARDED, 1)
            changed = True
        else:
            missing_patterns.append("test_dataset_block")

    if ON_TEST_EPOCH_START_FEATURE_DUMP_RETURN not in text:
        if ON_TEST_EPOCH_START_ORIGINAL_TAIL in text:
            text = text.replace(ON_TEST_EPOCH_START_ORIGINAL_TAIL, ON_TEST_EPOCH_START_FEATURE_DUMP_RETURN, 1)
            changed = True
        else:
            missing_patterns.append("on_test_epoch_start_feature_dump_return")

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

    if TEST_STEP_RESUMABLE not in text:
        if TEST_STEP_ORIGINAL in text:
            text = text.replace(TEST_STEP_ORIGINAL, TEST_STEP_RESUMABLE, 1)
            changed = True
        else:
            missing_patterns.append("test_step")

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


def apply_trainer_raw_dump_patch(source_root: Path) -> dict[str, Any]:
    rel_file = "open3dsg/scripts/trainer.py"
    path = source_root / rel_file
    record: dict[str, Any] = {"file": rel_file, "patch": "h001_raw_dump_export"}
    if not path.is_file():
        record["status"] = "missing_file"
        return record

    text = path.read_text(encoding="utf-8")
    changed = False
    missing_patterns: list[str] = []

    if RAW_DUMP_HELPERS not in text:
        if ON_TEST_EPOCH_END_MARKER in text:
            text = text.replace(ON_TEST_EPOCH_END_MARKER, RAW_DUMP_HELPERS + ON_TEST_EPOCH_END_MARKER, 1)
            changed = True
        elif ON_TEST_EPOCH_END_RAW_DUMP in text:
            text = text.replace(ON_TEST_EPOCH_END_RAW_DUMP, RAW_DUMP_HELPERS + ON_TEST_EPOCH_END_RAW_DUMP, 1)
            changed = True
        else:
            missing_patterns.append("on_test_epoch_end_marker")

    if ON_TEST_EPOCH_END_RAW_DUMP not in text:
        if ON_TEST_EPOCH_END_MARKER in text:
            text = text.replace(ON_TEST_EPOCH_END_MARKER, ON_TEST_EPOCH_END_RAW_DUMP, 1)
            changed = True
        else:
            missing_patterns.append("on_test_epoch_end_call")

    if ON_TEST_EPOCH_END_RAW_DUMP_FEATURE_RETURN not in text:
        if ON_TEST_EPOCH_END_RAW_DUMP in text:
            text = text.replace(ON_TEST_EPOCH_END_RAW_DUMP, ON_TEST_EPOCH_END_RAW_DUMP_FEATURE_RETURN, 1)
            changed = True
        else:
            missing_patterns.append("on_test_epoch_end_dump_feature_return")

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


def apply_sgpn_blip_chunk_patch(source_root: Path) -> dict[str, Any]:
    rel_file = "open3dsg/models/sgpn.py"
    path = source_root / rel_file
    record: dict[str, Any] = {"file": rel_file, "patch": "chunked_blip_embedding"}
    if not path.is_file():
        record["status"] = "missing_file"
        return record

    text = path.read_text(encoding="utf-8")
    if BLIP_ENCODE_CHUNKED in text:
        record["status"] = "already_patched"
        return record
    if BLIP_ENCODE_ORIGINAL not in text:
        record["status"] = "pattern_missing"
        record["missing_pattern"] = "blip_encode_images"
        return record

    path.write_text(text.replace(BLIP_ENCODE_ORIGINAL, BLIP_ENCODE_CHUNKED, 1), encoding="utf-8")
    record["status"] = "patched"
    return record


def apply_sgpn_blip_projector_chunk_patch(source_root: Path) -> dict[str, Any]:
    rel_file = "open3dsg/models/sgpn.py"
    path = source_root / rel_file
    record: dict[str, Any] = {"file": rel_file, "patch": "chunked_blip_projector"}
    if not path.is_file():
        record["status"] = "missing_file"
        return record

    text = path.read_text(encoding="utf-8")
    if BLIP_PROJECTOR_CHUNKED in text:
        record["status"] = "already_patched"
        return record
    if BLIP_PROJECTOR_ORIGINAL not in text:
        record["status"] = "pattern_missing"
        record["missing_pattern"] = "blip_projector_forward"
        return record

    path.write_text(text.replace(BLIP_PROJECTOR_ORIGINAL, BLIP_PROJECTOR_CHUNKED, 1), encoding="utf-8")
    record["status"] = "patched"
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
        "Apply explicit `weights_only=False` to trusted local Open3DSG checkpoint/feature loads required by PyTorch 2.6+, install a NumPy pickle compatibility alias for staged preprocess artifacts, enable env-controlled lazy dataset loading to avoid full-train preload OOM, make train/validation/test feature dumping resumable before expensive forward passes, support H001 eval feature-dump sharding over remaining missing ids, skip eval-only relation mapper allocation during feature dumping, keep test-mode feature dumping from falling through into metric evaluation, chunk BLIP image embedding/projector forwards to reduce peak GPU memory, and export H001 identity-preserving raw prediction JSONL during Open3DSG test.",
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
    records.append(apply_open_dataset_numpy_pickle_compat_patch(source_root))
    records.append(apply_trainer_feature_dump_patch(source_root))
    records.append(apply_trainer_raw_dump_patch(source_root))
    records.append(apply_sgpn_blip_chunk_patch(source_root))
    records.append(apply_sgpn_blip_projector_chunk_patch(source_root))
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
