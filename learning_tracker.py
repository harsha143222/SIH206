"""
EduMind AI - Learning Tracker Module
Tracks student doubts, normalizes academic topics/subtopics, detects subjects,
manages student progress analytics, learning streaks, and persists data to SQLite.
"""

import re
import json
import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Set, Tuple

import config
import database

logger = logging.getLogger("learning_tracker")


class TopicRecord:
    """Represents an academic topic learned by the student."""

    def __init__(
        self,
        topic: str,
        subtopic: Optional[str] = None,
        subject: str = config.DEFAULT_SUBJECT,
        explanation: Optional[str] = None
    ):
        self.topic: str = topic.strip().title()
        self.subtopic: str = subtopic.strip().title() if subtopic else "General Concepts"
        self.subject: str = subject.strip().title()
        self.explanation: str = explanation.strip() if explanation else f"Academic concept covering {self.subtopic} in {self.subject}."
        self.subtopics: Set[str] = {self.subtopic}
        self.status: str = "Explained"  # "Explained" or "Tested"
        self.user_questions: List[str] = []
        self.source_citations: Set[str] = set()
        self.historical_scores: List[float] = []
        self.performance_level: str = "Not Tested"  # "Strong", "Needs Practice", "Needs Revision", "Not Tested"

    def add_interaction(
        self,
        question: str,
        subtopic: Optional[str] = None,
        source: Optional[str] = None,
        explanation: Optional[str] = None
    ):
        if question and question not in self.user_questions:
            self.user_questions.append(question)
        if subtopic:
            self.subtopics.add(subtopic.strip().title())
        if source:
            self.source_citations.add(source)
        if explanation and (not self.explanation or "Academic concept covering" in self.explanation):
            self.explanation = explanation.strip()

    def record_quiz_score(self, score_pct: float):
        self.historical_scores.append(score_pct)
        self.status = "Tested"

        avg = sum(self.historical_scores[-3:]) / len(self.historical_scores[-3:])
        if avg >= 80.0:
            self.performance_level = "Strong"
        elif avg >= 50.0:
            self.performance_level = "Needs Practice"
        else:
            self.performance_level = "Needs Revision"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "subject": self.subject,
            "subtopic": self.subtopic,
            "explanation": self.explanation,
            "subtopics": list(self.subtopics),
            "status": self.status,
            "user_questions_count": len(self.user_questions),
            "source_citations": list(self.source_citations),
            "performance_level": self.performance_level,
            "latest_score": self.historical_scores[-1] if self.historical_scores else None
        }


def detect_subject(
    user_message: str,
    documents: Optional[List[Dict[str, Any]]] = None,
    current_subject: str = config.DEFAULT_SUBJECT
) -> str:
    """Detect or refine the active study subject from user input or uploaded file names."""
    text_lower = user_message.lower()

    match = re.search(r"(?:i am learning|subject:|studying|learning|course in)\s+([a-zA-Z0-9\s\+#]+)", text_lower)
    if match:
        raw_subj = match.group(1).strip()
        clean_subj = re.split(r"[\.,;\!\?]", raw_subj)[0].strip()
        if 2 <= len(clean_subj) <= 40:
            return clean_subj.title()

    common_subjects = {
        "c programming": "C Programming",
        "c++": "C++ Programming",
        "java": "Java Programming",
        "python": "Python Programming",
        "data structures": "Data Structures & Algorithms",
        "dbms": "Database Management Systems",
        "database": "Database Management Systems",
        "sql": "Database Management Systems",
        "operating systems": "Operating Systems",
        "computer networks": "Computer Networks",
        "artificial intelligence": "Artificial Intelligence",
        "machine learning": "Machine Learning",
        "digital electronics": "Digital Electronics",
        "web development": "Web Development",
        "physics": "Physics",
        "chemistry": "Chemistry",
        "mathematics": "Mathematics"
    }

    for kw, subj_name in common_subjects.items():
        if kw in text_lower:
            return subj_name

    if current_subject == config.DEFAULT_SUBJECT and documents:
        for doc in documents:
            fname = doc.get("filename", "").lower()
            for kw, subj_name in common_subjects.items():
                if kw in fname:
                    return subj_name

    return current_subject


