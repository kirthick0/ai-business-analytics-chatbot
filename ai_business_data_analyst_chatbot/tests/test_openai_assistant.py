import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import httpx
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from modules.openai_assistant import (
    AssistantConfigurationError,
    AssistantRequestError,
    build_dataset_context,
    build_verified_result,
    generate_assistant_response,
)


class OpenAIAssistantTests(unittest.TestCase):
    def test_responses_api_uses_model_and_limited_context(self):
        client = MagicMock()
        client.responses.create.return_value = SimpleNamespace(output_text="A useful explanation.")
        frame = pd.DataFrame({"Revenue": [100, 200], "Customer": ["A", "B"]})

        answer = generate_assistant_response(
            "What is total revenue?",
            api_key=None,
            model="gpt-4.1-mini",
            history=[{"role": "user", "content": "Previous question"}],
            dataset_context=build_dataset_context(frame),
            verified_result=build_verified_result("Total Revenue: 300", pd.DataFrame({"Revenue": [300]})),
            client=client,
        )

        self.assertEqual(answer, "A useful explanation.")
        request = client.responses.create.call_args.kwargs
        self.assertEqual(request["model"], "gpt-4.1-mini")
        self.assertFalse(request["store"])
        self.assertEqual(request["input"][0]["content"], "Previous question")
        self.assertEqual(request["input"][-1]["content"], "What is total revenue?")
        self.assertIn("Pandas-calculated result", request["instructions"])
        self.assertNotIn("Customer A", build_dataset_context(frame))

    def test_missing_key_and_empty_question_are_rejected(self):
        with self.assertRaises(AssistantConfigurationError):
            generate_assistant_response("Hello", api_key=None)
        with self.assertRaises(ValueError):
            generate_assistant_response("  ", api_key="test-key")

    def test_invalid_key_has_actionable_error(self):
        client = MagicMock()
        client.responses.create.side_effect = AuthenticationError(
            "invalid key", response=MagicMock(), body={}
        )
        with self.assertRaisesRegex(AssistantConfigurationError, "API key"):
            generate_assistant_response("Hello", api_key="invalid", client=client)

    def test_quota_error_is_distinguished_from_rate_limit(self):
        client = MagicMock()
        client.responses.create.side_effect = RateLimitError(
            "insufficient quota",
            response=MagicMock(),
            body={"error": {"code": "insufficient_quota"}},
        )
        with self.assertRaisesRegex(AssistantRequestError, "quota or credits"):
            generate_assistant_response("Hello", api_key="test-key", client=client)

    def test_timeout_and_network_errors_are_actionable(self):
        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        for exception, expected in (
            (APITimeoutError(request=request), "timed out"),
            (APIConnectionError(message="offline", request=request), "Could not connect"),
        ):
            client = MagicMock()
            client.responses.create.side_effect = exception
            with self.subTest(exception=type(exception).__name__):
                with self.assertRaisesRegex(AssistantRequestError, expected):
                    generate_assistant_response("Hello", api_key="test-key", client=client)


if __name__ == "__main__":
    unittest.main()
