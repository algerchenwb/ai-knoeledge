"""Independent numerical explanations, standard library only; not SHAP library."""
import math
from statistics import mean


def mse(model, rows, targets):
    return mean((model(row) - y) ** 2 for row, y in zip(rows, targets))


def permute_columns(rows, columns, order):
    if sorted(order) != list(range(len(rows))):
        raise ValueError("order must be a permutation")
    return [[rows[order[i]][j] if j in columns else value
             for j, value in enumerate(row)] for i, row in enumerate(rows)]


def ice(model, rows, column, grid):
    curves = []
    for row in rows:
        curve = []
        for value in grid:
            replaced = list(row)
            replaced[column] = value
            curve.append(model(replaced))
        curves.append(curve)
    return curves


def coalition_value(model, sample, background, known):
    return mean(model([sample[j] if j in known else row[j]
                       for j in range(len(sample))]) for row in background)


def shapley_two(model, sample, background):
    if len(sample) != 2 or not background:
        raise ValueError("this demo requires two features and nonempty background")
    v0 = coalition_value(model, sample, background, set())
    va = coalition_value(model, sample, background, {0})
    vb = coalition_value(model, sample, background, {1})
    vab = coalition_value(model, sample, background, {0, 1})
    return v0, [(va - v0 + vab - vb) / 2, (vb - v0 + vab - va) / 2]


def main():
    model = lambda r: 2 * r[0] + r[1]
    rows = [[0, 0], [0, 1], [1, 0], [1, 1]]
    y = [model(row) for row in rows]
    assert mse(model, rows, y) == 0
    ia = mse(model, permute_columns(rows, {0}, [2, 3, 0, 1]), y)
    ib = mse(model, permute_columns(rows, {1}, [1, 0, 3, 2]), y)
    assert ia == 4 and ib == 1
    # Higher-is-better score convention agrees with direct MSE increase.
    assert (0 - (-ia)) == ia
    duplicate = [[0, 0], [0, 0], [1, 1], [1, 1]]
    redundant_model = lambda r: max(r)
    target = [0, 0, 1, 1]
    single = mse(redundant_model, permute_columns(duplicate, {0}, [2, 3, 0, 1]), target)
    grouped = mse(redundant_model, permute_columns(duplicate, {0, 1}, [2, 3, 0, 1]), target)
    assert single == .5 and grouped == 1
    curves = ice(lambda r: r[0] * r[1], [[0, -1], [0, 1]], 0, [0, 1, 2])
    pdp = [mean(col) for col in zip(*curves)]
    assert curves == [[0, -1, -2], [0, 1, 2]] and pdp == [0, 0, 0]
    mixed = ice(lambda r: r[0] * r[1], [[0, -1], [0, 1], [0, 1], [0, 1]], 0, [0, 1, 2])
    assert [mean(col) for col in zip(*mixed)] == [0, .5, 1]
    offset_curves = ice(lambda r: 10 * r[1] + r[0] * r[1], [[0, -1], [0, 1]], 0, [0, 1, 2])
    centered = [[v - curve[0] for v in curve] for curve in offset_curves]
    assert centered == curves
    interaction = lambda r: 2 * r[0] + r[1] + 3 * r[0] * r[1]
    base, phi = shapley_two(interaction, [1, 1], [[0, 0]])
    assert base == 0 and phi == [3.5, 2.5]
    assert math.isclose(base + sum(phi), interaction([1, 1]))
    second_base, second_phi = shapley_two(interaction, [1, 1], [[0, 1]])
    assert second_base == 1 and second_phi == [5, 0]
    assert second_base + sum(second_phi) == interaction([1, 1])
    # Multiple background samples: must average outputs, not average inputs first.
    nonlinear = lambda r: r[0] ** 2 + r[1]
    nonlinear_base, nonlinear_phi = shapley_two(nonlinear, [2, 1], [[-1, 0], [1, 0]])
    assert nonlinear_base == 1 and nonlinear_phi == [3, 1]
    assert nonlinear([0, 0]) != nonlinear_base
    assert nonlinear_base + sum(nonlinear_phi) == nonlinear([2, 1])
    print("fixed permutation MSE increases:", ia, ib)
    print("correlated single/group MSE:", single, grouped)
    print("ICE:", curves, "PDP:", pdp)
    print("two-feature Shapley:", base, phi, "changed background:", second_base, second_phi)
    print("PASS: permutation direction, grouped correlation, ICE/PDP cancellation,")
    print("      background mix, centered ICE, Shapley interaction, background change,")
    print("      nonlinear background expectation and additivity")


if __name__ == "__main__":
    main()
