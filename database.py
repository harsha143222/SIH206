"""
EduMind AI - SQLite Database Persistence Module
Manages persistent local storage for subjects, document metadata, processing status,
chat history, quiz results, learning progress, and group data.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import config

logger = logging.getLogger("database")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the local SQLite database."""
    config.DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                coin_balance INTEGER DEFAULT 100,
                streak_days INTEGER DEFAULT 1,
                last_active_date TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Subjects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Uploaded document metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                subject TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size_mb REAL NOT NULL,
                total_units INTEGER NOT NULL,
                storage_path TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Document chunks metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                filename TEXT NOT NULL,
                unit_label TEXT NOT NULL,
                unit_num INTEGER NOT NULL,
                section_title TEXT,
                text TEXT NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
            )
        """)

        # Learning progress / learned topics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_topics (
                topic_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                subtopic TEXT,
                explanation TEXT,
                status TEXT DEFAULT 'Explained',
                performance_level TEXT DEFAULT 'Not Tested',
                subtopics_json TEXT,
                user_questions_json TEXT,
                source_citations_json TEXT,
                historical_scores_json TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Quiz results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                attempt_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                quiz_title TEXT,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                coins_earned INTEGER DEFAULT 0,
                report_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Study Groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_groups (
                group_id TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                join_code TEXT UNIQUE NOT NULL,
                created_by TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
    logger.info("Database initialized successfully at %s", config.DB_PATH)


# User profile functions
def save_user_profile(user_id: str, username: str, coin_balance: int, streak_days: int, last_active_date: str) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, coin_balance, streak_days, last_active_date, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                coin_balance = excluded.coin_balance,
                streak_days = excluded.streak_days,
                last_active_date = excluded.last_active_date,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, username, coin_balance, streak_days, last_active_date))
        conn.commit()


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# Subject functions
def save_subject(subject_name: str) -> None:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject_name.strip().title(),))
        conn.commit()


def get_all_subjects() -> List[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM subjects ORDER BY name ASC")
        return [row["name"] for row in cursor.fetchall()]


# Document functions
def save_document_record(doc_data: Dict[str, Any], storage_path: str = "") -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO documents (doc_id, filename, file_hash, subject, file_type, file_size_mb, total_units, storage_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                filename = excluded.filename,
                subject = excluded.subject,
                total_units = excluded.total_units,
                storage_path = excluded.storage_path
        """, (
            doc_data["doc_id"],
            doc_data["filename"],
            doc_data.get("file_hash", ""),
            doc_data.get("subject", config.DEFAULT_SUBJECT),
            doc_data["file_type"],
            doc_data["file_size_mb"],
            doc_data["total_units"],
            storage_path
        ))
        conn.commit()
        save_subject(doc_data.get("subject", config.DEFAULT_SUBJECT))


def get_documents_by_subject(subject: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE subject = ?", (subject.strip().title(),))
        return [dict(row) for row in cursor.fetchall()]


def get_all_documents() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY processed_at DESC")
        return [dict(row) for row in cursor.fetchall()]


# Quiz result functions
def save_quiz_result(attempt_id: str, user_id: str, subject: str, title: str, score: int, total: int, pct: float, coins: int, report: Dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO quiz_results (attempt_id, user_id, subject, quiz_title, score, total_questions, percentage, coins_earned, report_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(attempt_id) DO UPDATE SET
                score = excluded.score,
                percentage = excluded.percentage,
                coins_earned = excluded.coins_earned,
                report_json = excluded.report_json
        """, (attempt_id, user_id, subject, title, score, total, pct, coins, json.dumps(report)))
        conn.commit()


# Initialize database on module load
init_db()
