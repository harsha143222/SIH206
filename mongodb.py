"""
EduMind AI - MongoDB Atlas Database Persistence Module
Manages MongoDB Atlas connection, collection schemas, indexes, and full CRUD operations
for users, profiles, documents, chat, quiz results, coins, progress, and group learning.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import config

logger = logging.getLogger("mongodb")

# Try importing pymongo
try:
    import pymongo
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from bson.objectid import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    logger.warning("pymongo is not installed.")

_mongo_client: Optional[Any] = None
_db_connected: Optional[bool] = None

def get_client() -> Optional[Any]:
    """Get or initialize singleton MongoClient instance."""
    global _mongo_client, _db_connected
    if not PYMONGO_AVAILABLE:
        return None
        
    uri = config.get_mongodb_uri()
    if not uri:
        return None

    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
            # Test ping
            _mongo_client.admin.command('ping')
            _db_connected = True
            logger.info("Successfully connected to MongoDB Atlas!")
            init_indexes()
        except Exception as e:
            logger.error("MongoDB Atlas connection failed: %s", str(e))
            _db_connected = False
            _mongo_client = None
    return _mongo_client

def is_mongodb_available() -> bool:
    """Check if MongoDB Atlas connection is live and reachable."""
    return get_client() is not None

def get_db():
    """Return edumind database instance."""
    client = get_client()
    if client is None:
        return None
    return client[config.get_mongodb_database()]

def init_indexes():
    """Create collection indexes for fast user-filtered queries."""
    db = get_db()
    if db is None:
        return

    try:
        # Users collection indexes
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("username", ASCENDING)], unique=True)

        # Profiles collection index
        db.profiles.create_index([("user_id", ASCENDING)], unique=True)

        # Documents collection index
        db.documents.create_index([("user_id", ASCENDING), ("subject", ASCENDING)])
        db.documents.create_index([("user_id", ASCENDING), ("doc_id", ASCENDING)], unique=True)

        # Chat history index
        db.chat_history.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        # Learned topics index
        db.learned_topics.create_index([("user_id", ASCENDING), ("subject", ASCENDING)])
        db.learned_topics.create_index([("user_id", ASCENDING), ("topic_id", ASCENDING)], unique=True)

        # Quiz results index
        db.quiz_results.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        # Coin transactions index
        db.coin_transactions.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        db.coin_transactions.create_index([("transaction_id", ASCENDING)], unique=True)

        # Groups indexes
        db.groups.create_index([("group_id", ASCENDING)], unique=True)
        db.groups.create_index([("invite_token", ASCENDING)])
        db.groups.create_index([("join_code", ASCENDING)])

        # Group membership index
        db.group_members.create_index([("user_id", ASCENDING), ("group_id", ASCENDING)], unique=True)

        logger.info("MongoDB Atlas indexes initialized successfully.")
    except Exception as e:
        logger.warning("Error creating MongoDB indexes: %s", str(e))

# ==============================================================================
# USER & PROFILE OPERATIONS
# ==============================================================================
def create_user(email: str, username: str, password_hash: str) -> Optional[Dict[str, Any]]:
    """Create a new user document in MongoDB."""
    db = get_db()
    if db is None:
        return None

    now = datetime.now()
    user_doc = {
        "email": email.strip().lower(),
        "username": username.strip(),
        "password_hash": password_hash,
        "created_at": now,
        "last_login": now,
        "is_active": True
    }
    try:
        res = db.users.insert_one(user_doc)
        user_doc["_id"] = str(res.inserted_id)
        return user_doc
    except Exception as e:
        logger.error("Failed to create user in MongoDB: %s", str(e))
        return None

def find_user_by_email_or_username(identifier: str) -> Optional[Dict[str, Any]]:
    """Find user document by email or username (case-insensitive)."""
    db = get_db()
    if db is None:
        return None

    clean = identifier.strip()
    import re
    regex_pattern = f"^{re.escape(clean)}$"
    query = {"$or": [{"email": clean.lower()}, {"username": {"$regex": regex_pattern, "$options": "i"}}]}
    try:
        user = db.users.find_one(query)
        if user:
            user["_id"] = str(user["_id"])
            return user
    except Exception as e:
        logger.error("Error finding user in MongoDB: %s", str(e))
    return None

def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Find user document by user_id string or ObjectId."""
    db = get_db()
    if db is None:
        return None

    try:
        try:
            oid = ObjectId(user_id)
            user = db.users.find_one({"_id": oid})
        except Exception:
            user = db.users.find_one({"_id": user_id})

        if user:
            user["_id"] = str(user["_id"])
            return user
    except Exception as e:
        logger.error("Error finding user by ID: %s", str(e))
    return None

