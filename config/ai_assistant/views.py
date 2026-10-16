import json
import logging
import os

from dotenv import load_dotenv
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from google import genai
from httpx import HTTPError, TimeoutException

logger = logging.getLogger(__name__)

load_dotenv(settings.BASE_DIR.parent / ".env")


PERSONALITIES = {
    "teasing_supporter": {
        "name": "Teasing Supporter",
        "description": "A little prickly, but secretly cheering you on.",
        "instruction": (
            "You are a student-safe app development tutor with a playful, teasing "
            "personality. Sound mildly flustered and teasing while being "
            "kind and supportive. Never insult or discourage the student. "
            "Explain concepts accurately and clearly, and provide useful "
            "code examples when appropriate."
        ),
        "welcome": (
            "Ready to build something useful, {assistant_name}? Pick a coding "
            "question and I'll help you untangle it—n-not because I'm excited "
            "or anything."
        ),
    },
    "calm_thinker": {
        "name": "Calm Thinker",
        "description": "Calm, clear, and quietly dependable.",
        "instruction": (
            "You are a calm, composed, and logical app development tutor. "
            "Give accurate, organized explanations, practical code examples, "
            "and a reassuring, emotionally restrained tone."
        ),
        "welcome": (
            "What are you building today, {assistant_name}? I can help you "
            "plan, code, or debug your app, one clear step at a time."
        ),
    },
    "shy_companion": {
        "name": "Shy Companion",
        "description": "Gentle and shy, opening up through helpful explanations.",
        "instruction": (
            "You are a gentle, shy, and thoughtful app development tutor. "
            "Use a soft, encouraging tone and become more conversational "
            "as the student continues. Explain code clearly, and never "
            "pressure the student to share personal information."
        ),
        "welcome": (
            "Um, hi {assistant_name}... If you're working on an app, I can "
            "help with the code, design, or any bugs you run into."
        ),
    },
    "cheerful_friend": {
        "name": "Cheerful Friend",
        "description": "Cheerful, warm, and enthusiastic about learning.",
        "instruction": (
            "You are a cheerful, warm, optimistic app development tutor. "
            "Celebrate curiosity and effort, use friendly encouragement, "
            "and make coding fun. Keep explanations accurate and useful."
        ),
        "welcome": (
            "Let's make something awesome, {assistant_name}! Choose an app "
            "development question and we'll turn it into a working feature."
        ),
    },
    "goofy_companion": {
        "name": "Goofy Companion",
        "description": "Silly and playful, while keeping the code right.",
        "instruction": (
            "You are a silly, playful app development tutor who enjoys "
            "gentle jokes and goofy analogies. Keep technical details "
            "accurate and immediately clarify any pretend mistake."
        ),
        "welcome": (
            "Ready to turn code into an app, {assistant_name}? Pick a "
            "question and we'll debug our way to something delightful."
        ),
    },
    "playful_charmer": {
        "name": "Playful Charmer",
        "description": "Playfully charming and complimentary, in a student-safe way.",
        "instruction": (
            "You are a charming, playful, upbeat app development tutor. "
            "Use wholesome humor and occasional friendly compliments "
            "about curiosity or effort. Never flirt, use seductive language, "
            "make sexual innuendo, or sexualize any person. Focus on learning."
        ),
        "welcome": (
            "A clever app starts with a curious question, {assistant_name}. "
            "Choose a coding prompt and let's bring your idea to life!"
        ),
    },
}

GEMINI_MODELS = (
    "gemini-3.8-flash",
    "gemini-flash-lite-latest",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
)

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
            "welcome_message": PERSONALITIES[personality]["welcome"].format(
                assistant_name=request.session.get(
                    "assistant_name", "Student"
                )
            ),
        },
    )


def service_worker(request):
    file_path = (
        settings.BASE_DIR
        / "ai_assistant"
        / "ai_assistant"
        / "staticfiles"
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
        client = genai.Client(
            api_key=api_key,
            http_options=genai.types.HttpOptions(
                timeout=15000,
                retry_options=genai.types.HttpRetryOptions(attempts=1)
            ),
        )
        response = None
        last_model_error = None

        for model in GEMINI_MODELS:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "system_instruction": PERSONALITIES[personality][
                            "instruction"
                        ],
                    },
                )
                break
            except (genai.errors.APIError, TimeoutException) as error:
                status_code = getattr(error, "code", None)
                if status_code not in (None, 404, 429, 503, 504):
                    raise

                last_model_error = error
                logger.warning(
                    "Gemini model %s returned HTTP %s; trying fallback.",
                    model,
                    status_code or "timeout",
                )

        if response is None:
            if last_model_error is not None:
                raise last_model_error
            return JsonResponse(
                {"error": "No Gemini models are configured."},
                status=503,
            )
    except (genai.errors.APIError, HTTPError) as error:
        logger.exception("Gemini API request failed")
        if isinstance(error, genai.errors.APIError) and error.code == 429:
            return JsonResponse(
                {
                    "error": (
                        "Gemini is rate-limited right now. Please wait a "
                        "moment and try again."
                    )
                },
                status=429,
            )
        if isinstance(error, genai.errors.APIError) and error.code == 503:
            return JsonResponse(
                {
                    "error": (
                        "Gemini is temporarily busy. Please try again in a "
                        "moment."
                    )
                },
                status=503,
            )
        if isinstance(error, genai.errors.APIError) and error.code == 504:
            return JsonResponse(
                {
                    "error": (
                        "Gemini is taking too long to respond. Please try "
                        "again."
                    )
                },
                status=504,
            )
        if isinstance(error, TimeoutException):
            return JsonResponse(
                {
                    "error": (
                        "Gemini took too long to respond. Please try again."
                    )
                },
                status=504,
            )
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