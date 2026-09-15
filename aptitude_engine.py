"""
EduMind AI - Aptitude Practice & Streak Module
Supports Quantitative Aptitude, Logical Reasoning, Verbal Ability, Data Interpretation,
Number Systems, Percentages, Profit & Loss, Time & Work, Speed & Distance, Ratios, Averages,
Probability, Permutations & Combinations, Basic Algebra, and Geometry.

Executes 100% in pure Python without consuming Gemini API quota.
Integrates with CoinManager for deduplicated rewards and Aptitude Streaks.
"""

import uuid
import random
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
from coin_manager import CoinManager

# ==============================================================================
# APTITUDE CATEGORIES & QUESTION BANK GENERATOR
# ==============================================================================
CATEGORIES = [
    "Quantitative Aptitude",
    "Logical Reasoning",
    "Verbal Ability",
    "Data Interpretation",
    "Number Systems",
    "Percentages",
    "Profit & Loss",
    "Time & Work",
    "Time, Speed & Distance",
    "Ratios",
    "Averages",
    "Probability",
    "Permutations & Combinations",
    "Basic Algebra",
    "Geometry"
]

APTITUDE_QUESTION_BANK = [
    # Quant / Number Systems
    {
        "id": "apt_q1",
        "category": "Number Systems",
        "difficulty": "Easy",
        "question": "What is the sum of the first 20 natural numbers?",
        "options": ["190", "200", "210", "220"],
        "correct_index": 2,
        "explanation": "Sum = n*(n+1)/2 = 20 * 21 / 2 = 210."
    },
    {
        "id": "apt_q2",
        "category": "Number Systems",
        "difficulty": "Medium",
        "question": "Find the HCF of 108, 288 and 360.",
        "options": ["18", "24", "36", "48"],
        "correct_index": 2,
        "explanation": "108 = 2^2 * 3^3, 288 = 2^5 * 3^2, 360 = 2^3 * 3^2 * 5. HCF = 2^2 * 3^2 = 36."
    },

    # Percentages & Profit & Loss
    {
        "id": "apt_q3",
        "category": "Percentages",
        "difficulty": "Easy",
        "question": "If 20% of a number is 45, what is 80% of that number?",
        "options": ["180", "160", "150", "200"],
        "correct_index": 0,
        "explanation": "80% is 4 times 20%. So 4 * 45 = 180."
    },
    {
        "id": "apt_q4",
        "category": "Profit & Loss",
        "difficulty": "Medium",
        "question": "A trader marks up his goods by 25% and offers a 10% discount. What is his net profit percentage?",
        "options": ["12.5%", "15%", "10%", "12%"],
        "correct_index": 0,
        "explanation": "Net change = 25 - 10 - (25*10)/100 = 15 - 2.5 = 12.5%."
    },

    # Time & Work / Time, Speed & Distance
    {
        "id": "apt_q5",
        "category": "Time & Work",
        "difficulty": "Medium",
        "question": "A can finish a work in 10 days, B in 15 days. Working together, in how many days can they complete it?",
        "options": ["5 days", "6 days", "7.5 days", "8 days"],
        "correct_index": 1,
        "explanation": "Combined rate = 1/10 + 1/15 = 5/30 = 1/6. Time = 6 days."
    },
    {
        "id": "apt_q6",
        "category": "Time, Speed & Distance",
        "difficulty": "Hard",
        "question": "Two trains of lengths 140 m and 160 m run on parallel tracks in opposite directions at 60 km/h and 40 km/h. Time to cross each other is:",
        "options": ["9.8 s", "10.8 s", "12 s", "15 s"],
        "correct_index": 1,
        "explanation": "Relative speed = 60 + 40 = 100 km/h = 100 * 5/18 = 250/9 m/s. Total distance = 140 + 160 = 300 m. Time = 300 / (250/9) = 10.8 seconds."
    },

    # Ratios & Averages
    {
        "id": "apt_q7",
        "category": "Ratios",
        "difficulty": "Easy",
        "question": "If A:B = 3:4 and B:C = 8:9, find A:C.",
        "options": ["1:2", "2:3", "3:4", "4:5"],
        "correct_index": 1,
        "explanation": "A/C = (A/B) * (B/C) = (3/4) * (8/9) = 24/36 = 2/3."
    },
    {
        "id": "apt_q8",
        "category": "Averages",
        "difficulty": "Medium",
        "question": "The average score of 5 students is 80. If a 6th student scoring 92 is added, what is the new average?",
        "options": ["81", "82", "83", "84"],
        "correct_index": 1,
        "explanation": "Sum of 5 = 400. Total sum = 400 + 92 = 492. New average = 492 / 6 = 82."
    },

    # Probability & Permutations & Combinations
    {
        "id": "apt_q9",
        "category": "Probability",
        "difficulty": "Medium",
        "question": "Two dice are thrown together. What is the probability that the sum is 7?",
        "options": ["1/6", "5/36", "1/12", "7/36"],
        "correct_index": 0,
        "explanation": "Pairs resulting in sum 7: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) -> 6 outcomes out of 36. P = 6/36 = 1/6."
    },
    {
        "id": "apt_q10",
        "category": "Permutations & Combinations",
        "difficulty": "Hard",
        "question": "In how many ways can 5 people be seated around a circular table?",
        "options": ["120", "24", "60", "48"],
        "correct_index": 1,
        "explanation": "Circular permutations = (n-1)! = 4! = 24 ways."
    },

    # Logical Reasoning & Data Interpretation
    {
        "id": "apt_q11",
        "category": "Logical Reasoning",
        "difficulty": "Easy",
        "question": "Which word does NOT belong with the others?",
        "options": ["Leopard", "Cheetah", "Cougar", "Elephant"],
        "correct_index": 3,
        "explanation": "Leopard, Cheetah, and Cougar belong to the feline family. Elephant does not."
    },
    {
        "id": "apt_q12",
        "category": "Logical Reasoning",
        "difficulty": "Medium",
        "question": "If CAT is coded as 3120, how is DOG coded in that same pattern?",
        "options": ["4157", "41515", "4147", "4158"],
        "correct_index": 0,
        "explanation": "C=3, A=1, T=20 -> 3120. D=4, O=15, G=7 -> 4157."
    },

    # Verbal Ability
    {
        "id": "apt_q13",
        "category": "Verbal Ability",
        "difficulty": "Easy",
        "question": "Choose the correct antonym for 'CANDID':",
        "options": ["Frank", "Outspoken", "Deceitful", "Honest"],
        "correct_index": 2,
        "explanation": "'Candid' means truthful and straightforward. 'Deceitful' is its opposite."
    },

    # Basic Algebra & Geometry
    {
        "id": "apt_q14",
        "category": "Basic Algebra",
        "difficulty": "Easy",
        "question": "Solve for x: 3x - 7 = 2x + 5.",
        "options": ["10", "12", "14", "15"],
        "correct_index": 1,
        "explanation": "3x - 2x = 5 + 7 => x = 12."
    },
    {
        "id": "apt_q15",
        "category": "Geometry",
        "difficulty": "Medium",
        "question": "What is the area of a circle with a radius of 7 cm? (Use pi = 22/7)",
        "options": ["154 cm²", "144 cm²", "176 cm²", "132 cm²"],
        "correct_index": 0,
        "explanation": "Area = pi * r^2 = (22/7) * 7 * 7 = 154 cm²."
    }
]


