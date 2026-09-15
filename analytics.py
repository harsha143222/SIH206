"""
EduMind AI - Student & Admin Performance Analytics Service
Calculates real metrics, subject/topic performance, quiz analytics, AI doubt analytics,
study session tracking, weak/strong topic detection, AI recommendations, and admin platform stats.
Strictly isolated by user_id.
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

import database
import mongodb

logger = logging.getLogger("analytics")


def get_user_overview(user_id: str) -> Dict[str, Any]:
    """
    Calculate and return comprehensive user overview metrics from persisted data.
    Strictly isolated by user_id.
    """
    clean_uid = str(user_id).strip()
    
    # User Profile Data
    profile = mongodb.get_profile(clean_uid) or database.get_user_profile(clean_uid) or {}
    coins = profile.get("coins") or profile.get("coin_balance", 100)
    current_streak = profile.get("streak_days") or profile.get("streak", 1)
    last_active = profile.get("last_active_date") or str(date.today())

    # Quiz Attempts & Answers
    attempts = database.get_user_quiz_attempts(clean_uid)
    if not attempts:
        mongo_quizzes = mongodb.get_user_quiz_results(clean_uid)
        attempts = []
        for mq in mongo_quizzes:
            rep = mq.get("report") or {}
            attempts.append({
                "attempt_id": mq.get("attempt_id") or str(mq.get("_id")),
                "quiz_id": mq.get("attempt_id") or "q_1",
                "user_id": clean_uid,
                "subject": mq.get("subject", "General"),
                "score": mq.get("score", 0),
                "total_questions": mq.get("total_questions", 0),
                "percentage": mq.get("percentage", 0.0),
                "correct_answers": rep.get("correct_count", mq.get("score", 0)),
                "wrong_answers": rep.get("wrong_count", 0),
                "difficulty": "Medium",
                "timestamp": str(mq.get("created_at", ""))
            })

    total_quizzes = len(attempts)
    if total_quizzes > 0:
        avg_quiz_score = round(sum(a["percentage"] for a in attempts) / total_quizzes, 1)
        total_q_answered = sum(a["total_questions"] for a in attempts)
        total_correct = sum(a.get("correct_answers", a["score"]) for a in attempts)
        quiz_accuracy = round((total_correct / total_q_answered) * 100, 1) if total_q_answered > 0 else 0.0
    else:
        avg_quiz_score = 0.0
        total_q_answered = 0
        total_correct = 0
        quiz_accuracy = 0.0

    # Question Answers & Hints
    answers = database.get_user_quiz_answers(clean_uid)
    hints_used = sum(1 for ans in answers if ans.get("hint_used"))

    # Chat / AI Doubts
    chats = database.get_user_chat_interactions(clean_uid)
    questions_asked = len(chats)

    # Topic Performance
    topics = database.get_user_topic_performances(clean_uid)
    if not topics:
        mongo_topics = mongodb.get_user_learned_topics(clean_uid)
        topics = list(mongo_topics.values()) if isinstance(mongo_topics, dict) else []

    strong_count = sum(1 for t in topics if t.get("mastery_level") == "Strong" or (isinstance(t, dict) and t.get("average_score", 0) >= 80))
    total_topics = len(topics)
    overall_progress = round((strong_count / total_topics) * 100, 1) if total_topics > 0 else (avg_quiz_score if total_quizzes > 0 else 0.0)

    # Study Sessions & Study Time
    sessions = database.get_user_learning_sessions(clean_uid)
    total_sessions = len(sessions)
    total_study_seconds = sum(s.get("duration_seconds", 0) for s in sessions)
    
    # Add estimated time from quiz attempts (approx 1 min per question if not logged)
    if total_study_seconds == 0 and total_q_answered > 0:
        total_study_seconds = total_q_answered * 90  # 1.5 min per question

    total_study_hours = round(total_study_seconds / 3600.0, 1)

    # Wallet / Transactions
    txs = database.get_user_transactions(clean_uid) or mongodb.get_coin_transactions(clean_uid) or []
    coins_earned = sum(tx.get("amount", 0) for tx in txs if tx.get("amount", 0) > 0)
    coins_spent = sum(abs(tx.get("amount", 0)) for tx in txs if tx.get("amount", 0) < 0)

    # Unique Subjects
    subjects_set = set()
    for a in attempts:
        if a.get("subject"):
            subjects_set.add(a["subject"])
    for c in chats:
        if c.get("subject"):
            subjects_set.add(c["subject"])
    for t in topics:
        if isinstance(t, dict) and t.get("subject"):
            subjects_set.add(t["subject"])
    subjects_studied_count = len(subjects_set)

    has_data = (total_quizzes > 0 or questions_asked > 0 or total_topics > 0)

    return {
        "user_id": clean_uid,
        "has_data": has_data,
        "overall_progress": overall_progress,
        "average_quiz_score": avg_quiz_score,
        "quiz_accuracy": quiz_accuracy,
        "total_quizzes": total_quizzes,
        "total_questions_answered": total_q_answered,
        "questions_asked_to_ai": questions_asked,
        "study_sessions_count": total_sessions,
        "total_study_hours": total_study_hours,
        "current_streak": current_streak,
        "longest_streak": max(current_streak, profile.get("longest_streak", current_streak)),
        "coins_earned": coins_earned,
        "coins_spent": coins_spent,
        "hints_used": hints_used,
        "subjects_studied_count": subjects_studied_count,
        "coins_balance": coins
    }


def get_subject_performance(user_id: str) -> List[Dict[str, Any]]:
    """
    Calculate performance metrics per subject for a specific user.
    """
    clean_uid = str(user_id).strip()
    attempts = database.get_user_quiz_attempts(clean_uid)
    chats = database.get_user_chat_interactions(clean_uid)
    topics = database.get_user_topic_performances(clean_uid)
    sessions = database.get_user_learning_sessions(clean_uid)

    subject_data: Dict[str, Dict[str, Any]] = {}

    # Map from attempts
    for a in attempts:
        subj = a.get("subject", "General").strip().title()
        if subj not in subject_data:
            subject_data[subj] = {
                "subject": subj,
                "scores": [],
                "quizzes_count": 0,
                "questions_count": 0,
                "correct_count": 0,
                "questions_asked": 0,
                "study_time_seconds": 0,
                "last_studied": str(a.get("timestamp", ""))
            }
        s_rec = subject_data[subj]
        s_rec["scores"].append(a.get("percentage", 0.0))
        s_rec["quizzes_count"] += 1
        s_rec["questions_count"] += a.get("total_questions", 0)
        s_rec["correct_count"] += a.get("correct_answers", a.get("score", 0))
        if a.get("timestamp") and str(a["timestamp"]) > s_rec["last_studied"]:
            s_rec["last_studied"] = str(a["timestamp"])

    # Map from chats
    for c in chats:
        subj = c.get("subject", "General").strip().title()
        if subj not in subject_data:
            subject_data[subj] = {
                "subject": subj,
                "scores": [],
                "quizzes_count": 0,
                "questions_count": 0,
                "correct_count": 0,
                "questions_asked": 0,
                "study_time_seconds": 0,
                "last_studied": str(c.get("timestamp", ""))
            }
        subject_data[subj]["questions_asked"] += 1

    # Map from sessions
    for s in sessions:
        subj = s.get("subject", "General").strip().title()
        if subj in subject_data:
            subject_data[subj]["study_time_seconds"] += s.get("duration_seconds", 0)

    # Also map registered subjects if available
    db_subjects = database.get_all_subjects()
    for s in db_subjects:
        subj_title = s.strip().title()
        if subj_title not in subject_data and (attempts or chats):
            pass  # keep empty list clean

    result = []
    for subj, data in subject_data.items():
        avg_score = round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else 0.0
        quiz_acc = round((data["correct_count"] / data["questions_count"]) * 100, 1) if data["questions_count"] > 0 else 0.0
        study_mins = round(data["study_time_seconds"] / 60.0, 1)
        progress_pct = avg_score if data["scores"] else min(data["questions_asked"] * 10, 50)

        # Clean last studied date
        last_date_display = data["last_studied"].split("T")[0].split(" ")[0] if data["last_studied"] else "Recently"

        result.append({
            "subject": subj,
            "average_score": avg_score,
            "quiz_accuracy": quiz_acc,
            "number_of_quizzes": data["quizzes_count"],
            "number_of_questions": data["questions_count"],
            "questions_asked": data["questions_asked"],
            "study_time_minutes": study_mins,
            "last_studied_date": last_date_display,
            "progress_percentage": progress_pct
        })

    result.sort(key=lambda x: x["progress_percentage"], reverse=True)
    return result


def get_topic_performance(user_id: str, subject: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Track performance at topic and subtopic level.
    Mastery categories: Strong (>=80%), Needs Practice (50-79%), Needs Revision (<50%).
    """
    clean_uid = str(user_id).strip()
    records = database.get_user_topic_performances(clean_uid, subject=subject)
    
    if not records:
        # Fallback load from learned_topics table/dict
        learned = database.get_connection()
        with learned:
            cursor = learned.cursor()
            if subject:
                cursor.execute("SELECT * FROM learned_topics WHERE user_id = ? AND subject = ?", (clean_uid, subject.strip().title()))
            else:
                cursor.execute("SELECT * FROM learned_topics WHERE user_id = ?", (clean_uid,))
            rows = cursor.fetchall()
            for r in rows:
                r_dict = dict(r)
                scores = json.loads(r_dict.get("historical_scores_json") or "[]")
                avg_s = round(sum(scores) / len(scores), 1) if scores else 0.0
                records.append({
                    "performance_id": r_dict.get("topic_id"),
                    "user_id": clean_uid,
                    "subject": r_dict.get("subject"),
                    "topic": r_dict.get("topic"),
                    "subtopic": r_dict.get("subtopic") or "General",
                    "attempt_count": len(scores),
                    "correct_count": int(avg_s * len(scores) / 100) if scores else 0,
                    "wrong_count": len(scores) - (int(avg_s * len(scores) / 100) if scores else 0),
                    "average_score": avg_s,
                    "last_score": scores[-1] if scores else 0.0,
                    "study_time_seconds": 300,
                    "ai_question_count": 1,
                    "mastery_level": r_dict.get("performance_level") or ("Strong" if avg_s >= 80 else ("Needs Practice" if avg_s >= 50 else "Needs Revision")),
                    "updated_at": r_dict.get("updated_at")
                })

    result = []
    for r in records:
        avg_score = r.get("average_score", 0.0)
        attempts = r.get("attempt_count", 0)
        if avg_score >= 80.0 and attempts > 0:
            status_tag = "🟢 Strong"
            mastery = "Strong"
        elif avg_score >= 50.0 and attempts > 0:
            status_tag = "🟡 Needs Practice"
            mastery = "Needs Practice"
        elif attempts > 0:
            status_tag = "🔴 Needs Revision"
            mastery = "Needs Revision"
        else:
            status_tag = "⚪ Not Tested"
            mastery = "Not Tested"

        result.append({
            "topic": r.get("topic", "Concept"),
            "subtopic": r.get("subtopic", "General"),
            "subject": r.get("subject", "General"),
            "average_score": avg_score,
            "last_score": r.get("last_score", 0.0),
            "attempt_count": attempts,
            "correct_count": r.get("correct_count", 0),
            "wrong_count": r.get("wrong_count", 0),
            "ai_question_count": r.get("ai_question_count", 0),
            "mastery_level": mastery,
            "status_tag": status_tag
        })

    return result