def update_user_last_login(user_id: str):
    """Update last_login timestamp."""
    db = get_db()
    if db is None:
        return
    now = datetime.now()
    try:
        try:
            oid = ObjectId(user_id)
            db.users.update_one({"_id": oid}, {"$set": {"last_login": now}})
        except Exception:
            db.users.update_one({"_id": user_id}, {"$set": {"last_login": now}})
    except Exception as e:
        logger.error("Failed to update last login: %s", str(e))

def create_or_update_profile(user_id: str, display_name: str, avatar: str = "??", bio: str = "", coins: int = 100, streak_days: int = 1, last_active_date: str = "") -> Dict[str, Any]:
    """Create or update user profile document."""
    db = get_db()
    now = datetime.now()
    profile_doc = {
        "user_id": str(user_id),
        "display_name": display_name.strip(),
        "avatar": avatar,
        "bio": bio.strip(),
        "coins": coins,
        "streak_days": streak_days,
        "last_active_date": last_active_date or now.strftime("%Y-%m-%d"),
        "updated_at": now
    }

    if db is not None:
        try:
            db.profiles.update_one(
                {"user_id": str(user_id)},
                {"$set": profile_doc, "$setOnInsert": {"created_at": now}},
                upsert=True
            )
        except Exception as e:
            logger.error("Error saving profile to MongoDB: %s", str(e))

    return profile_doc

def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve profile document for user_id."""
    db = get_db()
    if db is None:
        return None

    try:
        prof = db.profiles.find_one({"user_id": str(user_id)})
        if prof:
            prof["_id"] = str(prof["_id"])
            return prof
    except Exception as e:
        logger.error("Error retrieving profile from MongoDB: %s", str(e))
    return None

# ==============================================================================
# COIN TRANSACTIONS & WALLET OPERATIONS
# ==============================================================================
def update_user_coins(user_id: str, new_balance: int, streak_days: int = 1, last_active_date: str = "") -> None:
    """Atomically update coin balance and streak in profile document."""
    db = get_db()
    if db is None:
        return

    update_fields = {"coins": new_balance, "updated_at": datetime.now()}
    if streak_days is not None:
        update_fields["streak_days"] = streak_days
    if last_active_date:
        update_fields["last_active_date"] = last_active_date

    try:
        db.profiles.update_one({"user_id": str(user_id)}, {"$set": update_fields}, upsert=True)
    except Exception as e:
        logger.error("Failed to update user coins in MongoDB: %s", str(e))

def save_coin_transaction(user_id: str, tx: Dict[str, Any]) -> None:
    """Insert a coin transaction record into coin_transactions collection."""
    db = get_db()
    if db is None:
        return

    tx_doc = {
        "user_id": str(user_id),
        "transaction_id": tx["transaction_id"],
        "amount": tx["amount"],
        "type": tx["type"],
        "reason": tx["reason"],
        "source": tx["source"],
        "reference_id": tx.get("reference_id", ""),
        "balance_after": tx["balance_after"],
        "timestamp": tx.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        db.coin_transactions.update_one(
            {"user_id": str(user_id), "transaction_id": tx["transaction_id"]},
            {"$setOnInsert": tx_doc},
            upsert=True
        )
    except Exception as e:
        logger.error("Failed to save transaction in MongoDB: %s", str(e))

def get_coin_transactions(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all coin transactions for user_id ordered by timestamp descending."""
    db = get_db()
    if db is None:
        return []

    try:
        cursor = db.coin_transactions.find({"user_id": str(user_id)}).sort("timestamp", DESCENDING)
        res = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            res.append(doc)
        return res
    except Exception as e:
        logger.error("Error reading transactions from MongoDB: %s", str(e))
        return []

