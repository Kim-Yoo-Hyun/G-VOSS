# RelCompat3D Source

`src/geocalib/` contains the Python entry points included in the verified H001
code-and-data supplement plus the point/mesh audit entry point required by the
current manuscript and its minimal calibration-export dependency. The active
tree is intentionally limited to fitting,
family-aware evaluation, matched comparators, controls, scan-level intervals,
point/mesh audits, runtime measurement, transfer evaluation, and candidate
artifact rendering.

Paper-facing executions must use configs/h001/compose.structured.yaml. Do not
install host-only dependencies to establish a paper result.

Superseded source adapters, dataset-preparation utilities, Qwen/FROSS/H002
extensions, and development-only review scripts are preserved in the ignored
local archive rather than the public submission tree.
