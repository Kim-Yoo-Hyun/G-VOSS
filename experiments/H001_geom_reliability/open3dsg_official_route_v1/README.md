# Open3DSG Public-Route Sensitivity

This experiment compares the unmodified public preprocessing route with the
documented 548-context recovery. It reports both the public-pipeline-eligible
533-context denominator and a conservative full-548 denominator with zero
predictions for the 15 public-pipeline drops.

Run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm open3dsg_official_route_sensitivity
```
