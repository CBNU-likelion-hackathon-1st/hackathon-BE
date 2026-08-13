import unittest
from random import Random

from app.games import balance


class BalanceGameTest(unittest.TestCase):
    def setUp(self):
        self.session = balance.start_game(Random(7))

    def test_start_game_selects_three_questions(self):
        self.assertEqual(len(self.session["questions"]), 3)
        self.assertEqual(self.session["round"], 1)
        self.assertEqual(len(balance.current_prompt(self.session)["choices"]), 2)

    def test_valid_choice_moves_to_next_round(self):
        choice = balance.current_prompt(self.session)["choices"][0]
        response = balance.play_turn(self.session, choice)

        self.assertEqual(response["round"], 2)
        self.assertFalse(response["ended"])
        self.assertIsNotNone(response["nextPrompt"])

    def test_invalid_choice_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "선택지"):
            balance.play_turn(self.session, "아무거나")

    def test_game_finishes_after_three_choices(self):
        for _ in range(3):
            choice = balance.current_prompt(self.session)["choices"][0]
            response = balance.play_turn(self.session, choice)

        self.assertTrue(response["ended"])
        self.assertEqual(self.session["status"], "finished")
        self.assertIsNone(response["nextPrompt"])
        self.assertEqual(balance.get_result(self.session)["metrics"]["completedRounds"], 3)


if __name__ == "__main__":
    unittest.main()
