# TravelCrew Smart Travel Planner

An offline-first travel-planning prototype using Python, CrewAI, Ollama (`llama3.2`), and Streamlit. A sequential crew passes specialist task outputs forward as context. Search, seasonal weather, mock lodging/transport, date scheduling, and budget calculations are exposed as tools; cost comparison and budget revision are also performed deterministically in Python.

## Important deployment constraint

There is no Ollama API key for a local Ollama installation. This application uses the local Ollama service at `http://localhost:11434` by default and makes no OpenAI, Groq, Gemini, or OpenRouter calls.

Streamlit Community Cloud cannot connect to Ollama running on your personal computer: `localhost` inside the hosted app means the cloud container. To deploy, run Streamlit on the same host as Ollama, or configure `OLLAMA_BASE_URL` to a securely reachable Ollama server. Do not expose Ollama directly to the public internet. Hosted compute may have a cost even though Ollama itself does not require a model API key.

## Local setup

Requires Python 3.10+ and Ollama installed locally.

```powershell
git clone https://github.com/Tejaswini910/TravelCrew_AI-.git
cd TravelCrew_AI-
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
ollama pull llama3.2
Copy-Item .env.example .env
streamlit run streamlit_app.py
```

The `.env.example` defaults to local Ollama at `http://localhost:11434`; local Ollama does not require an API key. The app opens at `http://localhost:8501`. `OLLAMA_MODEL=llama3.2` is translated to CrewAI's Ollama provider identifier `ollama/llama3.2`.

## Deploy to Streamlit Community Cloud

1. Connect `Tejaswini910/TravelCrew_AI-` and select branch `main`.
2. Set the main file path to `streamlit_app.py`.
3. In the app's **Settings → Secrets**, configure the Ollama endpoint:

```toml
OLLAMA_BASE_URL = "https://ollama.com/v1"
OLLAMA_MODEL = "gemma4:31b"
OLLAMA_API_KEY = "your-ollama-cloud-key"
```

Use a cloud model listed by Ollama, such as `gemma4:31b`; locally downloaded names such as `llama3.2` may not be available to direct cloud API access. The Ollama Cloud OpenAI-compatible base URL is `https://ollama.com/v1`, not `/api`; the app appends `/models` for its cloud preflight and CrewAI calls `/chat/completions`. A legacy `https://ollama.com/api` setting is normalized to `/v1`. The app checks `/api/tags` only for loopback/local Ollama. Streamlit Cloud cannot use `http://localhost:11434` to reach your computer. Never paste a real key into GitHub or `.env.example`.

## Offline behavior and tools

- **Destination search:** a bundled city catalog works offline. Unknown destinations return no verified offline results instead of fabricated attractions. Set `ENABLE_WEB_SEARCH=true` to optionally use keyless DuckDuckGo search; network errors fall back to local results.
- **Weather:** an explicitly labeled seasonal estimate works offline. When enabled and dates are within the forecast window, weather may be retrieved from Open-Meteo without an API key.
- **Hotels and transport:** local mock data only. These prices are illustrative USD estimates, not actual properties, schedules, availability, or bookable fares.
- **Budget:** deterministic Python calculation includes hotel, transport, food allowance, and attraction costs. When over budget it tries less expensive mock options, free activities, and a reduced food allowance, then reports any remaining shortfall.
- **Dates:** validates the request and creates exact day/date/weekday entries.

Food is a planning allowance, not a researched restaurant quote. This prototype does not book travel or guarantee prices. Verify actual venue details, transport routes, costs, and travel requirements before booking.

## Configuration

Copy `.env.example` to `.env`. Keep `ENABLE_WEB_SEARCH=false` for fully offline operation. Ollama is the only supported model provider. For a remote Ollama host, protect the endpoint with TLS and network controls; never commit credentials or private endpoints.

## Tests

```powershell
python -m pytest
```

## Project layout

```text
TravelCrew_AI-/
  agents/       CrewAI role definitions
  config/       Ollama and runtime settings
  crew/         Sequential crew orchestration
  services/     Tool invocation and budget revision
  tasks/        Agent task descriptions and context dependencies
  tools/        Search, weather, mock offers, calculator, and dates
  streamlit_app.py
```
