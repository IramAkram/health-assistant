"""Deterministic, rule-based alerts.

Critical alerts never depend on an AI-generated response (see proposal, section 5).
Thresholds are general reference values for adults and are configurable below.
They must be reviewed/validated with a medical reference before real-world use.
"""
from typing import Any

THRESHOLDS = {
    "systolic_critical_high": 180,
    "diastolic_critical_high": 120,
    "systolic_high": 140,
    "diastolic_high": 90,
    "systolic_low": 90,
    "diastolic_low": 60,
    "glucose_critical_low": 54,
    "glucose_low": 70,
    "glucose_high": 180,
    "glucose_critical_high": 300,
    "sleep_low": 5,
    "stress_high": 8,
}

URGENT = " If you feel unwell, seek urgent medical care."
SEE_DOCTOR = " Consider discussing this with a healthcare professional."


def _alert(severity: str, metric: str, message: str) -> dict[str, str]:
    return {"severity": severity, "metric": metric, "message": message}


def evaluate_record(rec: dict[str, Any], t: dict[str, int] = THRESHOLDS) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []

    sys_, dia = rec.get("systolic"), rec.get("diastolic")
    if sys_ is not None and dia is not None:
        if sys_ >= t["systolic_critical_high"] or dia >= t["diastolic_critical_high"]:
            alerts.append(_alert("critical", "blood_pressure",
                                 f"Blood pressure {sys_}/{dia} mmHg is very high." + URGENT))
        elif sys_ >= t["systolic_high"] or dia >= t["diastolic_high"]:
            alerts.append(_alert("warning", "blood_pressure",
                                 f"Blood pressure {sys_}/{dia} mmHg is above the usual range." + SEE_DOCTOR))
        elif sys_ < t["systolic_low"] or dia < t["diastolic_low"]:
            alerts.append(_alert("warning", "blood_pressure",
                                 f"Blood pressure {sys_}/{dia} mmHg is lower than the usual range." + SEE_DOCTOR))

    g = rec.get("glucose")
    if g is not None:
        if g < t["glucose_critical_low"]:
            alerts.append(_alert("critical", "glucose", f"Blood glucose {g:g} mg/dL is very low." + URGENT))
        elif g >= t["glucose_critical_high"]:
            alerts.append(_alert("critical", "glucose", f"Blood glucose {g:g} mg/dL is very high." + URGENT))
        elif g < t["glucose_low"]:
            alerts.append(_alert("warning", "glucose", f"Blood glucose {g:g} mg/dL is low." + SEE_DOCTOR))
        elif g >= t["glucose_high"]:
            alerts.append(_alert("warning", "glucose", f"Blood glucose {g:g} mg/dL is high." + SEE_DOCTOR))

    s = rec.get("sleep_hours")
    if s is not None and s < t["sleep_low"]:
        alerts.append(_alert("info", "sleep", f"Only {s:g} hours of sleep recorded. Rest is important for recovery."))

    st = rec.get("stress_level")
    if st is not None and st >= t["stress_high"]:
        alerts.append(_alert("info", "stress", f"Stress level {st}/10 is high. Consider a short break or relaxation exercise."))

    return alerts
