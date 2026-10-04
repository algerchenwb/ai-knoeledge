"""Original standard-library experiments for training concepts.

No PyTorch/GPU/framework integration is exercised. Run from repo root:
python knowledge/training-engineering/examples/training_math_checks.py
"""

import copy
import json
import math
import random
import struct
import tempfile
from pathlib import Path


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12), (a, b)


def cosine_schedule(update, warmup, total, peak, floor):
    """Pedagogical boundaries, intentionally not identical to nanoGPT get_lr."""
    if not 0 < warmup < total - 1:
        raise ValueError("Need room for warmup and decay")
    if update < warmup:
        return peak * (update + 1) / warmup
    progress = min(1.0, (update - warmup) / (total - 1 - warmup))
    return floor + 0.5 * (1 + math.cos(math.pi * progress)) * (peak - floor)


def gradient_sum(w, xs, ys):
    return sum(2 * x * (w * x - y) for x, y in zip(xs, ys))


def clip_norm(vector, maximum):
    norm = math.sqrt(sum(v * v for v in vector))
    factor = min(1.0, maximum / norm) if norm else 1.0
    return [factor * v for v in vector]


def half_round(value):
    return struct.unpack("e", struct.pack("e", value))[0]


def batches(indices, size, drop_last=False):
    result = [indices[i:i + size] for i in range(0, len(indices), size)]
    return [b for b in result if len(b) == size] if drop_last else result


def as_tuple(value):
    return tuple(as_tuple(v) for v in value) if isinstance(value, list) else value


def run_updates(state, rng, count):
    """Scalar regression, momentum SGD, fixed data cursor and RNG augmentation."""
    trace = []
    data = [0.5, 1.0, 1.5, 2.0]
    for _ in range(count):
        x = data[state["cursor"] % len(data)] + rng.uniform(-0.1, 0.1)
        y = 2 * x
        g = 2 * x * (state["w"] * x - y)
        state["momentum"] = 0.8 * state["momentum"] + g
        state["w"] -= 0.01 * state["momentum"]
        state["step"] += 1
        state["cursor"] += 1
        trace.append({"step": state["step"], "w": state["w"], "x": x})
    return trace