def get_quiz_analytics(user_id: str) -> Dict[str, Any]:
    """
    Detailed quiz performance metrics (average, best, lowest, difficulty breakdown, subject breakdown).
    """
    clean_uid = str(user_id).strip()
    attempts = database.get_user_quiz_attempts(clean_uid)

    if not attempts:
        return {
            "has_data": False,
            "average_score": 0.0,
            "best_score": 0.0,
            "lowest_score": 0.0,
            "total_attempts": 0,
            "accuracy": 0.0,
            "by_difficulty": {},
            "by_subject": {},
            "by_topic": {},
            "recent_attempts": []
        }

    percentages = [a["percentage"] for a in attempts]
    avg_score = round(sum(percentages) / len(percentages), 1)
    best_score = round(max(percentages), 1)
    lowest_score = round(min(percentages), 1)
    total_attempts = len(attempts)

    total_q = sum(a["total_questions"] for a in attempts)
    total_c = sum(a.get("correct_answers", a["score"]) for a in attempts)
    accuracy = round((total_c / total_q) * 100, 1) if total_q > 0 else 0.0

    # Difficulty Breakdown
    by_diff: Dict[str, List[float]] = {}
    for a in attempts:
        diff = a.get("difficulty", "Medium").strip().title()
        if diff not in by_diff:
            by_diff[diff] = []
        by_diff[diff].append(a["percentage"])

    diff_stats = {}
    for diff, scores in by_diff.items():
        diff_stats[diff] = {
            "avg_score": round(sum(scores) / len(scores), 1),
            "count": len(scores)
        }

    # Subject Breakdown
    by_subj: Dict[str, List[float]] = {}
    for a in attempts:
        subj = a.get("subject", "General").strip().title()
        if subj not in by_subj:
            by_subj[subj] = []
        by_subj[subj].append(a["percentage"])

    subj_stats = {}
    for subj, scores in by_subj.items():
        subj_stats[subj] = {
            "avg_score": round(sum(scores) / len(scores), 1),
            "count": len(scores)
        }

    return {
        "has_data": True,
        "average_score": avg_score,
        "best_score": best_score,
        "lowest_score": lowest_score,
        "total_attempts": total_attempts,
        "accuracy": accuracy,
        "by_difficulty": diff_stats,
        "by_subject": subj_stats,
        "recent_attempts": attempts[:10]
    }


