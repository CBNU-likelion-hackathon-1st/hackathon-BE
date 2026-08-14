import unittest
from unittest.mock import patch

from app.games import battle


SAFE_JUDGEMENT = {
    "user": {
        "logic": 8,
        "impact": 8,
        "flow": 8,
        "aggressionLevel": 0,
        "violations": [],
        "reason": "상대의 말을 논리적으로 잘 받아쳤습니다.",
    },
    "ai": {
        "logic": 6,
        "impact": 6,
        "flow": 6,
        "aggressionLevel": 0,
        "violations": [],
        "reason": "무난하게 반박했습니다.",
    },
}


class BattleGameTest(unittest.TestCase):
    def test_opponent_list_contains_card_information(self):
        opponents = battle.list_opponents()

        self.assertEqual(
            [opponent["type"] for opponent in opponents],
            ["boss", "older_brother", "ex"],
        )
        self.assertTrue(all(opponent["description"] for opponent in opponents))
        self.assertTrue(all(len(opponent["tags"]) == 2 for opponent in opponents))

    def test_start_game_supports_only_three_personas(self):
        for opponent_type in ("boss", "older_brother", "ex"):
            session = battle.start_game(opponent_type)
            response = battle.get_start_response(session)
            self.assertEqual(response["opponent"]["type"], opponent_type)
            self.assertEqual(response["maxRounds"], 5)

        with self.assertRaisesRegex(ValueError, "opponentType"):
            battle.start_game("friend")

    @patch("app.games.battle.gemini_battle.judge_turn", return_value=SAFE_JUDGEMENT)
    @patch(
        "app.games.battle.gemini_battle.generate_persona_reply",
        return_value="그래도 결과로 증명해야 하지 않겠어?",
    )
    def test_five_turns_finish_with_user_win(self, _reply, _judge):
        session = battle.start_game("boss")

        for index in range(5):
            response = battle.play_turn(session, f"제 근거는 결과 {index}에 있습니다.")

        self.assertTrue(response["ended"])
        self.assertEqual(response["winner"], "me")
        result = battle.get_result(session)
        self.assertEqual(result["metrics"]["completedRounds"], 5)
        self.assertEqual(result["metrics"]["logic"], 80)

    @patch("app.games.battle.gemini_battle.generate_persona_reply")
    def test_profanity_causes_immediate_loss_without_gemini(self, generate_reply):
        session = battle.start_game("older_brother")

        response = battle.play_turn(session, "닥쳐, 더 듣기 싫어")

        self.assertTrue(response["ended"])
        self.assertEqual(response["winner"], "ai")
        self.assertEqual(response["score"], {"me": 0, "ai": 100})
        generate_reply.assert_not_called()

    def test_anger_reduces_score_but_does_not_immediately_end_game(self):
        calm_score, _ = battle.calculate_turn_score(
            {"logic": 8, "impact": 8, "flow": 8, "aggressionLevel": 0}
        )
        angry_score, analysis = battle.calculate_turn_score(
            {"logic": 8, "impact": 8, "flow": 8, "aggressionLevel": 2}
        )

        self.assertEqual(calm_score - angry_score, 15)
        self.assertEqual(analysis["angerPenalty"], 15)

    def test_allowed_word_is_not_mistaken_for_profanity(self):
        self.assertIsNone(battle.detect_critical_violation("오늘이 새로운 시발점입니다."))


if __name__ == "__main__":
    unittest.main()
