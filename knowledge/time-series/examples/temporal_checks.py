"""Small original temporal checks; actual sklearn TimeSeriesSplit integration."""
import json
from statistics import mean
import numpy as np
import sklearn
from sklearn.model_selection import TimeSeriesSplit, train_test_split


def past_features(values, t, window=3):
    if t < window:
        raise ValueError("not enough history")
    return [values[t - 1], values[t - 2], mean(values[t - window:t])]


def main():
    y = [10, 20, 30, 40, 50]
    assert past_features(y, 3) == [30, 20, 20]
    changed = y.copy()
    changed[3:] = [999, 1000]
    assert past_features(changed, 3) == past_features(y, 3)
    assert mean(y[1:4]) == 30  # deliberately includes target, unlike safe feature
    groups = {"A": [10, 11, 12], "B": [100, 101, 102]}
    assert groups["A"][1] == 11 and groups["B"][1] == 101
    interleaved = [10, 100, 11, 101, 12, 102]
    assert interleaved[3] != groups["A"][1]  # global lag for A's last row is wrong
    folds = []
    splitter = TimeSeriesSplit(n_splits=3, test_size=2, gap=2)
    for train, test in splitter.split(np.arange(12)):
        assert train[-1] < test[0]
        assert test[0] - train[-1] - 1 == 2
        assert train[-1] + 2 < test[0]  # label ends two rows after sample index
        folds.append({"train": train.tolist(), "test": test.tolist()})
    assert folds[0] == {"train": [0, 1, 2, 3], "test": [6, 7]}
    sliding = list(TimeSeriesSplit(n_splits=3, test_size=2, gap=2,
                                   max_train_size=3).split(np.arange(12)))
    assert all(len(train) == 3 for train, _ in sliding)
    random_train, random_test = train_test_split(np.arange(30), random_state=42)
    assert max(random_train) > min(random_test)
    weekly = [10, 20, 30, 40, 50, 60, 70] * 4
    seasonal_mae = mean(abs(weekly[t] - weekly[t - 7]) for t in range(7, len(weekly)))
    previous_mae = mean(abs(weekly[t] - weekly[t - 1]) for t in range(7, len(weekly)))
    assert seasonal_mae == 0 and previous_mae > 0
    pooled = mean([10] + [0] * 9)
    macro = mean([10, 0])
    assert pooled == 1 and macro == 5
    print(json.dumps({"sklearn": sklearn.__version__, "folds": folds,
                      "seasonal_mae": seasonal_mae, "previous_mae": previous_mae,
                      "pooled_mae": pooled, "macro_store_mae": macro,
                      "checks": "PASS"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
