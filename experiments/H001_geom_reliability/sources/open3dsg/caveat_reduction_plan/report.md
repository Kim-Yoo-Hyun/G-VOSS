# Open3DSG Caveat-Reduction Plan

Created at: `2026-05-28T08:04:18+00:00`
Status: `open3dsg_caveat_reduction_plan_frozen_no_execution`

## Current Caveats

- current variant: `avg_blip_full_variant`
- H001 covered contexts: `377/388`
- missing preprocessed H001 contexts: `11`
- attachment Open3DSG missing exact-label GT rows: `199`
- attachment missing due to missing H001 contexts: `23`
- attachment missing due to absent Open3DSG candidate pairs: `176`

## Frozen Retry Order

### R1_exact_non_avg_blip_route_retry

- priority: `1`
- goal: Reduce the averaged-BLIP variant caveat for the main Open3DSG source.
- execution policy: Docker/tmux background job only; do not overwrite existing avg-BLIP result artifacts.

### R2_h001_covered_loadable_context_retry_388

- priority: `2`
- goal: Try to reduce the H001 covered-scope caveat from 377/388 to 388/388 contexts.
- execution policy: Target only the 11 missing-preprocessed H001 contexts first, then audit.

### R3_attachment_deferred_G5d_after_open3dsg_decision

- priority: `3`
- goal: Run attachment full-source scoring only after Open3DSG caveat-reduction decisions are resolved or explicitly waived.
- execution policy: No attachment main-claim promotion without explicit final user confirmation.

## Interpretation

Non-avg BLIP success and 388/388 covered-context success would strengthen Open3DSG source credibility.
They do not by themselves make `attachment_deferred_G5d` successful: the 388 retry can only address the missing-preprocessed-context portion, while candidate-pair absence remains a separate denominator/source-universe issue.

## Claim Boundary

- This artifact is a no-execution plan.
- It does not change current AAAI main-claim wording.
- Attachment promotion still requires explicit final user confirmation.
- Any successful retry must regenerate downstream artifacts before paper wording changes.
