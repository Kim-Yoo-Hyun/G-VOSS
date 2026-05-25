# Figure 3 Geometry Panel Generation

Status: `figure3_geometry_panels_generated_verified`

Generated outputs:

- `figure3_geometry_panels.svg`: point-cloud geometry panels for the locked Figure 3 cases.
- `figure3_geometry_cases.json`: case-level source rows, measurements, and object geometry stats.
- `figure3_geometry_manifest.json`: generation and validation manifest.

Claim boundary:

- These panels are qualitative reviewer-defense / failure-mechanism examples.
- They are not a representative human visual audit, not a new metric, and not broad open-vocabulary evidence.
- They preserve the same locked Open3DSG case IDs used by `figure3_failure_cases.svg`.

Reproduction command:

```bash
docker run --rm --user "$(id -u):$(id -g)" -v /home/yoohyun/research:/workspace -w /workspace h001-open3dsg-repro:cu128 bash -lc 'python paper/scripts/render_figure3_geometry_panels.py'
```

Validation:

- Expected locked cases: `open3dsg_case_001, open3dsg_case_005, open3dsg_case_010, open3dsg_case_007`
- Rendered cases: `open3dsg_case_001, open3dsg_case_005, open3dsg_case_010, open3dsg_case_007`
- Missing cases: `none`
- Output SVG exists: `True`
- Output case JSON exists: `True`
