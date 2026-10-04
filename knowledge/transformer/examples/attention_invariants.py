"""Small, independent attention demonstrations; Python standard library only.

True in a mask means allowed. No training, batching, multihead, or dropout.
"""
import math


def dot(a, b):
    if len(a) != len(b):
        raise ValueError("dot dimensions differ")
    return sum(x * y for x, y in zip(a, b))


def softmax(scores, allowed=None):
    if not scores or not all(math.isfinite(s) for s in scores):
        raise ValueError("scores must be nonempty and finite")
    if allowed is None:
        allowed = [True] * len(scores)
    if len(allowed) != len(scores) or not any(allowed):
        raise ValueError("invalid mask or all positions masked")
    offset = max(s for s, ok in zip(scores, allowed) if ok)
    exps = [math.exp(s - offset) if ok else 0.0
            for s, ok in zip(scores, allowed)]
    total = sum(exps)
    return [e / total for e in exps]


def attention(queries, keys, values, mask=None):
    if not queries or not keys or len(keys) != len(values):
        raise ValueError("invalid sequence lengths")
    dk, dv = len(keys[0]), len(values[0])
    if not dk or not dv:
        raise ValueError("empty feature dimension")
    if any(len(row) != dk for row in queries + keys):
        raise ValueError("invalid Q/K dimensions")
    if any(len(row) != dv for row in values):
        raise ValueError("invalid V dimensions")
    if mask is not None and len(mask) != len(queries):
        raise ValueError("invalid mask query dimension")
    weights, outputs = [], []
    for i, q in enumerate(queries):
        scores = [dot(q, k) / math.sqrt(dk) for k in keys]
        w = softmax(scores, None if mask is None else mask[i])
        weights.append(w)
        outputs.append([sum(w[j] * values[j][c] for j in range(len(keys)))
                        for c in range(dv)])
    return weights, outputs


def positional_encoding(position, dimension):
    if dimension <= 0 or dimension % 2:
        raise ValueError("this demo requires a positive even dimension")
    result = []
    for i in range(dimension // 2):
        angle = position / (10000 ** (2 * i / dimension))
        result.extend([math.sin(angle), math.cos(angle)])
    return result


def close(a, b):
    return len(a) == len(b) and all(
        math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9)
        for x, y in zip(a, b))


def main():
    table = [[0, 0, 0], [1, 0, .5], [0, 1, .5], [.5, .5, 1]]
    embedded = [table[i] for i in [1, 2, 3]]
    assert embedded == [[1, 0, .5], [0, 1, .5], [.5, .5, 1]]
    q, k, v = [[1, 0]], [[1, 0], [0, 1], [1, 1]], [[10, 0], [0, 20], [10, 10]]
    w, out = attention(q, k, v)
    # Independent scalar reference using the unshifted exponential formula.
    e = math.exp(1 / math.sqrt(2))
    expected = [e / (2 * e + 1), 1 / (2 * e + 1), e / (2 * e + 1)]
    assert close(w[0], expected)
    assert close(out[0], [20 * expected[0], 20 * expected[1] + 10 * expected[2]])
    assert math.isclose(sum(w[0]), 1)
    print("attention weights:", [round(x, 9) for x in w[0]])
    print("attention output:", [round(x, 9) for x in out[0]])
    mw, mo = attention(q, k, v, [[True, True, False]])
    assert mw[0][2] == 0 and close(mw[0][:2], [e / (e + 1), 1 / (e + 1)])
    print("masked output:", [round(x, 9) for x in mo[0]])
    changed_v = [v[0], v[1], [999999, -999999]]
    assert close(attention(q, k, changed_v, [[True, True, False]])[1][0], mo[0])
    # Future-token perturbation must not alter earlier causal outputs.
    x = [[1, 0], [0, 1], [1, 1]]
    mask = [[j <= i for j in range(3)] for i in range(3)]
    cw, co = attention(x, x, x, mask)
    perturbed = [x[0], x[1], [9, -4]]
    pw, po = attention(perturbed, perturbed, perturbed, mask)
    assert all(close(co[i], po[i]) for i in [0, 1])
    assert not close(co[2], po[2])
    assert all(cw[i][j] == 0 for i in range(3) for j in range(i + 1, 3))
    # No positions and no mask: permuting rows permutes outputs.
    order = [2, 0, 1]
    plain = attention(x, x, x)[1]
    perm = [x[i] for i in order]
    perm_out = attention(perm, perm, perm)[1]
    assert all(close(perm_out[i], plain[order[i]]) for i in range(3))
    assert close(softmax([1000, 1001]), softmax([0, 1]))
    try:
        softmax([1, 2], [False, False])
    except ValueError:
        pass
    else:
        raise AssertionError("all-masked input must be rejected")
    assert positional_encoding(0, 4) == [0, 1, 0, 1]
    assert not close(positional_encoding(0, 4), positional_encoding(1, 4))
    print("PASS: lookup, scalar reference, mask isolation, causal isolation, permutation,")
    print("      stable softmax, all-masked rejection, positional encoding")


if __name__ == "__main__":
    main()
