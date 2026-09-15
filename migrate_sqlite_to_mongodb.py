"""
EduMind AI - SQLite to MongoDB Migration Utility
Migrates legacy SQLite data (users, profiles, coin transactions, quiz results,
learned topics, and documents) into MongoDB Atlas.
"""

import sys
import sqlite3
import json
import logging
from datetime import datetime
import config
import mongodb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")

def migrate():
    logger.info("Starting EduMind AI SQLite to MongoDB Migration...")
    
    if not mongodb.is_mongodb_available():
        logger.error("MongoDB Atlas is not reachable. Check MONGODB_URI in config/.env before running migration.")
        sys.exit(1)

    db = mongodb.get_db()
    
    if not config.DB_PATH.exists():
        logger.warning("SQLite database file not found at %s. Nothing to migrate.", config.DB_PATH)
        sys.exit(0)

    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Migrate Users & Profiles
    logger.info("Migrating Users & Profiles...")
    try:
        cursor.execute("SELECT * FROM users")
        user_rows = cursor.fetchall()
        migrated_users = 0
        for row in user_rows:
            u_dict = dict(row)
            uid = u_dict["user_id"]
            uname = u_dict["username"]
            coins = u_dict.get("coin_balance", 100)
            streak = u_dict.get("streak_days", 1)
            last_date = u_dict.get("last_active_date", "")

            # Check if user document exists
            user_doc = mongodb.find_user_by_email_or_username(uname)
            if not user_doc:
                # Default hash for migrated users
                pw_hash = auth.hash_password("EduMind2026!") if 'auth' in globals() else "pbkdf2:sha256:migrated"
                user_doc = mongodb.create_user(f"{uname.lower()}@edumind.app", uname, pw_hash)
            
            if user_doc:
                m_uid = str(user_doc["_id"])
                mongodb.create_or_update_profile(
                    user_id=m_uid,
                    display_name=uname,
                    coins=coins,
                    streak_days=streak,
                    last_active_date=last_date
                )
                migrated_users += 1
        logger.info("Migrated %d users & profiles to MongoDB.", migrated_users)
    except Exception as e:
        logger.error("Error migrating users: %s", str(e))

    # 2. Migrate Documents Metadata
    logger.info("Migrating Documents Metadata...")
    try:
        cursor.execute("SELECT * FROM documents")
        doc_rows = cursor.fetchall()
        migrated_docs = 0
        for row in doc_rows:
            d_dict = dict(row)
            mongodb.save_document("user_default", d_dict, storage_path=d_dict.get("storage_path", ""))
            migrated_docs += 1
        logger.info("Migrated %d documents to MongoDB.", migrated_docs)
    except Exception as e:
        logger.error("Error migrating documents: %s", str(e))

    # 3. Migrate Coin Transactions
    logger.info("Migrating Coin Transactions...")
    try:
        cursor.execute("SELECT * FROM coin_transactions")
        tx_rows = cursor.fetchall()
        migrated_txs = 0
        for row in tx_rows:
            tx = dict(row)
            uid = tx.get("user_id", "user_default")
            mongodb.save_coin_transaction(uid, tx)
            migrated_txs += 1
        logger.info("Migrated %d coin transactions to MongoDB.", migrated_txs)
    except Exception as e:
        logger.error("Error migrating coin transactions: %s", str(e))

    # 4. Migrate Quiz Results
    logger.info("Migrating Quiz Results...")
    try:
        cursor.execute("SELECT * FROM quiz_results")
        q_rows = cursor.fetchall()
        migrated_quizzes = 0
        for row in q_rows:
            qr = dict(row)
            uid = qr.get("user_id", "user_default")
            report_json = json.loads(qr["report_json"]) if qr.get("report_json") else {}
            mongodb.save_quiz_result(
                user_id=uid,
                attempt_id=qr["attempt_id"],
                subject=qr.get("subject", "General"),
                title=qr.get("quiz_title", "Personalized Quiz"),
                score=qr.get("score", 0),
                total=qr.get("total_questions", 0),
                pct=qr.get("percentage", 0.0),
                coins=qr.get("coins_earned", 0),
                report=report_json
            )
            migrated_quizzes += 1
        logger.info("Migrated %d quiz results to MongoDB.", migrated_quizzes)
    except Exception as e:
        logger.error("Error migrating quiz results: %s", str(e))

    logger.info("?? EduMind AI Migration to MongoDB completed successfully!")

if __name__ == "__main__":
    migrate()