def get_learning_trends(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Generate daily time-series data for the past 7, 30, or 90 days.
    """
    clean_uid = str(user_id).strip()
    attempts = database.get_user_quiz_attempts(clean_uid)
    chats = database.get_user_chat_interactions(clean_uid)
    sessions = database.get_user_learning_sessions(clean_uid)

    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # Initialize dates dict
    date_map = {}
    curr = start_date
    while curr <= today:
        d_str = curr.isoformat()
        date_map[d_str] = {
            "date": d_str,
            "display_date": curr.strftime("%b %d"),
            "quiz_scores": [],
            "questions_asked": 0,
            "study_time_minutes": 0.0,
            "quiz_attempts": 0
        }
        curr += timedelta(days=1)

    has_any_data = False

    # Aggregate quiz attempts
    for a in attempts:
        ts = str(a.get("timestamp", ""))
        d_str = ts.split("T")[0].split(" ")[0]
        if d_str in date_map:
            date_map[d_str]["quiz_scores"].append(a["percentage"])
            date_map[d_str]["quiz_attempts"] += 1
            has_any_data = True

    # Aggregate chats
    for c in chats:
        ts = str(c.get("timestamp", ""))
        d_str = ts.split("T")[0].split(" ")[0]
        if d_str in date_map:
            date_map[d_str]["questions_asked"] += 1
            has_any_data = True

    # Aggregate study sessions
    for s in sessions:
        ts = str(s.get("start_time", ""))
        d_str = ts.split("T")[0].split(" ")[0]
        if d_str in date_map:
            date_map[d_str]["study_time_minutes"] += round(s.get("duration_seconds", 0) / 60.0, 1)
            has_any_data = True

    timeline = []
    for d_str, data in date_map.items():
        avg_score = round(sum(data["quiz_scores"]) / len(data["quiz_scores"]), 1) if data["quiz_scores"] else None
        timeline.append({
            "date": data["date"],
            "display_date": data["display_date"],
            "average_quiz_score": avg_score,
            "questions_asked": data["questions_asked"],
            "study_time_minutes": data["study_time_minutes"],
            "quiz_attempts": data["quiz_attempts"]
        })

    return {
        "has_data": has_any_data,
        "days": days,
        "timeline": timeline
    }


def get_weak_topics(user_id: str) -> List[Dict[str, Any]]:
    """
    Identify weak topics (<50% score, wrong answers, or high AI doubt count).
    """
    topics = get_topic_performance(user_id)
    chats = database.get_user_chat_interactions(str(user_id))

    # Count AI doubts per topic
    doubt_counts: Dict[str, int] = {}
    for c in chats:
        t = c.get("topic")
        if t:
            norm_t = t.strip().title()
            doubt_counts[norm_t] = doubt_counts.get(norm_t, 0) + 1

    weak_list = []
    for t in topics:
        topic_name = t["topic"]
        score = t["average_score"]
        attempts = t["attempt_count"]
        wrong = t["wrong_count"]
        doubts = doubt_counts.get(topic_name, t.get("ai_question_count", 0))

        if (score < 50.0 and attempts > 0) or doubts >= 3 or (attempts > 0 and wrong > attempts * 2):
            weak_list.append({
                "topic": topic_name,
                "subject": t["subject"],
                "score": score,
                "attempts": attempts,
                "wrong_answers": wrong,
                "ai_doubts": doubts,
                "status": "🔴 Needs Revision",
                "reason": f"Score is {score}% across {attempts} quiz attempt(s) with {doubts} AI doubt(s)."
            })

    weak_list.sort(key=lambda x: x["score"])
    return weak_list


def get_strong_topics(user_id: str) -> List[Dict[str, Any]]:
    """
    Identify strong topics (>=80% score).
    """
    topics = get_topic_performance(user_id)
    strong_list = []
    for t in topics:
        if t["average_score"] >= 80.0 and t["attempt_count"] > 0:
            strong_list.append({
                "topic": t["topic"],
                "subject": t["subject"],
                "score": t["average_score"],
                "attempts": t["attempt_count"],
                "status": "🟢 Strong Topic"
            })
    strong_list.sort(key=lambda x: x["score"], reverse=True)
    return strong_list


def get_ai_question_analytics(user_id: str) -> Dict[str, Any]:
    """
    AI Doubt Analytics: Most asked subjects, topics, and confusing areas.
    """
    chats = database.get_user_chat_interactions(str(user_id))
    if not chats:
        return {"has_data": False, "most_asked_subjects": [], "most_asked_topics": [], "most_confusing_topics": []}

    subject_counts: Dict[str, int] = {}
    topic_counts: Dict[str, int] = {}

    for c in chats:
        s = c.get("subject", "General").strip().title()
        subject_counts[s] = subject_counts.get(s, 0) + 1

        t = c.get("topic") or c.get("question")
        if t:
            # Extract simple topic keyword
            for word in ["pointers", "recursion", "arrays", "trees", "graphs", "loops", "functions", "sql", "inheritance", "variables"]:
                if word in str(t).lower():
                    t_name = word.title()
                    topic_counts[t_name] = topic_counts.get(t_name, 0) + 1
                    break

    most_asked_subj = sorted([{"subject": k, "count": v} for k, v in subject_counts.items()], key=lambda x: x["count"], reverse=True)
    most_asked_top = sorted([{"topic": k, "count": v} for k, v in topic_counts.items()], key=lambda x: x["count"], reverse=True)

    return {
        "has_data": True,
        "total_doubts": len(chats),
        "most_asked_subjects": most_asked_subj,
        "most_asked_topics": most_asked_top,
        "most_confusing_topics": most_asked_top[:5]
    }


def get_recommendations(user_id: str) -> List[Dict[str, Any]]:
    """
    Generate AI & Rule-based recommendations based on actual stored student performance.
    """
    clean_uid = str(user_id).strip()
    weak = get_weak_topics(clean_uid)
    strong = get_strong_topics(clean_uid)
    topic_perfs = get_topic_performance(clean_uid)
    chats = database.get_user_chat_interactions(clean_uid)

    recs = []

    # Recommendation for weak topics (<50%)
    for w in weak[:3]:
        recs.append({
            "type": "revision",
            "icon": "🔴",
            "title": f"Revise {w['topic']} ({w['subject']})",
            "message": f"Your accuracy in {w['topic']} is {w['score']}% across {w['attempts']} quiz attempt(s). Revise key concepts before trying a new quiz.",
            "recommended_action": f"Review {w['topic']} Course Notes",
            "subject": w["subject"],
            "topic": w["topic"],
            "target_page": "🏠 Home / Individual Learning"
        })

    # Recommendation for topics needing practice (50-79%)
    for t in topic_perfs:
        if 50.0 <= t["average_score"] < 80.0 and t["attempt_count"] > 0:
            recs.append({
                "type": "practice",
                "icon": "🟡",
                "title": f"Practice {t['topic']} Questions",
                "message": f"You scored {t['average_score']}% in {t['topic']}. Taking another practice quiz will help push your mastery above 80%.",
                "recommended_action": f"Take {t['topic']} Quiz",
                "subject": t["subject"],
                "topic": t["topic"],
                "target_page": "🏠 Home / Individual Learning"
            })

    # Recommendation for strong topics (>=80%) -> advance
    for s in strong[:2]:
        recs.append({
            "type": "advance",
            "icon": "🟢",
            "title": f"Mastery Achieved: {s['topic']}!",
            "message": f"Great job! You achieved {s['score']}% in {s['topic']}. Try harder questions or move to the next topic.",
            "recommended_action": "Try Harder Quiz",
            "subject": s["subject"],
            "topic": s["topic"],
            "target_page": "🏠 Home / Individual Learning"
        })

    # Fallback if brand new student
    if not recs:
        recs.append({
            "type": "starter",
            "icon": "🚀",
            "title": "Start Your Learning Journey",
            "message": "Ask your first AI doubt or take a quiz to generate personalized learning recommendations.",
            "recommended_action": "Ask AI Tutor",
            "subject": "General",
            "topic": "Getting Started",
            "target_page": "🏠 Home / Individual Learning"
        })

    return recs[:5]


def get_achievements(user_id: str) -> List[Dict[str, Any]]:
    """
    Calculate and persistently award user achievements based on real activity metrics.
    Prevent duplicate awarding.
    """
    clean_uid = str(user_id).strip()
    overview = get_user_overview(clean_uid)

    ach_definitions = [
        ("first_quiz", "🏆", "First Quiz", "Completed your first personalized quiz", overview["total_quizzes"] >= 1),
        ("streak_7", "🔥", "7 Day Streak", "Maintained a 7-day active study streak", overview["current_streak"] >= 7),
        ("studied_5_subj", "📚", "Studied 5 Subjects", "Explored learning in 5 different subjects", overview["subjects_studied_count"] >= 5),
        ("quizzes_10", "🎯", "10 Quizzes Completed", "Completed 10 quizzes successfully", overview["total_quizzes"] >= 10),
        ("score_90", "💯", "90% Quiz Score", "Scored 90% or higher on a quiz", overview["average_quiz_score"] >= 90.0 or overview["overall_progress"] >= 90.0),
        ("mastered_10", "🧠", "Mastered 10 Topics", "Achieved Strong mastery in 10 topics", len(get_strong_topics(clean_uid)) >= 10),
        ("questions_100", "⚡", "100 Questions Answered", "Answered 100 questions across all quizzes", overview["total_questions_answered"] >= 100)
    ]

    unlocked_db = database.get_unlocked_achievements(clean_uid)
    result = []

    for ach_id, icon, title, desc, condition in ach_definitions:
        is_unlocked = (ach_id in unlocked_db) or condition
        if condition and ach_id not in unlocked_db:
            database.save_achievement(clean_uid, ach_id)
            unlocked_db.add(ach_id)

        result.append({
            "id": ach_id,
            "icon": icon,
            "title": title,
            "desc": desc,
            "unlocked": is_unlocked
        })

    return result


def get_admin_analytics() -> Dict[str, Any]:
    """
    Retrieve aggregated platform analytics for Admin Dashboard.
    Ensures private individual student details are kept private.
    """
    summary = database.get_all_users_analytics_summary()
    subj_summary = database.get_all_subject_analytics_summary()

    return {
        "total_users": summary.get("total_users", 1),
        "active_users": summary.get("active_users", 1),
        "active_today": summary.get("active_today", 0),
        "total_questions_asked": summary.get("total_questions_asked", 0),
        "total_quizzes": summary.get("total_quizzes", 0),
        "average_quiz_score": summary.get("average_quiz_score", 0.0),
        "quiz_completion_rate": summary.get("quiz_completion_rate", 0.0),
        "subjects_summary": subj_summary
    }
