"""Health-data analysis with pandas (pure functions, no database access)."""
from datetime import date
from typing import Any, Optional

import numpy as np
import pandas as pd

METRICS = ["systolic", "diastolic", "glucose", "weight_kg", "sleep_hours", "exercise_minutes", "stress_level"]


def record_to_dict(r: Any) -> dict[str, Any]:
    d = {m: getattr(r, m, None) for m in METRICS}
    d["id"] = getattr(r, "id", None)
    d["recorded_at"] = getattr(r, "recorded_at")
    d["notes"] = getattr(r, "notes", None)
    return d


def bmi(weight_kg: Optional[float], height_cm: Optional[float]) -> Optional[float]:
    if not weight_kg or not height_cm:
        return None
    return round(weight_kg / ((height_cm / 100) ** 2), 1)


def age_from_dob(dob: Optional[date], today: Optional[date] = None) -> Optional[int]:
    if not dob:
        return None
    today = today or date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _trend(values: list[float]) -> str:
    n = len(values)
    if n < 3:
        return "not enough data"
    slope = float(np.polyfit(np.arange(n), values, 1)[0])
    mean = float(np.mean(values))
    if mean == 0:
        return "stable"
    change = slope * (n - 1) / abs(mean)
    if change > 0.05:
        return "rising"
    if change < -0.05:
        return "falling"
    return "stable"


def _df(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    return df.sort_values("recorded_at").reset_index(drop=True)


def summarize(records: list[dict]) -> dict[str, Any]:
    df = _df(records)
    out: dict[str, Any] = {"record_count": len(df), "metrics": {}}
    if df.empty:
        return out
    for m in METRICS:
        series = df[m].dropna()
        if series.empty:
            continue
        vals = [float(v) for v in series]
        out["metrics"][m] = {
            "count": len(vals),
            "mean": round(float(np.mean(vals)), 1),
            "min": round(min(vals), 1),
            "max": round(max(vals), 1),
            "latest": round(vals[-1], 1),
            "trend": _trend(vals),
        }
    return out


def build_series(records: list[dict], period: str) -> dict[str, dict[str, list]]:
    """Chart-ready data. 'daily' = individual readings; others = per-day averages."""
    df = _df(records)
    result: dict[str, dict[str, list]] = {}
    if df.empty:
        return result
    for m in METRICS:
        sub = df[["recorded_at", m]].dropna()
        if sub.empty:
            continue
        if period == "daily":
            xs = [t.isoformat() for t in sub["recorded_at"]]
            ys = [round(float(v), 1) for v in sub[m]]
        else:
            g = sub.groupby(sub["recorded_at"].dt.date)[m].mean()
            xs = [d.isoformat() for d in g.index]
            ys = [round(float(v), 1) for v in g.values]
        result[m] = {"x": xs, "y": ys}
    return result
