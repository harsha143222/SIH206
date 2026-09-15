"""
EduMind AI - Centralized Coin & Reward Engine (CoinManager)
Manages the single global coin wallet, transaction history logging, strict Streamlit rerun
deduplication, and study activity tracking.
"""

import uuid
import hashlib
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import streamlit as st
import database


# ==============================================================================
# COIN MANAGER CLASS
# ==============================================================================
class CoinManager:
    """
    Centralized Coin Engine for EduMind AI.
    Controls all coin state, transaction recording, and deduplication.
    """

    @staticmethod
    def initialize():
        """Initialize all coin-related session state safely."""
        import mongodb
        user_id = st.session_state.get("user_id", "user_default")
        user_prof = mongodb.get_profile(user_id) or database.get_user_profile(user_id)

        default_bal = user_prof.get("coins", user_prof.get("coin_balance", 100)) if user_prof else 100
        default_streak = user_prof.get("streak_days", 1) if user_prof else 1
        default_last_date = user_prof.get("last_active_date", str(date.today())) if user_prof else str(date.today())

        if "coin_balance" not in st.session_state:
            st.session_state.coin_balance = default_bal

        if "rewarded_events" not in st.session_state:
            st.session_state.rewarded_events = set()

        if "coin_transactions" not in st.session_state:
            db_txs = mongodb.get_coin_transactions(user_id) or database.get_user_transactions(user_id)
            st.session_state.coin_transactions = db_txs

        if "current_streak" not in st.session_state:
            st.session_state.current_streak = default_streak

        if "longest_streak" not in st.session_state:
            st.session_state.longest_streak = default_streak

        if "last_study_date" not in st.session_state:
            st.session_state.last_study_date = default_last_date

        if "activity_counts" not in st.session_state:
            st.session_state.activity_counts = {
                "doubts": 0,
                "quizzes": 0,
                "correct_quiz_answers": 0,
                "aptitude_tests": 0,
                "games_played": 0,
                "games_won": 0,
                "topics_completed": 0
            }

        # Keep legacy aliases in sync
        st.session_state.coins = st.session_state.coin_balance
        st.session_state.learning_streak = st.session_state.current_streak

    @classmethod
    def get_balance(cls) -> int:
        cls.initialize()
        return st.session_state.coin_balance

    @classmethod
    def can_afford(cls, amount: int) -> bool:
        cls.initialize()
        return amount >= 0 and st.session_state.coin_balance >= amount

    @classmethod
    def claim_reward(cls, reward_id: str, amount: int, reason: str, source: str, reference_id: Optional[str] = None) -> bool:
        """
        Claim a coin reward with automatic deduplication using reward_id.
        Returns True if awarded, False if already rewarded or invalid.
        """
        cls.initialize()

        if not reward_id or reward_id in st.session_state.rewarded_events:
            return False

        if amount <= 0:
            return False

        st.session_state.rewarded_events.add(reward_id)
        cls.add_coins(amount=amount, reason=reason, source=source, reference_id=reference_id or reward_id)
        return True

    @classmethod
    def add_coins(cls, amount: int, reason: str, source: str, reference_id: Optional[str] = None) -> int:
        """Add coins directly to wallet and record transaction."""
        cls.initialize()
        if amount <= 0:
            return st.session_state.coin_balance

        st.session_state.coin_balance += amount
        st.session_state.coins = st.session_state.coin_balance

        tx_id = f"tx_{uuid.uuid4().hex[:10]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        tx_record = {
            "transaction_id": tx_id,
            "timestamp": timestamp,
            "amount": amount,
            "type": "EARNING",
            "reason": reason,
            "source": source,
            "reference_id": reference_id or "",
            "balance_after": st.session_state.coin_balance
        }

        st.session_state.coin_transactions.insert(0, tx_record)

        # Save to MongoDB & SQLite
        import mongodb
        user_id = st.session_state.get("user_id", "user_default")
        user_name = st.session_state.get("user_name", "Student")
        
        mongodb.save_coin_transaction(user_id, tx_record)
        mongodb.update_user_coins(user_id, st.session_state.coin_balance, st.session_state.current_streak, st.session_state.last_study_date)
        
        database.save_transaction(user_id, tx_record)
        database.save_user_profile(
            user_id,
            user_name,
            st.session_state.coin_balance,
            st.session_state.current_streak,
            st.session_state.last_study_date
        )

        return st.session_state.coin_balance

    @classmethod
    def spend_coins(cls, amount: int, reason: str, source: str, reference_id: Optional[str] = None) -> bool:
        """Deduct coins from wallet if sufficient balance exists."""
        cls.initialize()
        if amount <= 0:
            return False

        if st.session_state.coin_balance < amount:
            return False

        st.session_state.coin_balance -= amount
        st.session_state.coins = st.session_state.coin_balance

        tx_id = f"tx_{uuid.uuid4().hex[:10]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        tx_record = {
            "transaction_id": tx_id,
            "timestamp": timestamp,
            "amount": -amount,
            "type": "SPENDING",
            "reason": reason,
            "source": source,
            "reference_id": reference_id or "",
            "balance_after": st.session_state.coin_balance
        }

        st.session_state.coin_transactions.insert(0, tx_record)

        # Save to MongoDB & SQLite
        import mongodb
        user_id = st.session_state.get("user_id", "user_default")
        user_name = st.session_state.get("user_name", "Student")

        mongodb.save_coin_transaction(user_id, tx_record)
        mongodb.update_user_coins(user_id, st.session_state.coin_balance, st.session_state.current_streak, st.session_state.last_study_date)

        database.save_transaction(user_id, tx_record)
        database.save_user_profile(
            user_id,
            user_name,
            st.session_state.coin_balance,
            st.session_state.current_streak,
            st.session_state.last_study_date
        )

        return True

    @classmethod
    def get_transactions(cls) -> List[Dict[str, Any]]:
        cls.initialize()
        return st.session_state.coin_transactions

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Calculate coin statistics for today and all-time."""
        cls.initialize()
        today_prefix = date.today().isoformat()

        today_earned = 0
        today_spent = 0
        total_earned = 0
        total_spent = 0

        for tx in st.session_state.coin_transactions:
            amt = tx.get("amount", 0)
            tx_time = str(tx.get("timestamp", ""))

            if amt > 0:
                total_earned += amt
                if tx_time.startswith(today_prefix):
                    today_earned += amt
            else:
                total_spent += abs(amt)
                if tx_time.startswith(today_prefix):
                    today_spent += abs(amt)

        return {
            "balance": st.session_state.coin_balance,
            "today_earned": today_earned,
            "today_spent": today_spent,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "streak": st.session_state.current_streak
        }

    @classmethod
    def record_study_activity(cls, activity_type: str, increment: int = 1):
        """
        Record genuine educational activity and update study streak.
        Does NOT update streak for simply opening dashboard or refreshing page.
        """
        cls.initialize()
        today_str = str(date.today())

        if activity_type in st.session_state.activity_counts:
            st.session_state.activity_counts[activity_type] += increment

        last_date_str = st.session_state.last_study_date
        if last_date_str != today_str:
            if last_date_str:
                try:
                    last_d = date.fromisoformat(last_date_str)
                    delta = (date.today() - last_d).days
                    if delta == 1:
                        st.session_state.current_streak += 1
                    elif delta > 1:
                        st.session_state.current_streak = 1
                except Exception:
                    st.session_state.current_streak = 1
            else:
                st.session_state.current_streak = 1

            st.session_state.last_study_date = today_str
            st.session_state.longest_streak = max(st.session_state.longest_streak, st.session_state.current_streak)
            st.session_state.learning_streak = st.session_state.current_streak

            # Check 7-day streak milestone
            if st.session_state.current_streak >= 7:
                cls.claim_reward(
                    reward_id=f"streak_reward_7_days_{today_str}",
                    amount=50,
                    reason="7-Day Study Streak Milestone!",
                    source="streak"
                )
