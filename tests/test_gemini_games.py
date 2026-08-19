import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services import gemini_games


class FakeGeminiError(RuntimeError):
    def __init__(self, code: int):
        super().__init__(f"Gemini error {code}")
        self.code = code


class GeminiRetryTest(unittest.TestCase):
    def setUp(self):
        self.settings = SimpleNamespace(gemini_model="gemini-test-model")
        logger_patcher = patch.object(gemini_games, "logger")
        logger_patcher.start()
        self.addCleanup(logger_patcher.stop)

    def _client_with_side_effects(self, side_effects: list[object]):
        generate_content = MagicMock(side_effect=side_effects)
        client = SimpleNamespace(
            models=SimpleNamespace(generate_content=generate_content)
        )
        return client, generate_content

    @patch.object(gemini_games.time, "sleep")
    @patch.object(gemini_games, "get_settings")
    @patch.object(gemini_games, "get_gemini_client")
    def test_transient_error_is_retried(
        self,
        get_client_mock,
        get_settings_mock,
        sleep_mock,
    ):
        response = SimpleNamespace(text='{"reply":"성공"}')
        client, generate_content = self._client_with_side_effects(
            [FakeGeminiError(503), response]
        )
        get_client_mock.return_value = client
        get_settings_mock.return_value = self.settings

        result = gemini_games.generate_json("테스트")

        self.assertEqual(result, {"reply": "성공"})
        self.assertEqual(generate_content.call_count, 2)
        sleep_mock.assert_called_once_with(0.5)

    @patch.object(gemini_games.time, "sleep")
    @patch.object(gemini_games, "get_settings")
    @patch.object(gemini_games, "get_gemini_client")
    def test_transient_error_stops_after_max_attempts(
        self,
        get_client_mock,
        get_settings_mock,
        sleep_mock,
    ):
        client, generate_content = self._client_with_side_effects(
            [FakeGeminiError(503) for _ in range(3)]
        )
        get_client_mock.return_value = client
        get_settings_mock.return_value = self.settings

        with self.assertRaises(gemini_games.GeminiGameError) as context:
            gemini_games.generate_json("테스트")

        self.assertIsInstance(context.exception.__cause__, FakeGeminiError)
        self.assertEqual(generate_content.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in sleep_mock.call_args_list],
            [0.5, 1.0],
        )

    @patch.object(gemini_games.time, "sleep")
    @patch.object(gemini_games, "get_settings")
    @patch.object(gemini_games, "get_gemini_client")
    def test_non_retryable_error_fails_immediately(
        self,
        get_client_mock,
        get_settings_mock,
        sleep_mock,
    ):
        client, generate_content = self._client_with_side_effects(
            [FakeGeminiError(400)]
        )
        get_client_mock.return_value = client
        get_settings_mock.return_value = self.settings

        with self.assertRaises(gemini_games.GeminiGameError):
            gemini_games.generate_json("테스트")

        self.assertEqual(generate_content.call_count, 1)
        sleep_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
