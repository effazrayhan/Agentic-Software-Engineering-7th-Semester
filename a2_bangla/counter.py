import time


FIXED_SYSTEM_PROMPT = "You are a helpful assistant."


def _call_chat(client, prompt, system_prompt=FIXED_SYSTEM_PROMPT, temperature=0, seed=0, num_predict=256, keep_alive=0):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    options = {"temperature": temperature, "seed": seed, "num_predict": num_predict}
    return client.chat(messages=messages, options=options, keep_alive=keep_alive)


def count_tokens(client, prompt, system_prompt=FIXED_SYSTEM_PROMPT, temperature=0, seed=0, num_predict=256):
    """Call Ollama via client and return token/latency/output info.

    Returns dict with: input_tokens, output_tokens, latency_s, done_reason, output_text,
    and optional flags (e.g. missing_counts).
    keep_alive is always 0 to avoid prompt caching effects between calls.
    """
    t0 = time.time()
    resp = _call_chat(
        client,
        prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        seed=seed,
        num_predict=num_predict,
        keep_alive=0,
    )
    latency = time.time() - t0

    missing = False
    in_tok = resp.get("prompt_eval_count", None)
    out_tok = resp.get("eval_count", None)
    if in_tok is None or out_tok is None:
        missing = True
        in_tok = 0 if in_tok is None else in_tok
        out_tok = 0 if out_tok is None else out_tok

    message = resp.get("message") or {}
    output_text = message.get("content", "")
    if output_text is None:
        output_text = ""

    result = {
        "input_tokens": int(in_tok),
        "output_tokens": int(out_tok),
        "latency_s": latency,
        "done_reason": resp.get("done_reason"),
        "output_text": output_text,
    }
    if missing:
        result["missing_counts"] = True
    return result


def measure_baseline(client, system_prompt=FIXED_SYSTEM_PROMPT, temperature=0, seed=0, num_predict=256):
    """Measure template/system overhead once using a tiny prompt ('hi')."""
    return count_tokens(
        client,
        "hi",
        system_prompt=system_prompt,
        temperature=temperature,
        seed=seed,
        num_predict=num_predict,
    )


def check_cache(client, prompt="hi", system_prompt=FIXED_SYSTEM_PROMPT, temperature=0, seed=0, num_predict=256):
    """Run same prompt twice with keep_alive=0 and confirm prompt_eval_count identical.
    Returns (ok, first_input_tokens, second_input_tokens, details).
    Flags mismatch or missing counts.
    """
    r1 = _call_chat(client, prompt, system_prompt, temperature, seed, num_predict, keep_alive=0)
    r2 = _call_chat(client, prompt, system_prompt, temperature, seed, num_predict, keep_alive=0)
    a = r1.get("prompt_eval_count", None)
    b = r2.get("prompt_eval_count", None)
    details = {"first": a, "second": b}
    if a is None or b is None:
        return False, a, b, {**details, "flag": "missing_counts"}
    ok = (a == b)
    if not ok:
        return False, a, b, {**details, "flag": "mismatch"}
    return True, a, b, details


def cost_usd(input_tokens, output_tokens, in_rate_per_m=0.15, out_rate_per_m=0.60):
    return (input_tokens / 1_000_000.0) * in_rate_per_m + (output_tokens / 1_000_000.0) * out_rate_per_m
