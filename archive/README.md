# Local Archive Boundary

The public repository tracks only this index. All other archive contents are
ignored and are not submission artifacts.

## Current Local Snapshot

The 2026-07-22 cleanup snapshot is stored at:

archive/local/pre_submission_20260722/

It preserves:

- the full pre-cleanup H001 experiment workspace;
- H002 experiments and hypothesis material;
- literature notes and downloaded papers;
- superseded source scripts and optional Docker configs;
- historical result mirrors, logs, caches, and venue snapshots;
- prior archive contents moved under previous_archive/.

The snapshot is approximately 23GB and is intended only for local recovery. It
must not be added to the anonymous submission repository or upload bundle.

## Recovery Rule

Restore only the smallest required subtree, document the reason in
docs/reproducibility.md and TODO.md, and rerun the relevant integrity checks.
Moving a file back into the active tree does not automatically promote its
scientific claim or result.
