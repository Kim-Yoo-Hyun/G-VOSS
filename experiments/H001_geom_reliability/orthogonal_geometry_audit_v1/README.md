# Orthogonal Geometry Audit v1

This folder owns the frozen non-human construct-validity audit for H001. The
primary audit covers proximity and relative-vertical predictions only. It reads
instance vertices and triangle faces from the raw annotated PLY files and never
uses the OBB measurements, compatibility score, source score, or existing
verifier status when assigning audit labels.

`protocol.json` was frozen before execution. `evaluation/` is generated only by
the Docker service `orthogonal_geometry_audit`; the runner records train-only
thresholds, point/mesh/consensus metrics at every reported K, scan-cluster paired
intervals, coverage, synthetic-intervention results, and a checksummed manifest.

The audit can reduce the OBB-rule circularity concern, but it is not a human
reference and does not establish physical truth beyond the reconstructed 3RScan
surface.

## Completed result

The final Docker run completed with exit `0`; all 17 manifest validations pass.
It reads 974/974 training scans containing an audit-family positive and all
157/157 validation scans. Main-scope Recall exactly matches the promoted
public/full comparator artifact at every K.

At K=50, strict-consensus Violation changes by
`-.0210 [-.0242,-.0181]` on VL-SAT, `-.4113 [-.4284,-.3937]` on Open3DSG,
and `-.0343 [-.0392,-.0300]` on SGFN. Supported-status coverage is
`.9551/.9823/.9576`; decided binary coverage is `.7099/.8375/.7992` because
point/mesh disagreement remains uncertain. K=100 is also negative with paired
scan-cluster intervals below zero for all three predictors. The full five-K
point, mesh, and consensus tables are in `evaluation/summary.md`.

Frozen compatibility responds monotonically in all 512 proximity and 512
vertical synthetic cases. Raw point/mesh measurements are 96.3%/94.7%
monotone for proximity translations and 100%/100% for vertical translations.

Final execution log and exit file:

- `logs/h001_orthogonal_geometry_audit_20260717_213229.log`
- `logs/h001_orthogonal_geometry_audit_20260717_213229.status`

The preceding `212626` execution was rejected before promotion because its
Recall report used the 11,254-label full ontology rather than the protocol's
3,972-label paper scope. The corrected run recomputed every surface and did not
change the frozen protocol, thresholds, rankings, or audit-status rules.