def main():
    results = {}
    initial, lr = 0.0, 0.1
    grad = 2 * (initial - 3)
    updated = initial - lr * grad
    close(updated, 0.6)
    close((updated - 3) ** 2, 5.76)
    bad_update = initial - 1.1 * grad
    assert (bad_update - 3) ** 2 > (initial - 3) ** 2
    results["sgd_learning_rate"] = {"updated": updated, "loss": (updated - 3) ** 2, "large_lr_loss": (bad_update - 3) ** 2}

    beta1, beta2, g = 0.9, 0.999, 2.0
    m, v = (1 - beta1) * g, (1 - beta2) * g * g
    close(m / (1 - beta1), 2)
    close(v / (1 - beta2), 4)
    decayed = 10 * (1 - 0.1 * 0.01)
    close(decayed, 9.99)
    results["adam_bias_correction_and_decay"] = {"m_hat": m / (1 - beta1), "v_hat": v / (1 - beta2), "zero_gradient_adamw_weight": decayed}

    rates = [cosine_schedule(u, 4, 13, 0.1, 0.01) for u in range(13)]
    for got, want in zip(rates[:4], [0.025, 0.05, 0.075, 0.1]):
        close(got, want)
    close(rates[4], 0.1)
    close(rates[8], 0.055)
    close(rates[-1], 0.01)
    assert math.ceil(101 / 5) == 21 and 101 // 5 == 20
    results["schedule_boundaries_and_update_counts"] = {"lr": rates, "updates_with_tail": 21, "full_windows_only": 20}

    indices = list(range(10))
    kept, dropped = batches(indices, 4), batches(indices, 4, True)
    assert [len(b) for b in kept] == [4, 4, 2]
    assert [len(b) for b in dropped] == [4, 4]
    assert [i for b in kept for i in b] == indices
    lengths = [2, 4, 3]
    slots, valid = len(lengths) * max(lengths), sum(lengths)
    close((slots - valid) / slots, 0.25)
    results["padding_and_tail_coverage"] = {"kept_batches": kept, "dropped_count": 2, "padding_fraction": 0.25}

    w, xs = 0.3, [1.0, 2.0, 3.0, 4.0]
    ys = [2 * x for x in xs]
    full_grad = gradient_sum(w, xs, ys) / len(xs)
    micro_means = [gradient_sum(w, xs[i:i + 2], ys[i:i + 2]) / 2 for i in (0, 2)]
    accumulated = sum(g / 2 for g in micro_means)
    close(full_grad, accumulated)
    close(w - 0.01 * full_grad, w - 0.01 * accumulated)
    def mse(parameter):
        return sum((parameter * x - y) ** 2 for x, y in zip(xs, ys)) / len(xs)
    delta = 1e-6
    finite_difference = (mse(w + delta) - mse(w - delta)) / (2 * delta)
    assert math.isclose(full_grad, finite_difference, rel_tol=1e-8)
    results["equal_microbatch_gradient_and_finite_difference"] = {"full_grad": full_grad, "accumulated": accumulated, "finite_difference": finite_difference}

    token_counts, token_means = [2, 8], [1.0, 3.0]
    correct = sum(n * g for n, g in zip(token_counts, token_means)) / sum(token_counts)
    wrong = sum(token_means) / 2
    close(correct, 2.6)
    close(wrong, 2.0)
    results["unequal_token_normalization"] = {"correct": correct, "wrong_mean_of_means": wrong}

    actual_tail_means, configured_k = [1.0, 3.0], 4
    correct_tail = sum(actual_tail_means) / len(actual_tail_means)
    wrong_tail = sum(actual_tail_means) / configured_k
    close(correct_tail, 2)
    close(wrong_tail, 1)
    results["partial_accumulation_window"] = {"correct": correct_tail, "wrong": wrong_tail}

    world_size, global_n = 2, 10
    local_loss_sum_gradients = [2 * 1.0, 8 * 3.0]
    scaled_local = [world_size * g / global_n for g in local_loss_sum_gradients]
    ddp_average = sum(scaled_local) / world_size
    close(ddp_average, 2.6)
    wrong_accuracy = (1 / 1 + 0 / 9) / 2
    correct_accuracy = (1 + 0) / (1 + 9)
    close(wrong_accuracy, 0.5)
    close(correct_accuracy, 0.1)
    results["ddp_global_normalization"] = {"gradient": ddp_average, "global_accuracy": correct_accuracy, "wrong_rank_mean": wrong_accuracy}

    true_g, scale = [3.0, 4.0], 100
    correct_clip = clip_norm(true_g, 1)
    wrong_clip = [g / scale for g in clip_norm([g * scale for g in true_g], 1)]
    close(correct_clip[0], 0.6)
    close(correct_clip[1], 0.8)
    close(wrong_clip[0], 0.006)
    results["unscale_before_clip"] = {"correct": correct_clip, "wrong": wrong_clip}

    tiny, half_scale = 1e-8, 1024
    direct = half_round(tiny)
    scaled_back = half_round(tiny * half_scale) / half_scale
    assert direct == 0 and scaled_back > 0
    results["half_precision_underflow"] = {"direct": direct, "scaled_then_unscaled": scaled_back}

    # Demonstrate sampler padding: five items across two ranks require six slots.
    padded = list(range(5)) + [0]
    rank0, rank1 = padded[0::2], padded[1::2]
    assert len(rank0) == len(rank1) == 3 and rank0 + rank1 != list(range(5))
    assert len(set(rank0 + rank1)) == 5
    results["distributed_sampler_padding"] = {"rank0": rank0, "rank1": rank1, "repeated_id": 0}

    initial_state = {"w": 0.0, "momentum": 0.0, "step": 0, "cursor": 0}
    continuous, rng_cont = copy.deepcopy(initial_state), random.Random(7)
    continuous_trace = run_updates(continuous, rng_cont, 20)
    split, rng_split = copy.deepcopy(initial_state), random.Random(7)
    run_updates(split, rng_split, 7)
    checkpoint = {"state": split, "rng": rng_split.getstate(), "data_version": "toy-v1"}
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "checkpoint.json"
        path.write_text(json.dumps(checkpoint))
        saved = json.loads(path.read_text())
    resumed, rng_resumed = copy.deepcopy(saved["state"]), random.Random()
    rng_resumed.setstate(as_tuple(saved["rng"]))
    resumed_trace = run_updates(resumed, rng_resumed, 13)
    assert resumed == continuous and resumed_trace == continuous_trace[7:]
    assert rng_resumed.getstate() == rng_cont.getstate()
    results["full_state_resume"] = {"final_weight": resumed["w"], "step": resumed["step"], "exact_trace_match": True}

    no_momentum, rng_restore = copy.deepcopy(saved["state"]), random.Random()
    no_momentum["momentum"] = 0
    rng_restore.setstate(as_tuple(saved["rng"]))
    run_updates(no_momentum, rng_restore, 13)
    no_rng = copy.deepcopy(saved["state"])
    run_updates(no_rng, random.Random(7), 13)
    no_cursor, rng_restore2 = copy.deepcopy(saved["state"]), random.Random()
    no_cursor["cursor"] = 0
    rng_restore2.setstate(as_tuple(saved["rng"]))
    run_updates(no_cursor, rng_restore2, 13)
    assert no_momentum["w"] != continuous["w"]
    assert no_rng["w"] != continuous["w"]
    assert no_cursor["w"] != continuous["w"]
    results["missing_state_changes_trajectory"] = {"complete": continuous["w"], "no_optimizer_momentum": no_momentum["w"], "no_rng_restore": no_rng["w"], "no_data_cursor": no_cursor["w"]}

    print(json.dumps({"status": "PASS", "check_groups": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
