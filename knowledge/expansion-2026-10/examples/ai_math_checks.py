"""Original standard-library demonstrations; no model downloads or GPU required.

Run from repository root:
    python knowledge/expansion-2026-10/examples/ai_math_checks.py
These checks verify mathematical examples, not real model quality or performance.
"""

import json
import math


def softmax(scores, temperature=1.0):
    if not scores or temperature <= 0:
        raise ValueError("Nonempty scores and positive temperature required")
    scaled = [x / temperature for x in scores]
    peak = max(scaled)
    if not math.isfinite(peak):
        raise ValueError("At least one finite score required")
    weights = [math.exp(x - peak) for x in scaled]
    total = sum(weights)
    return [x / total for x in weights]


def dot(a, b):
    if len(a) != len(b):
        raise ValueError("Shape mismatch")
    return sum(x * y for x, y in zip(a, b))


def normalize(v):
    norm = math.sqrt(dot(v, v))
    if norm == 0:
        raise ValueError("Zero vector has no cosine direction")
    return [x / norm for x in v]


def attention(query, keys, values, visible):
    if not keys or len(keys) != len(values) or len(keys) != len(visible):
        raise ValueError("Inconsistent attention inputs")
    scores = [dot(query, k) / math.sqrt(len(query)) if ok else -math.inf
              for k, ok in zip(keys, visible)]
    weights = softmax(scores)
    output = [sum(w * v[j] for w, v in zip(weights, values))
              for j in range(len(values[0]))]
    return weights, output


def matmul(a, b):
    if len(a[0]) != len(b):
        raise ValueError("Shape mismatch")
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def rrf(rankings, c=60):
    scores = {}
    for ranking in rankings:
        if len(set(ranking)) != len(ranking):
            raise ValueError("Each ranking must contain unique document IDs")
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (c + rank)
    return scores


def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta):
    margin = (policy_chosen - ref_chosen) - (policy_rejected - ref_rejected)
    z = beta * margin
    return max(0.0, -z) + math.log1p(math.exp(-abs(z)))


def group_advantages(rewards):
    """Population std for pedagogy; not a reproduction of a trainer variant."""
    mean = sum(rewards) / len(rewards)
    std = math.sqrt(sum((r - mean) ** 2 for r in rewards) / len(rewards))
    return [(r - mean) / (std + 1e-8) for r in rewards]


def q_update(old_q, reward, next_max, gamma, learning_rate, terminated):
    target = reward if terminated else reward + gamma * next_max
    return old_q + learning_rate * (target - old_q), target


