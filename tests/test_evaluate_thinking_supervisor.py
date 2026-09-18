import unittest
import time
from unittest.mock import patch

from scripts.evaluate_thinking_supervisor import (
    chat_url, normalized_answer, parse_event, should_interrupt, stream_chat,
)


class ThinkingSupervisorTests(unittest.TestCase):
    def test_chat_url_accepts_base_or_complete_path(self):
        self.assertEqual(chat_url("https://example.test/v1"), "https://example.test/v1/chat/completions")
        self.assertEqual(chat_url("https://example.test/v1/chat/completions"), "https://example.test/v1/chat/completions")

    def test_parse_wrapped_sse_event(self):
        self.assertEqual(parse_event(b'data: {"data":{"choices":[{"delta":{"reasoning":"step"}}]}}\n')["choices"][0]["delta"]["reasoning"], "step")
        self.assertIsNone(parse_event(b"data: [DONE]\n"))
        with self.assertRaisesRegex(RuntimeError, "unsuccessful"):
            parse_event(b'data: {"success":false,"data":{"error":"secret omitted"}}\n')

    def test_conservative_interrupt(self):
        answer = {"action": {"choice": "answer_now", "probabilities": {"answer_now": 0.85}}, "needs_more": {"noul": 0.1}}
        self.assertTrue(should_interrupt(answer, 0.7))
        answer["needs_more"]["noul"] = 0.4
        self.assertFalse(should_interrupt(answer, 0.7))

    def test_answer_normalization_preserves_numbers(self):
        self.assertEqual(normalized_answer(" Yes. \n"), "yes")
        self.assertEqual(normalized_answer("0.8"), "0.8")
        self.assertNotEqual(normalized_answer("0.75"), "0.8")

    def test_stream_can_be_interrupted_before_final_content(self):
        class FakeStream:
            headers = {"Content-Type": "text/event-stream"}

            def __init__(self):
                self.closed = False

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.closed = True

            def __iter__(self):
                for _ in range(100):
                    time.sleep(0.002)
                    yield b'data: {"data":{"choices":[{"delta":{"reasoning":"step "}}]}}\n'
                yield b'data: {"data":{"choices":[{"delta":{"content":"37"},"finish_reason":"stop"}]}}\n'

        stream = FakeStream()
        verdict = {
            "answer": {
                "action": {"choice": "answer_now", "probabilities": {"answer_now": 0.95}},
                "needs_more": {"noul": 0.05},
            },
            "latency_ms": 1,
        }
        config = {
            "DEEPSEEK_MODEL": "test-model", "DEEPSEEK_REASONING_EFFORT": "high",
            "DEEPSEEK_BASE_URL": "https://example.test/v1", "DEEPSEEK_API_KEY": "test-key",
            "TYPESAFE_API_KEY": "test-jev-key",
        }
        with patch("scripts.evaluate_thinking_supervisor.urllib.request.urlopen", return_value=stream), patch(
            "scripts.evaluate_thinking_supervisor.judge", return_value=verdict
        ):
            result = stream_chat(config, "7 * 6 - 5?", "intervene", 0.7, 100, 10)
        self.assertTrue(result["interrupted"])
        self.assertTrue(stream.closed)
        self.assertEqual(result["content"], "")
        self.assertTrue(result["checks"][0]["would_interrupt"])


if __name__ == "__main__":
    unittest.main()
