"""
EduMind AI - Streamlit Application
Powered by Gemini AI Model Integration (google-genai SDK)
Smart Education Assistant | Smart India Hackathon 2026 (Problem Statement ID 26207)
"""

import os
import datetime
import streamlit as st
import config
import database
import gemini_client
import document_processor
import learning_tracker
import quiz_engine
import voice_engine
import group_learning
from gemini_client import (
    GeminiClientError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)

# ==============================================================================
# 1. STREAMLIT PAGE CONFIGURATION & THEME STYLES
# ==============================================================================
st.set_page_config(
    page_title="EduMind AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme-aware CSS styling for Light Mode & Dark Mode legibility
st.markdown(
    """
    <style>
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.1rem; }
    .main-subtitle { font-size: 1.05rem; color: var(--text-color, #4B5563); font-weight: 400; }
    .badge-pill {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-left: 0.4rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .badge-coins { background-color: #FEF08A; color: #854D0E; border: 1px solid #FDE047; }
    .badge-streak { background-color: #FFEDD5; color: #C2410C; border: 1px solid #FDBA74; }
    .status-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; }
    .status-active { background-color: #DEF7EC; color: #03543F; }
    .status-missing { background-color: #FDE8E8; color: #9B1C1C; }

    /* Theme-aware topic badges */
    .topic-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.82rem; font-weight: 600; margin: 3px; }
    .badge-learned { background-color: rgba(99, 102, 241, 0.15); color: var(--text-color, #3730A3); border: 1px solid rgba(99, 102, 241, 0.3); }
    .badge-strong { background-color: rgba(16, 185, 129, 0.15); color: #047857; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-practice { background-color: rgba(245, 158, 11, 0.15); color: #B45309; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-revision { background-color: rgba(239, 68, 68, 0.15); color: #B91C1C; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-reward { background-color: rgba(234, 179, 8, 0.15); color: #A16207; border: 1px dashed #EAB308; }

    /* THEME-AWARE QUIZ & HINT CARDS */
    .quiz-card {
        background-color: var(--background-secondary-color, rgba(128, 128, 128, 0.08));
        color: var(--text-color, inherit);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .quiz-question-heading {
        color: var(--text-color, inherit) !important;
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 0.9rem;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    .hint-card {
        background-color: rgba(254, 240, 138, 0.2);
        color: var(--text-color, inherit);
        border: 1px solid rgba(234, 179, 8, 0.4);
        border-radius: 10px;
        padding: 1rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }
    .image-preview-card {
        background-color: var(--background-secondary-color, rgba(128, 128, 128, 0.08));
        border: 1px dashed rgba(59, 130, 246, 0.5);
        border-radius: 10px;
        padding: 0.8rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .leaderboard-card {
        background-color: var(--background-secondary-color, rgba(128, 128, 128, 0.08));
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================================================================
# 2. CENTRALIZED SESSION STATE INITIALIZATION & DATABASE SYNC
# ==============================================================================
def initialize_session_state():
    """
    Centralized Session State Initialization System.
    Sets defaults and synchronizes with SQLite persistent database.
    """
    default_name = "Student (You)"
    user_id = "user_default"
    user_prof = database.get_user_profile(user_id)

    coin_bal = user_prof["coin_balance"] if user_prof else 100
    streak = user_prof["streak_days"] if user_prof else 1
    last_act = user_prof["last_active_date"] if user_prof else str(datetime.date.today())

    sample_groups = group_learning.create_sample_groups(default_name)
    first_group_id = list(sample_groups.keys())[0] if sample_groups else ""

    defaults = {
        "user_id": user_id,
        "user_name": default_name,
        "coin_balance": coin_bal,
        "rewarded_questions": set(),
        "completed_quiz_ids": set(),
        "messages": [{"role": "assistant", "content": config.INITIAL_GREETING}],
        "documents": [],
        "learned_topics": {},
        "current_subject": config.DEFAULT_SUBJECT,
        "quiz_mode": False,
        "current_quiz": None,
        "quiz_answers": {},
        "quiz_hints_used": {},
        "quiz_submitted": False,
        "quiz_index": 0,
        "streak_days": streak,
        "learning_streak": streak,
        "last_active_date": last_act,
        "selected_voice_gender": "Female",
        "my_groups": sample_groups,
        "active_group_id": first_group_id,
        "attached_image": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Compatibility Aliases
    st.session_state.coins = st.session_state.coin_balance
    st.session_state.groups = st.session_state.my_groups
    st.session_state.chat_history = st.session_state.messages
    st.session_state.learning_history = st.session_state.learned_topics
    st.session_state.selected_voice = st.session_state.selected_voice_gender
    st.session_state.learning_streak = st.session_state.streak_days


initialize_session_state()

# Streak Update Check
today_str = str(datetime.date.today())
if st.session_state.last_active_date != today_str:
    yesterday_str = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_active_date == yesterday_str:
        st.session_state.streak_days += 1
    else:
        st.session_state.streak_days = 1
    st.session_state.last_active_date = today_str
    database.save_user_profile(
        st.session_state.user_id,
        st.session_state.user_name,
        st.session_state.coin_balance,
        st.session_state.streak_days,
        st.session_state.last_active_date
    )

# ==============================================================================
# 3. SIDEBAR: NAVIGATION, VOICE, SUBJECT, UPLOAD & CONTROLS
# ==============================================================================
with st.sidebar:
    st.image("https://api.iconify.design/lucide:graduation-cap.svg?color=%231E3A8A", width=44)
    st.title("EduMind AI")
    st.caption(f"Powered by Gemini ({config.GEMINI_MODEL}) | SIH 2026")
    st.markdown("---")

    # Navigation Mode Selector
    nav_mode = st.radio(
        "📌 Navigation",
        options=["🏠 Home / Individual Learning", "👥 Friends Dashboard"],
        index=0,
        key="main_nav_radio"
    )
    st.markdown("---")

    # API Connection Status (Secure Server-Side Secret / Env Var)
    if config.is_gemini_api_key_configured():
        st.markdown('<span class="status-badge status-active">● Gemini Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-missing">● Gemini API Key Missing</span>', unsafe_allow_html=True)
        st.error("⚠️ Set `GEMINI_API_KEY` in environment variables or Streamlit secrets.")

    st.markdown(f"**AI Model:** `{config.GEMINI_MODEL}`")
    st.markdown("---")

    # User Profile / Identity
    st.subheader("👤 Student Profile")
    u_name_input = st.text_input("Student Name", value=st.session_state.user_name, key="student_name_input")
    if u_name_input and u_name_input.strip() != st.session_state.user_name:
        st.session_state.user_name = u_name_input.strip()
        database.save_user_profile(
            st.session_state.user_id,
            st.session_state.user_name,
            st.session_state.coin_balance,
            st.session_state.streak_days,
            st.session_state.last_active_date
        )

    st.markdown("---")

    # AI Tutor Voice Selection & Test Button
    st.subheader("🎙️ AI Tutor Voice")
    voice_choice = st.radio(
        "Voice Selection",
        options=["👩 Female Voice", "👨 Male Voice"],
        index=0 if st.session_state.selected_voice_gender == "Female" else 1,
        key="voice_selector_radio",
        label_visibility="collapsed"
    )
    st.session_state.selected_voice_gender = "Female" if "Female" in voice_choice else "Male"

    voice_engine.render_voice_test_button(st.session_state.selected_voice_gender)
    st.markdown("---")

    if "Friends" not in nav_mode:
        # Subject Selection / Auto-Detection
        st.subheader("📚 Study Subject")
        subject_input = st.text_input(
            "Current Subject",
            value=st.session_state.current_subject,
            key="subject_text_box",
            help="Specify your academic subject (e.g. C Programming, DBMS, Physics)"
        )
        if subject_input and subject_input.strip() != st.session_state.current_subject:
            st.session_state.current_subject = subject_input.strip().title()

        st.markdown("---")

        # Private Study Material Upload (PDF / PPT / PPTX up to 100 MB)
        st.subheader("🔒 Upload Private Material")
        st.caption("Upload PDF, PPT, or PPTX notes (Max 100 MB per file)")

        uploaded_files = st.file_uploader(
            "Choose PDF, PPT or PPTX",
            type=config.SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="doc_uploader"
        )

        if uploaded_files:
            for file in uploaded_files:
                already_uploaded = any(d["filename"] == file.name for d in st.session_state.documents)
                if not already_uploaded:
                    with st.spinner(f"📖 Parsing & indexing {file.name}..."):
                        try:
                            file_bytes = file.read()
                            doc_data = document_processor.process_uploaded_file(
                                file_bytes,
                                file.name,
                                subject=st.session_state.current_subject
                            )
                            st.session_state.documents.append(doc_data)
                            st.success(f"✅ Indexed: {file.name} ({doc_data['total_units']} {doc_data['file_type']} units)")
                        except document_processor.FileSizeExceededError as e:
                            st.error(f"❌ File too large: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Failed to process {file.name}: {str(e)}")

        if st.session_state.documents:
            st.markdown("**Uploaded Materials (Private):**")
            for doc in st.session_state.documents:
                st.markdown(f"- 📄 `{doc['filename']}` ({doc['file_size_mb']} MB, {doc['total_units']} units)")

        st.markdown("---")

        # Image Question / Doubt Attachment
        st.subheader("📷 Image Question / Doubt")
        st.caption("Upload textbook question, handwritten note, code error, or math problem")

        img_file = st.file_uploader(
            "Upload Question Image",
            type=config.SUPPORTED_IMAGE_TYPES,
            key="image_doubt_uploader"
        )

        if img_file is not None:
            file_bytes = img_file.getvalue()
            mime_type = f"image/{img_file.type.split('/')[-1]}"
            st.session_state.attached_image = {
                "filename": img_file.name,
                "bytes": file_bytes,
                "mime_type": mime_type
            }
            st.success(f"📷 Attached: {img_file.name}")

        if st.session_state.attached_image:
            if st.button("❌ Remove Attached Image", use_container_width=True):
                st.session_state.attached_image = None
                st.rerun()

        st.markdown("---")

        # My Learning Progress & Streak Dashboard
        st.subheader("🎯 My Learning Progress")
        analytics = learning_tracker.get_learning_analytics(st.session_state.learned_topics)

        col1, col2 = st.columns(2)
        col1.metric("Explored", analytics["total_explored"])
        col2.metric("Tested", analytics["total_tested"])

        if analytics["total_tested"] > 0:
            st.metric("Avg Score", f"{analytics['average_score']}%")

        if st.session_state.learned_topics:
            st.markdown("**Topics Learned:**")
            for topic_name, record in st.session_state.learned_topics.items():
                lvl = getattr(record, 'performance_level', 'Not Tested')
                if lvl == "Strong":
                    badge = f'<span class="topic-badge badge-strong">🟢 {topic_name} (Strong)</span>'
                elif lvl == "Needs Practice":
                    badge = f'<span class="topic-badge badge-practice">🟡 {topic_name} (Practice)</span>'
                elif lvl == "Needs Revision":
                    badge = f'<span class="topic-badge badge-revision">🔴 {topic_name} (Revision)</span>'
                else:
                    badge = f'<span class="topic-badge badge-learned">✅ {topic_name} (Learned)</span>'
                st.markdown(badge, unsafe_allow_html=True)
        else:
            st.caption("No topics explored yet. Ask doubts in chat!")

        st.markdown("---")

        # Test My Learning Button
        if st.button("🧠 Test My Learning", use_container_width=True, type="primary"):
            with st.spinner("Generating personalized grounded quiz via Gemini..."):
                try:
                    quiz = quiz_engine.generate_personalized_quiz(
                        registry=st.session_state.learned_topics,
                        documents=st.session_state.documents,
                        subject=st.session_state.current_subject
                    )
                    st.session_state.current_quiz = quiz
                    st.session_state.quiz_mode = True
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_hints_used = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_index = 0
                    st.rerun()
                except quiz_engine.GroundedQuizError as e:
                    st.warning(f"⚠️ {str(e)}")
                except Exception as e:
                    st.error(f"Failed to generate quiz: {str(e)}")

        if st.session_state.quiz_mode:
            if st.button("💬 Return to Chat / Doubts", use_container_width=True):
                st.session_state.quiz_mode = False
                st.rerun()

        if st.button("🗑️ New Chat (Keep Balance)", use_container_width=True, type="secondary"):
            st.session_state.messages = [{"role": "assistant", "content": config.INITIAL_GREETING}]
            st.session_state.learned_topics = {}
            st.session_state.current_quiz = None
            st.session_state.quiz_mode = False
            st.session_state.quiz_answers = {}
            st.session_state.quiz_hints_used = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_index = 0
            st.session_state.attached_image = None
            st.rerun()

# ==============================================================================
# 4. MAIN INTERFACE HEADER
# ==============================================================================
col_title, col_rewards = st.columns([3, 1])

with col_title:
    st.markdown(
        f"""
        <div>
            <div class="main-title">🎓 EduMind AI</div>
            <div class="main-subtitle">Personalized Gemini AI Tutor | Subject: <b>{st.session_state.current_subject}</b> | Student: <b>{st.session_state.user_name}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_rewards:
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 0.4rem;">
            <span class="badge-pill badge-coins">🪙 {st.session_state.coin_balance} Coins</span>
            <span class="badge-pill badge-streak">🔥 {st.session_state.learning_streak} Day Streak</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ==============================================================================
# 5. FRIENDS & GROUP LEARNING DASHBOARD RENDERER
# ==============================================================================
def render_friends_dashboard():
    try:
        group_learning.init_group_state()

        st.subheader("👥 Friends & Group Learning System")
        st.caption("Learn together with friends, ask EduMind AI in group chat, share notes, take group quizzes, and compete on the group leaderboard!")

        groups_dict = st.session_state.my_groups
        group_ids = list(groups_dict.keys())

        col_sel, col_create, col_join = st.columns([2, 1, 1])

        with col_sel:
            current_g_id = st.session_state.active_group_id
            if current_g_id not in group_ids and group_ids:
                current_g_id = group_ids[0]
                st.session_state.active_group_id = current_g_id

            selected_g_id = st.selectbox(
                "Active Study Group",
                options=group_ids,
                format_func=lambda gid: f"👥 {groups_dict[gid]['group_name']} ({groups_dict[gid]['subject']})",
                index=group_ids.index(current_g_id) if current_g_id in group_ids else 0,
                key="friends_group_select_box"
            )
            if selected_g_id != st.session_state.active_group_id:
                st.session_state.active_group_id = selected_g_id
                st.rerun()

        with col_create:
            with st.popover("➕ Create Group"):
                st.markdown("### ➕ Create Study Group")
                g_name = st.text_input("Group Name", value="C++ Wizards", key="pop_g_name")
                g_subj = st.text_input("Subject", value="C++ Programming", key="pop_g_subj")
                u_handle = st.text_input("Your Handle", value=st.session_state.user_name, key="pop_u_handle")
                if st.button("Create Group Now", type="primary", key="pop_btn_create"):
                    if g_name.strip() and g_subj.strip() and u_handle.strip():
                        st.session_state.user_name = u_handle.strip()
                        new_id = group_learning.create_new_group(g_name, g_subj, st.session_state.user_name)
                        st.success(f"Study group created successfully! Code: `{new_id}`")
                        st.rerun()
                    else:
                        st.warning("Please enter Group Name, Subject, and Handle.")

        with col_join:
            with st.popover("🔗 Join Group"):
                st.markdown("### 🔗 Join Study Group")
                code_in = st.text_input("Enter Group Code", value="", key="pop_join_code")
                u_handle_join = st.text_input("Your Handle", value=st.session_state.user_name, key="pop_join_handle")
                if st.button("Join Group Now", type="primary", key="pop_btn_join"):
                    if code_in.strip() and u_handle_join.strip():
                        st.session_state.user_name = u_handle_join.strip()
                        ok, msg = group_learning.join_group_by_code(code_in, st.session_state.user_name)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter Group Code and Handle.")

        active_group = st.session_state.my_groups.get(st.session_state.active_group_id)
        if not active_group:
            st.info("No active study group. Create or join one above!")
            return

        st.markdown(
            f"""
            <div class="quiz-card" style="margin-top: 0.4rem; margin-bottom: 1rem;">
                <span class="topic-badge badge-learned">Subject: <b>{active_group['subject']}</b></span>
                <span class="topic-badge badge-strong">Join Code: <code>{active_group['join_code']}</code></span>
                <span class="topic-badge badge-practice">Members: 👥 {len(active_group['members'])}</span>
                <span class="badge-pill badge-coins">Created by: {active_group['created_by']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        tab_chat, tab_docs, tab_together, tab_gquiz, tab_lead, tab_analytics = st.tabs([
            "💬 Group Chat",
            "📚 Shared Materials",
            "🧠 Learn Together",
            "📝 Group Quiz",
            "🏆 Group Leaderboard",
            "📊 Group Progress"
        ])

        with tab_chat:
            st.markdown("### 💬 Group Chat & AI Tutor")
            st.caption("Ask questions, discuss topics with group members, or request EduMind AI's explanation.")

            chat_messages = active_group.get("group_chat_messages", [])
            for idx, msg in enumerate(chat_messages):
                sender = msg.get("sender", "Member")
                role = msg.get("role", "user")
                avatar = "🎓" if role == "assistant" else "👤"

                with st.chat_message(role, avatar=avatar):
                    st.markdown(f"**{sender}**: {msg['content']}")
                    if role == "assistant":
                        voice_engine.render_voice_button(
                            msg['content'],
                            button_id=f"g_chat_msg_{idx}",
                            voice_gender=st.session_state.selected_voice_gender
                        )

            st.markdown("---")
            g_prompt = st.text_input("Type your group message or doubt:", key=f"g_chat_input_{active_group['group_id']}")

            g_col1, g_col2 = st.columns([1, 1])
            with g_col1:
                if st.button("💬 Post Message to Group", use_container_width=True):
                    if g_prompt and g_prompt.strip():
                        group_learning.add_group_chat_message(
                            group_id=active_group["group_id"],
                            sender=st.session_state.user_name,
                            role="user",
                            content=g_prompt.strip()
                        )
                        st.rerun()

            with g_col2:
                if st.button("🤖 Ask EduMind AI in Group", use_container_width=True, type="primary"):
                    user_msg = g_prompt.strip() if g_prompt else "Explain the core concepts from our shared group notes."
                    group_learning.add_group_chat_message(
                        group_id=active_group["group_id"],
                        sender=st.session_state.user_name,
                        role="user",
                        content=user_msg
                    )
                    with st.spinner("🤖 EduMind AI is analyzing group context via Gemini..."):
                        try:
                            g_docs = active_group.get("group_documents", [])
                            g_docs_context = document_processor.format_context_for_prompt(g_docs) if g_docs else ""
                            ai_resp = gemini_client.generate_group_explanation(
                                group_name=active_group["group_name"],
                                subject=active_group["subject"],
                                chat_history_summary=user_msg,
                                user_doubt=user_msg,
                                shared_document_context=g_docs_context
                            )
                            group_learning.add_group_chat_message(
                                group_id=active_group["group_id"],
                                sender="EduMind AI",
                                role="assistant",
                                content=ai_resp
                            )

                            top_n, sub_n = learning_tracker.heuristic_topic_extractor(user_msg)
                            learning_tracker.record_learned_topic(
                                registry=active_group["learned_topics"],
                                topic_name=top_n,
                                subtopic_name=sub_n,
                                subject=active_group["subject"],
                                user_question=user_msg,
                                source="Group Shared Notes",
                                explanation=ai_resp
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error getting AI answer: {str(e)}")

        with tab_docs:
            st.markdown("### 📚 Group Shared Materials")
            st.info("🔒 **Privacy Isolated**: Materials uploaded here are shared ONLY with members of this study group.")

            group_files = st.file_uploader(
                "Upload Group PDF, PPT or PPTX (Max 100 MB)",
                type=config.SUPPORTED_FILE_TYPES,
                accept_multiple_files=True,
                key=f"group_doc_uploader_{active_group['group_id']}"
            )

            if group_files:
                for file in group_files:
                    already_in_group = any(d.get("title") == file.name for d in active_group["group_documents"])
                    if not already_in_group:
                        with st.spinner(f"📖 Uploading {file.name} to Group..."):
                            try:
                                file_bytes = file.read()
                                doc_data = document_processor.process_uploaded_file(
                                    file_bytes, file.name, subject=active_group["subject"]
                                )
                                doc_data["title"] = file.name
                                doc_data["uploaded_by"] = st.session_state.user_name
                                group_learning.add_group_document(active_group["group_id"], doc_data)
                                st.success(f"✅ Added {file.name} to group shared notes!")
                            except Exception as e:
                                st.error(f"Failed to process {file.name}: {str(e)}")

            g_docs = active_group.get("group_documents", [])
            if g_docs:
                st.markdown("**Group Shared Notes & PDFs:**")
                for doc in g_docs:
                    title = doc.get("title") or doc.get("filename", "Shared Note")
                    uploaded_by = doc.get("uploaded_by", "Group Member")
                    total_units = doc.get("total_units", 1)
                    st.markdown(f"- 📄 **`{title}`** (Uploaded by `{uploaded_by}` — {total_units} units)")
            else:
                st.caption("No shared group materials uploaded yet.")

        with tab_together:
            st.markdown("### 🧠 Learn Together — Group Topics")
            g_topics = active_group.get("learned_topics", {})
            if g_topics:
                for top_name, rec in g_topics.items():
                    st.markdown(f"#### 📖 {top_name}")
                    exp_text = getattr(rec, 'explanation', None) or f"Academic concept covering {getattr(rec, 'subtopic', 'General Concepts')}."
                    st.write(exp_text)
                    st.markdown("---")
            else:
                st.info("No group topics tracked yet. Ask doubts in Group Chat to start learning together!")

        with tab_gquiz:
            st.markdown("### 📝 Group Quiz")
            active_g_quiz_data = active_group.get("active_group_quiz")

            if not active_g_quiz_data:
                st.info("No active group quiz currently exists. Create one for your study group below!")
                with st.form(key=f"create_g_quiz_form_{active_group['group_id']}"):
                    st.markdown("#### 📝 Create Group Quiz")
                    g_subj = st.text_input("Group Subject", value=active_group["subject"])
                    g_topics_dict = active_group.get("learned_topics", {})
                    topic_options = list(g_topics_dict.keys()) if g_topics_dict else [f"{active_group['subject']} Fundamentals"]
                    g_target_topic = st.selectbox("Quiz Topic focus", options=topic_options)
                    g_num_q = st.radio("Number of Questions", options=[5, 10], index=0, horizontal=True)
                    g_diff = st.selectbox("Difficulty Level", options=["Mixed (Easy, Medium, Hard)", "Easy", "Medium", "Hard"])
                    
                    submit_create = st.form_submit_button("🚀 Generate Shared Group Quiz", type="primary")

                if submit_create:
                    if not g_topics_dict:
                        learning_tracker.record_learned_topic(
                            registry=g_topics_dict,
                            topic_name=g_target_topic,
                            subtopic_name="General Concepts",
                            subject=g_subj,
                            explanation=f"Core principles of {g_subj}"
                        )

                    with st.spinner("Generating shared group quiz via Gemini..."):
                        try:
                            g_quiz = quiz_engine.generate_personalized_quiz(
                                registry=g_topics_dict,
                                documents=active_group.get("group_documents", []),
                                subject=g_subj,
                                target_topics=[g_target_topic],
                                difficulty_preference=g_diff,
                                num_questions_override=g_num_q
                            )
                            group_learning.set_active_group_quiz(
                                group_id=active_group["group_id"],
                                quiz_obj=g_quiz,
                                created_by=st.session_state.user_name
                            )
                            st.success("🎉 Shared Group Quiz generated!")
                            st.rerun()
                        except quiz_engine.GroundedQuizError as e:
                            st.warning(f"⚠️ {str(e)}")
                        except Exception as e:
                            st.error(f"Failed to generate group quiz: {str(e)}")
            else:
                g_quiz_id = active_g_quiz_data["group_quiz_id"]
                shared_quiz: quiz_engine.Quiz = active_g_quiz_data["quiz"]
                creator = active_g_quiz_data.get("created_by", "Group Admin")

                st.markdown(f"#### 🧠 {shared_quiz.title}")
                st.caption(f"Shared Quiz ID: `{g_quiz_id}` | Created by: `{creator}` | Total Questions: {shared_quiz.total_questions}")

                member_attempt = group_learning.get_member_quiz_attempt(active_group["group_id"], st.session_state.user_name)
                is_submitted = member_attempt.get("submitted", False)

                if st.button("🔄 Create New Shared Group Quiz", key=f"btn_reset_gquiz_{g_quiz_id}"):
                    active_group["active_group_quiz"] = None
                    active_group["member_quiz_attempts"] = {}
                    st.rerun()

                st.markdown("---")

                if not is_submitted:
                    total_q = shared_quiz.total_questions
                    curr_idx = member_attempt.get("current_index", 0)
                    if curr_idx >= total_q:
                        curr_idx = total_q - 1

                    q = shared_quiz.questions[curr_idx]
                    st.progress((curr_idx + 1) / total_q, text=f"Question {curr_idx + 1} of {total_q}")

                    st.markdown(
                        f"""
                        <div class="quiz-card">
                            <span class="topic-badge badge-learned">Subject: {q.subject}</span>
                            <span class="topic-badge badge-learned">Topic: {q.topic} ({q.subtopic})</span>
                            <span class="topic-badge badge-practice">Difficulty: {q.difficulty}</span>
                            <span class="badge-pill badge-reward">Reward: 🪙 {q.coin_reward} Coins</span>
                            <div class="quiz-question-heading">{q.question}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    voice_engine.render_voice_button(
                        f"Question {curr_idx + 1}. {q.question}",
                        button_id=f"g_quiz_q_{q.id}",
                        voice_gender=st.session_state.selected_voice_gender
                    )

                    user_hints = member_attempt.get("hints_used", {})
                    has_used_hint = user_hints.get(q.id, False)

                    h_col1, h_col2 = st.columns([1, 3])
                    with h_col1:
                        if has_used_hint:
                            st.info("💡 Hint Used")
                        else:
                            if st.button(f"💡 Hint — 🪙 {config.HINT_COST}", key=f"btn_g_hint_{q.id}"):
                                if st.session_state.coin_balance < config.HINT_COST:
                                    st.warning(f"💰 Not enough coins! You need {config.HINT_COST} coins to use a hint.")
                                else:
                                    st.session_state.coin_balance -= config.HINT_COST
                                    user_hints[q.id] = True
                                    member_attempt["hints_used"] = user_hints
                                    st.rerun()

                    if has_used_hint:
                        st.markdown(
                            f"""
                            <div class="hint-card">
                                <div><b>💡 Hint:</b> {q.hint}</div>
                                <div style="font-size:0.8rem; margin-top:0.3rem; opacity:0.8;">🪙 {config.HINT_COST} coins used</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown("---")
                    user_ans_dict = member_attempt.get("answers", {})
                    existing_ans = user_ans_dict.get(q.id)

                    selected_opt = st.radio(
                        "Select your answer:",
                        options=q.options,
                        index=existing_ans if existing_ans is not None else 0,
                        key=f"g_q_radio_{q.id}_{g_quiz_id}"
                    )
                    user_ans_dict[q.id] = q.options.index(selected_opt)
                    member_attempt["answers"] = user_ans_dict

                    nav_c1, nav_c2, nav_c3 = st.columns([1, 2, 1])

                    with nav_c1:
                        if curr_idx > 0:
                            if st.button("← Previous", key="btn_g_prev"):
                                member_attempt["current_index"] = curr_idx - 1
                                st.rerun()

                    with nav_c3:
                        if curr_idx < total_q - 1:
                            if st.button("Next Question →", key="btn_g_next"):
                                member_attempt["current_index"] = curr_idx + 1
                                st.rerun()
                        else:
                            if st.button("Submit Group Quiz ✅", type="primary", key="btn_g_submit"):
                                report = quiz_engine.evaluate_quiz(
                                    quiz=shared_quiz,
                                    student_answers=member_attempt["answers"],
                                    registry=active_group.get("learned_topics", {}),
                                    hints_used=member_attempt.get("hints_used", {}),
                                    user_id=st.session_state.user_id
                                )
                                score = report.get("score", 0)
                                coins_earned = report.get("coins_earned", 0)

                                member_attempt["submitted"] = True
                                member_attempt["score"] = score
                                member_attempt["coins_earned"] = coins_earned
                                member_attempt["report"] = report
                                member_attempt["submitted_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                                st.session_state.coin_balance += coins_earned
                                group_learning.record_group_quiz_result(
                                    group_id=active_group["group_id"],
                                    username=st.session_state.user_name,
                                    score=score,
                                    total_questions=total_q,
                                    coins_earned=coins_earned
                                )
                                st.balloons()
                                st.rerun()
                else:
                    report = member_attempt.get("report", {})
                    score = member_attempt.get("score", 0)
                    total_q = shared_quiz.total_questions
                    coins_earned = member_attempt.get("coins_earned", 0)
                    pct = report.get("percentage", round((score / total_q) * 100, 1) if total_q > 0 else 0)

                    st.success("✅ Group Quiz Completed!")
                    r_c1, r_c2, r_c3, r_c4 = st.columns(4)
                    r_c1.metric("Your Score", f"{score} / {total_q}")
                    r_c2.metric("Score %", f"{pct}%")
                    r_c3.metric("Coins Earned", f"🪙 +{coins_earned}")
                    r_c4.metric("Total Balance", f"💰 {st.session_state.coin_balance}")

                    st.markdown("---")
                    st.subheader("📖 Detailed Question Review")
                    for fb in report.get("question_feedback", []):
                        status_icon = "✅" if fb["is_correct"] else "❌"
                        st.markdown(f"**Question {fb['question_id']}: {status_icon} {fb['question']}**")
                        if fb["is_correct"]:
                            st.success(f"Your Answer: **{fb['selected_text']}** (Correct!) — Earned 🪙 +{fb['coin_reward']}")
                        else:
                            st.error(f"Your Answer: **{fb['selected_text']}**\n\nCorrect Answer: **{fb['correct_text']}**")
                            st.info(f"💡 Explanation: {fb['explanation']}")
                        st.markdown("---")

        with tab_lead:
            st.markdown("### 🏆 Group Leaderboard")
            leaderboard = group_learning.get_sorted_group_leaderboard(active_group["group_id"])
            for m in leaderboard:
                rank = m.get("rank", 1)
                rank_icon = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
                username = m.get("username", "Member")
                is_you = " (You)" if username == st.session_state.user_name else ""

                st.markdown(
                    f"""
                    <div class="leaderboard-card">
                        <div>
                            <span style="font-size: 1.2rem; font-weight:700; margin-right:0.6rem;">{rank_icon}</span>
                            <b style="font-size: 1.05rem;">{username}{is_you}</b>
                        </div>
                        <div>
                            <span class="badge-pill badge-streak">⭐ {m.get('points', 0)} Points</span>
                            <span class="badge-pill badge-coins">🪙 {m.get('coins_earned', 0)} Coins</span>
                            <span class="topic-badge badge-learned">Quizzes: {m.get('quizzes_taken', 0)}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with tab_analytics:
            st.markdown("### 📊 Group Progress & Analytics")
            g_docs_cnt = len(active_group.get("group_documents", []))
            g_topics_cnt = len(active_group.get("learned_topics", {}))
            g_members_cnt = len(active_group.get("members", {}))

            c1, c2, c3 = st.columns(3)
            c1.metric("Group Members", f"👥 {g_members_cnt}")
            c2.metric("Shared Materials", f"📚 {g_docs_cnt}")
            c3.metric("Group Topics", f"🧠 {g_topics_cnt}")

    except Exception as e:
        st.error("⚠️ AI Service temporarily busy or error occurred. Please try again.")
        st.caption(f"Technical note: {str(e)}")

# ==============================================================================
# 6. DISPATCHER: RENDER HOME CHAT OR FRIENDS DASHBOARD
# ==============================================================================
if "Friends" in nav_mode:
    render_friends_dashboard()
else:
    # --------------------------------------------------------------------------
    # MODE A: INDIVIDUAL CHAT INTERFACE & GROUNDED RAG DOUBT CLEARING
    # --------------------------------------------------------------------------
    if not st.session_state.quiz_mode:
        for idx, message in enumerate(st.session_state.messages):
            role = message["role"]
            avatar = "🎓" if role == "assistant" else "👤"
            with st.chat_message(role, avatar=avatar):
                st.markdown(message["content"])

                if role == "assistant" and idx > 0:
                    voice_engine.render_voice_button(
                        message["content"],
                        button_id=f"msg_{idx}",
                        voice_gender=st.session_state.selected_voice_gender
                    )

        if st.session_state.attached_image:
            img_info = st.session_state.attached_image
            st.markdown(
                f"""
                <div class="image-preview-card">
                    <div>📷 <b>Attached Question Image:</b> <code>{img_info['filename']}</code></div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.image(img_info["bytes"], caption="Attached Question Image", width=220)

        user_prompt = st.chat_input("Ask an academic doubt, attach an image, or request a quiz...")

        if user_prompt is not None or st.session_state.attached_image is not None:
            if user_prompt is not None:
                cleaned_prompt = user_prompt.strip()
                img_payload = st.session_state.attached_image

                if cleaned_prompt or img_payload:
                    prompt_lower = cleaned_prompt.lower() if cleaned_prompt else ""

                    if cleaned_prompt:
                        detected_sub = learning_tracker.detect_subject(
                            cleaned_prompt, st.session_state.documents, st.session_state.current_subject
                        )
                        if detected_sub != st.session_state.current_subject:
                            st.session_state.current_subject = detected_sub

                    quiz_trigger_phrases = ["test my learning", "quiz me", "test me", "start quiz", "give me a quiz"]
                    if any(phrase in prompt_lower for phrase in quiz_trigger_phrases):
                        user_display = cleaned_prompt or "Start Quiz"
                        st.session_state.messages.append({"role": "user", "content": user_display})
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(user_display)

                        with st.chat_message("assistant", avatar="🎓"):
                            with st.spinner("Generating personalized grounded quiz via Gemini..."):
                                try:
                                    quiz = quiz_engine.generate_personalized_quiz(
                                        registry=st.session_state.learned_topics,
                                        documents=st.session_state.documents,
                                        subject=st.session_state.current_subject
                                    )
                                    st.session_state.current_quiz = quiz
                                    st.session_state.quiz_mode = True
                                    st.session_state.quiz_answers = {}
                                    st.session_state.quiz_hints_used = {}
                                    st.session_state.quiz_submitted = False
                                    st.session_state.quiz_index = 0
                                    st.session_state.attached_image = None
                                    st.rerun()
                                except quiz_engine.GroundedQuizError as e:
                                    msg = f"⚠️ {str(e)}"
                                    st.warning(msg)
                                    st.session_state.messages.append({"role": "assistant", "content": msg})
                                except Exception as e:
                                    st.error(f"Error launching quiz: {str(e)}")
                    else:
                        user_display = cleaned_prompt
                        if img_payload and not user_display:
                            user_display = f"📷 [Uploaded Image: {img_payload['filename']}] Analyze this question image and explain the answer."
                        elif img_payload and user_display:
                            user_display = f"📷 [Uploaded Image: {img_payload['filename']}]\n\n{cleaned_prompt}"

                        st.session_state.messages.append({"role": "user", "content": user_display})
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(user_display)
                            if img_payload:
                                st.image(img_payload["bytes"], width=200)

                        with st.chat_message("assistant", avatar="🎓"):
                            if not config.is_gemini_api_key_configured():
                                err = "⚠️ **Gemini API Key is not configured.** Please set `GEMINI_API_KEY` in environment variables or Streamlit secrets."
                                st.error(err)
                                st.session_state.messages.append({"role": "assistant", "content": err})
                            else:
                                try:
                                    img_bytes = img_payload["bytes"] if img_payload else None

                                    if img_bytes:
                                        with st.spinner("Analyzing image with Gemini Vision..."):
                                            full_response = gemini_client.analyze_image_doubt(
                                                image_bytes=img_bytes,
                                                user_question=cleaned_prompt,
                                                subject=st.session_state.current_subject
                                            )
                                            st.markdown(full_response)
                                    else:
                                        # REAL RAG SEMANTIC RETRIEVAL PIPELINE
                                        matching_chunks = document_processor.search_documents(
                                            documents=st.session_state.documents,
                                            query=cleaned_prompt,
                                            subject=st.session_state.current_subject,
                                            top_k=config.TOP_K
                                        )

                                        # Check if student is asking about uploaded materials
                                        doc_keywords = ["notes", "pdf", "ppt", "document", "uploaded", "material", "slides", "page"]
                                        is_doc_query = any(k in prompt_lower for k in doc_keywords) or bool(st.session_state.documents)

                                        if is_doc_query and not matching_chunks:
                                            # Grounded Answer Policy (Requirement 9 & Check 8)
                                            full_response = "I couldn't find this information in the uploaded course material."
                                            st.markdown(full_response)
                                        else:
                                            doc_context = document_processor.format_context_for_prompt(matching_chunks) if matching_chunks else ""
                                            stream_gen = gemini_client.generate_chat_response_stream(
                                                messages=st.session_state.messages,
                                                document_context=doc_context,
                                                subject=st.session_state.current_subject
                                            )
                                            full_response = st.write_stream(stream_gen)

                                            # Append source citations if retrieved material was used
                                            if matching_chunks and full_response and full_response != "I couldn't find this information in the uploaded course material.":
                                                sources_text = "\n\n📍 **Sources:** " + ", ".join(
                                                    f"`{c.get('filename', 'Doc')} — {c.get('unit_label', 'Page 1')}`" for c in matching_chunks
                                                )
                                                st.markdown(sources_text)
                                                full_response += sources_text

                                    if full_response:
                                        st.session_state.messages.append({"role": "assistant", "content": full_response})

                                        voice_engine.render_voice_button(
                                            full_response,
                                            button_id=f"msg_{len(st.session_state.messages)-1}",
                                            voice_gender=st.session_state.selected_voice_gender
                                        )

                                        topic_name, subtopic_name = learning_tracker.heuristic_topic_extractor(cleaned_prompt or "Image Doubt")
                                        source_citation = "Direct Doubt"

                                        if matching_chunks:
                                            first_match = matching_chunks[0]
                                            source_citation = f"{first_match.get('filename', 'Doc')} — {first_match.get('unit_label', 'Page 1')}"

                                        learning_tracker.record_learned_topic(
                                            registry=st.session_state.learned_topics,
                                            topic_name=topic_name,
                                            subtopic_name=subtopic_name,
                                            subject=st.session_state.current_subject,
                                            user_question=user_display,
                                            source=source_citation,
                                            explanation=full_response,
                                            user_id=st.session_state.user_id
                                        )

                                        st.session_state.attached_image = None

                                except Exception as e:
                                    err_text = f"❌ **Error:** {str(e)}"
                                    st.error(err_text)
                                    st.session_state.messages.append({"role": "assistant", "content": err_text})

    # --------------------------------------------------------------------------
    # MODE B: INTERACTIVE PERSONALIZED GAMIFIED QUIZ & COIN HINTS
    # --------------------------------------------------------------------------
    else:
        quiz: quiz_engine.Quiz = st.session_state.current_quiz

        if not quiz or not quiz.questions:
            st.error("No active quiz found.")
            if st.button("Return to Chat"):
                st.session_state.quiz_mode = False
                st.rerun()
        else:
            st.subheader(f"🧠 {quiz.title}")
            st.caption(f"Subject: {quiz.subject} | Topics: {', '.join(quiz.topics_covered)} | Max Possible: 🪙 {quiz.total_possible_coins} Coins")

            if not st.session_state.quiz_submitted:
                total_q = quiz.total_questions
                curr_idx = st.session_state.quiz_index
                q = quiz.questions[curr_idx]

                progress_pct = int(((curr_idx + 1) / total_q) * 100)
                st.progress(progress_pct / 100, text=f"Question {curr_idx + 1} of {total_q}")

                st.markdown(
                    f"""
                    <div class="quiz-card">
                        <span class="topic-badge badge-learned">Subject: {q.subject}</span>
                        <span class="topic-badge badge-learned">Topic: {q.topic} ({q.subtopic})</span>
                        <span class="topic-badge badge-practice">Difficulty: {q.difficulty}</span>
                        <span class="badge-pill badge-reward">Reward: 🪙 {q.coin_reward} Coins</span>
                        <div class="quiz-question-heading">{q.question}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                voice_engine.render_voice_button(
                    f"Question {curr_idx + 1}. {q.question}",
                    button_id=f"quiz_q_{q.id}",
                    voice_gender=st.session_state.selected_voice_gender
                )

                has_used_hint = st.session_state.quiz_hints_used.get(q.id, False)

                hint_col1, hint_col2 = st.columns([1, 3])
                with hint_col1:
                    if has_used_hint:
                        st.info("💡 Hint Used")
                    else:
                        if st.button(f"💡 Hint — 🪙 {config.HINT_COST}", key=f"btn_hint_{q.id}"):
                            if st.session_state.coin_balance < config.HINT_COST:
                                st.warning(f"💰 **Not enough coins!** You need {config.HINT_COST} coins to use a hint. You have {st.session_state.coin_balance} coins.")
                            else:
                                st.session_state.coin_balance -= config.HINT_COST
                                st.session_state.quiz_hints_used[q.id] = True
                                st.rerun()

                if st.session_state.quiz_hints_used.get(q.id, False):
                    st.markdown(
                        f"""
                        <div class="hint-card">
                            <div><b>💡 Hint:</b> {q.hint}</div>
                            <div style="font-size:0.8rem; margin-top:0.3rem; opacity:0.8;">🪙 {config.HINT_COST} coins used</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    voice_engine.render_voice_button(
                        f"Hint: {q.hint}",
                        button_id=f"hint_speech_{q.id}",
                        voice_gender=st.session_state.selected_voice_gender
                    )

                st.markdown("---")

                existing_ans = st.session_state.quiz_answers.get(q.id)
                selected_option = st.radio(
                    "Select your answer:",
                    options=q.options,
                    index=existing_ans if existing_ans is not None else 0,
                    key=f"q_radio_{q.id}"
                )

                st.session_state.quiz_answers[q.id] = q.options.index(selected_option)

                col_prev, col_space, col_next = st.columns([1, 2, 1])

                with col_prev:
                    if curr_idx > 0:
                        if st.button("← Previous"):
                            st.session_state.quiz_index -= 1
                            st.rerun()

                with col_next:
                    if curr_idx < total_q - 1:
                        if st.button("Next Question →"):
                            st.session_state.quiz_index += 1
                            st.rerun()
                    else:
                        if st.button("Submit Quiz & Earn Coins ✅", type="primary"):
                            report = quiz_engine.evaluate_quiz(
                                quiz=quiz,
                                student_answers=st.session_state.quiz_answers,
                                registry=st.session_state.learned_topics,
                                completed_attempt_ids=st.session_state.completed_attempt_ids,
                                hints_used=st.session_state.quiz_hints_used,
                                user_id=st.session_state.user_id
                            )
                            if not report.get("already_awarded"):
                                st.session_state.coin_balance += report.get("coins_earned", 0)

                            database.save_user_profile(
                                st.session_state.user_id,
                                st.session_state.user_name,
                                st.session_state.coin_balance,
                                st.session_state.streak_days,
                                st.session_state.last_active_date
                            )

                            st.session_state.quiz_submitted = True
                            st.rerun()

            else:
                report = quiz.report or {}
                score = report.get("score", 0)
                total = report.get("total_questions", 0)
                pct = report.get("percentage", 0.0)
                coins_earned = report.get("coins_earned", 0)
                hints_used_cnt = report.get("hints_used_count", 0)

                st.balloons()
                st.markdown("## 🎉 Quiz Complete!")

                score_col1, score_col2, score_col3, score_col4, score_col5 = st.columns(5)
                score_col1.metric("Total Score", f"{score} / {total}")
                score_col2.metric("Percentage", f"{pct}%")
                score_col3.metric("Coins Earned", f"🪙 +{coins_earned}")
                score_col4.metric("Total Balance", f"💰 {st.session_state.coin_balance}")
                score_col5.metric("Hints Used", f"💡 {hints_used_cnt} / {total}")

                st.markdown("---")

                st.subheader("📊 Topic Performance Breakdown")
                topic_perf = report.get("topic_performance", {})
                for top_name, top_pct in topic_perf.items():
                    st.write(f"**{top_name}**: {top_pct}%")
                    st.progress(top_pct / 100)

                st.markdown("---")

                st.subheader("🧠 EduMind Learning Analysis")
                col_s, col_p, col_r = st.columns(3)

                with col_s:
                    st.markdown("#### 🟢 Strong Topics")
                    strong = report.get("strong_topics", [])
                    if strong:
                        for s in strong:
                            st.markdown(f"- ✅ **{s}**")
                    else:
                        st.caption("None yet.")

                with col_p:
                    st.markdown("#### 🟡 Needs Practice")
                    practice = report.get("needs_practice", [])
                    if practice:
                        for p in practice:
                            st.markdown(f"- 🟡 **{p}**")
                    else:
                        st.caption("None.")

                with col_r:
                    st.markdown("#### 🔴 Needs Revision")
                    revision = report.get("needs_revision", [])
                    if revision:
                        for r in revision:
                            st.markdown(f"- ❌ **{r}**")
                    else:
                        st.caption("None.")

                st.markdown("---")

                st.subheader("📖 Detailed Question Review")

                for fb in report.get("question_feedback", []):
                    is_correct = fb["is_correct"]
                    used_h = fb["used_hint"]
                    status_icon = "✅" if is_correct else "❌"
                    hint_tag = " (💡 Hint Used)" if used_h else ""

                    st.markdown(f"**Question {fb['question_id']}: {status_icon} {fb['question']}**{hint_tag}")
                    st.caption(f"Topic: {fb['topic']} ({fb['subtopic']}) | Difficulty: {fb['difficulty']} | Reward: 🪙 {fb['coin_reward']}")

                    if is_correct:
                        st.success(f"Your answer: **{fb['selected_text']}** (Correct!) — Earned: **🪙 +{fb['coin_reward']} Coins**")
                    else:
                        st.error(f"Your answer: **{fb['selected_text']}**\n\nCorrect answer: **{fb['correct_text']}** — Earned: **🪙 0 Coins**")
                        st.info(f"💡 **Explanation:** {fb['explanation']}\n\n📍 **Source:** {fb['source_citation']}")

                        voice_engine.render_voice_button(
                            f"Question: {fb['question']}. Correct answer: {fb['correct_text']}. Explanation: {fb['explanation']}",
                            button_id=f"quiz_explain_{fb['question_id']}",
                            voice_gender=st.session_state.selected_voice_gender
                        )

                    st.markdown("---")

                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    if st.button("🔄 Retry Weak Topics", use_container_width=True, type="primary"):
                        with st.spinner("Generating targeted retry quiz..."):
                            try:
                                retry_quiz = quiz_engine.generate_retry_quiz(
                                    previous_report=report,
                                    registry=st.session_state.learned_topics,
                                    documents=st.session_state.documents,
                                    subject=st.session_state.current_subject
                                )
                                st.session_state.current_quiz = retry_quiz
                                st.session_state.quiz_answers = {}
                                st.session_state.quiz_hints_used = {}
                                st.session_state.quiz_submitted = False
                                st.session_state.quiz_index = 0
                                st.rerun()
                            except quiz_engine.GroundedQuizError as e:
                                st.warning(f"⚠️ {str(e)}")
                            except Exception as e:
                                st.error(f"Failed to generate retry quiz: {str(e)}")

                with btn_col2:
                    if st.button("💬 Return to Doubts & Chat", use_container_width=True):
                        st.session_state.quiz_mode = False
                        st.rerun()
