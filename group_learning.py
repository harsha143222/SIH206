"""
EduMind AI - Group Learning & Friends Engine
Manages Study Groups, Group Chat, Group Shared Materials, Group Quizzes (Shared Content + Individual Attempts),
Group Leaderboards, and Group Topic Tracking with strict privacy isolation from Personal Learning.
"""

import uuid
import random
import string
import datetime
import re
from typing import List, Dict, Any, Tuple, Optional
import streamlit as st
import config
from learning_tracker import TopicRecord, record_learned_topic


def generate_join_code(group_name: str = "STUDY") -> str:
    """Generate a clean, readable uppercase join code like C-WIZARDS-8K4M or C_SQUAD-9824."""
    sanitized = "".join(c if (c.isalnum() or c in ("-", "_")) else ("-" if c == " " else "") for c in group_name.upper())
    clean_prefix = re.sub(r"-+", "-", sanitized)[:12].strip("-_")
    if not clean_prefix:
        clean_prefix = "STUDY"
    rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{clean_prefix}-{rand_suffix}"


def create_sample_groups(user_name: str = "Student (You)") -> Dict[str, Dict[str, Any]]:
    """
    Create initial sample study groups so the student can immediately test
    and experience group features upon first launch.
    """
    g1_id = "grp_c_squad_101"
    g2_id = "grp_ai_hack_2026"

    # Learned topics for Group 1
    g1_topics: Dict[str, TopicRecord] = {}
    record_learned_topic(
        registry=g1_topics,
        topic_name="Pointers & Memory Addresses",
        subtopic_name="Pointer Syntax",
        subject="C Programming",
        user_question="What is a pointer in C?",
        source="C_Pointers_and_Memory_Shared.pdf",
        explanation="Pointers hold memory addresses of variables and allow direct memory manipulation in C."
    )
    record_learned_topic(
        registry=g1_topics,
        topic_name="Dynamic Memory Allocation",
        subtopic_name="malloc & free",
        subject="C Programming",
        user_question="Difference between malloc and calloc",
        source="C_Pointers_and_Memory_Shared.pdf",
        explanation="Allocating memory at runtime using malloc, calloc, realloc, and freeing it using free()."
    )

    # Group 1: C Programming Squad
    group1 = {
        "group_id": g1_id,
        "group_name": "C Programming Squad",
        "subject": "C Programming",
        "join_code": "C_SQUAD_101",
        "invite_token": "inv_c_squad_101",
        "created_by": "Rahul Sharma",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "members": {
            user_name: {"username": user_name, "points": 120, "quizzes_taken": 2, "correct_answers": 7, "coins_earned": 60},
            "Rahul Sharma": {"username": "Rahul Sharma", "points": 180, "quizzes_taken": 3, "correct_answers": 11, "coins_earned": 90},
            "Priya Patel": {"username": "Priya Patel", "points": 140, "quizzes_taken": 2, "correct_answers": 9, "coins_earned": 70},
            "Ananya Tech": {"username": "Ananya Tech", "points": 90, "quizzes_taken": 1, "correct_answers": 5, "coins_earned": 40},
        },
        "group_documents": [
            {
                "title": "C_Pointers_and_Memory_Shared.pdf",
                "file_type": "pdf",
                "text_content": "Pointers in C store memory addresses. Dereferencing a pointer using * accesses the value at that address. Arrays decay into pointers. Dynamic memory allocation is done using malloc and free.",
                "total_chars": 210,
                "uploaded_by": "Rahul Sharma"
            }
        ],
        "group_chat_messages": [
            {
                "role": "user",
                "sender": "Rahul Sharma",
                "content": "Hey everyone! Let's study C Pointers and dynamic memory allocation today."
            },
            {
                "role": "user",
                "sender": "Priya Patel",
                "content": "Sounds great! What is the difference between malloc and calloc?"
            },
            {
                "role": "assistant",
                "sender": "EduMind AI",
                "content": "📖 **EduMind AI Group Explanation**:\n- `malloc(size)` allocates uninitialized memory block.\n- `calloc(num, size)` allocates memory block and initializes all bytes to zero.\nBoth return a pointer to allocated memory."
            }
        ],
        "learned_topics": g1_topics,
        "active_group_quiz": None,         # Stores {group_quiz_id, quiz, created_at, created_by}
        "member_quiz_attempts": {}         # Stores {username: {current_index, answers, hints_used, submitted, report, coins_earned}}
    }

    # Learned topics for Group 2
    g2_topics: Dict[str, TopicRecord] = {}
    record_learned_topic(
        registry=g2_topics,
        topic_name="Python Data Structures",
        subtopic_name="Lists & Dictionaries",
        subject="Python & AI",
        user_question="How do Python dictionaries work?",
        source="Python_Data_Structures_Shared.pdf",
        explanation="Built-in data types like Lists, Tuples, Sets, and Dictionaries for data mapping."
    )

    # Group 2: AI & Python Hackers
    group2 = {
        "group_id": g2_id,
        "group_name": "AI & Python Hackers",
        "subject": "Python & AI",
        "join_code": "AI_HACK_2026",
        "invite_token": "inv_ai_hack_2026",
        "created_by": "Vikram Dev",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "members": {
            user_name: {"username": user_name, "points": 150, "quizzes_taken": 2, "correct_answers": 8, "coins_earned": 75},
            "Vikram Dev": {"username": "Vikram Dev", "points": 210, "quizzes_taken": 4, "correct_answers": 13, "coins_earned": 110},
            "Neha Singh": {"username": "Neha Singh", "points": 130, "quizzes_taken": 2, "correct_answers": 7, "coins_earned": 65},
        },
        "group_documents": [
            {
                "title": "Python_Data_Structures_Shared.pdf",
                "file_type": "pdf",
                "text_content": "Python lists are ordered, mutable sequences. Dictionaries are key-value mappings. Sets store unique elements. List comprehensions offer concise syntax.",
                "total_chars": 170,
                "uploaded_by": "Vikram Dev"
            }
        ],
        "group_chat_messages": [
            {
                "role": "user",
                "sender": "Vikram Dev",
                "content": "Welcome to Python & AI Hackers! Ask any doubt about Python or Gemini API here."
            }
        ],
        "learned_topics": g2_topics,
        "active_group_quiz": None,
        "member_quiz_attempts": {}
    }

    return {g1_id: group1, g2_id: group2}


