## Home Design & Building Code Chatbot (FastAPI + OpenAI)

Professional, location-aware chatbot for home design, construction, and building code questions. Connects directly to OpenAI's ChatGPT API, keeps conversation context, and is designed for future integration with city/county APIs.

### Features
- Location-specific guidance (city/county/state/zip)
- Conversation context via `session_id`
- FastAPI backend with typed schemas
- Structured prompt for precise, plain-English answers
- Robust error handling

### Quickstart
1) Create and activate a virtual environment
```bash
python -m venv .venv && . .venv/Scripts/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure environment
Create `.env` from `.env.example` and set values.

4) Run the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5) Test endpoints
```bash
curl    

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "demo-session-1",
        "message": "Can I build a second floor on my house?",
        "location": {"city": "San Jose", "state": "CA", "zip": "95112"}
      }'
```

### Environment
See `.env.example` for required variables.

### Project Structure
```text
app/
  __init__.py
  main.py
  config.py
  schemas.py
  context.py
  openai_client.py
requirements.txt
.env.example
README.md
```

### Notes
- This project does not scrape or store local code databases; it queries OpenAI with structured prompts. Future versions can integrate city/county APIs.
- Always provide a location for the most accurate guidance.



