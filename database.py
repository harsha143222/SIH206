"""
EduMind AI - SQLite Database Persistence Module
Manages persistent local storage for subjects, document metadata, processing status,
chat history, quiz results, learning progress, and group data.
"""

import sqlite3
import json
import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Set
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

        # Users table with email and password_hash support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT,
                coin_balance INTEGER DEFAULT 100,
                streak_days INTEGER DEFAULT 1,
                last_active_date TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure optional columns exist if table was created earlier
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "email" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if "password_hash" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        if "display_name" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")

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

        # Coin Transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coin_transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                tx_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                source TEXT NOT NULL,
                reference_id TEXT,
                balance_after INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User Achievements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id TEXT NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id)
            )
        """)

        # Learning sessions tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topics_studied_json TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                duration_seconds INTEGER DEFAULT 0,
                activity_type TEXT DEFAULT 'study',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # AI Doubt / Chat interactions tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_interactions (
                interaction_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                subtopic TEXT,
                question TEXT NOT NULL,
                response_status TEXT DEFAULT 'success',
                source_doc TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Detailed Quiz attempts tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                attempt_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                quiz_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topics_json TEXT,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                correct_answers INTEGER NOT NULL,
                wrong_answers INTEGER NOT NULL,
                difficulty TEXT,
                time_taken_seconds INTEGER DEFAULT 0,
                attempt_number INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Question-level performance tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_answers (
                answer_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                attempt_id TEXT NOT NULL,
                quiz_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                subtopic TEXT,
                selected_answer INTEGER,
                correct_answer INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                difficulty TEXT,
                hint_used INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Topic & Subtopic performance summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_performance (
                performance_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                subtopic TEXT DEFAULT 'General',
                attempt_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                average_score REAL DEFAULT 0.0,
                last_attempt DATETIME,
                last_score REAL DEFAULT 0.0,
                study_time_seconds INTEGER DEFAULT 0,
                ai_question_count INTEGER DEFAULT 0,
                mastery_level TEXT DEFAULT 'Not Tested',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, subject, topic, subtopic)
            )
        """)

        # AI Recommendations persistence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                rec_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                recommended_difficulty TEXT,
                recommended_quiz TEXT,
                recommended_source_pages TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Material Automatic Overview Persistence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS material_overviews (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                subject TEXT NOT NULL,
                overview_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Shared Study Spaces persistence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_spaces (
                space_id TEXT PRIMARY KEY,
                owner_user_id TEXT NOT NULL,
                owner_username TEXT NOT NULL,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT,
                invite_token TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_space_members (
                space_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (space_id, user_id),
                FOREIGN KEY (space_id) REFERENCES study_spaces (space_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_space_documents (
                doc_id TEXT PRIMARY KEY,
                space_id TEXT NOT NULL,
                uploaded_by TEXT NOT NULL,
                uploaded_by_name TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size_mb REAL NOT NULL,
                total_units INTEGER NOT NULL,
                storage_path TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (space_id) REFERENCES study_spaces (space_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_space_messages (
                message_id TEXT PRIMARY KEY,
                space_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                sender_name TEXT NOT NULL,
                message_text TEXT NOT NULL,
                message_type TEXT DEFAULT 'chat',
                reactions_json TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (space_id) REFERENCES study_spaces (space_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_space_activity (
                activity_id TEXT PRIMARY KEY,
                space_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (space_id) REFERENCES study_spaces (space_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_space_quizzes (
                quiz_id TEXT PRIMARY KEY,
                space_id TEXT NOT NULL,
                created_by TEXT NOT NULL,
                title TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (space_id) REFERENCES study_spaces (space_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_space_quiz_attempts (
                attempt_id TEXT PRIMARY KEY,
                quiz_id TEXT NOT NULL,
                space_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                correct_answers INTEGER NOT NULL,
                wrong_answers INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (space_id) REFERENCES study_spaces (space_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
    logger.info("Database initialized successfully at %s", config.DB_PATH)



# User profile functions
def save_user_profile(user_id: str, username: str, coin_balance: int, streak_days: int, last_active_date: str, email: str = "", password_hash: str = "", display_name: str = "") -> None:
    clean_u = username.strip()
    clean_e = email.strip().lower()
    disp = display_name.strip() if display_name else clean_u

    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO users (user_id, username, display_name, email, password_hash, coin_balance, streak_days, last_active_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    display_name = CASE WHEN excluded.display_name != '' THEN excluded.display_name ELSE users.display_name END,
                    email = CASE WHEN excluded.email != '' THEN excluded.email ELSE users.email END,
                    password_hash = CASE WHEN excluded.password_hash != '' THEN excluded.password_hash ELSE users.password_hash END,
                    coin_balance = excluded.coin_balance,
                    streak_days = excluded.streak_days,
                    last_active_date = excluded.last_active_date,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, clean_u, disp, clean_e, password_hash, coin_balance, streak_days, last_active_date))
            conn.commit()
    except sqlite3.IntegrityError:
        try:
            with get_connection() as conn:
                conn.execute("""
                    UPDATE users SET
                        display_name = CASE WHEN ? != '' THEN ? ELSE display_name END,
                        password_hash = CASE WHEN ? != '' THEN ? ELSE password_hash END,
                        coin_balance = ?,
                        streak_days = ?,
                        last_active_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE LOWER(username) = LOWER(?) OR (email != '' AND LOWER(email) = LOWER(?))
                """, (disp, disp, password_hash, password_hash, coin_balance, streak_days, last_active_date, clean_u, clean_e))
                conn.commit()
        except Exception as e:
            logger.error("Error updating existing user profile: %s", str(e))
    except Exception as e:
        logger.error("Error saving user profile: %s", str(e))


def get_user_profile(identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieve user profile by user_id, username, or email."""
    if not identifier:
        return None
    clean_id = identifier.strip().lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users 
            WHERE user_id = ? OR LOWER(username) = ? OR LOWER(email) = ?
        """, (identifier.strip(), clean_id, clean_id))
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


# Coin Transaction functions
def save_transaction(user_id: str, tx: Dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO coin_transactions (transaction_id, user_id, amount, tx_type, reason, source, reference_id, balance_after, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_id) DO NOTHING
        """, (
            tx["transaction_id"],
            user_id,
            tx["amount"],
            tx["type"],
            tx["reason"],
            tx["source"],
            tx.get("reference_id", ""),
            tx["balance_after"],
            tx.get("timestamp")
        ))
        conn.commit()


def get_user_transactions(user_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM coin_transactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


# Achievement functions
def save_achievement(user_id: str, achievement_id: str) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO user_achievements (user_id, achievement_id)
            VALUES (?, ?)
            ON CONFLICT(user_id, achievement_id) DO NOTHING
        """, (user_id, achievement_id))
        conn.commit()


def get_unlocked_achievements(user_id: str) -> Set[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
        return {row["achievement_id"] for row in cursor.fetchall()}


# ==============================================================================
# ANALYTICS EXTENSION PERSISTENCE FUNCTIONS
# ==============================================================================
def save_chat_interaction(
    interaction_id: str,
    user_id: str,
    subject: str,
    question: str,
    topic: str = "",
    subtopic: str = "",
    source_doc: str = "",
    status: str = "success"
) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO chat_interactions (interaction_id, user_id, subject, topic, subtopic, question, response_status, source_doc, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(interaction_id) DO NOTHING
        """, (interaction_id, user_id, subject, topic, subtopic, question, status, source_doc))
        conn.commit()


def get_user_chat_interactions(user_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_interactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def save_quiz_attempt_record(
    attempt_id: str,
    quiz_id: str,
    user_id: str,
    subject: str,
    topics_json: str,
    score: int,
    total_questions: int,
    pct: float,
    correct: int,
    wrong: int,
    difficulty: str = "Medium",
    time_taken_seconds: int = 0,
    attempt_number: int = 1
) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO quiz_attempts (attempt_id, quiz_id, user_id, subject, topics_json, score, total_questions, percentage, correct_answers, wrong_answers, difficulty, time_taken_seconds, attempt_number, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(attempt_id) DO UPDATE SET
                score = excluded.score,
                percentage = excluded.percentage,
                correct_answers = excluded.correct_answers,
                wrong_answers = excluded.wrong_answers
        """, (attempt_id, quiz_id, user_id, subject, topics_json, score, total_questions, pct, correct, wrong, difficulty, time_taken_seconds, attempt_number))
        conn.commit()


def get_user_quiz_attempts(user_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def save_quiz_answers_batch(answers: List[Dict[str, Any]]) -> None:
    if not answers:
        return
    with get_connection() as conn:
        for a in answers:
            conn.execute("""
                INSERT INTO quiz_answers (answer_id, user_id, attempt_id, quiz_id, question_id, subject, topic, subtopic, selected_answer, correct_answer, is_correct, difficulty, hint_used, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(answer_id) DO NOTHING
            """, (
                a["answer_id"],
                a["user_id"],
                a["attempt_id"],
                a["quiz_id"],
                a["question_id"],
                a["subject"],
                a["topic"],
                a.get("subtopic", "General"),
                a.get("selected_answer"),
                a["correct_answer"],
                1 if a.get("is_correct") else 0,
                a.get("difficulty", "Medium"),
                1 if a.get("hint_used") else 0
            ))
        conn.commit()


def get_user_quiz_answers(user_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quiz_answers WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def save_or_update_topic_performance(
    user_id: str,
    subject: str,
    topic: str,
    subtopic: str = "General",
    score_pct: Optional[float] = None,
    num_correct: int = 0,
    num_wrong: int = 0,
    ai_question_inc: int = 0,
    study_time_inc: int = 0
) -> None:
    norm_subj = subject.strip().title()
    norm_topic = topic.strip().title()
    norm_subtopic = subtopic.strip().title() if subtopic else "General"
    perf_id = f"tp_{user_id}_{norm_subj}_{norm_topic}_{norm_subtopic}".replace(" ", "_")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM topic_performance 
            WHERE user_id = ? AND subject = ? AND topic = ? AND subtopic = ?
        """, (user_id, norm_subj, norm_topic, norm_subtopic))
        row = cursor.fetchone()

        if row:
            row_dict = dict(row)
            attempt_count = row_dict["attempt_count"] + (1 if score_pct is not None else 0)
            correct_count = row_dict["correct_count"] + num_correct
            wrong_count = row_dict["wrong_count"] + num_wrong
            ai_count = row_dict["ai_question_count"] + ai_question_inc
            study_time = row_dict["study_time_seconds"] + study_time_inc
            last_score = score_pct if score_pct is not None else row_dict["last_score"]

            if score_pct is not None:
                # Recalculate average score
                prev_avg = row_dict["average_score"]
                prev_cnt = row_dict["attempt_count"]
                new_avg = round(((prev_avg * prev_cnt) + score_pct) / (prev_cnt + 1), 1)
            else:
                new_avg = row_dict["average_score"]

            # Compute mastery level
            if new_avg >= 80.0 and attempt_count > 0:
                mastery = "Strong"
            elif new_avg >= 50.0 and attempt_count > 0:
                mastery = "Needs Practice"
            elif attempt_count > 0:
                mastery = "Needs Revision"
            else:
                mastery = "Not Tested"

            cursor.execute("""
                UPDATE topic_performance SET
                    attempt_count = ?,
                    correct_count = ?,
                    wrong_count = ?,
                    average_score = ?,
                    last_attempt = CURRENT_TIMESTAMP,
                    last_score = ?,
                    study_time_seconds = ?,
                    ai_question_count = ?,
                    mastery_level = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND subject = ? AND topic = ? AND subtopic = ?
            """, (attempt_count, correct_count, wrong_count, new_avg, last_score, study_time, ai_count, mastery, user_id, norm_subj, norm_topic, norm_subtopic))
        else:
            attempt_count = 1 if score_pct is not None else 0
            new_avg = score_pct if score_pct is not None else 0.0
            last_score = score_pct if score_pct is not None else 0.0

            if new_avg >= 80.0 and attempt_count > 0:
                mastery = "Strong"
            elif new_avg >= 50.0 and attempt_count > 0:
                mastery = "Needs Practice"
            elif attempt_count > 0:
                mastery = "Needs Revision"
            else:
                mastery = "Not Tested"

            cursor.execute("""
                INSERT INTO topic_performance (performance_id, user_id, subject, topic, subtopic, attempt_count, correct_count, wrong_count, average_score, last_attempt, last_score, study_time_seconds, ai_question_count, mastery_level, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (perf_id, user_id, norm_subj, norm_topic, norm_subtopic, attempt_count, num_correct, num_wrong, new_avg, last_score, study_time_inc, ai_question_inc, mastery))

        conn.commit()


def get_user_topic_performances(user_id: str, subject: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if subject:
            cursor.execute("SELECT * FROM topic_performance WHERE user_id = ? AND subject = ? ORDER BY updated_at DESC", (user_id, subject.strip().title()))
        else:
            cursor.execute("SELECT * FROM topic_performance WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def save_learning_session(
    session_id: str,
    user_id: str,
    subject: str,
    topics_studied_json: str,
    start_time: str,
    end_time: str,
    duration_seconds: int,
    activity_type: str = "study"
) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO learning_sessions (session_id, user_id, subject, topics_studied_json, start_time, end_time, duration_seconds, activity_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                end_time = excluded.end_time,
                duration_seconds = excluded.duration_seconds
        """, (session_id, user_id, subject, topics_studied_json, start_time, end_time, duration_seconds, activity_type))
        conn.commit()


def get_user_learning_sessions(user_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM learning_sessions WHERE user_id = ? ORDER BY start_time DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def save_recommendation(
    recommendation_id: str,
    user_id: str,
    subject: str,
    topic: str,
    rec_type: str,
    title: str,
    message: str,
    recommended_difficulty: str = "Medium",
    recommended_quiz: str = "",
    recommended_source_pages: str = ""
) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO recommendations (recommendation_id, user_id, subject, topic, rec_type, title, message, recommended_difficulty, recommended_quiz, recommended_source_pages, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(recommendation_id) DO UPDATE SET
                title = excluded.title,
                message = excluded.message,
                created_at = CURRENT_TIMESTAMP
        """, (recommendation_id, user_id, subject, topic, rec_type, title, message, recommended_difficulty, recommended_quiz, recommended_source_pages))
        conn.commit()


def get_user_recommendations(user_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recommendations WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


# ==============================================================================
# AGGREGATED ADMIN ANALYTICS FUNCTIONS
# ==============================================================================
def get_all_users_analytics_summary() -> Dict[str, Any]:
    """Retrieve aggregated platform statistics for Admin Dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(DISTINCT user_id) as active_users FROM quiz_results")
        active_quiz_users = cursor.fetchone()["active_users"]

        today_str = date.today().isoformat()
        cursor.execute("SELECT COUNT(DISTINCT user_id) as active_today FROM users WHERE last_active_date = ?", (today_str,))
        active_today = cursor.fetchone()["active_today"]

        cursor.execute("SELECT COUNT(*) as total_chats FROM chat_interactions")
        total_chats = cursor.fetchone()["total_chats"]

        cursor.execute("SELECT COUNT(*) as total_quizzes, AVG(percentage) as avg_score FROM quiz_results")
        q_row = cursor.fetchone()
        total_quizzes = q_row["total_quizzes"] or 0
        avg_score = round(q_row["avg_score"] or 0.0, 1)

        cursor.execute("SELECT COUNT(*) as total_answers, SUM(is_correct) as correct_answers FROM quiz_answers")
        ans_row = cursor.fetchone()
        tot_ans = ans_row["total_answers"] or 0
        corr_ans = ans_row["correct_answers"] or 0
        completion_rate = round((corr_ans / tot_ans) * 100, 1) if tot_ans > 0 else 0.0

        return {
            "total_users": max(total_users, 1),
            "active_users": max(active_quiz_users, 1),
            "active_today": active_today,
            "total_questions_asked": total_chats,
            "total_quizzes": total_quizzes,
            "average_quiz_score": avg_score,
            "quiz_completion_rate": completion_rate
        }


def get_all_subject_analytics_summary() -> List[Dict[str, Any]]:
    """Retrieve aggregated subject performance for Admin Dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                subject,
                COUNT(DISTINCT user_id) as student_count,
                COUNT(*) as total_quizzes,
                AVG(percentage) as avg_score
            FROM quiz_results
            GROUP BY subject
            ORDER BY student_count DESC, avg_score ASC
        """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                "subject": r["subject"],
                "students": r["student_count"],
                "total_quizzes": r["total_quizzes"],
                "average_score": round(r["avg_score"] or 0.0, 1)
            })
        return result


# ==============================================================================
# MATERIAL AUTOMATIC OVERVIEW FUNCTIONS
# ==============================================================================
def save_material_overview(doc_id: str, filename: str, subject: str, overview_data: Dict[str, Any]) -> None:
    """Save or update generated material overview for a document."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO material_overviews (doc_id, filename, subject, overview_json, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(doc_id) DO UPDATE SET
                overview_json = excluded.overview_json,
                created_at = CURRENT_TIMESTAMP
        """, (doc_id, filename, subject.strip().title(), json.dumps(overview_data)))
        conn.commit()


def get_material_overview(doc_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve material overview by document ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM material_overviews WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()
        if row:
            try:
                data = json.loads(row["overview_json"])
                data["doc_id"] = doc_id
                return data
            except Exception:
                pass
        return None


# ==============================================================================
# FEATURE 2 — STUDY SPACE DATABASE PERSISTENCE MODULE
# ==============================================================================
def create_study_space(
    space_id: str,
    owner_user_id: str,
    owner_username: str,
    name: str,
    subject: str,
    description: str,
    invite_token: str
) -> Dict[str, Any]:
    """Create a new shared Study Space and register owner as first member."""
    clean_name = name.strip()
    clean_subject = subject.strip().title()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO study_spaces (space_id, owner_user_id, owner_username, name, subject, description, invite_token, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (space_id, owner_user_id, owner_username, clean_name, clean_subject, description.strip(), invite_token))
        
        # Add owner as 'owner' role member
        conn.execute("""
            INSERT INTO study_space_members (space_id, user_id, username, role, joined_at)
            VALUES (?, ?, ?, 'owner', CURRENT_TIMESTAMP)
            ON CONFLICT(space_id, user_id) DO UPDATE SET role = 'owner'
        """, (space_id, owner_user_id, owner_username))
        
        # Log creation activity
        act_id = f"act_{space_id}_created"
        conn.execute("""
            INSERT INTO study_space_activity (activity_id, space_id, user_id, username, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, 'create', ?, CURRENT_TIMESTAMP)
        """, (act_id, space_id, owner_user_id, owner_username, f"created study space '{clean_name}'"))

        conn.commit()

    return get_study_space_by_id(space_id) or {}


def get_study_space_by_id(space_id: str) -> Optional[Dict[str, Any]]:
    """Fetch Study Space metadata by space_id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_spaces WHERE space_id = ? AND status = 'active'", (space_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_study_space_by_token(invite_token: str) -> Optional[Dict[str, Any]]:
    """Fetch Study Space metadata by secure invite_token."""
    if not invite_token:
        return None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_spaces WHERE invite_token = ? AND status = 'active'", (invite_token.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_study_spaces(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all study spaces where user is a member or owner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, m.role as user_role, m.joined_at
            FROM study_spaces s
            JOIN study_space_members m ON s.space_id = m.space_id
            WHERE m.user_id = ? AND s.status = 'active'
            ORDER BY s.updated_at DESC
        """, (str(user_id),))
        return [dict(row) for row in cursor.fetchall()]


def update_study_space(space_id: str, user_id: str, name: str, subject: str, description: str) -> bool:
    """Update study space details (Owner permission required)."""
    if not is_study_space_owner(space_id, user_id):
        return False
    with get_connection() as conn:
        conn.execute("""
            UPDATE study_spaces 
            SET name = ?, subject = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE space_id = ?
        """, (name.strip(), subject.strip().title(), description.strip(), space_id))
        conn.commit()
    return True


def delete_study_space(space_id: str, user_id: str) -> bool:
    """Delete a study space (Owner permission required)."""
    if not is_study_space_owner(space_id, user_id):
        return False
    with get_connection() as conn:
        conn.execute("UPDATE study_spaces SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE space_id = ?", (space_id,))
        conn.commit()
    return True


def regenerate_invite_token(space_id: str, user_id: str, new_token: str) -> bool:
    """Regenerate invite token for space (Owner permission required)."""
    if not is_study_space_owner(space_id, user_id):
        return False
    with get_connection() as conn:
        conn.execute("UPDATE study_spaces SET invite_token = ?, updated_at = CURRENT_TIMESTAMP WHERE space_id = ?", (new_token, space_id))
        conn.commit()
    return True


def is_study_space_member(space_id: str, user_id: str) -> bool:
    """Verify if user is a member or owner of the Study Space (Backend Security Gate)."""
    if not space_id or not user_id:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM study_space_members WHERE space_id = ? AND user_id = ?", (space_id, str(user_id)))
        return cursor.fetchone() is not None


def is_study_space_owner(space_id: str, user_id: str) -> bool:
    """Verify if user is the Owner of the Study Space."""
    if not space_id or not user_id:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM study_spaces WHERE space_id = ? AND owner_user_id = ?", (space_id, str(user_id)))
        return cursor.fetchone() is not None


def add_study_space_member(space_id: str, user_id: str, username: str, role: str = "member") -> bool:
    """Add a registered user to a Study Space."""
    space = get_study_space_by_id(space_id)
    if not space:
        return False

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO study_space_members (space_id, user_id, username, role, joined_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(space_id, user_id) DO UPDATE SET username = excluded.username
        """, (space_id, str(user_id), username, role))

        # Log join activity
        act_id = f"act_{space_id}_{user_id}_joined_{int(datetime.now().timestamp())}"
        conn.execute("""
            INSERT INTO study_space_activity (activity_id, space_id, user_id, username, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, 'join', ?, CURRENT_TIMESTAMP)
        """, (act_id, space_id, str(user_id), username, f"{username} joined the study space"))

        conn.commit()
    return True


def remove_study_space_member(space_id: str, user_id: str, target_user_id: str) -> bool:
    """Remove a member from space (Owner can remove anyone; members can leave themselves)."""
    is_owner = is_study_space_owner(space_id, user_id)
    is_self = (str(user_id) == str(target_user_id))
    if not (is_owner or is_self):
        return False

    with get_connection() as conn:
        conn.execute("DELETE FROM study_space_members WHERE space_id = ? AND user_id = ?", (space_id, str(target_user_id)))
        conn.commit()
    return True


def get_study_space_members(space_id: str) -> List[Dict[str, Any]]:
    """Get all members of a study space."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_space_members WHERE space_id = ? ORDER BY joined_at ASC", (space_id,))
        return [dict(row) for row in cursor.fetchall()]


def save_study_space_document(
    doc_id: str,
    space_id: str,
    uploaded_by: str,
    uploaded_by_name: str,
    filename: str,
    file_type: str,
    file_size_mb: float,
    total_units: int,
    storage_path: str = ""
) -> bool:
    """Register uploaded document in Study Space (Membership enforced)."""
    if not is_study_space_member(space_id, uploaded_by):
        return False

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO study_space_documents (doc_id, space_id, uploaded_by, uploaded_by_name, filename, file_type, file_size_mb, total_units, storage_path, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(doc_id) DO UPDATE SET
                filename = excluded.filename,
                total_units = excluded.total_units
        """, (doc_id, space_id, str(uploaded_by), uploaded_by_name, filename, file_type, file_size_mb, total_units, storage_path))

        # Log document upload activity
        act_id = f"act_{space_id}_doc_{doc_id}"
        conn.execute("""
            INSERT INTO study_space_activity (activity_id, space_id, user_id, username, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, 'upload', ?, CURRENT_TIMESTAMP)
        """, (act_id, space_id, str(uploaded_by), uploaded_by_name, f"{uploaded_by_name} uploaded study material '{filename}'"))

        conn.commit()
    return True


def get_study_space_documents(space_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Retrieve shared materials in Study Space (Membership enforced)."""
    if not is_study_space_member(space_id, user_id):
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_space_documents WHERE space_id = ? ORDER BY added_at DESC", (space_id,))
        return [dict(row) for row in cursor.fetchall()]


def delete_study_space_document(doc_id: str, space_id: str, user_id: str) -> bool:
    """Remove a shared material (Owner or original uploader only)."""
    if not is_study_space_member(space_id, user_id):
        return False
    
    # Check if user is owner or uploader
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT uploaded_by FROM study_space_documents WHERE doc_id = ? AND space_id = ?", (doc_id, space_id))
        row = cursor.fetchone()
        if not row:
            return False
        if not (is_study_space_owner(space_id, user_id) or str(row["uploaded_by"]) == str(user_id)):
            return False

        conn.execute("DELETE FROM study_space_documents WHERE doc_id = ? AND space_id = ?", (doc_id, space_id))
        conn.commit()
    return True


def save_study_space_message(
    message_id: str,
    space_id: str,
    user_id: str,
    sender_name: str,
    message_text: str,
    message_type: str = "chat"
) -> bool:
    """Save persistent group chat message/thought in Study Space."""
    if not is_study_space_member(space_id, user_id):
        return False

    clean_text = message_text.strip()
    if not clean_text:
        return False

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO study_space_messages (message_id, space_id, user_id, sender_name, message_text, message_type, reactions_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, '{}', CURRENT_TIMESTAMP)
        """, (message_id, space_id, str(user_id), sender_name, clean_text, message_type))
        conn.commit()
    return True


def get_study_space_messages(space_id: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch persistent chat messages in Study Space (Membership enforced)."""
    if not is_study_space_member(space_id, user_id):
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_space_messages WHERE space_id = ? ORDER BY created_at ASC LIMIT ?", (space_id, limit))
        rows = cursor.fetchall()
        messages = []
        for r in rows:
            m = dict(r)
            try:
                m["reactions"] = json.loads(m.get("reactions_json") or "{}")
            except Exception:
                m["reactions"] = {}
            messages.append(m)
        return messages


def toggle_message_reaction(message_id: str, space_id: str, user_id: str, emoji: str) -> bool:
    """Add/remove emoji reaction to a chat message."""
    if not is_study_space_member(space_id, user_id):
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reactions_json FROM study_space_messages WHERE message_id = ? AND space_id = ?", (message_id, space_id))
        row = cursor.fetchone()
        if not row:
            return False

        try:
            reactions = json.loads(row["reactions_json"] or "{}")
        except Exception:
            reactions = {}

        users_who_reacted = reactions.get(emoji, [])
        if user_id in users_who_reacted:
            users_who_reacted.remove(user_id)
        else:
            users_who_reacted.append(user_id)

        if users_who_reacted:
            reactions[emoji] = users_who_reacted
        else:
            reactions.pop(emoji, None)

        conn.execute("UPDATE study_space_messages SET reactions_json = ? WHERE message_id = ?", (json.dumps(reactions), message_id))
        conn.commit()
    return True


def log_study_space_activity(
    activity_id: str,
    space_id: str,
    user_id: str,
    username: str,
    activity_type: str,
    description: str
) -> None:
    """Log an activity event in Study Space."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO study_space_activity (activity_id, space_id, user_id, username, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (activity_id, space_id, str(user_id), username, activity_type, description))
        conn.commit()


def get_study_space_activity(space_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve activity log for Study Space (Membership enforced)."""
    if not is_study_space_member(space_id, user_id):
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_space_activity WHERE space_id = ? ORDER BY created_at DESC LIMIT ?", (space_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def save_study_space_quiz(quiz_id: str, space_id: str, created_by: str, title: str, questions: List[Dict[str, Any]]) -> bool:
    """Save shared group quiz in Study Space."""
    if not is_study_space_member(space_id, created_by):
        return False
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO study_space_quizzes (quiz_id, space_id, created_by, title, questions_json, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(quiz_id) DO UPDATE SET questions_json = excluded.questions_json
        """, (quiz_id, space_id, created_by, title, json.dumps(questions)))

        # Log activity
        act_id = f"act_{space_id}_quiz_{quiz_id}"
        conn.execute("""
            INSERT INTO study_space_activity (activity_id, space_id, user_id, username, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, 'quiz', ?, CURRENT_TIMESTAMP)
        """, (act_id, space_id, created_by, created_by, f"started a new shared Group Quiz: {title}"))

        conn.commit()
    return True


def get_study_space_quizzes(space_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Get all shared quizzes created in Study Space."""
    if not is_study_space_member(space_id, user_id):
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_space_quizzes WHERE space_id = ? ORDER BY created_at DESC", (space_id,))
        rows = cursor.fetchall()
        quizzes = []
        for r in rows:
            q = dict(r)
            try:
                q["questions"] = json.loads(q["questions_json"])
            except Exception:
                q["questions"] = []
            quizzes.append(q)
        return quizzes


def save_study_space_quiz_attempt(
    attempt_id: str,
    quiz_id: str,
    space_id: str,
    user_id: str,
    username: str,
    score: int,
    total: int,
    pct: float,
    correct: int,
    wrong: int
) -> bool:
    """Record individual member quiz attempt in Study Space."""
    if not is_study_space_member(space_id, user_id):
        return False
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO study_space_quiz_attempts (attempt_id, quiz_id, space_id, user_id, username, score, total_questions, percentage, correct_answers, wrong_answers, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(attempt_id) DO UPDATE SET score = excluded.score, percentage = excluded.percentage
        """, (attempt_id, quiz_id, space_id, str(user_id), username, score, total, pct, correct, wrong))

        # Log completion activity
        act_id = f"act_{space_id}_attempt_{attempt_id}"
        conn.execute("""
            INSERT INTO study_space_activity (activity_id, space_id, user_id, username, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, 'quiz_complete', ?, CURRENT_TIMESTAMP)
        """, (act_id, space_id, str(user_id), username, f"{username} completed Group Quiz ({score}/{total} - {pct}%)"))

        conn.commit()
    return True


def get_study_space_quiz_attempts(space_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Get group quiz attempts in Study Space."""
    if not is_study_space_member(space_id, user_id):
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_space_quiz_attempts WHERE space_id = ? ORDER BY timestamp DESC", (space_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_study_space_aggregate_analytics(space_id: str, user_id: str) -> Dict[str, Any]:
    """Calculate group aggregate metrics for Study Space (without revealing private individual answer choices)."""
    if not is_study_space_member(space_id, user_id):
        return {}

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Member count
        cursor.execute("SELECT COUNT(*) as member_count FROM study_space_members WHERE space_id = ?", (space_id,))
        member_count = cursor.fetchone()["member_count"]

        # Shared materials count
        cursor.execute("SELECT COUNT(*) as doc_count FROM study_space_documents WHERE space_id = ?", (space_id,))
        doc_count = cursor.fetchone()["doc_count"]

        # Shared quizzes count
        cursor.execute("SELECT COUNT(*) as quiz_count FROM study_space_quizzes WHERE space_id = ?", (space_id,))
        quiz_count = cursor.fetchone()["quiz_count"]

        # Total messages
        cursor.execute("SELECT COUNT(*) as msg_count FROM study_space_messages WHERE space_id = ?", (space_id,))
        msg_count = cursor.fetchone()["msg_count"]

        # Average group quiz score
        cursor.execute("SELECT AVG(percentage) as avg_score FROM study_space_quiz_attempts WHERE space_id = ?", (space_id,))
        avg_score_row = cursor.fetchone()
        avg_score = round(avg_score_row["avg_score"] or 0.0, 1)

        # Space details
        cursor.execute("SELECT name, subject FROM study_spaces WHERE space_id = ?", (space_id,))
        space_row = cursor.fetchone()
        name = space_row["name"] if space_row else "Study Space"
        subject = space_row["subject"] if space_row else "General"

        return {
            "space_id": space_id,
            "name": name,
            "subject": subject,
            "member_count": member_count,
            "shared_documents_count": doc_count,
            "shared_quizzes_count": quiz_count,
            "messages_count": msg_count,
            "average_group_quiz_score": avg_score
        }


# Initialize database on module load
init_db()


