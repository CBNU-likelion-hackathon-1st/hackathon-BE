import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.store import games


class GamesApiTest(unittest.TestCase):
    def setUp(self):
        games.clear()
        self.client = TestClient(app)

    def test_balance_game_full_flow(self):
        start = self.client.post("/api/games", json={"mode": "balance"})
        self.assertEqual(start.status_code, 201)
        start_data = start.json()
        game_id = start_data["gameId"]
        prompt = start_data["nextPrompt"]

        for _ in range(3):
            turn = self.client.post(
                f"/api/games/{game_id}/turn",
                json={"input": prompt["choices"][0]},
            )
            self.assertEqual(turn.status_code, 200)
            turn_data = turn.json()
            prompt = turn_data["nextPrompt"]

        self.assertTrue(turn_data["ended"])
        result = self.client.get(f"/api/games/{game_id}/result")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["metrics"]["completedRounds"], 3)

    def test_battle_requires_opponent_type(self):
        response = self.client.post("/api/games", json={"mode": "battle"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_INPUT")

    def test_battle_opponents_are_available_for_home_cards(self):
        response = self.client.get("/api/battle/opponents")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 3)
        self.assertEqual(data["opponents"][0]["type"], "boss")
        self.assertIn("description", data["opponents"][0])
        self.assertIn("tags", data["opponents"][0])

    @patch("app.games.battle.gemini_battle.judge_turn")
    @patch("app.games.battle.gemini_battle.generate_persona_reply")
    def test_battle_game_starts_and_plays_a_turn(self, generate_reply, judge_turn):
        generate_reply.return_value = "성과로 보여주면 인정하지."
        judge_turn.return_value = {
            "user": {
                "logic": 8,
                "impact": 7,
                "flow": 8,
                "aggressionLevel": 0,
                "violations": [],
                "reason": "근거가 분명합니다.",
            },
            "ai": {
                "logic": 6,
                "impact": 6,
                "flow": 7,
                "aggressionLevel": 0,
                "violations": [],
                "reason": "무난한 반박입니다.",
            },
        }
        start = self.client.post(
            "/api/games",
            json={"mode": "battle", "opponentType": "boss"},
        )

        self.assertEqual(start.status_code, 201)
        self.assertEqual(start.json()["opponent"]["name"], "직장 상사")
        turn = self.client.post(
            f"/api/games/{start.json()['gameId']}/turn",
            json={"input": "지난달보다 성과가 20% 올랐습니다."},
        )
        self.assertEqual(turn.status_code, 200)
        self.assertFalse(turn.json()["ended"])
        self.assertIn("logic", turn.json()["analysis"])

    def test_word_chain_flow_can_finish_and_return_result(self):
        start = self.client.post("/api/games", json={"mode": "word_chain"})
        self.assertEqual(start.status_code, 201)
        start_data = start.json()

        turn = self.client.post(
            f"/api/games/{start_data['gameId']}/turn",
            json={"input": "잘못된단어"},
        )
        self.assertEqual(turn.status_code, 200)
        self.assertTrue(turn.json()["ended"])

        result = self.client.get(f"/api/games/{start_data['gameId']}/result")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["mode"], "word_chain")


if __name__ == "__main__":
    unittest.main()
