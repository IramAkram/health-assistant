"""Downloads the REAL Pima Indians Diabetes dataset into data/diabetes.csv (needs internet)."""
import shutil
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
COLS = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome"]

target = ROOT / "data" / "diabetes.csv"
backup = ROOT / "data" / "diabetes_synthetic.csv"
if target.exists() and not backup.exists():
    shutil.copy(target, backup)
tmp = ROOT / "data" / "_pima_raw.csv"
urllib.request.urlretrieve(URL, tmp)
df = pd.read_csv(tmp, header=None, names=COLS)
tmp.unlink()
assert df.shape == (768, 9), f"Unexpected shape {df.shape}"
df.to_csv(target, index=False)
print("Real Pima dataset saved:", target, df.shape)