def init_group_state():
    """Ensure group-related session state keys exist."""
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Student (You)"
    if "my_groups" not in st.session_state:
        st.session_state.my_groups = create_sample_groups(st.session_state.user_name)
    if "active_group_id" not in st.session_state:
        group_ids = list(st.session_state.my_groups.keys())
        st.session_state.active_group_id = group_ids[0] if group_ids else ""


def find_group_by_token_or_code(token_or_code: str) -> Optional[Dict[str, Any]]:
    """Search groups in session state by invite_token, group_id, or join_code."""
    init_group_state()
    if not token_or_code or not str(token_or_code).strip():
        return None

    clean_query = str(token_or_code).strip().lower()
    clean_upper = str(token_or_code).strip().upper()

    for g_id, g_data in st.session_state.my_groups.items():
        inv_token = str(g_data.get("invite_token", "")).lower()
        grp_id = str(g_data.get("group_id", "")).lower()
        j_code = str(g_data.get("join_code", "")).upper()

        if clean_query in (inv_token, grp_id) or clean_upper == j_code or g_id.lower() == clean_query:
            return g_data
    return None


def join_existing_group(group_id: str, user_name: str) -> Tuple[bool, str]:
    """Join an existing group without creating a new group."""
    init_group_state()
    group = st.session_state.my_groups.get(group_id)
    if not group:
        return False, "Group not found or has been deleted."

    if user_name not in group["members"]:
        group["members"][user_name] = {
            "username": user_name,
            "points": 0,
            "quizzes_taken": 0,
            "correct_answers": 0,
            "coins_earned": 0
        }
        group["group_chat_messages"].append({
            "role": "assistant",
            "sender": "EduMind AI",
            "content": f"👋 **{user_name}** joined the group!"
        })
    st.session_state.active_group_id = group_id
    return True, f"🎉 You joined **{group['group_name']}** successfully!"


