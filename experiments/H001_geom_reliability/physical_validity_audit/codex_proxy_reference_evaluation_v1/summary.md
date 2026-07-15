# Codex Blind Proxy Audit

Status: `completed_nonhuman_proxy_only`

This analysis is intentionally excluded from the submission manuscript.

## Verifier--proxy construct agreement

- Decidable rows: 282 / 390
- Design-weighted accuracy: 0.7306 (scan-bootstrap 95% CI [0.6132669408718814, 0.858315103026092])
- Design-weighted kappa: 0.4665
- Invalid precision / recall / F1: 1.0000 / 0.4713 / 0.6407

## Design-weighted proxy Violation@K

| Source | Method | K | Proxy violation | Resolution coverage | Resolved / sampled |
| --- | --- | ---: | ---: | ---: | ---: |
| vlsat_closed_set | semantic_only | 10 | 0.0517 | 0.8894 | 39 / 45 |
| vlsat_closed_set | semantic_only | 50 | 0.1978 | 0.7176 | 112 / 140 |
| vlsat_closed_set | semantic_only | 100 | 0.3599 | 0.7203 | 179 / 228 |
| vlsat_closed_set | family_conditional_risk | 10 | 0.0493 | 0.8936 | 38 / 44 |
| vlsat_closed_set | family_conditional_risk | 50 | 0.1622 | 0.7474 | 96 / 122 |
| vlsat_closed_set | family_conditional_risk | 100 | 0.2888 | 0.7179 | 147 / 197 |
| open3dsg_ov_recovery | semantic_only | 10 | 0.6432 | 0.8356 | 46 / 53 |
| open3dsg_ov_recovery | semantic_only | 50 | 0.6308 | 0.7816 | 136 / 165 |
| open3dsg_ov_recovery | semantic_only | 100 | 0.5802 | 0.8047 | 196 / 236 |
| open3dsg_ov_recovery | family_conditional_risk | 10 | 0.1934 | 0.7043 | 30 / 41 |
| open3dsg_ov_recovery | family_conditional_risk | 50 | 0.2266 | 0.7920 | 106 / 134 |
| open3dsg_ov_recovery | family_conditional_risk | 100 | 0.2827 | 0.7414 | 161 / 215 |

These are design-weighted Codex proxy-reference estimates, not human measurements.
