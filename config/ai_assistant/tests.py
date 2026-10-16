import json
import os
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import reverse
from google import genai


class AssistantViewsTests(TestCase):
    def setUp(self):
        self.client.post(
            reverse("personality_login"),
            {"name": "Alex", "personality": "teasing_supporter"},
        )

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_root_redirects_to_login(self):
        response = self.client.get("/")
        self.assertRedirects(
            response,
            reverse("personality_login"),
        )

    def test_home_requires_personality(self):
        self.client.session.flush()
        response = self.client.get(reverse("index"))
        self.assertRedirects(
            response,
            reverse("personality_login"),
        )

    def test_home_renders_chat_workspace(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="sidebar"')
        self.assertContains(response, 'class="conversation-scroll"')
        self.assertContains(response, 'class="composer"')
        self.assertContains(response, 'id="recent-chats"')
        self.assertContains(response, 'aria-label="Your chats"')
        self.assertNotContains(response, "Recent chats")
        self.assertContains(response, 'id="current-chat-item"')
        self.assertContains(response, 'id="offline-game"')
        self.assertContains(response, "js/offline-game.js")
        self.assertContains(
            response,
            "Ready to build something useful, Alex?",
        )
        self.assertContains(response, "How do I create a Django view and URL?")
        self.assertContains(response, "Help me debug a Python error")
        self.assertNotContains(response, "photosynthesis")

    def test_welcome_message_matches_selected_personality(self):
        self.client.post(
            reverse("personality_login"),
            {"name": "Sam", "personality": "calm_thinker"},
        )

        response = self.client.get(reverse("index"))

        self.assertContains(
            response,
            "What are you building today, Sam?",
        )

    def test_login_accepts_valid_selection(self):
        response = self.client.post(
            reverse("personality_login"),
            {"name": "Sam", "personality": "calm_thinker"},
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(
            self.client.session["assistant_name"], "Sam"
        )
        self.assertEqual(
            self.client.session["assistant_personality"], "calm_thinker"
        )

    def test_login_rejects_unknown_personality(self):
        response = self.client.post(
            reverse("personality_login"),
            {"name": "Sam", "personality": "custom"},
        )
        self.assertEqual(response.status_code, 400)

    def test_chat_rejects_invalid_json(self):
        response = self.client.post(
            reverse("ask_gemini"),
            data="{",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"error": "Invalid request."}
        )

    def test_chat_rejects_empty_message(self):
        response = self.client.post(
            reverse("ask_gemini"),
            data=json.dumps({"message": "   "}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("ai_assistant.views.genai.Client")
    def test_chat_returns_mocked_gemini_answer(self, mock_client):
        mock_client.return_value.models.generate_content.return_value.text = (
            "Plants use sunlight to make food."
        )

        response = self.client.post(
            reverse("ask_gemini"),
            data=json.dumps({"message": "Explain photosynthesis"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"answer": "Plants use sunlight to make food."},
        )

        mock_client.return_value.models.generate_content.assert_called_once()
        self.assertEqual(
            mock_client.return_value.models.generate_content.call_args.kwargs[
                "model"
            ],
            "gemini-3.8-flash",
        )
        self.assertEqual(
            mock_client.call_args.kwargs["http_options"]
            .retry_options.attempts,
            1,
        )
        self.assertEqual(
            mock_client.call_args.kwargs["http_options"].timeout,
            15000,
        )

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("ai_assistant.views.genai.Client")
    def test_chat_falls_back_when_gemini_model_is_busy(self, mock_client):
        generate_content = mock_client.return_value.models.generate_content
        generate_content.side_effect = [
            genai.errors.ServerError(
                503, {"error": {"message": "busy"}}
            ),
            SimpleNamespace(
                text="Leaves reflect green light."
            ),
        ]

        response = self.client.post(
            reverse("ask_gemini"),
            data=json.dumps({"message": "Why are leaves green?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "Leaves reflect green light."})
        self.assertEqual(
            [
                call.kwargs["model"]
                for call in generate_content.call_args_list
            ],
            ["gemini-3.8-flash", "gemini-flash-lite-latest"],
        )

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("ai_assistant.views.genai.Client")
    def test_chat_falls_back_after_gemini_deadline(self, mock_client):
        generate_content = mock_client.return_value.models.generate_content
        generate_content.side_effect = [
            genai.errors.ServerError(
                504, {"error": {"message": "deadline exceeded"}}
            ),
            SimpleNamespace(text="Chlorophyll reflects green light."),
        ]

        response = self.client.post(
            reverse("ask_gemini"),
            data=json.dumps({"message": "Why are leaves green?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"answer": "Chlorophyll reflects green light."},
        )
        self.assertEqual(
            [
                call.kwargs["model"]
                for call in generate_content.call_args_list
            ],
            ["gemini-3.8-flash", "gemini-flash-lite-latest"],
        )

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("ai_assistant.views.genai.Client")
    def test_chat_reports_when_all_gemini_models_are_busy(self, mock_client):
        generate_content = mock_client.return_value.models.generate_content
        generate_content.side_effect = genai.errors.ServerError(
            503, {"error": {"message": "busy"}}
        )

        response = self.client.post(
            reverse("ask_gemini"),
            data=json.dumps({"message": "Why are leaves green?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "error": (
                    "Gemini is temporarily busy. Please try again in a "
                    "moment."
                )
            },
        )
        self.assertEqual(generate_content.call_count, 4)

    def test_pwa_files_exist(self):
        for asset in (
            "css/styles.css",
            "js/app.js",
            "js/offline-game.js",
            "js/service-worker.js",
            "json/manifest.json",
            "img/ailogo.svg",
            "img/background.jpg",
        ):
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset))
