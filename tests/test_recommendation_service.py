import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SERVICE_DIR = ROOT_DIR / "services" / "recommendation-service"
CATALOG_PATH = SERVICE_DIR / "catalog.json"
RECOMMENDER_PATH = SERVICE_DIR / "recommender.py"


def load_recommender_module():
    spec = importlib.util.spec_from_file_location("recommender", RECOMMENDER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recommender"] = module
    spec.loader.exec_module(module)
    return module


class RecommendationServiceTests(unittest.TestCase):
    def setUp(self):
        self.recommender = load_recommender_module()
        self.catalog = self.recommender.load_catalog(CATALOG_PATH)

    def test_catalog_has_rich_metadata(self):
        self.assertGreaterEqual(len(self.catalog), 10)
        for item in self.catalog:
            self.assertIn("description", item)
            self.assertIn("difficulty", item)
            self.assertIn("duration", item)
            self.assertEqual(len(item["vector"]), 5)

    def test_rank_recommendations_returns_sorted_items(self):
        user_vector = self.recommender.default_user_vector({"username": "ai_builder"})
        recommendations = self.recommender.rank_items(self.catalog, user_vector, context="genai", limit=5)
        scores = [item["score"] for item in recommendations]

        self.assertEqual(len(recommendations), 5)
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all("signals" in item for item in recommendations))

    def test_interaction_updates_profile_vector(self):
        before = self.recommender.default_user_vector()
        item = next(item for item in self.catalog if item["item_id"] == "llm-prompt-engineering")

        after = self.recommender.update_profile_vector(
            before,
            item["vector"],
            event_type="like",
            rating=5,
        )

        self.assertNotEqual(before, after)
        self.assertEqual(len(after), 5)

    def test_ranked_items_are_json_serializable(self):
        user_vector = self.recommender.default_user_vector()
        recommendations = self.recommender.rank_items(self.catalog, user_vector, limit=3)
        encoded = json.dumps(recommendations)

        self.assertEqual(json.loads(encoded), recommendations)


if __name__ == "__main__":
    unittest.main()
