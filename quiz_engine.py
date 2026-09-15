"""
EduMind AI - Gamified Quiz Engine (Strictly Grounded)
Generates, validates, evaluates, and awards coin rewards for personalized quizzes
strictly based on Subject + Uploaded PDF/PPT course materials + Student's Learned Topics.
Removes unsafe fallback generic questions.
"""

import uuid
import json
import logging
from typing import List, Dict, Any, Optional, Set

import config
import database
import document_processor
import gemini_client
from learning_tracker import TopicRecord, format_learned_topics_summary
from coin_manager import CoinManager

logger = logging.getLogger("quiz_engine")


class GroundedQuizError(Exception):
    """Raised when a grounded quiz cannot be generated due to missing course materials."""
    pass


class QuizQuestion:
    """Represents a single gamified multiple-choice question grounded in course material."""

    def __init__(
        self,
        q_id: int,
        subject: str,
        topic: str,
        subtopic: str,
        difficulty: str,
        coin_reward: int,
        question: str,
        options: List[str],
        correct_index: int,
        explanation: str,
        hint: Optional[str] = None,
        source_citation: str = ""
    ):
        self.id: int = q_id
        self.subject: str = subject
        self.topic: str = topic
        self.subtopic: str = subtopic
        self.difficulty: str = difficulty
        self.coin_reward: int = coin_reward
        self.question: str = question
        self.options: List[str] = options
        self.correct_index: int = correct_index
        self.explanation: str = explanation
        self.hint: str = hint or generate_problem_solving_hint(question, options, correct_index, topic, subtopic)
        self.source_citation: str = source_citation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "difficulty": self.difficulty,
            "coin_reward": self.coin_reward,
            "question": self.question,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
            "hint": self.hint,
            "source_citation": self.source_citation
        }


class Quiz:
    """Represents a complete personalized gamified quiz session."""

    def __init__(self, subject: str, title: str, topics_covered: List[str], questions: List[QuizQuestion]):
        self.quiz_id: str = str(uuid.uuid4())
        self.subject: str = subject
        self.title: str = title
        self.topics_covered: List[str] = topics_covered
        self.questions: List[QuizQuestion] = questions
        self.student_answers: Dict[int, int] = {}
        self.hints_used: Dict[int, bool] = {}
        self.completed: bool = False
        self.score: int = 0
        self.total_questions: int = len(questions)
        self.percentage: float = 0.0
        self.coins_earned: int = 0
        self.total_possible_coins: int = sum(q.coin_reward for q in questions)
        self.report: Optional[Dict[str, Any]] = None


def generate_problem_solving_hint(
    question_text: str,
    options: List[str],
    correct_index: int,
    topic: str,
    subtopic: str
) -> str:
    """
    Generate a non-spoiling problem-solving hint that helps the student think
    WITHOUT revealing the correct option or final answer.
    """
    q_lower = question_text.lower()
    topic_lower = topic.lower()

    if "pointer" in topic_lower or "pointer" in q_lower or "memory" in q_lower:
        return "💡 Think about the difference between the value stored inside a variable and the memory location where that variable is stored."
    if "variable" in topic_lower or "data type" in topic_lower or "declaration" in q_lower:
        return "💡 Focus on what kind of data (numbers, characters, addresses) this concept is designed to hold."
    if "output" in q_lower or "printf" in q_lower or "cout" in q_lower or "++" in q_lower:
        return "💡 Trace the variable's value from initial assignment up to the final execution statement."
    if "loop" in topic_lower or "while" in q_lower or "for" in q_lower:
        return "💡 First check the termination condition of the loop, then count how many times the loop body executes."

    return f"💡 Recall the primary purpose of {subtopic or topic} in {topic} and eliminate options dealing with unrelated concepts."


def validate_quiz_question(q_data: Dict[str, Any]) -> bool:
    """Strict validation to ensure every quiz question has 4 options and valid correct_index."""
    if not isinstance(q_data, dict):
        return False

    question_text = str(q_data.get("question", "")).strip()
    if not question_text or len(question_text) < 8:
        return False

    options = q_data.get("options")
    if not isinstance(options, list) or len(options) != 4:
        return False

    if any(not isinstance(opt, str) or not opt.strip() for opt in options):
        return False

    try:
        correct_idx = int(q_data.get("correct_index", -1))
        if correct_idx < 0 or correct_idx >= 4:
            return False
    except (ValueError, TypeError):
        return False

    return True


