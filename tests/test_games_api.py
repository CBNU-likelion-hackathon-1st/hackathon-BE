import unittest

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

    def test_unimplemented_game_returns_400(self):
        response = self.client.post("/api/games", json={"mode": "battle"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "GAME_NOT_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
