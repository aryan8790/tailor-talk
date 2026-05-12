# 🗂️ TailorTalk — AI-Powered Google Drive Assistant

A conversational AI agent that searches, filters, and discovers files in a designated Google Drive folder using natural language.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│   (Chat UI · Suggestion chips · Conversation history)│
└──────────────────────┬──────────────────────────────┘
                       │  HTTP POST /chat
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                     │
│                                                     │
│   LangChain Agent  ──tool call──►  DriveSearchTool  │
│   (OpenAI / Groq / Gemini)               │          │
│                                          ▼          │
│                               Google Drive API      │
│                               files.list + q param  │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · Uvicorn |
| Agent | LangChain · `create_openai_tools_agent` |
| Tool | `DriveSearchTool` (Drive API `files.list` / `q`) |
| LLM | OpenAI GPT-4o-mini *(or Groq / Gemini — configurable)* |
| Drive Auth | Google Service Account |
| Frontend | Streamlit |
| Deployment | Railway / Render / Fly.io |

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/<you>/tailor-talk.git
cd tailor-talk
```

### 2. Set up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com) → **IAM & Admin → Service Accounts**.
2. Create a new service account and download the **JSON key**.
3. Enable the **Google Drive API** in your project.
4. Copy the sample Drive folder to your own Drive:
   `https://drive.google.com/drive/folders/1qkx58doSeYrcLjHPDysJyVJ36PsSqqlt`
5. **Share the folder** with your service account's email (e.g. `my-bot@project.iam.gserviceaccount.com`) — grant *Viewer* access.

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your keys
```

Key variables:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}   # or use GOOGLE_SERVICE_ACCOUNT_FILE
GOOGLE_DRIVE_FOLDER_ID=1qkx58doSeYrcLjHPDysJyVJ36PsSqqlt
BACKEND_URL=http://localhost:8000
```

### 4. Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. Run the frontend (new terminal)

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Deployment on Railway

1. Push your repo to GitHub.
2. Create a **new Railway project** → *Deploy from GitHub repo*.
3. Add **two services** — one for `backend/`, one for `frontend/`.

**Backend service:**
- Root Dir: `backend`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Env vars: `LLM_PROVIDER`, `OPENAI_API_KEY`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_DRIVE_FOLDER_ID`

**Frontend service:**
- Root Dir: `frontend`
- Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Env vars: `BACKEND_URL=https://<your-backend-railway-domain>`

---

## Google Drive Query Examples

The agent automatically translates natural language into Drive API queries:

| User says | Drive query generated |
|---|---|
| "Find all PDFs" | `mimeType = 'application/pdf'` |
| "Show files named invoice" | `name contains 'invoice'` |
| "Files modified last week" | `modifiedTime > '2024-06-05T00:00:00'` |
| "Spreadsheets with budget data" | `mimeType = 'application/vnd.google-apps.spreadsheet' and fullText contains 'budget'` |
| "Images uploaded this month" | `mimeType contains 'image/' and modifiedTime > '2024-06-01T00:00:00'` |

---

## Project Structure

```
tailor-talk/
├── backend/
│   ├── main.py           # FastAPI app + /chat endpoint
│   ├── agent.py          # LangChain agent + DriveSearchTool
│   ├── drive_service.py  # Google Drive API wrapper
│   ├── requirements.txt
│   └── Procfile
├── frontend/
│   ├── app.py            # Streamlit chat UI
│   └── requirements.txt
├── .env.example
├── railway.toml
└── README.md
```

---

## Switching LLM Provider

Set `LLM_PROVIDER` in your `.env`:

| Value | Env var needed | Default model |
|---|---|---|
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `groq` | `GROQ_API_KEY` | `llama3-70b-8192` |
| `gemini` | `GOOGLE_API_KEY` | `gemini-1.5-flash` |

---

## License

MIT
