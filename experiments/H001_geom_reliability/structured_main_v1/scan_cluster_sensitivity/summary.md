# Scan-Cluster Bootstrap Sensitivity

Status: `completed`

The promoted rankings and point estimates are unchanged. This sensitivity resamples 157 scans with replacement and carries every relation context from each sampled scan together.

| Source | dRecall@100 (95% scan-cluster CI) | dVerifier-V@100 (95% scan-cluster CI) |
| --- | ---: | ---: |
| VL-SAT | +0.0053 [+0.0000, +0.0119] | -0.0151 [-0.0171, -0.0135] |
| Open3DSG | +0.0894 [+0.0646, +0.1119] | -0.0903 [-0.0959, -0.0846] |
| SGFN | +0.0184 [+0.0137, +0.0230] | -0.0258 [-0.0285, -0.0233] |

At K=100, no Recall interval crosses below zero (the VL-SAT lower bound reaches zero), and all verifier-V intervals remain below zero. This is a dependence sensitivity, not a new score-selection result.
