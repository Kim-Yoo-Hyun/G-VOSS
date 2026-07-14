# Attachment Subtype v2 Development Diagnostic

Status: `attachment_subtype_v2_development_diagnostic_ready`

This is a retrospective development diagnostic. It does not update the
RelCompat3D main claim and is not an untouched or confirmatory result.

## Fit

- `attached to` train pos/neg: 67/90; dev pos/neg: 15/26; dev AUROC/Brier: 1.0000/0.0000
- `hanging on` train pos/neg: 21/50; dev pos/neg: 12/30; dev AUROC/Brier: 1.0000/0.0002

## Official-validation diagnostic

Scored rows: 190722; fitted direct-route rows: 74433; neutral rows: 116289.
The gate requires paired-bootstrap dR CI lower bound >= -0.01 and dV CI upper bound < 0.

| Source | K | Source R/V | `selective_family_product` R/V | dR | dV | Gate |
|---|---:|---:|---:|---:|---:|:---:|
| open3dsg_ov | 10 | 0.2149/0.3174 | 0.2386/0.3741 | +0.0238 | +0.0567 | fail |
| open3dsg_ov | 50 | 0.4917/0.3343 | 0.5568/0.3444 | +0.0651 | +0.0101 | fail |
| open3dsg_ov | 100 | 0.7738/0.3163 | 0.9101/0.3278 | +0.1364 | +0.0115 | fail |
| vlsat_closed_set | 10 | 0.9336/0.1265 | 0.9344/0.1332 | +0.0008 | +0.0068 | fail |
| vlsat_closed_set | 50 | 0.9959/0.1626 | 0.9959/0.1761 | +0.0000 | +0.0136 | fail |
| vlsat_closed_set | 100 | 1.0000/0.2176 | 1.0000/0.2270 | +0.0000 | +0.0094 | fail |

The Violation diagnostic still uses the legacy attachment policy and
therefore does not establish independent construct validity. A promotable
v2 result requires the frozen mechanism review and a rebuilt target/verifier
contract before model and source-evaluation hashes are locked.
