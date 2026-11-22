"""Loads the trained diabetes-risk model and produces an informational estimate."""
import json
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "ml" / "models" / "diabetes_model.joblib"
METRICS_PATH = BASE_DIR / "ml" / "models" / "metrics.json"
FEATURES = ["Glucose", "BloodPressure", "BMI", "Age"]

DISCLAIMER = (
    "This is a statistical estimate from a limited dataset, not a diagnosis. "
    "Please consult a healthcare professional for medical advice."
)

_model = None


def _load():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    return _model


def is_available() -> bool:
    return MODEL_PATH.exists()


def model_info() -> dict[str, Any]:
    if METRICS_PATH.exists():
        return json.loads(METRICS_PATH.read_text())
    return {}


def estimate_diabetes_risk(glucose: Optional[float], diastolic: Optional[float],
                           bmi: Optional[float], age: Optional[int]) -> dict[str, Any]:
    missing = [name for name, v in [("glucose", glucose), ("diastolic blood pressure", diastolic),
                                    ("BMI (needs weight and height)", bmi), ("age (needs date of birth)", age)]
               if v is None]
    if missing:
        return {"available": False, "reason": "Missing data: " + ", ".join(missing) + "."}
    model = _load()
    if model is None:
        return {"available": False, "reason": "Model not trained yet. Run: python ml/train_diabetes.py"}

    X = pd.DataFrame([[glucose, diastolic, bmi, age]], columns=FEATURES)
    prob = float(model.predict_proba(X)[0][1])
    band = "low" if prob < 0.33 else "moderate" if prob < 0.66 else "high"
    return {
        "available": True,
        "probability": round(prob, 3),
        "band": band,
        "inputs": {"glucose": glucose, "diastolic": diastolic, "bmi": bmi, "age": age},
        "model": model_info().get("best_model"),
        "disclaimer": DISCLAIMER,
    }
