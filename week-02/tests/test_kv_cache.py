import unittest

from kv_cache import kv_cache_bytes, model_config


class TestKVCache(unittest.TestCase):
    def setUp(self):
        self.config = model_config("qwen2.5:7b")

    def test_qwen25_7b_config(self):
        self.assertEqual(self.config["layers"], 28)
        self.assertEqual(self.config["kv_heads"], 4)
        self.assertEqual(self.config["head_dim"], 128)

    def test_bytes_per_token(self):
        self.assertEqual(kv_cache_bytes(self.config, 1), 2 * 28 * 4 * 128 * 2)

    def test_context_sizes(self):
        self.assertEqual(kv_cache_bytes(self.config, 8192), 448 * 1024 ** 2)
        self.assertEqual(kv_cache_bytes(self.config, 32768), 1792 * 1024 ** 2)

    def test_scales_linearly(self):
        self.assertEqual(
            kv_cache_bytes(self.config, 32768), 4 * kv_cache_bytes(self.config, 8192)
        )


if __name__ == "__main__":
    unittest.main()
