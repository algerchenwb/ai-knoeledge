# -*- coding: utf-8 -*-
"""Trusted local artifact roundtrip and explicit input contract checks.
Run with NumPy, SciPy, joblib and scikit-learn. No download or service deployment.
"""
import hashlib
import json
import platform
import tempfile
from pathlib import Path

import joblib
import numpy as np
import scipy
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SCHEMA = ["area_m2", "population_500m"]
SCHEMA_VERSION = "poi-demo-v1"

def rows_to_matrix(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows must be a nonempty list")
    matrix = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(SCHEMA):
            raise ValueError("exact field set required")
        values = []
        for field in SCHEMA:
            value = row[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("numeric values required; bool is not accepted")
            if not np.isfinite(value) or value < 0:
                raise ValueError("finite nonnegative values required")
            values.append(float(value))
        matrix.append(values)
    return np.array(matrix, dtype=np.float64)

def environment():
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "sklearn": sklearn.__version__,
            "joblib": joblib.__version__}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_verified_local(model_path, manifest_path):
    # Only for artifacts and manifests produced by this trusted example.
    # A matching digest does NOT establish authenticity.
    metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
    if metadata["environment"] != environment():
        raise ValueError("demo requires matching environment")
    if metadata["schema"] != SCHEMA or metadata["schema_version"] != SCHEMA_VERSION:
        raise ValueError("schema mismatch")
    if digest(model_path) != metadata["sha256"]:
        raise ValueError("artifact digest mismatch")
    loaded = joblib.load(model_path)
    if loaded.n_features_in_ != len(SCHEMA):
        raise ValueError("feature count mismatch")
    if loaded.classes_.tolist() != metadata["classes"]:
        raise ValueError("class mapping mismatch")
    return loaded

def main():
    print("environment", environment())
    train = [
        {"area_m2": 40, "population_500m": 100},
        {"area_m2": 60, "population_500m": 150},
        {"area_m2": 80, "population_500m": 250},
        {"area_m2": 160, "population_500m": 700},
        {"area_m2": 200, "population_500m": 900},
        {"area_m2": 250, "population_500m": 1200},
    ]
    labels = ["low", "low", "low", "high", "high", "high"]
    pipe = make_pipeline(StandardScaler(), LogisticRegression(random_state=42))
    pipe.fit(rows_to_matrix(train), labels)
    requests = [
        {"population_500m": 200, "area_m2": 70},
        {"area_m2": 220, "population_500m": 1000},
    ]
    matrix = rows_to_matrix(requests)
    # JSON key order is ignored; the schema defines matrix column order.
    assert np.array_equal(matrix[0], [70., 200.])
    before = pipe.predict_proba(matrix)

    bad_rows = [
        {"area_m2": 70},  # missing
        {"area_m2": 70, "population_500m": 200, "extra": 1},
        {"area_m2": True, "population_500m": 200},
        {"area_m2": "70", "population_500m": 200},
        {"area_m2": float("nan"), "population_500m": 200},
        {"area_m2": -1, "population_500m": 200},
    ]
    for row in bad_rows:
        try:
            rows_to_matrix([row])
        except ValueError:
            pass
        else:
            raise AssertionError("invalid request accepted")
    print("invalid request cases rejected", len(bad_rows))

    with tempfile.TemporaryDirectory() as directory:
        model_path = Path(directory) / "model.joblib"
        manifest_path = Path(directory) / "manifest.json"
        # Save the fitted full pipeline, including training scaler state.
        joblib.dump(pipe, model_path, compress=0)
        metadata = {
            "schema": SCHEMA, "schema_version": SCHEMA_VERSION,
            "environment": environment(), "classes": pipe.classes_.tolist(),
            "positive_label": "high", "decision_threshold": 0.5,
            "sha256": digest(model_path),
            "training_data": "synthetic-six-rows-defined-in-this-script",
        }
        manifest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        restored = load_verified_local(model_path, manifest_path)
        after = restored.predict_proba(matrix)
        assert np.allclose(before, after, rtol=1e-12, atol=1e-12)
        positive_col = np.flatnonzero(restored.classes_ == metadata["positive_label"])[0]
        p_high = after[:, positive_col]
        decisions = np.where(p_high >= metadata["decision_threshold"], "high", "low")
        print("classes", restored.classes_, "positive column", positive_col)
        print("p(high)", p_high, "threshold decisions", decisions)
        print("roundtrip max probability delta", np.max(np.abs(before-after)))

        # Detect byte changes before deserialization; never load the modified file.
        model_path.write_bytes(model_path.read_bytes() + b"modified")
        try:
            load_verified_local(model_path, manifest_path)
        except ValueError as error:
            assert "digest mismatch" in str(error)
            print("modified artifact rejected before load")
        else:
            raise AssertionError("modified artifact accepted")

if __name__ == "__main__":
    main()
