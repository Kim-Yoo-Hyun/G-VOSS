"""Minimal pytictoc-compatible timer used by the official SGFN dataloader."""

from __future__ import annotations

import time


class TicToc:
    def __init__(self) -> None:
        self._started = time.perf_counter()

    def tic(self) -> None:
        self._started = time.perf_counter()

    def tocvalue(self) -> float:
        return time.perf_counter() - self._started

