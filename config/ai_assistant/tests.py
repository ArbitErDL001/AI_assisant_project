import json
import os
from unittest.mock import patch

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import reverse


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

    def test_pwa_files_exist(self):
        for asset in (
            "css/styles.css",
            "js/app.js",
            "js/service-worker.js",
            "json/manifest.json",
            "img/ailogo.svg",
        ):
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset))
