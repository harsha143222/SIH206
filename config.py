"""
EduMind AI - Central Configuration Module
Handles environment variables, model parameters, system prompts, coin rewards, document limits,
and centralized directory paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically locate and load the .env file from the project root
ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# ==============================================================================
# 1. PATHS & DIRECTORY STRUCTURE
# ==============================================================================
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
INDEXES_DIR = DATA_DIR / "indexes"
DB_DIR = DATA_DIR / "database"
DB_PATH = DB_DIR / "edumind.db"

# Create directories if they do not exist
for folder in [DATA_DIR, UPLOADS_DIR, PROCESSED_DIR, INDEXES_DIR, DB_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 2. API & MODEL CONFIGURATION (OFFICIAL GOOGLE GENAI SDK)
# ==============================================================================
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004").strip()

GEMINI_MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

GENERATION_CONFIG = {
    "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "4096")),
}

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.5

# ==============================================================================
# 3. RAG & RETRIEVAL CONFIGURATION
# ==============================================================================
TOP_K = int(os.getenv("TOP_K", "4"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# ==============================================================================
# 4. FILE UPLOAD & SUBJECT CONFIGURATION
# ==============================================================================
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_FILE_TYPES = ["pdf", "ppt", "pptx"]
SUPPORTED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]
MAX_IMAGE_SIZE_MB = 15
DEFAULT_SUBJECT = "General Computer Science"

# ==============================================================================
# 5. GAMIFIED COIN REWARDS & HINT CONFIGURATION
# ==============================================================================
COINS_EASY = 10
COINS_MEDIUM = 15
COINS_HARD = 20
HINT_COST = 5

# ==============================================================================
# 6. SYSTEM INSTRUCTION & PROMPTS (GROUNDED ANSWER POLICY)
# ==============================================================================
SYSTEM_INSTRUCTION = """You are an educational AI tutor.

Use the retrieved content from the selected course materials as the primary source.

Answer clearly and accurately.

Do not invent information.

Do not claim that a statement came from the document unless it is supported by retrieved material.

If sufficient relevant information cannot be found in the selected course materials, say:
'I couldn't find this information in the uploaded course material.'

Do not fabricate source names, page numbers, or slide numbers."""

INITIAL_GREETING = (
    "Hello! 👋 I'm **EduMind AI**, your personal learning assistant.\n\n"
    "Upload your PDF, PPT, or PPTX study materials (up to 100 MB), select your subject, or ask me any academic doubt!\n\n"
    "What would you like to learn today?"
)

# Prompt template for generating personalized quizzes from Subject + PDF + Learned Topics
QUIZ_GENERATION_PROMPT = """You are EduMind AI's Quiz Generator.
Generate a personalized educational quiz based STRICTLY on the student's Subject, Uploaded Study Material, and Learned Topics.

SUBJECT: {subject}

LEARNED TOPICS & SUBTOPICS:
{learned_topics_summary}

STUDY MATERIAL CONTEXT:
{document_context}

TARGET NUMBER OF QUESTIONS: {num_questions}
DIFFICULTY LEVEL: {difficulty}

RULES:
1. Every question MUST relate directly to the Subject ({subject}) AND the listed Learned Topics.
2. Questions MUST be derived strictly from the study material context provided above. Do NOT generate generic or ungrounded questions.
3. If the context is insufficient or empty, output an empty JSON array `[]`.
4. Include a balanced mix of Easy (definitions), Medium (understanding/examples), and Hard (application/code/output) questions.
5. Set "coin_reward" based on difficulty: Easy = 10, Medium = 15, Hard = 20.
6. Each question must have exactly 4 distinct options (A, B, C, D) with exactly one correct answer index (0, 1, 2, or 3).
7. Provide a clear educational explanation for why the correct answer is right.
8. Provide the exact source citation (e.g. "C_Language_Notes.pdf — Page 27" or "Slide 12") matching the context snippet.

Respond ONLY with a valid JSON array of question objects matching this exact schema:
[
  {{
    "id": 1,
    "subject": "{subject}",
    "topic": "Topic Name",
    "subtopic": "Subtopic Name",
    "difficulty": "Easy|Medium|Hard",
    "coin_reward": 10,
    "question": "Question text...",
    "options": [
      "Option A text",
      "Option B text",
      "Option C text",
      "Option D text"
    ],
    "correct_index": 0,
    "explanation": "Clear educational explanation...",
    "source_citation": "File.pdf — Page X"
  }}
]
"""

# ==============================================================================
# 7. SECURE API KEY MANAGEMENT
# ==============================================================================
def get_gemini_api_key() -> str:
    """
    Retrieve Gemini API Key securely from environment variables or Streamlit secrets.
    Does NOT rely on public UI text inputs.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_api_key_here":
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                key = str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            pass
    return key


def is_gemini_api_key_configured() -> bool:
    """Check if a non-empty, non-placeholder Gemini API key is configured."""
    key = get_gemini_api_key()
    return bool(key and key != "your_api_key_here" and key != "your_gemini_api_key_here")


# Compatibility wrappers
def get_xai_api_key() -> str:
    return get_gemini_api_key()

def is_xai_api_key_configured() -> bool:
    return is_gemini_api_key_configured()

def get_api_key() -> str:
    return get_gemini_api_key()

def is_api_key_configured() -> bool:
    return is_gemini_api_key_configured()
