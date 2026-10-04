"""Real scikit-learn checks on original synthetic data."""
import json
import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler, TargetEncoder


def main():
    scaler = StandardScaler().fit([[10.], [20.], [30.]])
    assert np.allclose(scaler.mean_, [20])
    assert np.allclose(scaler.scale_, [np.sqrt(200 / 3)])
    assert np.allclose(scaler.transform([[40]]), [[np.sqrt(6)]])
    assert MinMaxScaler().fit([[10], [30]]).transform([[40]])[0, 0] == 1.5
    imp = SimpleImputer(strategy="median", add_indicator=True).fit([[10], [np.nan], [30]])
    assert np.array_equal(imp.transform([[np.nan], [100]]), [[20, 1], [100, 0]])
    enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit([["A"], ["B"]])
    assert np.array_equal(enc.transform([["C"]]), [[0, 0]])
    cats, y = np.array([["a"], ["b"], ["c"], ["d"]]), np.array([0., 2., 4., 6.])
    kwargs = dict(target_type="continuous", smooth=0, cv=2, shuffle=False)
    leaked = TargetEncoder(**kwargs).fit(cats, y).transform(cats)
    oof = TargetEncoder(**kwargs).fit_transform(cats, y)
    assert np.allclose(leaked.ravel(), y)
    assert np.allclose(oof.ravel(), [5, 5, 1, 1])
    train = np.array([[10., "A"], [np.nan, "B"], [30., "A"]], dtype=object)
    pre = ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), [0]),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), [1]),
    ])
    pre.fit(train)
    result = pre.transform(np.array([[np.nan, "C"]], dtype=object))
    assert np.allclose(result, [[0, 0, 0]])
    assert pre.get_feature_names_out().tolist() == ["num__x0", "cat__x1_A", "cat__x1_B"]
    print(json.dumps({"sklearn": sklearn.__version__, "numpy": np.__version__,
                      "standardized_40": float(scaler.transform([[40]])[0, 0]),
                      "target_full": leaked.ravel().tolist(), "target_oof": oof.ravel().tolist(),
                      "feature_names": pre.get_feature_names_out().tolist(),
                      "checks": "PASS"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
