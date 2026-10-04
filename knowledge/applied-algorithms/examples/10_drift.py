"""Independent first-alarm upward PH, alpha=1; not a complete River port."""
def first_alarm(stream, threshold, delta=0.005, min_instances=30):
    mean = cumulative = 0.
    minimum = float("inf")
    for n, value in enumerate(stream, 1):
        mean += (value - mean) / n
        cumulative += value - mean - delta
        minimum = min(minimum, cumulative)
        if n >= min_instances and cumulative - minimum > threshold:
            return n
    return None

assert first_alarm([0.] * 500, threshold=5) is None
assert first_alarm([1.] * 500, threshold=5) is None
step = [0.] * 100 + [1.] * 100
early = first_alarm(step, threshold=5)
late = first_alarm(step, threshold=20)
assert early is not None and late is not None
assert 100 < early < late <= 200
print(f"PASS stable streams, upward step, threshold sensitivity (alarms {early}, {late})")