def assign_coin_reward(difficulty: str) -> int:
    """Assign coin rewards based on question difficulty."""
    diff_lower = str(difficulty).lower()
    if "hard" in diff_lower:
        return config.COINS_HARD
    elif "medium" in diff_lower:
        return config.COINS_MEDIUM
    else:
        return config.COINS_EASY


def calculate_quiz_size(num_learned_topics: int) -> int:
    """Determine dynamic quiz length based on learned topic count."""
    if num_learned_topics <= 2:
        return 5
    elif num_learned_topics <= 5:
        return 10
    else:
        return 12


def generate_personalized_quiz(
    registry: Dict[str, TopicRecord],
    documents: Optional[List[Dict[str, Any]]] = None,
    subject: str = config.DEFAULT_SUBJECT,
    target_topics: Optional[List[str]] = None,
    difficulty_preference: Optional[str] = None,
    num_questions_override: Optional[int] = None
) -> Quiz:
    """
    Generate a personalized quiz strictly derived from retrieved course material.
    If no relevant course material is found, raises GroundedQuizError.
    """
    if target_topics:
        norm_targets = [t.strip().title() for t in target_topics]
        eligible_topics = {t: rec for t, rec in registry.items() if t in norm_targets}
        if not eligible_topics:
            eligible_topics = registry
    else:
        eligible_topics = registry or {"General Concepts": TopicRecord("General Concepts", subject=subject)}

    num_learned = len(eligible_topics)
    num_questions = num_questions_override or calculate_quiz_size(num_learned)
    difficulty = difficulty_preference or "Mixed (Easy, Medium, Hard)"

    # Semantic RAG retrieval for topics
    context_chunks = []
    for topic_name in eligible_topics.keys():
        matches = document_processor.search_documents(
            documents=documents,
            query=f"{subject} {topic_name}",
            subject=subject,
            top_k=3
        )
        context_chunks.extend(matches)

    # STRICT GROUNDING CHECK: If no document context is found, fail gracefully!
    doc_context = document_processor.format_context_for_prompt(context_chunks)
    if not doc_context or not doc_context.strip():
        raise GroundedQuizError(
            f"Cannot generate a grounded quiz because no uploaded course material was found for subject '{subject}'. "
            "Please upload course notes (PDF/PPT) first."
        )

    learned_summary = format_learned_topics_summary(eligible_topics)

    prompt = config.QUIZ_GENERATION_PROMPT.format(
        subject=subject,
        learned_topics_summary=learned_summary,
        document_context=doc_context,
        num_questions=num_questions,
        difficulty=difficulty
    )

    questions_data = []
    try:
        parsed_data = gemini_client.generate_json_response(prompt)
        if isinstance(parsed_data, str):
            parsed_data = json.loads(parsed_data)
        if isinstance(parsed_data, list):
            for q in parsed_data:
                if validate_quiz_question(q):
                    questions_data.append(q)
        elif isinstance(parsed_data, dict) and "questions" in parsed_data:
            for q in parsed_data["questions"]:
                if validate_quiz_question(q):
                    questions_data.append(q)
    except Exception as e:
        logger.error("Error generating or parsing quiz JSON from Gemini: %s", str(e))

    if not questions_data:
        raise GroundedQuizError(
            "Could not extract valid grounded quiz questions from the retrieved course material. "
            "Please ensure the uploaded document contains sufficient explanatory text."
        )

    quiz_questions: List[QuizQuestion] = []
    for idx, q in enumerate(questions_data[:num_questions], 1):
        diff_str = q.get("difficulty", "Medium").strip().title()
        coin_rew = int(q.get("coin_reward", assign_coin_reward(diff_str)))
        q_topic = q.get("topic", "General")
        q_subtopic = q.get("subtopic", "Concept")
        q_text = q.get("question", f"Question {idx}")
        q_options = q.get("options", ["Option A", "Option B", "Option C", "Option D"])
        q_corr_idx = int(q.get("correct_index", 0))

        # Real source citation matching retrieved chunk
        source_cite = q.get("source_citation", "")
        if not source_cite or source_cite == "Study Notes":
            if context_chunks:
                first_chunk = context_chunks[0]
                source_cite = f"{first_chunk.get('filename', 'Doc')} — {first_chunk.get('unit_label', 'Page 1')}"
            else:
                source_cite = f"{subject} Notes"

        qq = QuizQuestion(
            q_id=idx,
            subject=q.get("subject", subject),
            topic=q_topic,
            subtopic=q_subtopic,
            difficulty=diff_str,
            coin_reward=coin_rew,
            question=q_text,
            options=q_options,
            correct_index=q_corr_idx,
            explanation=q.get("explanation", "No explanation provided."),
            hint=q.get("hint") or generate_problem_solving_hint(q_text, q_options, q_corr_idx, q_topic, q_subtopic),
            source_citation=source_cite
        )
        quiz_questions.append(qq)

    topics_list = list(eligible_topics.keys())
    quiz_title = f"{subject} Grounded Quiz ({', '.join(topics_list[:2])})"
    return Quiz(subject=subject, title=quiz_title, topics_covered=topics_list, questions=quiz_questions)


