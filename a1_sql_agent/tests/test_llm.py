import json
import unittest

import llm


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestLLMClient(unittest.TestCase):
    def test_chat_uses_injectable_transport(self):
        calls = {}

        def transport(url, data, headers, timeout):
            calls["url"] = url
            calls["body"] = json.loads(data.decode("utf-8"))
            calls["headers"] = headers
            calls["timeout"] = timeout
            return _FakeResponse(
                {
                    "message": {"role": "assistant", "content": "ok"},
                    "prompt_eval_count": 1,
                    "eval_count": 1,
                    "done_reason": "stop",
                }
            )

        client = llm.OllamaClient(
            model="qwen2.5:3b",
            base_url="http://localhost:11434",
            transport=transport,
        )
        result = client.chat(messages=[{"role": "user", "content": "hi"}])

        self.assertEqual(calls["url"], "http://localhost:11434/api/chat")
        self.assertEqual(calls["body"]["model"], "qwen2.5:3b")
        self.assertEqual(calls["body"]["messages"][0]["content"], "hi")
        self.assertEqual(result["message"]["content"], "ok")

    def test_chat_forwards_tools_and_options(self):
        seen = {}

        def transport(url, data, headers, timeout):
            seen["body"] = json.loads(data.decode("utf-8"))
            return _FakeResponse({"message": {"role": "assistant", "content": ""}})

        client = llm.OllamaClient(transport=transport)
        tools = [{"type": "function", "function": {"name": "ping"}}]
        client.chat(
            messages=[{"role": "user", "content": "x"}],
            tools=tools,
            options={"temperature": 0},
            keep_alive=0,
        )
        self.assertEqual(seen["body"]["tools"], tools)
        self.assertEqual(seen["body"]["options"], {"temperature": 0})
        self.assertEqual(seen["body"]["keep_alive"], 0)


if __name__ == "__main__":
    unittest.main()
