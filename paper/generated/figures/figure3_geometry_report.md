# Geometry-Backed Figure Generation

Status: `figure3_geometry_panels_generated_verified`

Generated outputs:

- `figure1_framework.{svg,pdf,png}`: source-backed framework overview.
- `figure3_geometry_panels.{svg,pdf,png}`: point-cloud qualitative panels.
- `figure3_geometry_cases.json`: case-level source rows, measurements, and object geometry stats.
- `figure3_geometry_manifest.json`: generation and validation manifest.

Claim boundary:

- The panels illustrate failure mechanisms and are not a representative evaluation sample.
- They preserve the selected Open3DSG case identities and use the corresponding preprocessed point clouds.

Reproduction command:

```bash
docker run --rm --entrypoint bash --user "$(id -u):$(id -g)" -v "$PWD":/workspace -w /workspace h001-geom-reliability:latest -lc 'python paper/scripts/render_figure3_geometry_panels.py'
```

Validation:

- Expected locked cases: `open3dsg_case_001, open3dsg_case_010, open3dsg_case_026`
- Rendered cases: `open3dsg_case_001, open3dsg_case_010, open3dsg_case_026`
- Missing cases: `none`
- Figure 1 PDF exists: `True`
- Figure 3 PDF exists: `True`
- Output case JSON exists: `True`