# ==============================================================================
# APTITUDE ENGINE CLASS & STREAKS
# ==============================================================================
class AptitudeEngine:

    @staticmethod
    def get_questions(category: str = "All Categories", difficulty: str = "Mixed", count: int = 5) -> List[Dict[str, Any]]:
        """Filter and select questions from the internal bank."""
        pool = list(APTITUDE_QUESTION_BANK)

        if category != "All Categories":
            pool = [q for q in pool if q["category"] == category]

        if difficulty != "Mixed":
            pool = [q for q in pool if q["difficulty"].lower() == difficulty.lower()]

        if not pool:
            pool = list(APTITUDE_QUESTION_BANK)

        random.shuffle(pool)
        return pool[:count]

    @staticmethod
    def calculate_rewards(difficulty: str, is_correct: bool) -> int:
        """Calculate per-question reward coins."""
        if not is_correct:
            return 0

        diff_l = difficulty.lower()
        if "hard" in diff_l:
            return 15
        elif "medium" in diff_l:
            return 10
        else:
            return 5

    @staticmethod
    def process_test_completion(attempt_id: str, score: int, total_questions: int, question_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate test performance, claim deduplicated per-question rewards and test completion bonuses.
        Also checks Aptitude Daily Streak!
        """
        pct = round((score / total_questions) * 100, 1) if total_questions > 0 else 0.0
        coins_gained = 0

        # Award per-question rewards
        for q in question_details:
            q_id = q["id"]
            diff = q["difficulty"]
            is_corr = q["is_correct"]

            if is_corr:
                rew = AptitudeEngine.calculate_rewards(diff, True)
                reward_key = f"apt_q_{attempt_id}_{q_id}_correct"
                awarded = CoinManager.claim_reward(
                    reward_id=reward_key,
                    amount=rew,
                    reason=f"Correct {diff} Aptitude question",
                    source="aptitude",
                    reference_id=q_id
                )
                if awarded:
                    coins_gained += rew

        # Award test completion bonus (+10)
        completion_key = f"apt_test_complete_{attempt_id}"
        if CoinManager.claim_reward(
            reward_id=completion_key,
            amount=10,
            reason="Completed Aptitude Test",
            source="aptitude",
            reference_id=attempt_id
        ):
            coins_gained += 10

        # Award perfect score bonus (+25)
        if pct >= 100.0:
            perfect_key = f"apt_test_perfect_{attempt_id}"
            if CoinManager.claim_reward(
                reward_id=perfect_key,
                amount=25,
                reason="Perfect Score on Aptitude Test!",
                source="aptitude",
                reference_id=attempt_id
            ):
                coins_gained += 25

        # Record study activity for general study streak
        CoinManager.record_study_activity("aptitude_tests")

        # Aptitude Daily Streak check
        today_str = str(date.today())
        apt_streak_key = f"apt_daily_streak_reward_{today_str}"
        streak_days = st.session_state.get("current_streak", 1)

        bonus_amt = 5
        if streak_days >= 30:
            bonus_amt = 100
        elif streak_days >= 7:
            bonus_amt = 25
        elif streak_days >= 3:
            bonus_amt = 10

        CoinManager.claim_reward(
            reward_id=apt_streak_key,
            amount=bonus_amt,
            reason=f"Aptitude Daily Streak ({streak_days} days)",
            source="aptitude_streak"
        )

        return {
            "score": score,
            "total": total_questions,
            "percentage": pct,
            "coins_earned": coins_gained,
            "streak_days": streak_days
        }
