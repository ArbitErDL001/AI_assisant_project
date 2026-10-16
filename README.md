# Lambda Xi Assistant

A Django-based app-development assistant powered by the Google Gemini API. Users choose an assistant personality, ask coding questions, and get responses from Gemini. The chat interface also includes browser-local conversation history, a PWA manifest, and an offline fish-feeding mini-game.

## Features

- Six selectable assistant personalities with distinct welcome messages and response styles.
- App-development prompts and a chat interface for coding questions.
- Gemini model fallback, bounded request timeouts, and useful API error responses.
- Recent conversations stored in browser `localStorage`.
- Responsive dark interface, installable PWA metadata, and an offline mini-game.

## Requirements

- Python compatible with Django 6.1.
- A Google Gemini API key for AI responses.
- Internet access for Gemini requests.

The exact Python dependencies and version ranges are in [`req.txt`](req.txt).

## Run locally on Windows

From the repository root in PowerShell:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r req.txt
```

Create a `.env` file in the repository root and add your key:

```text
GEMINI_API_KEY=your_gemini_api_key
```

Then run database migrations, tests, and the development server:

```powershell
python .\config\manage.py migrate
python .\config\manage.py test ai_assistant
python .\config\manage.py runserver 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/>. The root URL redirects to the personality selection page. For a full walkthrough, see [`TUTORIAL.txt`](TUTORIAL.txt).

## Project layout

```text
.
|-- req.txt
|-- README.md
|-- TUTORIAL.txt
|-- config/
|   |-- manage.py
|   |-- config/                 Django settings and root URLs
|   `-- ai_assistant/           Django app, views, tests, and app URLs
|       `-- ai_assistant/
|           |-- templates/html/ Chat and personality pages
|           `-- staticfiles/    CSS, JavaScript, images, and PWA manifest
`-- .env                       Local Gemini API key (not committed)
```

## Gemini API configuration

The Django view reads `GEMINI_API_KEY` from the root `.env` file using `python-dotenv`. The key is used only on the server; do not put it in HTML or browser JavaScript. The chat endpoint is `/ai_assistant/ask/`. It validates the request and session personality, calls Gemini, then returns a JSON answer.

The server tries a sequence of Gemini models when a model is unavailable, busy, rate-limited, or times out. API usage is subject to Google's model availability, quotas, and billing policies.

## Tests

Run the application tests explicitly:

```powershell
python .\config\manage.py test ai_assistant
```

The tests cover the Django views, personality-dependent welcome messages, static assets, and Gemini fallback/error behavior.

## Security and deployment

This repository is configured for local development, not production deployment. Before deploying, move Django's `SECRET_KEY` out of source code, set `DEBUG=False`, configure `ALLOWED_HOSTS`, configure HTTPS and secure cookies, and provide `GEMINI_API_KEY` through the hosting provider's secret/environment-variable system. Review Django's deployment checklist and run:

```powershell
python .\config\manage.py check --deploy
```

Do not commit `.env` or publish API keys. Conversation history is stored in the visitor's browser and is not shared across devices.
