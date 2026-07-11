#!/usr/bin/env python3
"""Run the pre-frozen H001 six-condition metrics for the fresh 3DSSG source."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import run_reviewer_extension_metrics as base


LOCKED_CONDITIONS = (
    "semantic_only",
    "family_conditional_risk",
    "pooled_calibration",
    "geometry_only_family",
    "rank_average_fusion",
    "reciprocal_rank_fusion",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260710)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base.CONDITIONS = LOCKED_CONDITIONS
    base.SOURCE_SPECS = {
        "3dssg_official_full_l160_confirmatory": {
            "predictions": "experiments/H001_geom_reliability/sources/3dssg_full_l160/adapter/predictions.jsonl",
            "verification": "experiments/H001_geom_reliability/sources/3dssg_full_l160/geometry/verification.jsonl",
            "ground_truth": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
        }
    }
    sys.argv = [
        "run_reviewer_extension_metrics.py",
        "--repo-root",
        str(args.repo_root),
        "--out",
        str(args.out),
        "--n-bootstrap",
        str(args.n_bootstrap),
        "--seed",
        str(args.seed),
    ]
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
