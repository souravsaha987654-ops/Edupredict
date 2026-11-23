"""Train and compare several algorithms, then save the best one.

Run:  python ml/train.py
Creates: models/best_algo.joblib  and  models/metrics.json  (shown on the 'How it works' page)
"""
import sys, json, shutil, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import config as cfg

try:
    from xgboost import XGBRegressor
except Exception:  # xgboost not installed
    XGBRegressor = None


def build(model, X):
    num = X.select_dtypes(include="number").columns.tolist()
    cat = [c for c in X.columns if c not in num]
    prep = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num),
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat),
    ])
    return Pipeline([("prep", prep), ("model", model)])


def run():
    df = pd.read_csv(cfg.DATA_PATH).drop_duplicates()
    df = df[df["Exam_Score"] <= 100]
    X, y = df.drop(columns=["Exam_Score", "Gender"], errors="ignore"), df["Exam_Score"]   # gender is never used
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Decision Tree": DecisionTreeRegressor(max_depth=6, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42),
    }
    if XGBRegressor:
        models["XGBoost"] = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42)

    results = []
    for name, m in models.items():
        pipe = build(m, X).fit(Xtr, ytr)
        p = pipe.predict(Xte)
        cv = cross_val_score(build(m, X), X, y, cv=5, scoring="r2").mean()
        results.append(dict(name=name, r2=round(float(r2_score(yte, p)), 4), mae=round(float(mean_absolute_error(yte, p)), 3),
                            rmse=round(float(np.sqrt(mean_squared_error(yte, p))), 3), cv_r2=round(float(cv), 4)))
        print(f"{name:20s} R2={results[-1]['r2']:.3f}  MAE={results[-1]['mae']:.2f}  CV-R2={cv:.3f}")

    best = max(results, key=lambda r: r["r2"])
    for r in results:
        r["best"] = r["name"] == best["name"]
    final = build(models[best["name"]], X).fit(X, y)          # refit the winning algorithm on all data
    cfg.MODEL_PATH.parent.mkdir(exist_ok=True)
    backup = cfg.MODEL_PATH.with_name("best_algo_original.joblib")
    if cfg.MODEL_PATH.exists() and not backup.exists():
        shutil.copy(cfg.MODEL_PATH, backup)               # keep a copy of your original saved model
    joblib.dump(final, cfg.MODEL_PATH)
    cfg.METRICS_PATH.write_text(json.dumps(dict(models=sorted(results, key=lambda r: -r["r2"]), best=best["name"],
                                                rows=int(len(df)), features=int(X.shape[1]),
                                                trained_on=datetime.date.today().isoformat()), indent=2))
    print(f"\nBest algorithm: {best['name']}  ->  saved to {cfg.MODEL_PATH}")


if __name__ == "__main__":
    run()