# ==============================================================================
# DOCUMENTS & CHAT HISTORY OPERATIONS
# ==============================================================================
def save_document(user_id: str, doc_data: Dict[str, Any], storage_path: str = "") -> None:
    """Save document metadata to MongoDB documents collection."""
    db = get_db()
    if db is None:
        return

    doc = {
        "user_id": str(user_id),
        "doc_id": doc_data["doc_id"],
        "filename": doc_data["filename"],
        "file_hash": doc_data.get("file_hash", ""),
        "subject": doc_data.get("subject", config.DEFAULT_SUBJECT),
        "file_type": doc_data["file_type"],
        "file_size_mb": doc_data["file_size_mb"],
        "total_units": doc_data["total_units"],
        "storage_path": storage_path,
        "created_at": datetime.now()
    }
    try:
        db.documents.update_one(
            {"user_id": str(user_id), "doc_id": doc_data["doc_id"]},
            {"$set": doc},
            upsert=True
        )
    except Exception as e:
        logger.error("Failed to save document in MongoDB: %s", str(e))

def get_user_documents(user_id: str, subject: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve user-specific documents, optionally filtered by subject."""
    db = get_db()
    if db is None:
        return []

    q = {"user_id": str(user_id)}
    if subject:
        q["subject"] = subject.strip().title()

    try:
        cursor = db.documents.find(q).sort("created_at", DESCENDING)
        res = []
        for d in cursor:
            d["_id"] = str(d["_id"])
            res.append(d)
        return res
    except Exception as e:
        logger.error("Error reading user documents from MongoDB: %s", str(e))
        return []

def save_chat_messages(user_id: str, subject: str, messages: List[Dict[str, Any]]) -> None:
    """Save user chat conversation to chat_history collection."""
    db = get_db()
    if db is None:
        return

    doc = {
        "user_id": str(user_id),
        "subject": subject,
        "messages": messages,
        "updated_at": datetime.now()
    }
    try:
        db.chat_history.update_one(
            {"user_id": str(user_id), "subject": subject},
            {"$set": doc, "$setOnInsert": {"created_at": datetime.now()}},
            upsert=True
        )
    except Exception as e:
        logger.error("Failed to save chat history in MongoDB: %s", str(e))

def get_chat_messages(user_id: str, subject: str) -> List[Dict[str, Any]]:
    """Retrieve user chat messages for a specific subject."""
    db = get_db()
    if db is None:
        return []

    try:
        record = db.chat_history.find_one({"user_id": str(user_id), "subject": subject})
        if record and "messages" in record:
            return record["messages"]
    except Exception as e:
        logger.error("Error reading chat history from MongoDB: %s", str(e))
    return []

# ==============================================================================
# QUIZ & LEARNING PROGRESS OPERATIONS
# ==============================================================================
def save_quiz_result(user_id: str, attempt_id: str, subject: str, title: str, score: int, total: int, pct: float, coins: int, report: Dict[str, Any]) -> None:
    """Save quiz result record in quiz_results collection."""
    db = get_db()
    if db is None:
        return

    doc = {
        "user_id": str(user_id),
        "attempt_id": attempt_id,
        "subject": subject,
        "quiz_title": title,
        "score": score,
        "total_questions": total,
        "percentage": pct,
        "coins_earned": coins,
        "report": report,
        "created_at": datetime.now()
    }
    try:
        db.quiz_results.update_one(
            {"user_id": str(user_id), "attempt_id": attempt_id},
            {"$set": doc},
            upsert=True
        )
    except Exception as e:
        logger.error("Failed to save quiz result in MongoDB: %s", str(e))

def get_user_quiz_results(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve user quiz results ordered by created_at descending."""
    db = get_db()
    if db is None:
        return []

    try:
        cursor = db.quiz_results.find({"user_id": str(user_id)}).sort("created_at", DESCENDING)
        res = []
        for d in cursor:
            d["_id"] = str(d["_id"])
            res.append(d)
        return res
    except Exception as e:
        logger.error("Error reading quiz results from MongoDB: %s", str(e))
        return []

def save_learned_topic(user_id: str, topic_doc: Dict[str, Any]) -> None:
    """Save learned topic record to learned_topics collection."""
    db = get_db()
    if db is None:
        return

    topic_doc["user_id"] = str(user_id)
    topic_doc["updated_at"] = datetime.now()
    t_id = topic_doc.get("topic_id") or topic_doc.get("topic")

    try:
        db.learned_topics.update_one(
            {"user_id": str(user_id), "topic_id": t_id},
            {"$set": topic_doc},
            upsert=True
        )
    except Exception as e:
        logger.error("Failed to save learned topic in MongoDB: %s", str(e))

def get_user_learned_topics(user_id: str) -> Dict[str, Any]:
    """Retrieve all learned topics for user_id."""
    db = get_db()
    if db is None:
        return {}

    try:
        cursor = db.learned_topics.find({"user_id": str(user_id)})
        res = {}
        for d in cursor:
            t_name = d.get("topic")
            if t_name:
                res[t_name] = d
        return res
    except Exception as e:
        logger.error("Error reading learned topics from MongoDB: %s", str(e))
        return {}

# ==============================================================================
# DASHBOARD ANALYTICS & ACHIEVEMENTS OPERATIONS
# ==============================================================================
def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """Calculate live user statistics from MongoDB collections."""
    db = get_db()
    default_stats = {
        "total_documents": 0,
        "total_explored": 0,
        "total_quizzes": 0,
        "average_score": 0.0,
        "has_quiz_data": False
    }

    if db is None:
        return default_stats

    try:
        u_str = str(user_id)
        doc_count = db.documents.count_documents({"user_id": u_str})
        topic_count = db.learned_topics.count_documents({"user_id": u_str})
        
        quizzes = list(db.quiz_results.find({"user_id": u_str}))
        quiz_count = len(quizzes)

        if quiz_count > 0:
            total_pct = sum(q.get("percentage", 0.0) for q in quizzes)
            avg_score = round(total_pct / quiz_count, 1)
            has_quiz = True
        else:
            avg_score = 0.0
            has_quiz = False

        return {
            "total_documents": doc_count,
            "total_explored": topic_count,
            "total_quizzes": quiz_count,
            "average_score": avg_score,
            "has_quiz_data": has_quiz
        }
    except Exception as e:
        logger.error("Error computing user analytics in MongoDB: %s", str(e))
        return default_stats

def get_user_recent_activity(user_id: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Retrieve unified recent activity timeline for user_id from MongoDB."""
    db = get_db()
    if db is None:
        return []

    activities = []
    u_str = str(user_id)

    try:
        # Quiz Results
        quiz_cursor = db.quiz_results.find({"user_id": u_str}).sort("created_at", DESCENDING).limit(limit)
        for q in quiz_cursor:
            dt = q.get("created_at")
            ts_str = dt.strftime("%Y-%m-%d %H:%M") if isinstance(dt, datetime) else str(dt)
            activities.append({
                "type": "quiz",
                "icon": "✓",
                "title": f"Completed {q.get('subject', 'Quiz')} Quiz",
                "detail": f"Score: {q.get('score', 0)}/{q.get('total_questions', 0)} ({q.get('percentage', 0)}%)",
                "badge": f"+{q.get('coins_earned', 0)} coins",
                "timestamp_raw": dt if isinstance(dt, datetime) else datetime.now(),
                "time_display": ts_str
            })

        # Documents
        doc_cursor = db.documents.find({"user_id": u_str}).sort("created_at", DESCENDING).limit(limit)
        for d in doc_cursor:
            dt = d.get("created_at")
            ts_str = dt.strftime("%Y-%m-%d %H:%M") if isinstance(dt, datetime) else str(dt)
            activities.append({
                "type": "document",
                "icon": "📚",
                "title": f"Uploaded {d.get('subject', 'Study')} Notes",
                "detail": d.get("filename", "Document added"),
                "badge": "Document added",
                "timestamp_raw": dt if isinstance(dt, datetime) else datetime.now(),
                "time_display": ts_str
            })

        # Coin Transactions
        tx_cursor = db.coin_transactions.find({"user_id": u_str}).sort("timestamp", DESCENDING).limit(limit)
        for tx in tx_cursor:
            amt = tx.get("amount", 0)
            sign = "+" if amt > 0 else ""
            activities.append({
                "type": "wallet",
                "icon": "🪙" if amt > 0 else "💰",
                "title": tx.get("reason", "Coin Activity"),
                "detail": f"Source: {tx.get('source', 'System')}",
                "badge": f"{sign}{amt} coins",
                "timestamp_raw": datetime.now(),
                "time_display": tx.get("timestamp", "")
            })

        # Sort combined activity timeline
        activities.sort(key=lambda x: x["time_display"], reverse=True)
        return activities[:limit]
    except Exception as e:
        logger.error("Error gathering user activity from MongoDB: %s", str(e))
        return []

def get_user_achievements(user_id: str) -> List[Dict[str, Any]]:
    """Determine unlocked/locked status of user achievements based on real MongoDB records."""
    db = get_db()
    u_str = str(user_id)

    prof = get_profile(u_str) or {}
    streak = prof.get("streak_days", 1)

    analytics = get_user_analytics(u_str)

    achievements = [
        {
            "id": "streak_7",
            "icon": "🔥",
            "title": "7 Day Streak",
            "desc": "Maintain a continuous 7-day study streak",
            "unlocked": streak >= 7
        },
        {
            "id": "first_doubt",
            "icon": "🧠",
            "title": "First AI Question",
            "desc": "Ask your first doubt to EduMind AI Tutor",
            "unlocked": analytics["total_explored"] > 0
        },
        {
            "id": "first_notes",
            "icon": "📚",
            "title": "First Notes Upload",
            "desc": "Upload course PDF or PPT notes to RAG knowledge base",
            "unlocked": analytics["total_documents"] > 0
        },
        {
            "id": "quiz_master",
            "icon": "🎯",
            "title": "Quiz Master",
            "desc": "Complete at least 1 quiz with a score of 80% or higher",
            "unlocked": analytics["total_quizzes"] > 0 and analytics["average_score"] >= 80.0
        },
        {
            "id": "game_explorer",
            "icon": "🎮",
            "title": "Game Explorer",
            "desc": "Play an educational learning game",
            "unlocked": False
        }
    ]

    if db is not None:
        try:
            # Check game progress
            gp = db.game_progress.find_one({"user_id": u_str})
            if gp:
                for a in achievements:
                    if a["id"] == "game_explorer":
                        a["unlocked"] = True
        except Exception:
            pass

    return achievements

# ==============================================================================
# USER-ISOLATED GAME PROGRESS OPERATIONS
# ==============================================================================
def save_user_game_progress(user_id: str, game_id: str, level_played: int, score: int, total_questions: int, coins_earned: int = 0) -> Dict[str, Any]:
    """
    Save or update user's game progress in MongoDB game_progress collection.
    Unlocks next level if percentage >= 60.0%.
    """
    db = get_db()
    u_str = str(user_id)
    pct = round((score / total_questions) * 100, 1) if total_questions > 0 else 0.0
    is_win = pct >= 60.0

    existing = get_user_game_progress(u_str, game_id)
    current_highest = existing.get("highest_unlocked_level", 1)
    best_score = max(existing.get("best_score", 0.0), pct)
    attempts = existing.get("attempts", 0) + 1

    new_highest = current_highest
    if is_win and level_played >= current_highest and current_highest < 5:
        new_highest = level_played + 1

    record = {
        "user_id": u_str,
        "game_id": game_id,
        "last_played_level": level_played,
        "highest_unlocked_level": new_highest,
        "best_score": best_score,
        "last_score": pct,
        "attempts": attempts,
        "coins_earned_total": existing.get("coins_earned_total", 0) + coins_earned,
        "updated_at": datetime.now()
    }

    if db is not None:
        try:
            db.game_progress.update_one(
                {"user_id": u_str, "game_id": game_id},
                {"$set": record},
                upsert=True
            )
        except Exception as e:
            logger.error("Error saving game progress to MongoDB: %s", str(e))

    return record

def get_user_game_progress(user_id: str, game_id: str) -> Dict[str, Any]:
    """Retrieve isolated game progress for a user and specific game."""
    db = get_db()
    u_str = str(user_id)
    default_rec = {
        "user_id": u_str,
        "game_id": game_id,
        "last_played_level": 1,
        "highest_unlocked_level": 1,
        "best_score": 0.0,
        "last_score": 0.0,
        "attempts": 0,
        "coins_earned_total": 0
    }

    if db is None:
        return default_rec

    try:
        doc = db.game_progress.find_one({"user_id": u_str, "game_id": game_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
    except Exception as e:
        logger.error("Error fetching game progress from MongoDB: %s", str(e))

    return default_rec

def get_all_user_game_progress(user_id: str) -> Dict[str, Dict[str, Any]]:
    """Retrieve all game progress records for user_id as a dict keyed by game_id."""
    db = get_db()
    u_str = str(user_id)
    res = {}

    if db is None:
        return res

    try:
        cursor = db.game_progress.find({"user_id": u_str})
        for doc in cursor:
            g_id = doc.get("game_id")
            if g_id:
                doc["_id"] = str(doc["_id"])
                res[g_id] = doc
    except Exception as e:
        logger.error("Error reading all game progress from MongoDB: %s", str(e))

    return res


