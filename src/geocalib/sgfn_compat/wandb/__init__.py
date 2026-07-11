"""Non-network wandb import stub; SGFN confirmatory inference disables logging."""

from __future__ import annotations


config = {}


def init(*args, **kwargs):  # pragma: no cover - logging is disabled by config.
    raise RuntimeError("wandb_disabled_for_sgfn_confirmatory_inference")

