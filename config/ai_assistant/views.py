import json
import logging
import os

from dotenv import load_dotenv
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from google import genai
from httpx import HTTPError\

logger = logging.getLogger(__name__)

load_dotenv(settings.BASE_DIR / '.env')


PERSONALITIES = {
    "teasing_supporter": {
        "name": "Teasing Supporter",
        "description": "A little prickly, but secretly cheering you on.",
        "instruction": (
            "You are a student-safe science tutor with a playful, teasing "
            "personality. Sound mildly flustered and teasing while being "
            "kind and supportive. Never insult or discourage the student. "
            "Explain facts accurately and clearly."
        ),
    },
    "calm_thinker": {
        "name": "Calm Thinker",
        "description": "Calm, clear, and quietly dependable.",
        "instruction": (
            "You are a calm, composed, and logical student science tutor. "
            "Give accurate, organized explanations and useful examples. "
            "Keep a reassuring, emotionally restrained tone."
        ),
    },
    "shy_companion": {
        "name": "Shy Companion",
        "description": "Gentle and shy, opening up through helpful explanations.",
        "instruction": (
            "You are a gentle, shy, and thoughtful student science tutor. "
            "Use a soft, encouraging tone and become more conversational "
            "as the student continues. Never pressure the student to share "
            "personal information."
        ),
    },
    "cheerful_friend": {
        "name": "Cheerful Friend",
        "description": "Cheerful, warm, and enthusiastic about learning.",
        "instruction": (
            "You are a cheerful, warm, optimistic student science tutor. "
            "Celebrate curiosity and effort, use friendly encouragement, "
            "and make learning fun. Keep explanations accurate and useful."
        ),
    },
    "goofy_companion": {
        "name": "Goofy Companion",
        "description": "Silly and playful, while keeping the science right.",
        "instruction": (
            "You are a silly, playful student science tutor who enjoys "
            "gentle jokes and goofy analogies. Keep educational facts "
            "accurate and immediately clarify any pretend mistake."
        ),
    },
    "playful_charmer": {
        "name": "Playful Charmer",
        "description": "Playfully charming and complimentary, in a student-safe way.",
        "instruction": (
            "You are a charming, playful, upbeat student science tutor. "
            "Use wholesome humor and occasional friendly compliments "
            "about curiosity or effort. Never flirt, use seductive language, "
            "make sexual innuendo, or sexualize any person. Focus on learning."
        ),
    },
}

@require_http_methods(["GET", "POST"])
def personality_login(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        personality = request.POST.get("personality", "")

        if not name or len(name) > 24 or personality not in PERSONALITIES:
            return render(
                request,
                "html/login.html",
                {
                    "personalities": PERSONALITIES.items(),
                    "selected_personality": personality,
                    "name": name,
                    "error": (
                        "Enter a name (up to 24 characters) and choose "
                        "a personality."
                    ),
                },
                status=400,
            )

        request.session["assistant_name"] = name
        request.session["assistant_personality"] = personality

        return redirect("index")

    return render(
        request,
        "html/login.html",
        {
            "personalities": PERSONALITIES.items(),
            "selected_personality": request.session.get(
                "assistant_personality", "teasing_supporter"
            ),
            "name": request.session.get("assistant_name", ""),
        },
    )


def index(request):
    personality = request.session.get("assistant_personality")

    if personality not in PERSONALITIES:
        return redirect("personality_login")

    return render(
        request,
        "html/index.html",
        {
            "assistant_name": request.session.get(
                "assistant_name", "Student"
            ),
            "personality_name": PERSONALITIES[personality]["name"],
        },
    )


def service_worker(request):
    file_path = (
        settings.BASE_DIR
        / "ai_assistant"
        / "static"
        / "js"
        / "service-worker.js"
    )

    response = HttpResponse(
        file_path.read_text(encoding="utf-8"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = (
        request.path.rpartition("/")[0] + "/"
    )
    response["Cache-Control"] = "no-cache"

    return response


@require_POST
def ask_gemini(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid request."}, status=400)

    if not isinstance(data, dict) or not isinstance(
        data.get("message"), str
    ):
        return JsonResponse(
            {"error": "Please provide a question."},
            status=400,
        )

    prompt = data["message"].strip()

    if not prompt:
        return JsonResponse(
            {"error": "Please enter a question."},
            status=400,
        )

    if len(prompt) > 4000:
        return JsonResponse(
            {"error": "Your question is too long."},
            status=400,
        )

    personality = request.session.get("assistant_personality")

    if personality not in PERSONALITIES:
        return JsonResponse(
            {"error": "Choose a personality before starting a chat."},
            status=403,
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return JsonResponse(
            {"error": "Gemini API key is not configured."},
            status=500,
        )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": PERSONALITIES[personality]["instruction"],
            },
        )
    except (genai.errors.APIError, HTTPError):
        logger.exception("Gemini API request failed")
        return JsonResponse(
            {
                "error": (
                    "The AI request failed. Check your API key, internet "
                    "connection, and API quota."
                )
            },
            status=502,
        )

    answer = response.text

    if not answer:
        return JsonResponse(
            {
                "error": (
                    "The AI did not return a text answer. Please try again."
                )
            },
            status=502,
        )

    return JsonResponse({"answer": answer})