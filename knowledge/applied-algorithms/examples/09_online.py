"""Actual sklearn partial_fit with predict-before-learn and deterministic replay."""
import numpy as np
from sklearn.linear_model import SGDClassifier

def replay():
    rng = np.random.default_rng(23)
    x = rng.normal(size=(100, 2))
    y = (x[:, 0] + 0.5 * x[:, 1] > 0).astype(int)
    model = SGDClassifier(loss="log_loss", learning_rate="constant", eta0=0.05,
                          random_state=7, shuffle=False)
    model.partial_fit(x[:10], y[:10], classes=[0, 1])
    initial = model.coef_.copy()
    predictions, events = [], []
    for i in range(10, len(x)):
        step_before = model.t_
        predictions.append(int(model.predict(x[i:i+1])[0]))
        events.append((i, "predict", model.t_))
        assert model.t_ == step_before
        model.partial_fit(x[i:i+1], y[i:i+1])
        events.append((i, "learn", model.t_))
        assert model.t_ == step_before + 1
    assert not np.array_equal(model.coef_, initial)
    for first, second in zip(events[::2], events[1::2]):
        assert first[0] == second[0] and first[1] == "predict" and second[1] == "learn"
    return np.array(predictions), model.coef_, model.t_

a, b = replay(), replay()
np.testing.assert_array_equal(a[0], b[0])
np.testing.assert_allclose(a[1], b[1])
assert a[2] == b[2]
print("PASS actual SGD partial_fit updates, prediction order and deterministic replay")