def regenerate_invite_token(group_id: str) -> Optional[str]:
    """Generate a new secure invite token for the group owner."""
    init_group_state()
    group = st.session_state.my_groups.get(group_id)
    if not group:
        return None
    new_token = f"inv_{uuid.uuid4().hex[:8]}"
    group["invite_token"] = new_token
    return new_token


def create_new_group(group_name: str, subject: str, creator_name: str) -> str:
    """Create a new study group with unique group_id, join_code, and invite_token."""
    init_group_state()
    join_code = generate_join_code(group_name)
    group_id = f"grp_{uuid.uuid4().hex[:8]}"
    invite_token = f"inv_{uuid.uuid4().hex[:8]}"

    new_group = {
        "group_id": group_id,
        "group_name": group_name.strip(),
        "subject": subject.strip(),
        "join_code": join_code,
        "invite_token": invite_token,
        "created_by": creator_name,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "members": {
            creator_name: {"username": creator_name, "points": 0, "quizzes_taken": 0, "correct_answers": 0, "coins_earned": 0}
        },
        "group_documents": [],
        "group_chat_messages": [
            {
                "role": "assistant",
                "sender": "EduMind AI",
                "content": f"🎉 **Welcome to {group_name}!**\nSubject: **{subject}**\nJoin Code: `{join_code}`\n\nShare notes, ask group doubts, and take group quizzes together!"
            }
        ],
        "learned_topics": {},
        "active_group_quiz": None,
        "member_quiz_attempts": {}
    }

    st.session_state.my_groups[group_id] = new_group
    st.session_state.active_group_id = group_id
    return group_id


def join_group_by_code(join_code: str, user_name: str) -> Tuple[bool, str]:
    """Join an existing study group using join code or invite token."""
    init_group_state()
    code_clean = join_code.strip()

    if not code_clean:
        return False, "Please enter a valid group code or invite link."

    found_group = find_group_by_token_or_code(code_clean)
    if found_group:
        return join_existing_group(found_group["group_id"], user_name)

    # Create new joined group if custom code provided and not found
    code_upper = code_clean.upper()
    new_group_name = f"Group ({code_upper})"
    g_id = f"grp_{uuid.uuid4().hex[:8]}"
    inv_tok = f"inv_{uuid.uuid4().hex[:8]}"
    new_group = {
        "group_id": g_id,
        "group_name": new_group_name,
        "subject": "General Studies",
        "join_code": code_upper,
        "invite_token": inv_tok,
        "created_by": "Study Friend",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "members": {
            user_name: {"username": user_name, "points": 50, "quizzes_taken": 1, "correct_answers": 3, "coins_earned": 25},
            "Study Friend": {"username": "Study Friend", "points": 100, "quizzes_taken": 2, "correct_answers": 6, "coins_earned": 50}
        },
        "group_documents": [],
        "group_chat_messages": [
            {
                "role": "assistant",
                "sender": "EduMind AI",
                "content": f"🎉 Welcome **{user_name}** to {new_group_name}!"
            }
        ],
        "learned_topics": {},
        "active_group_quiz": None,
        "member_quiz_attempts": {}
    }
    st.session_state.my_groups[g_id] = new_group
    st.session_state.active_group_id = g_id
    return True, f"Joined **{new_group_name}** successfully!"


