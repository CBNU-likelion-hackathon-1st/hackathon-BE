import unittest
from random import Random

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


if __name__ == "__main__":
    unittest.main()
