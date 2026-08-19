import unittest
import json
from random import Random
from tempfile import TemporaryDirectory
from pathlib import Path

from app.games import word_chain


class WordChainGameTest(unittest.TestCase):
    def setUp(self):
        self.session = word_chain.start_game(Random(1))

    def _valid_word(self) -> str:
        required = self.session["last_word"][-1]
        return next(
            word
            for word in word_chain.WORDS
            if word.startswith(required) and word not in self.session["used_words"]
        )

    def test_start_game_returns_required_syllable(self):
        response = word_chain.get_start_response(self.session)

        self.assertEqual(response["nextPrompt"], response["message"][-1])
        self.assertEqual(response["wordHistory"], [response["message"]])

    def test_valid_word_returns_ai_word(self):
        response = word_chain.play_turn(self.session, self._valid_word())

        self.assertTrue(response["accepted"])
        self.assertGreaterEqual(len(response["wordHistory"]), 2)
        if not response["ended"]:
            self.assertEqual(response["nextPrompt"], response["reply"][-1])

    def test_wrong_starting_syllable_ends_game(self):
        response = word_chain.play_turn(self.session, "학교")

        self.assertFalse(response["accepted"])
        self.assertTrue(response["ended"])
        self.assertEqual(response["winner"], "ai")
        self.assertEqual(word_chain.get_result(self.session)["mode"], "word_chain")

    def test_unknown_word_ends_game(self):
        required = self.session["last_word"][-1]
        response = word_chain.play_turn(self.session, f"{required}가나다")

        self.assertFalse(response["accepted"])
        self.assertTrue(response["ended"])
        self.assertIn("단어 목록", response["reply"])

    def test_official_dictionary_noun_is_accepted(self):
        session = word_chain.start_game(Random(1))
        session["last_word"] = "영화"
        session["used_words"] = ["영화"]

        valid, reason = word_chain.validate_word(session, "화장")

        self.assertTrue(valid, reason)
        self.assertGreater(len(word_chain.WORDS), 20_000)

    def test_word_json_has_no_duplicates_and_supports_every_start_word(self):
        self.assertEqual(len(word_chain.WORDS), len(set(word_chain.WORDS)))
        self.assertEqual(list(word_chain.START_WORDS), sorted(word_chain.START_WORDS))
        self.assertEqual(list(word_chain.WORDS), sorted(word_chain.WORDS))
        for start_word in word_chain.START_WORDS:
            self.assertTrue(any(word.startswith(start_word[-1]) for word in word_chain.WORDS))

    def test_invalid_word_json_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "words.json"
            path.write_text(
                json.dumps({"start_words": ["사과"], "words": ["과자", "과자"]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "중복"):
                word_chain.load_word_data(path)


if __name__ == "__main__":
    unittest.main()
