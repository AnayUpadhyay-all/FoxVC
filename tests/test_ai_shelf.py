"""
Tests for FoxVC AI & LLM Agent Shelf (fuse ai).
Verifies AI orchestration, agent state retention, message formatting, and model maps.
"""

import unittest
from engine.shelves.ai import (
    get_ai_shelf,
    FoxAIAgent,
    _resolve_api_key,
    DEFAULT_MODELS,
    DEFAULT_ENDPOINTS
)


class TestAIShelf(unittest.TestCase):
    def setUp(self):
        self.ai = get_ai_shelf()

    def test_shelf_exports(self):
        self.assertIn("aiPrompt", self.ai)
        self.assertIn("aiChat", self.ai)
        self.assertIn("aiAgent", self.ai)
        self.assertIn("aiIsOnline", self.ai)
        self.assertIn("AI_MODELS", self.ai)

    def test_default_models_and_endpoints(self):
        self.assertEqual(DEFAULT_MODELS["ollama"], "llama3")
        self.assertEqual(DEFAULT_MODELS["groq"], "llama-3.3-70b-versatile")
        self.assertIn("localhost:11434", DEFAULT_ENDPOINTS["ollama"])
        self.assertIn("api.groq.com", DEFAULT_ENDPOINTS["groq"])

    def test_ai_agent_state_retention(self):
        agent = FoxAIAgent("You are an autonomous DevOps supervisor.", provider="ollama")
        self.assertEqual(len(agent.history), 1)
        self.assertEqual(agent.history[0]["role"], "system")
        self.assertEqual(agent.history[0]["content"], "You are an autonomous DevOps supervisor.")

        agent.reset()
        self.assertEqual(len(agent.history), 1)

    def test_ai_is_online_graceful_offline(self):
        # A non-existent port should return 0 instead of throwing an unhandled exception
        status = self.ai["aiIsOnline"](endpoint="http://127.0.0.1:59999")
        self.assertEqual(status, 0)

    def test_api_key_resolver(self):
        key = _resolve_api_key("groq", "explicit_test_key_123")
        self.assertEqual(key, "explicit_test_key_123")


if __name__ == "__main__":
    unittest.main()
