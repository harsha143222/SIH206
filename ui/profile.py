"""
EduMind AI - Student Profile & Learning Analytics View
Displays authenticated student profile info, member since date, coin balance history,
learned topics breakdown, and profile edit options.
"""

import streamlit as st
import mongodb
import database
from coin_manager import CoinManager
import learning_tracker

def render_profile_page():
    user_id = st.session_state.get("user_id", "user_default")
    user_doc = mongodb.find_user_by_id(user_id) or {}
    prof = mongodb.get_profile(user_id) or database.get_user_profile(user_id) or {}

    username = user_doc.get("username") or st.session_state.get("username", "student")
    email = user_doc.get("email") or st.session_state.get("user_email", "student@edumind.app")
    user_name = prof.get("display_name") or st.session_state.get("display_name") or st.session_state.get("user_name", username.title())
    avatar = prof.get("avatar") or st.session_state.get("avatar", "🎓")
    bio = prof.get("bio") or st.session_state.get("user_bio", "EduMind AI Scholar")

    created_at = user_doc.get("created_at") or prof.get("created_at")
    if hasattr(created_at, "strftime"):
        member_since = created_at.strftime("%B %Y")
    else:
        member_since = st.session_state.get("member_since", "September 2026")

    coins = CoinManager.get_balance()
    streak = prof.get("streak_days") or st.session_state.get("current_streak", 1)

    st.subheader(f"👤 {user_name}'s Profile & Analytics")

    # Profile Card Header
    st.markdown(
        f"""
        <div class="dash-welcome-card" style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;">
                <div style="font-size: 3.5rem; background: rgba(99, 102, 241, 0.2); border: 2px solid #60A5FA; width: 84px; height: 84px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    {avatar}
                </div>
                <div>
                    <h2 style="margin: 0; color: #F8FAFC; font-weight: 800; font-size: 1.8rem;">{user_name}</h2>
                    <div style="color: #60A5FA; font-size: 1rem; margin-top: 0.2rem;">@{username} • 📧 {email}</div>
                    <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 0.3rem;">📅 Member Since: <b>{member_since}</b></div>
                    <div style="margin-top: 0.5rem; font-size: 0.92rem; color: #CBD5E1; font-style: italic;">"{bio}"</div>
                    <div style="margin-top: 0.8rem; display: flex; gap: 0.6rem;">
                        <span class="badge-pill badge-coins">🪙 {coins} Coins</span>
                        <span class="badge-pill badge-streak">🔥 {streak} Day Streak</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Edit Profile Accordion
    with st.expander("✏️ Edit Profile Info", expanded=False):
        with st.form("edit_profile_form"):
            new_disp = st.text_input("Display Name", value=user_name)
            new_bio = st.text_input("Bio", value=bio)
            avatar_opts = ["🎓", "🚀", "🧠", "⭐", "💻", "🔥", "🏆", "🦁", "🦉"]
            curr_avatar_idx = avatar_opts.index(avatar) if avatar in avatar_opts else 0
            new_avatar = st.selectbox(
                "Choose Avatar",
                options=avatar_opts,
                index=curr_avatar_idx
            )
            submit_profile = st.form_submit_button("Save Profile Changes", type="primary")

        if submit_profile:
            st.session_state.user_name = new_disp.strip()
            st.session_state.display_name = new_disp.strip()
            st.session_state.avatar = new_avatar
            st.session_state.user_bio = new_bio.strip()

            mongodb.create_or_update_profile(
                user_id=user_id,
                display_name=new_disp.strip(),
                avatar=new_avatar,
                bio=new_bio.strip(),
                coins=coins,
                streak_days=streak
            )
            database.save_user_profile(user_id, new_disp.strip(), coins, streak, "")
            st.success("✅ Profile updated successfully!")
            st.rerun()

    st.markdown("---")

    # Learning Progress Analytics
    st.subheader("📊 Learning Performance Breakdown")
    analytics = mongodb.get_user_analytics(user_id)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Explored Topics", analytics["total_explored"])
    col2.metric("Uploaded Materials", analytics["total_documents"])
    col3.metric("Quizzes Completed", analytics["total_quizzes"])
    col4.metric("Average Score", f"{analytics['average_score']}%" if analytics["has_quiz_data"] else "N/A")

    learned_topics = mongodb.get_user_learned_topics(user_id) or st.session_state.get("learned_topics", {})
    if learned_topics:
        st.markdown("**Topics Mastery:**")
        for topic_name, record in learned_topics.items():
            if isinstance(record, dict):
                lvl = record.get("performance_level", "Not Tested")
            else:
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

    # Full Transaction Log
    st.subheader("📜 Complete Coin Transaction History")
    txs = mongodb.get_coin_transactions(user_id) or CoinManager.get_transactions()
    if txs:
        for tx in txs:
            amt = tx.get("amount", 0)
            reason = tx.get("reason", "Activity")
            tx_time = tx.get("timestamp", "")
            bal_after = tx.get("balance_after", coins)
            color = "#10B981" if amt > 0 else "#EF4444"
            sign = "+" if amt > 0 else ""

            st.markdown(
                f"""
                <div style="background-color: rgba(30, 41, 59, 0.5); border-bottom: 1px solid rgba(148, 163, 184, 0.15); padding: 0.75rem 0.6rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; color: #F8FAFC;">{reason}</div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">{tx_time} | Ref: {tx.get('reference_id', 'N/A')}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 700; color: {color};">🪙 {sign}{amt} Coins</div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">Balance: 🪙 {bal_after}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.caption("No transactions logged yet.")
