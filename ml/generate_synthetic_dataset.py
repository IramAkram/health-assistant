"""Creates data/diabetes.csv - a SYNTHETIC dataset with the same columns as the Pima Indians Diabetes dataset.

Why: so the project runs out-of-the-box with no download. For your FYP report/viva, replace
data/diabetes.csv with the REAL Pima dataset (see README, section 'Datasets') and re-run train_diabetes.py.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "diabetes.csv"
rng = np.random.default_rng(42)
N = 768

age = np.clip(21 + rng.gamma(2.0, 7.5, N), 21, 81).round()
pregnancies = np.clip(rng.poisson(np.clip((age - 18) / 9, 0.3, None)), 0, 17)
bmi = np.clip(rng.normal(32, 6.8, N), 18, 60).round(1)
glucose = np.clip(rng.normal(118, 28, N) + (bmi - 32) * 0.6, 60, 199).round()
blood_pressure = np.clip(rng.normal(68 + (age - 33) * 0.25, 12, N), 40, 122).round()
skin = np.clip(rng.normal(20 + (bmi - 32) * 0.8, 9, N), 0, 60).round()
insulin = np.clip(rng.lognormal(4.3, 0.7, N) + (glucose - 118) * 0.5, 0, 600).round()
pedigree = np.clip(rng.lognormal(-0.9, 0.55, N), 0.08, 2.4).round(3)

logit = (0.045 * (glucose - 120) + 0.07 * (bmi - 32) + 0.03 * (age - 33)
         + 0.012 * (blood_pressure - 69) + 0.9 * (pedigree - 0.47) + 0.05 * (pregnancies - 3))
lo, hi = -10.0, 10.0
for _ in range(60):  # calibrate intercept so ~35% are positive (like Pima)
    mid = (lo + hi) / 2
    if (1 / (1 + np.exp(-(logit + mid)))).mean() > 0.35:
        hi = mid
    else:
        lo = mid
prob = 1 / (1 + np.exp(-(logit + (lo + hi) / 2)))
outcome = (rng.random(N) < prob).astype(int)

df = pd.DataFrame({"Pregnancies": pregnancies, "Glucose": glucose, "BloodPressure": blood_pressure,
                   "SkinThickness": skin, "Insulin": insulin, "BMI": bmi,
                   "DiabetesPedigreeFunction": pedigree, "Age": age.astype(int), "Outcome": outcome})
# Pima encodes missing values as 0 - mimic that for a few columns
for col, frac in [("BloodPressure", 0.045), ("SkinThickness", 0.29), ("Insulin", 0.48), ("BMI", 0.014), ("Glucose", 0.007)]:
    df.loc[rng.random(N) < frac, col] = 0
df = df.astype({"Pregnancies": int, "Glucose": int, "BloodPressure": int, "SkinThickness": int, "Insulin": int})

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Saved {len(df)} rows to {OUT}  (positive rate: {df.Outcome.mean():.2%})")
