# Support/Contact Applicability Routing

This experiment evaluates two parameter-free ways to leave support/contact
uncorrected while applying relation-algebra-constrained compatibility to
proximity and vertical relations. Selection is made on the 117-scan internal
development split; all fixed conditions are then reported on the 157-scan
official 3DSSG validation split for VL-SAT, Open3DSG, and SGFN.

Run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm support_contact_routing
```

Compact results are written to `evaluation/`.
