# Candidate-Pool Oracle Recall

This folder quantifies how much exact-match Recall can be recovered by
re-ranking the fixed candidate pool. It reports:

- candidate-pool ground-truth coverage
- an unconstrained perfect-ranking oracle
- an oracle that preserves source top-\(K\) family counts
- an active-route oracle that also fixes the selected support/contact
  subsequence

The evaluation consumes only the pseudonymized row bundle from
`row_reproduction_v1`.

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_candidate_oracle
```

The oracle is a diagnostic upper bound. It does not change the active method
or claim that RelCompat3D generates relations absent from the candidate pool.