def heuristic_topic_extractor(user_message: str) -> Tuple[str, str]:
    """Identify topic and subtopic keywords from student doubt."""
    text = user_message.strip()
    text_lower = text.lower()

    keywords_map = {
        "pointer": ("Pointers", "Pointer concepts"),
        "variable": ("Variables", "Variable declaration"),
        "data type": ("Data Types", "Primitive data types"),
        "loop": ("Loops", "Control structures"),
        "while": ("Loops", "While loops"),
        "for loop": ("Loops", "For loops"),
        "array": ("Arrays", "Data structures"),
        "dbms": ("Database Systems", "DBMS fundamentals"),
        "database": ("Database Systems", "Databases"),
        "sql": ("Database Systems", "SQL Queries"),
        "machine learning": ("Artificial Intelligence", "Machine Learning"),
        "ai": ("Artificial Intelligence", "AI Principles"),
        "function": ("Functions", "Modular programming"),
        "recursion": ("Functions", "Recursion"),
        "structure": ("Structures", "Composite data types"),
        "class": ("Object-Oriented Programming", "Classes & Objects"),
        "object": ("Object-Oriented Programming", "Classes & Objects"),
        "inheritance": ("Object-Oriented Programming", "Inheritance"),
    }

    for kw, (t, st) in keywords_map.items():
        if kw in text_lower:
            return t, st

    clean_words = [w.title() for w in text.split() if len(w) > 3 and w.lower() not in [
        "what", "how", "why", "where", "can", "explain", "does", "meaning", "about", "with", "example", "please", "learning", "subject"
    ]]

    if clean_words:
        topic_name = clean_words[0]
        subtopic_name = " ".join(clean_words[:2])
        return topic_name, subtopic_name

    return "General Concepts", "Academic Doubts"


def record_learned_topic(
    registry: Dict[str, TopicRecord],
    topic_name: str,
    subtopic_name: Optional[str] = None,
    subject: str = config.DEFAULT_SUBJECT,
    user_question: str = "",
    source: Optional[str] = None,
    explanation: Optional[str] = None,
    user_id: str = "default_user"
) -> TopicRecord:
    """Record or update a learned topic in the student's registry."""
    norm_topic = topic_name.strip().title()

    if norm_topic not in registry:
        registry[norm_topic] = TopicRecord(norm_topic, subtopic_name, subject=subject, explanation=explanation)

    rec = registry[norm_topic]
    rec.add_interaction(question=user_question, subtopic=subtopic_name, source=source, explanation=explanation)

    database.save_subject(subject)

    # Save to Chat Interactions and Topic Performance tables
    if user_question:
        import uuid
        int_id = f"chat_{uuid.uuid4().hex[:10]}"
        database.save_chat_interaction(
            interaction_id=int_id,
            user_id=user_id,
            subject=subject,
            question=user_question,
            topic=norm_topic,
            subtopic=subtopic_name or "General",
            source_doc=source or "",
            status="success"
        )
        database.save_or_update_topic_performance(
            user_id=user_id,
            subject=subject,
            topic=norm_topic,
            subtopic=subtopic_name or "General",
            ai_question_inc=1,
            study_time_inc=120
        )

    return rec


def update_learning_streak(last_active_str: str, current_streak: int) -> Tuple[int, str]:
    """Update student learning streak based on current date."""
    today_str = date.today().isoformat()
    if not last_active_str:
        return 1, today_str

    if last_active_str == today_str:
        return current_streak, today_str

    try:
        last_date = date.fromisoformat(last_active_str)
        delta = (date.today() - last_date).days
        if delta == 1:
            return current_streak + 1, today_str
        elif delta > 1:
            return 1, today_str
    except Exception:
        pass

    return max(current_streak, 1), today_str


def get_learning_analytics(registry: Dict[str, TopicRecord]) -> Dict[str, Any]:
    """Calculate learning analytics metrics across registered topics."""
    total_explored = len(registry)
    tested_topics = [t for t in registry.values() if t.status == "Tested"]
    total_tested = len(tested_topics)

    scores = [t.historical_scores[-1] for t in tested_topics if t.historical_scores]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    strong = [t.topic for t in registry.values() if t.performance_level == "Strong"]
    needs_practice = [t.topic for t in registry.values() if t.performance_level == "Needs Practice"]
    needs_revision = [t.topic for t in registry.values() if t.performance_level == "Needs Revision"]
    untested = [t.topic for t in registry.values() if t.performance_level == "Not Tested"]

    return {
        "total_explored": total_explored,
        "total_tested": total_tested,
        "average_score": avg_score,
        "strong_topics": strong,
        "needs_practice": needs_practice,
        "needs_revision": needs_revision,
        "untested_topics": untested,
    }


def format_learned_topics_summary(registry: Dict[str, TopicRecord]) -> str:
    """Format learned topics into text summary for LLM prompt context."""
    if not registry:
        return "No topics learned yet."

    lines = []
    for topic_name, record in registry.items():
        sub_str = ", ".join(record.subtopics) if record.subtopics else "General"
        sources_str = ", ".join(record.source_citations) if record.source_citations else "Direct Doubt"
        lines.append(
            f"- Subject: {record.subject} | Topic: {topic_name} (Subtopics: {sub_str} | Status: {record.status} | Sources: {sources_str})"
        )

    return "\n".join(lines)