def main():
    results = {}
    p = softmax([2, 0])
    assert math.isclose(p[0], 0.8807970779778823)
    assert math.isclose(sum(p), 1)
    assert softmax([10002, 10000]) == p
    cold, hot = softmax([2, 0], 0.5), softmax([2, 0], 2)
    assert cold[0] > p[0] > hot[0]
    results["softmax_temperature"] = {"T1": p, "T0.5": cold, "T2": hot}

    weights, out = attention([2.0], [[1.0], [0.0]], [[10, 0], [0, 10]], [True, True])
    assert math.isclose(out[0], 10 * p[0])
    masked_w, masked_out = attention([2.0], [[1.0], [0.0]], [[10, 0], [0, 10]], [True, False])
    _, altered_out = attention([2.0], [[1.0], [0.0]], [[10, 0], [99999, -99999]], [True, False])
    assert masked_w == [1.0, 0.0]
    assert masked_out == altered_out == [10.0, 0.0]
    results["attention_and_causal_mask"] = {"weights": weights, "out": out, "masked": masked_out}

    try:
        attention([1.0], [[1.0]], [[2.0]], [False])
    except ValueError:
        pass
    else:
        raise AssertionError("All-masked row must be rejected")
    results["all_masked_row_rejected"] = True

    values = [1.0, 3.0]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    normalized = [(v - mean) / math.sqrt(variance + 1e-5) for v in values]
    assert abs(sum(normalized)) < 1e-12
    assert math.isclose(normalized[0], -1, abs_tol=1e-5)
    results["layer_norm"] = normalized

    loss = -math.log(0.8)
    perplexity = math.exp(-math.log(0.5))
    assert math.isclose(loss, 0.2231435513142097)
    assert math.isclose(perplexity, 2)
    results["cross_entropy_and_perplexity"] = {"loss_p0.8": loss, "ppl_p0.5": perplexity}

    probs, threshold = [0.6, 0.25, 0.1, 0.05], 0.8
    selected, cumulative = [], 0
    for prob in probs:  # already descending
        selected.append(prob)
        cumulative += prob
        if cumulative >= threshold:
            break
    nucleus = [p / cumulative for p in selected]
    assert len(nucleus) == 2 and math.isclose(nucleus[0], 0.6 / 0.85)
    results["top_p_boundary"] = nucleus

    a, b = normalize([1.0, 2.0]), normalize([3.0, 1.0])
    cosine = dot(a, b)
    distance_sq = sum((x - y) ** 2 for x, y in zip(a, b))
    assert math.isclose(distance_sq, 2 - 2 * cosine, abs_tol=1e-12)
    results["cosine_l2_equivalence"] = {"cosine": cosine, "squared_l2": distance_sq}

    scores = rrf([["A", "B", "C"], ["C", "B", "D"]])
    ranking = sorted(scores, key=lambda doc: (-scores[doc], doc))
    assert ranking == ["C", "B", "A", "D"]
    relevant, retrieved = {"A", "D"}, ["A", "B", "C"]
    recall = len(relevant.intersection(retrieved)) / len(relevant)
    hit = int(bool(relevant.intersection(retrieved)))
    assert recall == 0.5 and hit == 1
    results["rrf_and_recall_vs_hit"] = {"ranking": ranking, "scores": scores, "recall": recall, "hit": hit}

    base = [[2, 0], [0, 3]]
    a_lora, b_lora = [[1, 2]], [[0], [0]]
    delta_zero = matmul(b_lora, a_lora)
    assert delta_zero == [[0, 0], [0, 0]]
    b_lora = [[0.5], [-0.5]]
    delta = matmul(b_lora, a_lora)  # alpha/r=1 for this illustration
    x = [[1], [2]]
    unmerged = [[z[0] + dz[0]] for z, dz in zip(matmul(base, x), matmul(delta, x))]
    merged_weights = [[w + dw for w, dw in zip(row, drow)] for row, drow in zip(base, delta)]
    merged = matmul(merged_weights, x)
    assert merged == unmerged == [[4.5], [3.5]]
    assert 8 * (4096 + 4096) == 65536
    results["lora_zero_and_merge"] = {"merged_output": merged, "rank8_params": 65536}

    baseline = dpo_loss(-2, -3, -2, -3, 0.1)
    improved = dpo_loss(-1, -4, -2, -3, 0.1)
    assert math.isclose(baseline, math.log(2)) and improved < baseline
    advantages = group_advantages([0, 0, 1, 1])
    assert all(math.isclose(a, b, abs_tol=1e-7) for a, b in zip(advantages, [-1, -1, 1, 1]))
    assert group_advantages([1, 1, 1]) == [0, 0, 0]
    results["dpo_and_group_advantage"] = {"baseline_loss": baseline, "improved_loss": improved, "advantages": advantages}

    kv_bytes = 2 * 32 * 1 * 8192 * 8 * 128 * 2
    assert kv_bytes == 2 ** 30
    raw_vector_bytes = 1_000_000 * 768 * 4
    results["memory_arithmetic"] = {"kv_bytes": kv_bytes, "kv_GiB": kv_bytes / 2**30, "million_vectors_GB": raw_vector_bytes / 10**9}

    original = [-1.0, -0.1, 0.2, 0.8]
    scale = max(abs(v) for v in original) / 127
    codes = [max(-127, min(127, round(v / scale))) for v in original]
    reconstructed = [q * scale for q in codes]
    errors = [abs(v - w) for v, w in zip(original, reconstructed)]
    assert max(errors) <= scale / 2 + 1e-12
    results["uniform_quantization"] = {"codes": codes, "max_error": max(errors), "half_step": scale / 2}

    image, text = normalize([1, 0]), normalize([0.8, 0.2])
    other = normalize([0, 1])
    scores = [dot(image, text), dot(image, other)]
    contrastive_probs = softmax(scores, 0.1)
    assert contrastive_probs[0] > contrastive_probs[1]
    results["contrastive_pair"] = {"scores": scores, "positive_loss": -math.log(contrastive_probs[0])}

    clean, epsilon, alpha_bar = 2.0, 0.5, 0.64
    noisy = math.sqrt(alpha_bar) * clean + math.sqrt(1 - alpha_bar) * epsilon
    recovered = (noisy - math.sqrt(1 - alpha_bar) * epsilon) / math.sqrt(alpha_bar)
    assert math.isclose(noisy, 1.9) and math.isclose(recovered, clean)
    results["diffusion_known_noise"] = {"noisy": noisy, "recovered": recovered}

    new_q, ordinary_target = q_update(2, 1, 4, 0.9, 0.5, False)
    terminal_q, terminal_target = q_update(2, 1, 4, 0.9, 0.5, True)
    assert math.isclose(new_q, 3.3) and math.isclose(ordinary_target, 4.6)
    assert terminal_q == 1.5 and terminal_target == 1
    results["q_update_terminal_vs_timeout"] = {"ordinary_target": ordinary_target, "new_q": new_q, "terminal_target": terminal_target}

    print(json.dumps({"check_groups": len(results), "status": "PASS", "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
