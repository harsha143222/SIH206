# 🎓 EduMind AI — Smart Education AI Tutor

EduMind AI is an intelligent, personalized, and grounded AI educational assistant built for Smart Education (SIH 2026, Problem Statement ID 26207). Powered by the official **Google GenAI Python SDK (`google-genai`)** and **Gemini 3.5 Flash**, EduMind AI enables students to upload course materials (PDF, PPT, PPTX up to 100 MB), clear doubts with strict grounded answer policies, take gamified quizzes with coin rewards and hints, learn together in study groups, track their progress persistently, and listen to explanations using browser voice synthesis.

---

## 🏛️ System Architecture

The application is built using a unified Streamlit framework with modular engine layers:

```
                  ┌─────────────────────────────────────┐
                  │          Streamlit Web UI           │
                  │   (Home / Chat / Quiz / Friends)    │
                  └──────────────────┬──────────────────┘
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      │                              │                              │
┌─────▼──────────────┐   ┌───────────▼──────────┐   ┌───────────────▼─────────────┐
│  gemini_client.py  │   │ document_processor.py│   │      database.py            │
│  (google-genai)    │   │  (Semantic RAG FAISS)│   │  (SQLite Local Persistence) │
└─────┬──────────────┘   └───────────┬──────────┘   └───────────────┬─────────────┘
      │                              │                              │
      ▼                              ▼                              ▼
  Gemini 3.5 Flash /       Subject-Isolated           edumind.db
  text-embedding-004       Vector Indexes (FAISS)     (Users, Docs, Quizzes, Groups)
```

---

## ✨ Key Features

1. **Official Google GenAI SDK Integration**: Fully updated to `from google import genai` (`google-genai` package) with configurable `GEMINI_MODEL=gemini-3.5-flash`.
2. **Real Semantic Retrieval (RAG)**: Full document text extraction (PDF via `pypdf`, PPT/PPTX via `python-pptx`), page/slide-level chunking, vector embedding generation (`text-embedding-004`), and FAISS vector indexing.
3. **Subject Isolation**: Course materials and vector indexes are completely isolated per subject (e.g. Java materials do not leak into Python searches).
4. **Strict Grounded Answer Policy**: Answers are strictly derived from retrieved course material. If information is missing, EduMind AI responds clearly: *"I couldn't find this information in the uploaded course material."*
5. **Real Source Citations**: Grounded responses display exact filename, page number, or slide number citations (`[Filename] — Page X / Slide Y`).
6. **Grounded Gamified Quizzes**: Quizzes generated strictly from course material context. Features hints (costing coins), coin rewards, difficulty levels, and performance feedback.
7. **SQLite Persistent Storage**: Documents, subjects, quiz attempts, streak history, and user profiles persist across application restarts in `data/database/edumind.db`.
8. **Browser Voice Engine**: Pure client-side browser speech synthesis using Web Speech API with female/male voice matching and pitch stability. Zero API calls consumed for audio.
9. **Multimodal Image Vision**: Upload textbook questions, code screenshots, or handwritten notes for instant step-by-step solutions using Gemini Multimodal Vision.
10. **Group Learning & Friends Dashboard**: Study groups, shared notes, group chat, group quizzes, and group leaderboards.

11. **Student Performance Analytics System (`📊 My Analytics`)**: Complete user-isolated dashboard tracking overall progress, quiz accuracy, study time, questions asked, weak & strong topic detection, time-series learning trends (7, 30, 90 days), AI doubt analytics, study session tracking, AI recommendations, and gamified achievements.
12. **Admin Analytics Dashboard (`📊 Admin Analytics`)**: Aggregated platform-wide statistics for administrators showing total active users, platform average scores, quiz completion rates, and subject distribution while strictly preserving student privacy.

---

## 📁 File Structure

