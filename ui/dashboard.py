"""
EduMind AI - Premium SaaS EdTech Student Dashboard View
Displays authenticated student MongoDB data, welcome summary, metric cards, quick action hub,
learning progress, profile preview, recent activity timeline, wallet logs, recommendations, and real achievements.
"""

import streamlit as st
import mongodb
import database
from coin_manager import CoinManager
import learning_tracker

def render_dashboard_page():
    # Fetch Authenticated MongoDB User Details
    user_id = st.session_state.get("user_id", "user_default")
    user_doc = mongodb.find_user_by_id(user_id) or {}
    profile_doc = mongodb.get_profile(user_id) or {}

    username = user_doc.get("username") or st.session_state.get("username", "student")
    email = user_doc.get("email") or st.session_state.get("user_email", "student@edumind.app")
    display_name = profile_doc.get("display_name") or st.session_state.get("display_name") or st.session_state.get("user_name", username.title())
    avatar = profile_doc.get("avatar") or st.session_state.get("avatar", "🎓")
    bio = profile_doc.get("bio") or st.session_state.get("user_bio", "EduMind AI Scholar")

    # Real Coins and Streak from MongoDB / CoinManager
    coins = CoinManager.get_balance()
    streak = profile_doc.get("streak_days") or st.session_state.get("current_streak", 1)

    # Member Since formatting
    created_at = user_doc.get("created_at") or profile_doc.get("created_at")
    if hasattr(created_at, "strftime"):
        member_since = created_at.strftime("%B %Y")
    else:
        member_since = st.session_state.get("member_since", "September 2026")

    # Real MongoDB Analytics & Documents
    analytics = mongodb.get_user_analytics(user_id)
    user_docs = mongodb.get_user_documents(user_id)
    learned_topics = mongodb.get_user_learned_topics(user_id) or st.session_state.get("learned_topics", {})

    total_docs = analytics.get("total_documents", len(user_docs))
    total_explored = analytics.get("total_explored", len(learned_topics))
    has_quiz_data = analytics.get("has_quiz_data", False)
    avg_score = analytics.get("average_score", 0.0)
    score_display = f"{avg_score}%" if has_quiz_data else "No tests yet"

    # CSS for SaaS Dashboard
    st.markdown(
        """
        <style>
        .dash-welcome-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 50%, rgba(30, 27, 75, 0.95) 100%);
            border: 1px solid rgba(99, 102, 241, 0.35);
            border-radius: 18px;
            padding: 1.8rem 2.2rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }
        .dash-welcome-title {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #60A5FA 0%, #A855F7 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 0.4rem 0;
        }
        .dash-welcome-sub {
            color: #94A3B8;
            font-size: 1.05rem;
            margin-bottom: 1.4rem;
        }
        .dash-summary-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 1.2rem;
            align-items: center;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 12px;
            padding: 0.75rem 1.4rem;
        }
        .dash-summary-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 700;
            font-size: 1.05rem;
            color: #F8FAFC;
        }

        /* Stats Cards */
        .stat-card-gradient {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 16px;
            padding: 1.3rem 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .stat-card-gradient:hover {
            transform: translateY(-3px);
            border-color: rgba(99, 102, 241, 0.6);
        }
        .stat-icon {
            font-size: 2rem;
            margin-bottom: 0.4rem;
        }
        .stat-num {
            font-size: 2rem;
            font-weight: 800;
            color: #F8FAFC;
            line-height: 1.1;
        }
        .stat-label {
            font-size: 0.92rem;
            font-weight: 600;
            color: #94A3B8;
            margin-top: 0.2rem;
        }
        .stat-sub {
            font-size: 0.8rem;
            color: #10B981;
            margin-top: 0.3rem;
            font-weight: 600;
        }

        /* Quick Action Hub */
        .action-card {
            background: rgba(30, 41, 59, 0.65);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            padding: 1.3rem 1.2rem;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.25s ease;
        }
        .action-card:hover {
            border-color: #3B82F6;
            background: rgba(30, 41, 59, 0.9);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.25);
        }
        .action-icon {
            font-size: 2.2rem;
            margin-bottom: 0.6rem;
        }
        .action-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 0.3rem;
        }
        .action-desc {
            font-size: 0.85rem;
            color: #94A3B8;
            line-height: 1.4;
            margin-bottom: 1rem;
        }
        .action-arrow {
            font-size: 1.1rem;
            font-weight: 700;
            color: #60A5FA;
            text-align: right;
        }

        /* Content Cards */
        .dashboard-section-card {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            margin-bottom: 1.4rem;
        }

        .profile-preview-box {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 1.6rem;
            text-align: center;
        }
        .avatar-circle {
            width: 72px;
            height: 72px;
            background: rgba(99, 102, 241, 0.2);
            border: 2px solid #60A5FA;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.6rem;
            margin: 0 auto 0.8rem auto;
        }

        .rec-card {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 14px;
            padding: 1.2rem;
            margin-bottom: 0.8rem;
        }

        .achieve-card {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 12px;
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }
        .achieve-unlocked {
            border-color: rgba(16, 185, 129, 0.4);
            background: rgba(16, 185, 129, 0.1);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ==============================================================================
    # 1. HEADER & WELCOME / STUDENT SUMMARY
    # ==============================================================================
    st.markdown(
        f"""
        <div class="dash-welcome-card">
            <div class="dash-welcome-title">👋 Welcome back, {display_name}!</div>
            <div class="dash-welcome-sub">Ready to continue your AI-assisted personalized learning journey today?</div>
            <div class="dash-summary-bar">
                <div class="dash-summary-item">🪙 <span>{coins} Coins</span></div>
                <div style="color: rgba(255,255,255,0.2);">|</div>
                <div class="dash-summary-item">🔥 <span>{streak} Day Streak</span></div>
                <div style="color: rgba(255,255,255,0.2);">|</div>
                <div class="dash-summary-item">📚 <span>{total_docs} Materials</span></div>
                <div style="color: rgba(255,255,255,0.2);">|</div>
                <div class="dash-summary-item">🎯 <span>{score_display} Avg Score</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==============================================================================
    # 2. STATISTICS CARDS
    # ==============================================================================
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        st.markdown(
            f"""
            <div class="stat-card-gradient">
                <div class="stat-icon">🪙</div>
                <div class="stat-num">{coins}</div>
                <div class="stat-label">Coins Balance</div>
                <div class="stat-sub">Global Wallet</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_s2:
        st.markdown(
            f"""
            <div class="stat-card-gradient">
                <div class="stat-icon">🔥</div>
                <div class="stat-num">{streak} Days</div>
                <div class="stat-label">Learning Streak</div>
                <div class="stat-sub">Active Scholar</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_s3:
        st.markdown(
            f"""
            <div class="stat-card-gradient">
                <div class="stat-icon">📚</div>
                <div class="stat-num">{total_docs}</div>
                <div class="stat-label">Study Materials</div>
                <div class="stat-sub">Uploaded Documents</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_s4:
        st.markdown(
            f"""
            <div class="stat-card-gradient">
                <div class="stat-icon">🎯</div>
                <div class="stat-num">{score_display}</div>
                <div class="stat-label">Quiz Performance</div>
                <div class="stat-sub">{f"{analytics['total_quizzes']} Quiz Attempted" if has_quiz_data else "Take your first quiz"}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ==============================================================================
    # 3. QUICK ACTIONS HUB
    # ==============================================================================
    st.subheader("⚡ Quick Actions")
    col_q1, col_q2, col_q3, col_q4, col_q5, col_q6 = st.columns(6)

    actions = [
        ("📊", "My Analytics", "Detailed performance & charts", "📊 My Analytics", col_q1),
        ("💬", "Ask AI Tutor", "Clear your doubts instantly", "🏠 Home / Individual Learning", col_q2),
        ("📚", "Upload Notes", "Add course materials & RAG", "🏠 Home / Individual Learning", col_q3),
        ("🎯", "Aptitude", "Practice reasoning & math", "🎯 Aptitude Practice", col_q4),
        ("🎮", "Games", "Play & learn concepts", "🎮 Educational Games", col_q5),
        ("👥", "Study Groups", "Collaborate with peers", "👥 Friends Dashboard", col_q6),
    ]

    for icon, title, desc, target_page, col in actions:
        with col:
            st.markdown(
                f"""
                <div class="action-card">
                    <div>
                        <div class="action-icon">{icon}</div>
                        <div class="action-title">{title}</div>
                        <div class="action-desc">{desc}</div>
                    </div>
                    <div class="action-arrow">→</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"Go to {title}", key=f"btn_quick_{title}", use_container_width=True):
                st.session_state.current_page = target_page
                st.rerun()

    st.markdown("---")

    # ==============================================================================
    # 4. LEARNING PROGRESS + PROFILE PREVIEW (2-COLUMN GRID)
    # ==============================================================================
    col_left, col_right = st.columns([1.5, 1], gap="large")

    with col_left:
        st.subheader("📈 My Learning Progress")
        if learned_topics:
            for topic_name, record in learned_topics.items():
                if isinstance(record, dict):
                    perf = record.get("performance_level", "Not Tested")
                    score = record.get("latest_score") or 0.0
                else:
                    perf = getattr(record, 'performance_level', 'Not Tested')
                    scores = getattr(record, 'historical_scores', [])
                    score = scores[-1] if scores else 0.0

                pct_val = int(score) if score else (85 if perf == "Strong" else (60 if perf == "Needs Practice" else 40))
                
                st.markdown(f"**{topic_name}**")
                st.progress(pct_val / 100, text=f"Mastery: {pct_val}% | Status: {perf}")
        else:
            st.info("💡 **No learning data yet.** Ask your first doubt or upload study notes to track your topic mastery.")
            if st.button("🚀 Start Learning Now", type="primary", key="btn_start_learning_progress"):
                st.session_state.current_page = "🏠 Home / Individual Learning"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================================================
        # 5. CONTINUE LEARNING
        # ==========================================================================
        st.subheader("📖 Continue Learning")
        if learned_topics:
            top_items = list(learned_topics.items())[:3]
            for topic_name, record in top_items:
                subj = record.get("subject", config.DEFAULT_SUBJECT) if isinstance(record, dict) else getattr(record, "subject", config.DEFAULT_SUBJECT)
                st.markdown(
                    f"""
                    <div style="background: rgba(30,41,59,0.5); border: 1px solid rgba(99,102,241,0.2); border-radius: 12px; padding: 1rem; margin-bottom: 0.6rem; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 700; color: #F8FAFC; font-size: 1.05rem;">{topic_name}</div>
                            <div style="font-size: 0.85rem; color: #94A3B8;">Subject: {subj}</div>
                        </div>
                        <span class="topic-badge badge-learned">Continue →</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.caption("Start your first learning session to build your study history.")

    with col_right:
        st.subheader("👤 Student Profile")
        st.markdown(
            f"""
            <div class="profile-preview-box">
                <div class="avatar-circle">{avatar}</div>
                <h3 style="margin: 0; color: #F8FAFC; font-weight: 700;">{display_name}</h3>
                <div style="color: #60A5FA; font-size: 0.95rem; margin-bottom: 0.3rem;">@{username}</div>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-bottom: 0.8rem;">📧 {email}</div>
                <div style="font-size: 0.82rem; color: #CBD5E1; font-style: italic; margin-bottom: 1.2rem;">Member since {member_since}</div>
                <div style="display: flex; justify-content: space-around; background: rgba(15, 23, 42, 0.6); border-radius: 10px; padding: 0.8rem; margin-bottom: 1.2rem;">
                    <div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">Coins</div>
                        <div style="font-weight: 700; color: #FEF08A;">🪙 {coins}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">Streak</div>
                        <div style="font-weight: 700; color: #FFEDD5;">🔥 {streak} Days</div>
                    </div>
                    <div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">Score</div>
                        <div style="font-weight: 700; color: #60A5FA;">🎯 {score_display}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("View Full Profile →", use_container_width=True, key="btn_view_full_profile"):
            st.session_state.current_page = "👤 Profile & Analytics"
            st.rerun()

    st.markdown("---")

    # ==============================================================================
    # 6. RECENT ACTIVITY & WALLET LOGS
    # ==============================================================================
    col_act, col_rec = st.columns([1.3, 1], gap="large")

    with col_act:
        st.subheader("🕘 Recent Activity & Wallet Logs")
        activities = mongodb.get_user_recent_activity(user_id, limit=6)

        if activities:
            for act in activities:
                st.markdown(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 10px; padding: 0.85rem 1.1rem; margin-bottom: 0.6rem; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 0.9rem;">
                            <span style="font-size: 1.4rem;">{act['icon']}</span>
                            <div>
                                <div style="font-weight: 700; color: #F8FAFC; font-size: 0.95rem;">{act['title']}</div>
                                <div style="font-size: 0.8rem; color: #94A3B8;">{act['detail']} • {act['time_display']}</div>
                            </div>
                        </div>
                        <span class="topic-badge badge-strong" style="font-size: 0.8rem;">{act['badge']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No recent activity yet.")
            if st.button("Start Learning →", key="btn_act_start"):
                st.session_state.current_page = "🏠 Home / Individual Learning"
                st.rerun()

    with col_rec:
        st.subheader("💡 Recommended Next Steps")

        recommendations = [
            ("📚", "Upload Course Notes", "Upload PDF or PPTX notes to ask grounded questions.", "🏠 Home / Individual Learning"),
            ("🎯", "Practice Aptitude", "Test your logical reasoning and math skills.", "🎯 Aptitude Practice"),
            ("🎮", "Play & Learn", "Improve knowledge through educational games.", "🎮 Educational Games"),
            ("🔥", "Maintain Your Streak", "Study today to keep your streak alive.", "🏠 Home / Individual Learning"),
        ]

        for icon, title, desc, target in recommendations:
            st.markdown(
                f"""
                <div class="rec-card">
                    <div style="font-weight: 700; color: #F8FAFC; font-size: 1rem;">{icon} {title}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.2rem;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")

    # ==============================================================================
    # 7. ACHIEVEMENTS & BADGES
    # ==============================================================================
    st.subheader("🏆 Achievements")
    achievements = mongodb.get_user_achievements(user_id)
    ach_cols = st.columns(len(achievements))

    for idx, ach in enumerate(achievements):
        unlocked_class = "achieve-unlocked" if ach["unlocked"] else ""
        badge_status = "✅ Unlocked" if ach["unlocked"] else "🔒 Locked"
        with ach_cols[idx]:
            st.markdown(
                f"""
                <div class="achieve-card {unlocked_class}">
                    <span style="font-size: 1.8rem;">{ach['icon']}</span>
                    <div>
                        <div style="font-weight: 700; color: #F8FAFC; font-size: 0.9rem;">{ach['title']}</div>
                        <div style="font-size: 0.75rem; color: #94A3B8;">{ach['desc']}</div>
                        <div style="font-size: 0.75rem; font-weight: 700; margin-top: 0.3rem; color: {'#10B981' if ach['unlocked'] else '#94A3B8'};">{badge_status}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
