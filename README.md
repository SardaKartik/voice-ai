# Healthcare.ai — Voice AI Healthcare Receptionist

A full-stack healthcare appointment booking system powered by a voice AI agent named **Kiara**. Users speak directly to Kiara through the browser to book, modify, or cancel medical appointments — no typing required.

---

## Demo

> **Kiara:** "Hi, I'm Kiara from Healthcare.ai. How can I help you today?"

---

## Architecture

```
voice_ai_avatar/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI REST API (token generation, appointments)
│   │   ├── agent.py         # LiveKit voice agent worker
│   │   ├── prompts.py       # Kiara's system prompt / persona
│   │   ├── tools/           # 7 appointment tool implementations
│   │   └── database/
│   │       ├── db.py        # SQLite query functions
│   │       └── schema.sql   # users + appointments schema
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── VoiceRoom.jsx    # Room lifecycle, audio monitoring
        │   ├── Avatar.jsx       # Animated avatar (reflects speaking state)
        │   ├── ControlBar.jsx   # Connect / mute / disconnect controls
        │   ├── CallSummary.jsx  # Post-call summary display
        │   └── ToolCallFeed.jsx # Real-time tool execution feed
        ├── api/backend.js       # getToken(), getAppointments()
        └── hooks/useToolEvents.js  # LiveKit data channel subscription
```

### How a call works

1. Frontend requests a LiveKit token from `POST /token`
2. User connects to a LiveKit room in the browser
3. The agent worker joins the same room and starts the speech pipeline
4. **Pipeline:** Deepgram STT → Azure OpenAI LLM → Cartesia TTS (Silero VAD)
5. Agent calls tools and broadcasts tool events back over the LiveKit data channel
6. `useToolEvents` hook picks up the events and renders them in `ToolCallFeed`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, LiveKit Components, Lottie |
| Backend API | FastAPI, Uvicorn |
| Voice Agent | livekit-agents, Deepgram STT, Cartesia TTS |
| LLM | Azure OpenAI (GPT-4o-mini) |
| VAD | Silero |
| Database | SQLite (Docker volume) |
| Containerisation | Docker, Docker Compose |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for full-stack run)
- Accounts / API keys for:
  - [LiveKit Cloud](https://livekit.io)
  - [Deepgram](https://deepgram.com)
  - [Cartesia](https://cartesia.ai)
  - [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) (or OpenAI)

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/voice_ai_avatar.git
cd voice_ai_avatar
```

### 2. Configure environment variables

**Backend:**

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
LIVEKIT_AGENT_NAME=healthcare-agent

DEEPGRAM_API_KEY=your_key
CARTESIA_API_KEY=your_key

AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21

# Optional fallback (non-Azure OpenAI)
OPENAI_API_KEY=your_key
```

**Frontend:**

```bash
cd frontend
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_BACKEND_URL=http://localhost:8000
```

---

### 3. Run with Docker Compose (recommended)

```bash
cd backend
docker-compose up --build
```

This starts two services from one image:
- **api** — FastAPI on `http://localhost:8000`
- **agent** — LiveKit worker (starts after the API healthcheck passes)

Both share the `sqlite_data` volume for database persistence.

---

### 4. Run manually (development)

**Backend API:**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Agent worker** (separate terminal):

```bash
cd backend
python app/agent.py start
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck |
| `GET` | `/token` | Generate LiveKit room token |
| `GET` | `/appointments/{phone_number}` | Fetch confirmed appointments |

**Token endpoint query params:**

| Param | Default | Description |
|---|---|---|
| `room` | auto-generated UUID | LiveKit room name |
| `participant` | `"user"` | Participant identity |

---

## Agent Tools

Kiara has access to seven tools during a conversation:

| Tool | Description |
|---|---|
| `identify_user` | Look up a patient by phone number |
| `fetch_slots` | Get available appointment slots for a date and department |
| `book_appointment` | Create a new confirmed appointment |
| `retrieve_appointments` | List all upcoming appointments for a patient |
| `cancel_appointment` | Cancel an existing appointment by ID |
| `modify_appointment` | Reschedule an appointment to a new date/time |
| `end_conversation` | Close the session cleanly with a summary |

All tool responses are plain text optimised for speech (no markdown or lists).

---

## Database Schema

**`users`**

| Column | Type | Notes |
|---|---|---|
| `phone_number` | TEXT PK | Patient identifier |
| `name` | TEXT | Display name |
| `created_at` | TIMESTAMP | Auto |
| `last_seen` | TIMESTAMP | Auto |

**`appointments`**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `phone_number` | TEXT | FK → users |
| `name` | TEXT | Name on the booking |
| `department` | TEXT | Clinic unit |
| `date` | TEXT | YYYY-MM-DD |
| `time` | TEXT | HH:MM AM/PM |
| `status` | TEXT | `confirmed` \| `cancelled` |

Unique constraint on `(date, time, department)` prevents double-booking.

---

## Frontend Scripts

```bash
npm run dev       # Dev server at http://localhost:5173
npm run build     # Production build → dist/
npm run preview   # Preview production build
npm run lint      # ESLint
```

---

## Deployment

### Backend (Railway / Render / Fly.io)

The `backend/` directory is self-contained with a `Dockerfile`. Deploy it as a single image and run both the API and agent as separate services (or use docker-compose on a VM).

Set all environment variables from the `.env.example` in your hosting provider's dashboard.

### Frontend (Vercel / Netlify)

```bash
cd frontend
npm run build
```

Deploy the `dist/` folder. Set `VITE_BACKEND_URL` to your deployed backend URL.

---

## Project Structure Details

```
backend/app/tools/
├── identify_user.py
├── fetch_slots.py
├── book_appointment.py
├── retrieve_appointments.py
├── cancel_appointment.py
├── modify_appointment.py
└── end_conversation.py
```

Each tool is a standalone Python function decorated with `@llm.ai_callable()` and registered at agent startup. Tools that modify data also publish a data event to the LiveKit room so the frontend can display real-time feedback.

---

## License

MIT