def evaluate_quiz(
    quiz: Quiz,
    student_answers: Dict[int, int],
    registry: Dict[str, TopicRecord],
    completed_attempt_ids: Optional[Set[str]] = None,
    hints_used: Optional[Dict[int, bool]] = None,
    user_id: str = "default_user"
) -> Dict[str, Any]:
    """Evaluate quiz submission, award coins, and save persistent result to SQLite database."""
    quiz.student_answers = student_answers
    quiz.hints_used = hints_used or {}
    quiz.completed = True

    already_awarded = False
    if completed_attempt_ids is not None:
        if quiz.quiz_id in completed_attempt_ids:
            already_awarded = True
        else:
            completed_attempt_ids.add(quiz.quiz_id)

    correct_count = 0
    coins_earned = 0
    topic_results: Dict[str, Dict[str, int]] = {}
    question_feedback = []

    for q in quiz.questions:
        topic = q.topic
        if topic not in topic_results:
            topic_results[topic] = {"correct": 0, "total": 0}

        topic_results[topic]["total"] += 1
        selected_opt = student_answers.get(q.id)
        is_correct = (selected_opt is not None and selected_opt == q.correct_index)
        used_hint = quiz.hints_used.get(q.id, False)

        q_coins = 0
        if is_correct:
            correct_count += 1
            topic_results[topic]["correct"] += 1
            q_reward_key = f"quiz_question_{quiz.quiz_id}_q{q.id}_correct"
            awarded = CoinManager.claim_reward(
                reward_id=q_reward_key,
                amount=q.coin_reward,
                reason=f"Correct {q.difficulty} quiz answer: {q.topic}",
                source="quiz",
                reference_id=f"q_{q.id}"
            )
            if awarded:
                q_coins = q.coin_reward
                coins_earned += q.coin_reward

        question_feedback.append({
            "question_id": q.id,
            "question": q.question,
            "topic": q.topic,
            "subtopic": q.subtopic,
            "difficulty": q.difficulty,
            "coin_reward": q.coin_reward,
            "is_correct": is_correct,
            "used_hint": used_hint,
            "hint_text": q.hint,
            "selected_index": selected_opt,
            "correct_index": q.correct_index,
            "selected_text": q.options[selected_opt] if selected_opt is not None else "Not answered",
            "correct_text": q.options[q.correct_index],
            "explanation": q.explanation,
            "source_citation": q.source_citation,
            "coins_earned": q_coins
        })

    # Quiz Completion Bonus (+10 coins)
    completion_key = f"quiz_completion_{quiz.quiz_id}"
    if CoinManager.claim_reward(
        reward_id=completion_key,
        amount=10,
        reason=f"Completed Quiz: {quiz.title}",
        source="quiz",
        reference_id=quiz.quiz_id
    ):
        coins_earned += 10

    # Record activity for streaks and achievements
    CoinManager.record_study_activity("quizzes")
    CoinManager.record_study_activity("correct_quiz_answers", increment=correct_count)

    quiz.score = correct_count
    quiz.percentage = round((correct_count / quiz.total_questions) * 100, 1) if quiz.total_questions > 0 else 0.0
    quiz.coins_earned = coins_earned if not already_awarded else 0

    topic_performance: Dict[str, float] = {}
    for topic, stats in topic_results.items():
        pct = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0
        topic_performance[topic] = pct
        norm_topic = topic.strip().title()
        if norm_topic in registry:
            registry[norm_topic].record_quiz_score(pct)

    strong_topics = [t for t, pct in topic_performance.items() if pct >= 80.0]
    needs_practice = [t for t, pct in topic_performance.items() if 50.0 <= pct < 80.0]
    needs_revision = [t for t, pct in topic_performance.items() if pct < 50.0]

    report = {
        "quiz_id": quiz.quiz_id,
        "subject": quiz.subject,
        "score": correct_count,
        "total_questions": quiz.total_questions,
        "percentage": quiz.percentage,
        "correct_count": correct_count,
        "wrong_count": quiz.total_questions - correct_count,
        "coins_earned": quiz.coins_earned,
        "total_possible_coins": quiz.total_possible_coins,
        "already_awarded": already_awarded,
        "hints_used_count": sum(1 for h in quiz.hints_used.values() if h),
        "topic_performance": topic_performance,
        "strong_topics": strong_topics,
        "needs_practice": needs_practice,
        "needs_revision": needs_revision,
        "question_feedback": question_feedback
    }

    quiz.report = report

    # Save to SQLite database
    database.save_quiz_result(
        attempt_id=quiz.quiz_id,
        user_id=user_id,
        subject=quiz.subject,
        title=quiz.title,
        score=correct_count,
        total=quiz.total_questions,
        pct=quiz.percentage,
        coins=quiz.coins_earned,
        report=report
    )

    # Save detailed analytics records
    import mongodb
    mongodb.save_quiz_result(
        user_id=user_id,
        attempt_id=quiz.quiz_id,
        subject=quiz.subject,
        title=quiz.title,
        score=correct_count,
        total=quiz.total_questions,
        pct=quiz.percentage,
        coins=quiz.coins_earned,
        report=report
    )

    # Save Quiz Attempt
    database.save_quiz_attempt_record(
        attempt_id=quiz.quiz_id,
        quiz_id=quiz.quiz_id,
        user_id=user_id,
        subject=quiz.subject,
        topics_json=json.dumps(quiz.topics_covered),
        score=correct_count,
        total_questions=quiz.total_questions,
        pct=quiz.percentage,
        correct=correct_count,
        wrong=quiz.total_questions - correct_count,
        difficulty="Mixed",
        time_taken_seconds=quiz.total_questions * 45
    )

    # Save Question-Level Answers
    answers_batch = []
    for fb in question_feedback:
        ans_id = f"ans_{quiz.quiz_id}_q{fb['question_id']}"
        answers_batch.append({
            "answer_id": ans_id,
            "user_id": user_id,
            "attempt_id": quiz.quiz_id,
            "quiz_id": quiz.quiz_id,
            "question_id": fb["question_id"],
            "subject": quiz.subject,
            "topic": fb["topic"],
            "subtopic": fb.get("subtopic", "General"),
            "selected_answer": fb.get("selected_index"),
            "correct_answer": fb["correct_index"],
            "is_correct": fb["is_correct"],
            "difficulty": fb.get("difficulty", "Medium"),
            "hint_used": fb.get("used_hint", False)
        })
    database.save_quiz_answers_batch(answers_batch)

    # Save / Update Topic Performance per topic
    for topic_name, stats in topic_results.items():
        t_pct = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0
        database.save_or_update_topic_performance(
            user_id=user_id,
            subject=quiz.subject,
            topic=topic_name,
            subtopic="General",
            score_pct=t_pct,
            num_correct=stats["correct"],
            num_wrong=stats["total"] - stats["correct"],
            study_time_inc=stats["total"] * 60
        )

    return report


def generate_retry_quiz(
    previous_report: Dict[str, Any],
    registry: Dict[str, TopicRecord],
    documents: Optional[List[Dict[str, Any]]] = None,
    subject: str = config.DEFAULT_SUBJECT
) -> Quiz:
    """Generate a 5-question retry quiz focusing on weak topics from previous report."""
    weak_topics = previous_report.get("needs_revision", []) + previous_report.get("needs_practice", [])
    if not weak_topics:
        weak_topics = list(registry.keys())

    return generate_personalized_quiz(
        registry=registry,
        documents=documents,
        subject=subject,
        target_topics=weak_topics,
        difficulty_preference="Focus on weak concepts & targeted practice",
        num_questions_override=5
    )
