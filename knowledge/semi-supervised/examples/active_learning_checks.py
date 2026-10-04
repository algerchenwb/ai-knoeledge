"""Independent uncertainty formulas and sklearn pool-based labeling simulation."""
import json
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def entropy(probabilities):
    p = np.asarray(probabilities, dtype=float)
    assert np.all(p >= 0) and np.all(np.isfinite(p))
    np.testing.assert_allclose(p.sum(axis=1), 1)
    return -np.sum(p * np.log(np.maximum(p, np.finfo(float).tiny)), axis=1)


def formula_checks():
    p = np.array([[0.51, 0.49, 0.], [0.6, 0.2, 0.2]])
    uncertainty = 1 - p.max(axis=1)
    ordered = np.sort(p, axis=1)
    margins = ordered[:, -1] - ordered[:, -2]
    assert np.argmax(uncertainty) == 0 and np.argmin(margins) == 0
    assert np.argmax(entropy(p)) == 1
    np.testing.assert_allclose(entropy([[1., 0.], [0.5, 0.5]]), [0., np.log(2)])
    tied = entropy([[0.5, 0.5]] * 3)
    np.testing.assert_array_equal(np.argsort(-tied, kind="stable")[:2], [0, 1])
    print("PASS uncertainty direction, multiclass disagreement, zero entropy and stable ties")


def query(model, available_x, batch_size, strategy, rng):
    # Does not receive labels. Returned positions are mapped to stable IDs by caller.
    if strategy == "random":
        return rng.choice(len(available_x), batch_size, replace=False)
    scores = entropy(model.predict_proba(available_x))
    return np.argsort(-scores, kind="stable")[:batch_size]


def experiment(seed):
    x, y = make_classification(n_samples=900, n_features=10, n_informative=6,
                               n_redundant=2, flip_y=0.1, class_sep=1.,
                               random_state=seed)
    pool_ids, test_ids = train_test_split(np.arange(len(y)), test_size=300,
                                         stratify=y, random_state=seed + 1)
    assert not set(pool_ids) & set(test_ids)
    rng = np.random.default_rng(seed + 2)
    # Simulation-only stratified seed setup; unknown real labels are not available this way.
    seeds = np.concatenate([rng.choice(pool_ids[y[pool_ids] == c], 10, replace=False)
                            for c in [0, 1]])
    result = {"seed": seed, "random": [], "entropy": []}
    for strategy in ["random", "entropy"]:
        labeled_ids = list(seeds)
        observed = {int(i): int(y[i]) for i in seeds}
        rng_query = np.random.default_rng(seed + 3)
        for budget in [20, 40, 60, 80]:
            assert len(labeled_ids) == len(set(labeled_ids)) == budget
            model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
            model.fit(x[labeled_ids], [observed[int(i)] for i in labeled_ids])
            result[strategy].append({"labels": budget, "test_accuracy": float(
                accuracy_score(y[test_ids], model.predict(x[test_ids])))})
            if budget == 80:
                break
            available_ids = np.array(sorted(set(pool_ids) - set(labeled_ids)))
            positions = query(model, x[available_ids], 20, strategy, rng_query)
            chosen = available_ids[positions]
            assert len(set(chosen)) == 20 and not set(chosen) & set(labeled_ids)
            assert not set(chosen) & set(test_ids)
            # Perfect, immediate oracle answers only queried IDs; no pseudo-labels.
            for sample_id in chosen:
                observed[int(sample_id)] = int(y[sample_id])
            labeled_ids.extend(chosen.tolist())
    return result


if __name__ == "__main__":
    formula_checks()
    for seed in [7, 19, 31]:
        print(json.dumps(experiment(seed), sort_keys=True))
