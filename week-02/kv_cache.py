MODELS = {
    "qwen2.5:7b": {
        "layers": 28,
        "kv_heads": 4,
        "head_dim": 128,
        "bytes_per_element": 2,
    }
}


def model_config(tag):
    return MODELS[tag]


def kv_cache_bytes(config, context_tokens):
    # Factor 2 is one K and one V tensor per layer.
    return (
        2
        * config["layers"]
        * config["kv_heads"]
        * config["head_dim"]
        * config["bytes_per_element"]
        * context_tokens
    )
