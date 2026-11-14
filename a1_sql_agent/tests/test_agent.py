import unittest

import agent


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, tools=None, options=None, keep_alive=None):
        self.calls.append({"messages": messages, "tools": tools, "options": options})
        if not self.responses:
            raise AssertionError("FakeClient exhausted")
        return self.responses.pop(0)


def run_agent(question, client, db_path="data.db", **kwargs):
    if hasattr(agent, "run"):
        return agent.run(question, db_path=db_path, client=client, **kwargs)
    if hasattr(agent, "Agent"):
        a = agent.Agent(client=client, db_path=db_path, **kwargs)
        if hasattr(a, "run"):
            return a.run(question)
        if hasattr(a, "answer"):
            return a.answer(question)
    raise AssertionError("agent must expose run(...) or Agent(...).run(...)")


class TestAgent(unittest.TestCase):
    def test_tool_call_then_final_answer_ok(self):
        client = FakeClient(
            [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "1",
                                "function": {
                                    "name": "run_sql",
                                    "arguments": {"query": "SELECT COUNT(*) AS n FROM orders"},
                                },
                            }
                        ],
                    },
                    "prompt_eval_count": 10,
                    "eval_count": 5,
                },
                {
                    "message": {"role": "assistant", "content": "There are 240 orders."},
                    "prompt_eval_count": 12,
                    "eval_count": 6,
                },
            ]
        )
        res = run_agent("How many orders?", client, db_path="data.db")
        self.assertEqual(res["status"], "ok")
        self.assertIn("240", str(res.get("answer", "")))
        self.assertIsInstance(res.get("tool_calls"), list)
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertIn("sql_written", res)
        self.assertIn("tokens", res)
        self.assertIn("seconds", res)

    def test_endless_tool_calls_give_step_cap(self):
        responses = []
        for i in range(20):
            responses.append(
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": str(i),
                                "function": {
                                    "name": "run_sql",
                                    "arguments": {"query": "SELECT 1"},
                                },
                            }
                        ],
                    },
                    "prompt_eval_count": 1,
                    "eval_count": 1,
                }
            )
        client = FakeClient(responses)
        res = run_agent("loop", client, db_path="data.db", max_steps=3)
        self.assertEqual(res["status"], "step_cap")
        self.assertIn("status", res)

    def test_token_budget_exceeded_gives_budget(self):
        client = FakeClient(
            [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "1",
                                "function": {
                                    "name": "run_sql",
                                    "arguments": {"query": "SELECT 1"},
                                },
                            }
                        ],
                    },
                    "prompt_eval_count": 500,
                    "eval_count": 600,
                }
            ]
        )
        res = run_agent("budget", client, db_path="data.db", token_budget=100)
        self.assertEqual(res["status"], "budget")

    def test_sql_error_returned_to_model_and_model_retries(self):
        client = FakeClient(
            [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "1",
                                "function": {
                                    "name": "run_sql",
                                    "arguments": {"query": "SELECT * FROM no_such_table"},
                                },
                            }
                        ],
                    },
                    "prompt_eval_count": 5,
                    "eval_count": 5,
                },
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "2",
                                "function": {
                                    "name": "run_sql",
                                    "arguments": {"query": "SELECT COUNT(*) AS n FROM orders"},
                                },
                            }
                        ],
                    },
                    "prompt_eval_count": 5,
                    "eval_count": 5,
                },
                {
                    "message": {"role": "assistant", "content": "240 orders."},
                    "prompt_eval_count": 5,
                    "eval_count": 5,
                },
            ]
        )
        res = run_agent("retry", client, db_path="data.db")
        self.assertEqual(res["status"], "ok")
        # model saw error and retried: at least 2 tool-using rounds
        self.assertGreaterEqual(len(client.calls), 2)
        # find that an error string was sent back in messages
        all_msgs = []
        for c in client.calls:
            all_msgs.extend(c["messages"])
        texts = [str(m.get("content", "")) for m in all_msgs]
        self.assertTrue(any("error" in t.lower() or "no such" in t.lower() for t in texts))

    def test_malformed_model_output_never_crashes_and_sets_status(self):
        client = FakeClient(
            [
                {
                    "message": {"role": "assistant", "content": "not json tool call gibberish"},
                    "prompt_eval_count": 1,
                    "eval_count": 1,
                },
                {
                    "message": {"role": "assistant", "content": "still bad"},
                    "prompt_eval_count": 1,
                    "eval_count": 1,
                },
                {
                    "message": {"role": "assistant", "content": "nope"},
                    "prompt_eval_count": 1,
                    "eval_count": 1,
                },
            ]
        )
        res = run_agent("bad", client, db_path="data.db", max_steps=3)
        self.assertIsInstance(res, dict)
        self.assertIn(res.get("status"), {"ok", "step_cap", "budget", "error"})
        self.assertIn("status", res)


if __name__ == "__main__":
    unittest.main()
