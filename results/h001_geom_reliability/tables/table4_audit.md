# Table 4 Audit And Visual Sanity Check

| source | status | rows | metric | value | note |
| --- | --- | --- | --- | --- | --- |
| structured_audit | ready | 250 | strict invalid-only precision | 0.7133 | non-independent structured audit |
| structured_audit | ready | 250 | quality-issue precision | 0.8933 | invalid, too coarse, scan-missing, or annotation-noise labels |
| visual_spotcheck | ready_sanity_pass | 50 | target-bucket quality-issue rate | 0.9333 | reduced 50-row visual sanity check |
| visual_spotcheck | ready_sanity_pass | 50 | target-bucket contradiction rate | 0.0333 | valid/verifier-error contradiction among target buckets |
| visual_spotcheck | ready_sanity_pass | 50 | private-reference exact match rate | 1.0000 | provenance caveat: Codex transcribed reviewer-confirmed labels |
