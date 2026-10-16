from django.test import TestCase, override_settings


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class AssistantFlowTests(TestCase):
    def test_root_redirects_to_personality_login(self):
        response = self.client.get("/")

        self.assertRedirects(
            response,
            "/ai_assistant/login/",
            fetch_redirect_response=False,
        )

    def test_login_page_renders_with_default_personality(self):
        response = self.client.get("/ai_assistant/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose your assistant's personality")
        self.assertRegex(
            response.content.decode(),
            r'value="teasing_supporter"\s+checked',
        )

    def test_valid_login_opens_chat_page(self):
        response = self.client.post(
            "/ai_assistant/login/",
            {
                "name": "Alex",
                "personality": "calm_thinker",
            },
        )

        self.assertRedirects(
            response,
            "/ai_assistant/",
            fetch_redirect_response=False,
        )

        response = self.client.get("/ai_assistant/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A little help for Alex")
        self.assertContains(
            response,
            'data-service-worker-url="/ai_assistant/service-worker.js"',
        )

    def test_service_worker_is_served_from_existing_staticfiles_folder(self):
        response = self.client.get("/ai_assistant/service-worker.js")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertContains(response, "self.skipWaiting()")
