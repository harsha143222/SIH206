"""
EduMind AI - Analytics & Privacy Isolation Validation Test Suite
Tests all 10 key requirements:
1. User A data isolation from User B
2. Quiz attempt updates analytics
3. Wrong answers update topic performance
4. AI question increments doubt analytics
5. Study session updates study time
6. Achievement awarded only once
7. Recommendations reflect real student performance
8. New users get clean empty-state analytics
9. Admin sees aggregated analytics only
10. Existing core database features continue to work
"""

import sys
import unittest
import database
import analytics
import quiz_engine
from learning_tracker import TopicRecord


class TestEduMindAnalytics(unittest.TestCase):

    def setUp(self):
        # Initialize test database tables
        database.init_db()

    def test_01_user_data_isolation(self):
        """Test 1: User A analytics are strictly isolated from User B."""
        user_a = "test_student_a_101"
        user_b = "test_student_b_202"

        # Record quiz attempt for User A
        database.save_quiz_attempt_record(
            attempt_id="att_a_1",
            quiz_id="quiz_a_1",
            user_id=user_a,
            subject="Java",
            topics_json='["Inheritance"]',
            score=5,
            total_questions=5,
            pct=100.0,
            correct=5,
            wrong=0
        )

        overview_a = analytics.get_user_overview(user_a)
        overview_b = analytics.get_user_overview(user_b)

        self.assertEqual(overview_a["total_quizzes"], 1)
        self.assertEqual(overview_a["overall_progress"], 100.0)

        # User B must have ZERO quizzes and ZERO progress from User A
        self.assertEqual(overview_b["total_quizzes"], 0)
        self.assertEqual(overview_b["average_quiz_score"], 0.0)

    def test_02_quiz_attempt_updates_analytics(self):
        """Test 2: Quiz attempt correctly updates analytics."""
        user_id = "test_student_quiz_303"

        database.save_quiz_attempt_record(
            attempt_id="att_q_303",
            quiz_id="quiz_303",
            user_id=user_id,
            subject="Python",
            topics_json='["Loops"]',
            score=4,
            total_questions=5,
            pct=80.0,
            correct=4,
            wrong=1
        )

        overview = analytics.get_user_overview(user_id)
        self.assertEqual(overview["total_quizzes"], 1)
        self.assertEqual(overview["average_quiz_score"], 80.0)
        self.assertEqual(overview["total_questions_answered"], 5)

    def test_03_wrong_answers_update_topic_performance(self):
        """Test 3: Wrong answers update topic performance and mastery level."""
        user_id = "test_student_weak_404"

        database.save_or_update_topic_performance(
            user_id=user_id,
            subject="DSA",
            topic="Trees",
            subtopic="Binary Trees",
            score_pct=42.0,
            num_correct=4,
            num_wrong=6
        )

        perfs = analytics.get_topic_performance(user_id, subject="DSA")
        self.assertTrue(len(perfs) > 0)
        trees_perf = perfs[0]
        self.assertEqual(trees_perf["topic"], "Trees")
        self.assertEqual(trees_perf["mastery_level"], "Needs Revision")

    def test_04_ai_question_increments_doubt_analytics(self):
        """Test 4: AI question increments doubt analytics."""
        user_id = "test_student_doubt_505"

        database.save_chat_interaction(
            interaction_id="chat_505_1",
            user_id=user_id,
            subject="C Programming",
            question="What is a pointer in C?",
            topic="Pointers"
        )

        doubt_stats = analytics.get_ai_question_analytics(user_id)
        self.assertTrue(doubt_stats["has_data"])
        self.assertEqual(doubt_stats["total_doubts"], 1)

    def test_05_study_session_updates_study_time(self):
        """Test 5: Study session updates study time."""
        user_id = "test_student_time_606"

        database.save_learning_session(
            session_id="sess_606_1",
            user_id=user_id,
            subject="Java",
            topics_studied_json='["Classes"]',
            start_time="2026-09-15 10:00:00",
            end_time="2026-09-15 11:00:00",
            duration_seconds=3600
        )

        overview = analytics.get_user_overview(user_id)
        self.assertEqual(overview["total_study_hours"], 1.0)
        self.assertEqual(overview["study_sessions_count"], 1)

    def test_06_achievement_awarded_once(self):
        """Test 6: Achievement is awarded only once without duplicate entry."""
        user_id = "test_student_achieve_707"

        database.save_achievement(user_id, "first_quiz")
        database.save_achievement(user_id, "first_quiz")

        unlocked = database.get_unlocked_achievements(user_id)
        self.assertIn("first_quiz", unlocked)
        self.assertEqual(len([a for a in unlocked if a == "first_quiz"]), 1)

    def test_07_recommendations_reflect_performance(self):
        """Test 7: Recommendations reflect actual performance."""
        user_id = "test_student_rec_808"

        database.save_or_update_topic_performance(
            user_id=user_id,
            subject="Java",
            topic="Threads",
            score_pct=40.0,
            num_correct=2,
            num_wrong=3
        )

        recs = analytics.get_recommendations(user_id)
        self.assertTrue(len(recs) > 0)
        rev_rec = [r for r in recs if r["topic"] == "Threads"]
        self.assertTrue(len(rev_rec) > 0)
        self.assertIn("Revise Threads", rev_rec[0]["title"])

    def test_08_new_user_empty_state(self):
        """Test 8: New users get an empty-state dashboard without errors."""
        user_id = "brand_new_student_909"

        overview = analytics.get_user_overview(user_id)
        self.assertFalse(overview["has_data"])
        self.assertEqual(overview["total_quizzes"], 0)
        self.assertEqual(overview["average_quiz_score"], 0.0)

    def test_09_admin_aggregated_analytics(self):
        """Test 9: Admin sees aggregated analytics only."""
        admin_stats = analytics.get_admin_analytics()
        self.assertIn("total_users", admin_stats)
        self.assertIn("total_quizzes", admin_stats)
        self.assertIn("average_quiz_score", admin_stats)
        self.assertNotIn("password_hash", admin_stats)

    def test_10_existing_functionality_preserved(self):
        """Test 10: Existing database functions remain fully operational."""
        database.save_subject("Artificial Intelligence")
        subjects = database.get_all_subjects()
        self.assertIn("Artificial Intelligence", subjects)


if __name__ == "__main__":
    unittest.main()
