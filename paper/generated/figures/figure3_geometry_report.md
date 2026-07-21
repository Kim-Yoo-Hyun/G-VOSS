# Geometry-Backed Figure Generation

Status: `figure3_geometry_panels_generated_verified`

Generated outputs:

- `figure1_framework.{svg,pdf,png}`: source-backed framework overview.
- `figure3_geometry_panels.{svg,pdf,png}`: point-cloud qualitative panels.
- `teaser_overview.{svg,pdf,png}`: fixed pair-level Top-50 exchange and separately labeled aggregate result for the optional first-page teaser.
- `figure3_geometry_cases.json`: case-level source rows, measurements, and object geometry stats.
- `figure3_geometry_manifest.json`: generation and validation manifest.

Claim boundary:

- The panels illustrate correction mechanisms and an applicability boundary; they are not a representative evaluation sample.
- They preserve the selected Open3DSG case identities and use the corresponding preprocessed point clouds.

Reproduction command:

```bash
docker run --rm --entrypoint bash --user "$(id -u):$(id -g)" -v "$PWD":/workspace -w /workspace h001-geom-reliability:latest -lc 'python paper/scripts/render_figure3_geometry_panels.py'
```

Validation:

- Expected locked cases: `open3dsg_case_001, open3dsg_case_019, open3dsg_case_026`
- Rendered cases: `open3dsg_case_001, open3dsg_case_019, open3dsg_case_026`
- Missing cases: `none`
- Figure 1 PDF exists: `True`
- Figure 3 PDF exists: `True`
- Teaser PDF exists: `True`
- Teaser exchange checks: `{'source_count': 50, 'method_count': 50, 'target_in_source_top50': True, 'target_not_in_method_top50': True, 'promoted_not_in_source_top50': True, 'promoted_in_method_top50': True, 'promoted_status_satisfied': True, 'promoted_exact_label_gt': True, 'removed_not_exact_label_gt': True, 'removed_status_violated': True, 'removed_rank_lock': True, 'promoted_rank_lock': True}`
- Output case JSON exists: `True`
