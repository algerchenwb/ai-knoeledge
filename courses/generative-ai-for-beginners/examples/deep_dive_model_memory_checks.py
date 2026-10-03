"""Pedagogical raw storage estimates, not device capacity predictions."""
import unittest


def positive_int(value):
    if type(value) is not int or value <= 0:
        raise ValueError("expected a positive integer")
    return value


def weight_bytes(parameters, bits):
    positive_int(parameters)
    positive_int(bits)
    if bits not in (2, 4, 8, 16, 32):
        raise ValueError("unsupported pedagogical bit width")
    return (parameters * bits + 7) // 8


def kv_bytes(batch, tokens, layers, kv_heads, head_dim, element_bytes):
    for value in (batch, tokens, layers, kv_heads, head_dim, element_bytes):
        positive_int(value)
    return batch * tokens * layers * 2 * kv_heads * head_dim * element_bytes


def gib(byte_count):
    return positive_int(byte_count) / (1024 ** 3)


class MemoryChecks(unittest.TestCase):
    def test_fp16_weights(self):
        self.assertEqual(weight_bytes(7_000_000_000, 16), 14_000_000_000)

    def test_4bit_weights(self):
        self.assertEqual(weight_bytes(7_000_000_000, 4), 3_500_000_000)

    def test_packing_rounds_up(self):
        self.assertEqual(weight_bytes(3, 4), 2)

    def test_binary_unit(self):
        self.assertEqual(gib(1_073_741_824), 1)

    def test_decimal_not_binary(self):
        self.assertNotEqual(gib(1_000_000_000), 1)

    def test_cache_example(self):
        self.assertEqual(kv_bytes(1, 4096, 32, 8, 128, 2), 536_870_912)

    def test_context_growth(self):
        self.assertEqual(kv_bytes(1, 8192, 32, 8, 128, 2), 2 * kv_bytes(1, 4096, 32, 8, 128, 2))

    def test_batch_growth(self):
        self.assertEqual(kv_bytes(2, 4096, 32, 8, 128, 2), 2 * kv_bytes(1, 4096, 32, 8, 128, 2))

    def test_kv_head_growth(self):
        self.assertEqual(kv_bytes(1, 4096, 32, 32, 128, 2), 4 * kv_bytes(1, 4096, 32, 8, 128, 2))

    def test_bad_weights(self):
        for value in (0, -1, True, 1.5, float('nan'), float('inf'), '7B'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    weight_bytes(value, 4)

    def test_bad_precision(self):
        for bits in (0, -4, 3, True, 4.0):
            with self.subTest(bits=bits):
                with self.assertRaises(ValueError):
                    weight_bytes(100, bits)

    def test_bad_cache_dimension(self):
        for position in range(6):
            for bad in (0, -1, True, 1.5):
                args = [1, 4096, 32, 8, 128, 2]
                args[position] = bad
                with self.subTest(position=position, bad=bad):
                    with self.assertRaises(ValueError):
                        kv_bytes(*args)


if __name__ == '__main__':
    unittest.main(verbosity=2)
