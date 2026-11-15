"""Causality check used across the project. A feature is causal if its value at
time t does not change when later data is removed. Any model feature must pass."""
from __future__ import annotations
import numpy as np
import pandas as pd


def assert_causal(fn, data, checkpoints=(120, 300, 500), atol=1e-9):
    """fn maps a DataFrame/Series to a same-indexed Series/DataFrame of features."""
    full = fn(data)
    for t in checkpoints:
        if t >= len(data):
            continue
        part = fn(data.iloc[: t + 1])
        a = np.asarray(part.iloc[-1], dtype=float)
        b = np.asarray(full.iloc[t], dtype=float)
        mask = ~(np.isnan(a) & np.isnan(b))
        if not np.allclose(a[mask], b[mask], atol=atol, equal_nan=True):
            raise AssertionError(f"look-ahead at row {t}: value changes when later data is removed")
