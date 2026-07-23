# RelCompat3D Source

`src/relcompat3d/` contains the Python entry points included in the verified
RelCompat3D code-and-data supplement. It also includes the point/mesh audit
entry point and the minimal training-row dependency required by the current
manuscript. The active tree is limited to fitting, family-aware evaluation,
matched comparators, controls, scan-level intervals, point/mesh audits, runtime
measurement, transfer evaluation, and paper-artifact rendering.

Paper-facing executions must use
`configs/relcompat3d/compose.structured.yaml`. Do not install host-only
dependencies to establish a paper result.

Superseded source adapters, dataset-preparation utilities, Qwen/FROSS/H002
extensions, and development-only review scripts are preserved in the ignored
local archive rather than the public submission tree.
