"""Train and compare Logistic Regression, Decision Tree and Random Forest for diabetes-risk estimation.

Usage:
    python ml/train_diabetes.py                      # uses data/diabetes.csv
    python ml/train_diabetes.py --data path/to/pima.csv

Only 4 features are used because the web app can supply them from user data:
Glucose, BloodPressure (diastolic), BMI (from weight+height), Age (from date of birth).
Outputs: ml/models/diabetes_model.joblib and ml/models/metrics.json
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["Glucose", "BloodPressure", "BMI", "Age"]  # keep in sync with app/services/ml_service.py


def main(data_path: Path) -> None:
    df = pd.read_csv(data_path)
    for col in ["Glucose", "BloodPressure", "BMI"]:  # zeros mean "missing" in the Pima dataset
        df[col] = df[col].replace(0, np.nan)
    X, y = df[FEATURES], df["Outcome"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Decision Tree": DecisionTreeClassifier(max_depth=4, min_samples_leaf=10, class_weight="balanced", random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=5,
                                                class_weight="balanced", random_state=42),
    }
    results, best_name, best_auc, best_pipe = {}, None, -1.0, None
    for name, clf in candidates.items():
        pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("clf", clf)])
        cv_auc = cross_val_score(pipe, X_train, y_train, cv=5, scoring="roc_auc").mean()
        pipe.fit(X_train, y_train)
        pred, proba = pipe.predict(X_test), pipe.predict_proba(X_test)[:, 1]
        results[name] = {
            "cv_roc_auc": round(float(cv_auc), 4),
            "test_accuracy": round(accuracy_score(y_test, pred), 4),
            "test_precision": round(precision_score(y_test, pred), 4),
            "test_recall": round(recall_score(y_test, pred), 4),
            "test_f1": round(f1_score(y_test, pred), 4),
            "test_roc_auc": round(roc_auc_score(y_test, proba), 4),
        }
        print(f"{name:20s} {results[name]}")
        if cv_auc > best_auc:
            best_name, best_auc, best_pipe = name, cv_auc, pipe

    out_dir = ROOT / "ml" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipe, out_dir / "diabetes_model.joblib")
    (out_dir / "metrics.json").write_text(json.dumps(
        {"best_model": best_name, "features": FEATURES, "data_file": str(data_path.name),
         "n_samples": int(len(df)), "results": results}, indent=2))
    print(f"\nBest model: {best_name}  -> saved to {out_dir / 'diabetes_model.joblib'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "diabetes.csv")
    main(ap.parse_args().data)
