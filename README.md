# VibeShift AI

VibeShift AI is a private communication workspace for rewriting drafts by audience and tone. It computes text differences and word counts in the browser, provides a deterministic, explicitly heuristic tone estimate, and uses a configurable backend text-generation provider for rewrites. It does not fabricate output when inference is unavailable.

## Features

- Four configurable personas and three length preferences.
- Optional context, audience, and target language.
- Vision summaries for JPEG, PNG, and WebP images, optional image questions, and persona transformation of the reviewed summary.
- Backend text generation with request validation, timeouts, and clear provider errors.
- Word-level insertion/deletion highlights and word count change calculated from actual text.
- Text-based tone estimates with cue phrases and uncertainty disclosure.
- Browser speech recognition (when supported), browser text-to-speech, and image preview.
- SQLite registration/login endpoints with password hashing and per-account history ownership.
- Responsive light/dark workspace.

## Requirements

- Node.js 20+ and npm.
- Python 3.10+.
- For real AI transformations, a Gemini API key is required. The app defaults to a Gemini OpenAI-compatible endpoint and `gemini-3.5-flash-lite`.

## Public shareable deployment (Render)

The project includes a Render Blueprint and Dockerfile for a single-origin deployment. The Docker image builds the existing Vite UI and serves it through Flask, so browser `/api` calls stay same-origin and sessions work over HTTPS. Render assigns the public `onrender.com` address after deployment.

To deploy, put this project in a **private GitHub repository** (confirm `backend/.env` and `backend/vibeshift.sqlite3` are not committed), connect that repository to Render, and create the service from its Blueprint using `render.yaml`. When Render asks for `AI_API_KEY`, add the existing Gemini key in Render's secret environment-variable form; do not add it to source files. The Blueprint generates `FLASK_SECRET_KEY` and sets secure cookies. Leave Gemini billing disabled. No API key is included in the Docker image.

Render's Free web service can sleep after inactivity and may restart; the first visit after sleeping can take a while. Its filesystem is ephemeral, so the SQLite account/history data is not durable across restarts. This app's current visible history is browser-session memory; use persistent managed storage before relying on account history. Free hosting availability and limits are controlled by Render and can change.
## One-click Codex development preview

From the project in Codex, start the integrated frontend and backend with:

```powershell
npm run dev:stack
```

The launcher starts Flask from the project virtual environment (Flask loads `backend/.env` relative to `backend/app.py`) and Vite with the matching `/api` proxy. It checks the health endpoint through the frontend before printing the preview URL. It reuses only the project-identified VibeShift API or a VibeShift preview with a healthy matching API; occupied ports owned by other services are left alone and the launcher chooses another available port. Keep the Codex terminal session open while using the preview; press Ctrl+C there to stop only services started by this launcher. API keys are never printed.

## Run locally

From the repository root:

```powershell
npm install
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

Edit `backend/.env` and set `AI_API_KEY` to a Gemini key. The default base URL and model are preconfigured in `backend/.env.example`; leave the Google Cloud project on the free tier and do not enable billing. Flask loads `backend/.env` relative to `backend/app.py` on startup. The Flask development server defaults to port 5001; set `$env:PORT` to override it. Then run:

```powershell
python backend/app.py
```

In another terminal:

```powershell
npm run dev
```

Open the Vite URL printed in the terminal. The UI proxies same-origin `/api` requests to Flask at `127.0.0.1:5001`. Set `VIBESHIFT_BACKEND_URL` before starting Vite to override that target. This proxy avoids cross-origin browser requests; Flask binds to loopback by default.

## Environment

| Name | Purpose |
|---|---|
| `FLASK_SECRET_KEY` | Required for secure production sessions. The development fallback must not be used on a public deployment. |
| `AI_API_KEY` | Backend-only provider key. Required for real rewrite inference. |
| `AI_BASE_URL` | Defaults to Gemini’s OpenAI-compatible endpoint: `https://generativelanguage.googleapis.com/v1beta/openai/`. |
| `AI_MODEL` | Defaults to `gemini-3.5-flash-lite`, which supports text and image input; standard image input and text output are currently listed as free-tier, subject to account access, rate limits, and quota. |
| `COOKIE_SECURE` | Set to `1` behind HTTPS in production. |

The backend uses the Chat Completions-compatible REST interface. Google documents this compatibility, including the Gemini endpoint and model names, in its [OpenAI compatibility guide](https://ai.google.dev/gemini-api/docs/openai/). Google’s [model card](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) confirms image input support. Its [pricing page](https://ai.google.dev/gemini-api/docs/pricing) currently lists standard image input and text output as free-tier, subject to account eligibility, region, rate, and quota limits. It still requires an API key. Create the key in [Google AI Studio](https://aistudio.google.com/apikey) for a project with no billing enabled; do not select or attach a paid-billing project. Free-tier submitted content may be used by Google to improve products according to its pricing disclosure, so avoid confidential messages unless that is acceptable. The app never turns on billing. Provider credentials stay in `backend/.env`, which is gitignored. If the free quota is exhausted, the app returns a retry-later message; it will not upgrade the account.

## Run provider tests

Run `python -m unittest tests.test_provider tests.test_image_vision -v`. These tests mock provider responses to verify JSON, image-type/size validation, request encoding, and provider-error handling. They do not replace a real Gemini request. A successful live transformation requires your own API key.

## Local-only / external capabilities

- Text length counts, diff, and heuristic tone analysis run locally in the browser/backend and need no paid API.
- Text rewrite requires a Gemini API key. `gemini-3.5-flash-lite` is listed as free-tier for text input/output at the time this README was updated; quota and access can vary by region/project. No billing is enabled by this app.
- Browser speech recognition depends on browser support and permissions; recognition may be processed by the browser vendor. Browser speech synthesis uses the installed browser/OS voices and does not apply genuine expressive controls beyond rate adjustment.
- Image analysis sends the selected image to the configured vision-capable Gemini model only after the user chooses Analyze image. It returns a factual summary and optional answer; the user reviews the summary in the draft editor before persona transformation. PNG, JPEG, and WebP uploads up to 5 MB are accepted after checking file signatures. Images are held in memory for the request and are not persisted by this app. Free-tier data handling follows Google’s current disclosure.
- Server-side transcription returns an explicit not-configured error.

## Accounts and history

Registration, login, session, and ownership-enforced history endpoints are implemented. Anonymous transformations are not persisted. The UI's current history list is in-memory for the current page session; the account endpoints are available to integrate with an account UI. SQLite stores salted password hashes and account transformation data. Deleting a history entry or clearing history is supported by the API. Use HTTPS and a secret key for deployment; production CSRF protections and rate limiting should be added before exposing public registration.

## API

- `GET /api/health`, `GET /api/session`
- `POST /api/register`, `POST /api/login`, `POST /api/logout`
- `POST /api/transform`, `POST /api/analyze-tone`
- `GET /api/history`, `GET /api/history/<id>`, `DELETE /api/history`, `DELETE /api/history/<id>`
- `POST /api/transcribe`, `POST /api/analyze-image`

## Limitations

Authentication endpoints and protected history operations are implemented, but a registration/login UI is not included yet. History shown in the current interface is session-memory only. Backend transcription remains explicitly unconfigured and returns a setup error. Image understanding uses live Gemini inference; it is not simulated. Tone analysis is a transparent keyword heuristic, not an ML classifier or a judgment of a person. Only English browser recognition is selected by the voice button. Target language choices depend on the configured model; browser TTS may lack the selected language voice. The provider endpoint tests use mocked HTTP responses; no live-provider inference test runs without a user-supplied key.