def add_group_chat_message(group_id: str, sender: str, role: str, content: str) -> None:
    """Append a chat message to group chat history."""
    init_group_state()
    if group_id in st.session_state.my_groups:
        st.session_state.my_groups[group_id]["group_chat_messages"].append({
            "role": role,
            "sender": sender,
            "content": content
        })


def add_group_document(group_id: str, doc_data: Dict[str, Any]) -> None:
    """Add shared document to group materials (isolated from private user docs)."""
    init_group_state()
    if group_id in st.session_state.my_groups:
        st.session_state.my_groups[group_id]["group_documents"].append(doc_data)


def get_sorted_group_leaderboard(group_id: str) -> List[Dict[str, Any]]:
    """Return sorted group members ranked by points and coins earned."""
    init_group_state()
    group = st.session_state.my_groups.get(group_id)
    if not group:
        return []

    members_list = list(group["members"].values())
    members_list.sort(key=lambda m: (m.get("points", 0), m.get("coins_earned", 0)), reverse=True)

    # Assign ranks
    for idx, m in enumerate(members_list, 1):
        m["rank"] = idx
    return members_list


def record_group_quiz_result(group_id: str, username: str, score: int, total_questions: int, coins_earned: int) -> None:
    """Update member's group leaderboard score and group coins."""
    init_group_state()
    group = st.session_state.my_groups.get(group_id)
    if not group:
        return

    if username not in group["members"]:
        group["members"][username] = {"username": username, "points": 0, "quizzes_taken": 0, "correct_answers": 0, "coins_earned": 0}

    member = group["members"][username]
    member["quizzes_taken"] += 1
    member["correct_answers"] += score
    points_gained = (score * 15) + coins_earned
    member["points"] += points_gained
    member["coins_earned"] += coins_earned


# ==============================================================================
# GROUP SHARED QUIZ & INDIVIDUAL MEMBER ATTEMPTS ENGINE
# ==============================================================================
def set_active_group_quiz(group_id: str, quiz_obj: Any, created_by: str) -> Dict[str, Any]:
    """
    Store ONE shared group quiz for the entire group.
    Resets member attempts so all members attempt the exact same generated quiz questions.
    """
    init_group_state()
    group = st.session_state.my_groups.get(group_id)
    if not group:
        raise KeyError(f"Group '{group_id}' not found.")

    group_quiz_id = f"group_quiz_{uuid.uuid4().hex[:8]}"
    group_quiz_data = {
        "group_quiz_id": group_quiz_id,
        "group_id": group_id,
        "subject": getattr(quiz_obj, "subject", group.get("subject")),
        "title": getattr(quiz_obj, "title", "Group Shared Quiz"),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "created_by": created_by,
        "quiz": quiz_obj
    }

    group["active_group_quiz"] = group_quiz_data
    group["member_quiz_attempts"] = {}  # Reset member attempts for the new quiz
    return group_quiz_data


def get_member_quiz_attempt(group_id: str, username: str) -> Dict[str, Any]:
    """
    Retrieve or initialize an individual member's private attempt state for the active group quiz.
    Guarantees question progress, answers, hints used, and scores are private per member.
    """
    init_group_state()
    group = st.session_state.my_groups.get(group_id)
    if not group or not group.get("active_group_quiz"):
        return {}

    g_quiz_data = group["active_group_quiz"]
    g_quiz_id = g_quiz_data["group_quiz_id"]

    if "member_quiz_attempts" not in group:
        group["member_quiz_attempts"] = {}

    attempts = group["member_quiz_attempts"]

    if username not in attempts or attempts[username].get("group_quiz_id") != g_quiz_id:
        attempts[username] = {
            "attempt_id": f"attempt_{username}_{g_quiz_id}",
            "group_quiz_id": g_quiz_id,
            "current_index": 0,
            "answers": {},          # {q_id: selected_option_index}
            "hints_used": {},       # {q_id: True/False}
            "submitted": False,
            "report": None,
            "score": 0,
            "coins_earned": 0,
            "submitted_at": None
        }

    return attempts[username]
