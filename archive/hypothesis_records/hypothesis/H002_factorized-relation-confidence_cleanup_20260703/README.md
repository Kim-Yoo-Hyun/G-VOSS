# H002 Cleanup Archive 2026-07-03

This archive stores superseded H002 stage documents, one-off hypothesis tools,
and historical artifact folders moved out of:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/
```

The cleanup keeps the active H002 folder focused on the current paper-facing
claim:

```text
S2_source_x_Ce = normalized_source_score * C_e
```

where `C_e` is computed from `T_e` and `G_e`, and `Z_e` source score is combined
only at the final reranking stage.

## Moved Content

```text
root_files/   historical root-level stage md/yaml files
tools/        historical one-off stage scripts
artifacts/    historical intermediate artifact folders
```

Counts at cleanup time:

```text
moved_root_files = 232
moved_tools_py = 475
moved_artifact_dirs = 210
```

The pre-cleanup H002 README is preserved as:

```text
root_files/README_before_cleanup.md
```

## Kept In Active H002 Folder

Active root files are reduced to current paper-facing owners:

- `README.md`
- `paper_claim_core.md`
- `summary_branch_v2.md`
- `RGA_framework.md`
- `method_contract_v1.md`
- `geometry_evidence_schema_v1.md`
- `compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock.md`

The active `tools/` folder keeps only current paper-claim chain validators and
table-materialization scripts. The actual executable experiment code remains in:

```text
experiments/H002_compatibility_routing/scripts/
```

## Restore Rule

Do not restore a whole archived tree by default. Restore only the specific file
or artifact needed for a concrete diagnostic branch, then record the reason in
the active H002 README or the relevant report.