```
SIH_206/
├── app.py                   # Main Streamlit Application UI & Dispatcher
├── analytics.py             # Student & Admin Analytics Calculation Service
├── config.py                # Central Configuration, Paths, Prompts, Models
├── database.py              # SQLite Local Persistence Layer & Analytics Schema
├── mongodb.py               # MongoDB Atlas Dual Persistence Layer & Analytics
├── document_processor.py    # Document Parsing, Chunking & FAISS Vector Indexing
├── gemini_client.py         # Official google-genai Client & Model Invocation
├── quiz_engine.py           # Grounded Gamified Quiz Generator & Analytics Logging
├── learning_tracker.py      # Topic Extraction, Progress Analytics & Streaks
├── group_learning.py        # Study Groups, Shared Materials & Leaderboards
├── test_analytics.py        # Analytics & Isolation Automated Test Suite
├── voice_engine.py          # Client-Side Browser Voice Synthesis
├── ui/                      # UI Views & Components
│   ├── analytics.py         # Student Analytics Dashboard UI
│   ├── admin_analytics.py   # Admin Platform Analytics Dashboard UI
│   ├── charts.py            # Plotly Visualization Charts
│   ├── dashboard.py         # Main Student Quick-Action Dashboard
│   ├── login.py             # Authentication Login View
│   ├── profile.py           # Student Profile & Wallet View
│   ├── register.py          # Account Registration View
│   └── settings.py          # Settings & Voice Configuration View
├── requirements.txt         # Dependency Manifest
├── .env.example             # Environment Variable Template
├── .gitignore               # Git Ignore Rules
└── data/                    # Persistent Data Directory
    ├── uploads/             # Raw Uploaded Files
    ├── processed/           # Processed Chunk Metadata
    ├── indexes/             # FAISS Vector Indexes by Subject
    └── database/            # edumind.db SQLite Database
```

---

## 🗄️ Analytics Database Schema Extension

The database architecture is extended with 6 new schema tables / collections, ensuring strict user isolation:

1. **`quiz_attempts`**: Stores attempt-level details (score, total questions, percentage, correct/wrong count, difficulty, timestamp).
2. **`quiz_answers`**: Stores question-level performance (selected option, correct option, is_correct, hint usage, difficulty).
3. **`topic_performance`**: Tracks topic & subtopic mastery levels (attempt count, average score, last attempt, mastery status `Strong` / `Needs Practice` / `Needs Revision`).
4. **`chat_interactions`**: Logs AI doubt queries and topics asked to AI for confusion detection.
5. **`learning_sessions`**: Tracks study session start time, duration, and subject activity.
6. **`recommendations`**: Persists AI personalized recommendations based on actual historical performance.

---

## ⚙️ Environment Variables & Streamlit Secrets

EduMind AI reads credentials securely without asking students to enter API keys in the public UI.

### 1. `.env` File (Local Development)
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
MAX_FILE_SIZE_MB=100
TOP_K=4
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

### 2. Streamlit Secrets Setup (Streamlit Community Cloud Deployment)
In your Streamlit Cloud Dashboard, navigate to **Settings -> Secrets** and paste:
```toml
GEMINI_API_KEY = "your_actual_gemini_api_key_here"
GEMINI_MODEL = "gemini-3.5-flash"
```

---

## 🚀 Local Run Instructions

### Prerequisites
- Python 3.10+
- Git

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd SIH_206
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API Key:**
   Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`.

5. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

6. Open your browser at `http://localhost:8501`.

---

## ☁️ Streamlit Deployment Instructions

1. Push code to your GitHub repository (ensure `.env` is ignored by `.gitignore`).
2. Log in to [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Click **New app**, select your repository and branch, and set Main file path to `app.py`.
4. Go to **Advanced settings -> Secrets** and add your `GEMINI_API_KEY` and optional `GEMINI_MODEL`.
5. Click **Deploy!**

---

## ❓ Troubleshooting

- **Gemini API Key Missing Error:** Ensure `GEMINI_API_KEY` is set in your `.env` or Streamlit Secrets.
- **Model Unavailable / 404 Error:** Ensure `GEMINI_MODEL` is set to a currently supported model like `gemini-3.5-flash`.
- **Quota Exceeded (429):** The application handles rate limits with exponential backoff; wait a minute before retrying.
- **Voice Not Playing:** Ensure browser audio permissions are allowed. Browser SpeechSynthesis requires a user gesture or page interaction.

---

## ⚠️ Known Limitations

- **Browser Voice Dependency:** Speech synthesis relies on Web Speech API built into student browsers (Chrome, Edge, Safari). Voice availability varies by operating system.
- **Ephemeral Storage on Free Cloud Hosting:** Streamlit Community Cloud resets disk state upon app restarts. For enterprise multi-instance production, persistent cloud database (PostgreSQL/Supabase) and S3 object storage would replace local SQLite.
