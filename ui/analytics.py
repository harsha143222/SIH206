"""
EduMind AI - Student Performance Analytics View (ui/analytics.py)
Renders modern, interactive user-specific student performance analytics dashboard.
Displays Overview metrics, Subject performance, Topic level mastery, Quiz Analytics,
Learning Activity trends, Weak/Strong topic detection, AI Recommendations, Achievements, and Recent Activity.
"""

import streamlit as st
import analytics
from coin_manager import CoinManager
import ui.charts as charts


def render_student_analytics_page():
    user_id = st.session_state.get("user_id", "user_default")
    user_disp_name = st.session_state.get("display_name", st.session_state.get("user_name", "Student"))
    avatar = st.session_state.get("avatar", "🎓")

    # Fetch live user-isolated analytics data
    overview = analytics.get_user_overview(user_id)
    subject_perf = analytics.get_subject_performance(user_id)
    topic_perf = analytics.get_topic_performance(user_id)
    quiz_stats = analytics.get_quiz_analytics(user_id)
    weak_topics = analytics.get_weak_topics(user_id)
    strong_topics = analytics.get_strong_topics(user_id)
    recommendations = analytics.get_recommendations(user_id)
    user_achievements = analytics.get_achievements(user_id)
    ai_doubt_stats = analytics.get_ai_question_analytics(user_id)

    # Styling
    st.markdown(
        """
        <style>
        .analytics-hero-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 50%, rgba(30, 27, 75, 0.95) 100%);
            border: 1px solid rgba(99, 102, 241, 0.35);
            border-radius: 18px;
            padding: 1.8rem 2.2rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }
        .analytics-hero-title {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #60A5FA 0%, #A855F7 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
        }
        .analytics-metric-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 16px;
            padding: 1.2rem 1.4rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .analytics-metric-card:hover {
            transform: translateY(-3px);
            border-color: rgba(99, 102, 241, 0.6);
        }
        .analytics-metric-icon { font-size: 1.8rem; margin-bottom: 0.3rem; }
        .analytics-metric-val { font-size: 1.8rem; font-weight: 800; color: #F8FAFC; line-height: 1.1; }
        .analytics-metric-lbl { font-size: 0.88rem; font-weight: 600; color: #94A3B8; margin-top: 0.2rem; }

        .analytics-box {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .weak-topic-card {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.35);
            border-radius: 12px;
            padding: 1.1rem;
            margin-bottom: 0.8rem;
        }

        .strong-topic-card {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 12px;
            padding: 1.1rem;
            margin-bottom: 0.8rem;
        }

        .rec-card-item {
            background: rgba(30, 41, 59, 0.75);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 14px;
            padding: 1.2rem;
            margin-bottom: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Header / Welcome
    st.markdown(
        f"""
        <div class="analytics-hero-card">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-size: 2.8rem; background: rgba(99, 102, 241, 0.2); width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #60A5FA;">
                    {avatar}
                </div>
                <div>
                    <div class="analytics-hero-title">Welcome back, {user_disp_name} 👋</div>
                    <div style="color: #94A3B8; font-size: 1.05rem;">Personalized Academic Analytics & Topic Mastery Dashboard</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # New Student / No Data State Notice if clean
    if not overview["has_data"]:
        st.info("💡 **Welcome to EduMind Analytics!** Complete your first quiz or ask an AI doubt to start tracking real performance, mastery, and learning trends.")

    # ==============================================================================
    # 1. OVERVIEW METRICS (6 Cards Row 1, 6 Cards Row 2)
    # ==============================================================================
    st.subheader("📊 Overview Metrics")

    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    with col_m1:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">📈</div>
                <div class="analytics-metric-val">{overview['overall_progress']}%</div>
                <div class="analytics-metric-lbl">Overall Progress</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m2:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">🎯</div>
                <div class="analytics-metric-val">{overview['average_quiz_score']}%</div>
                <div class="analytics-metric-lbl">Avg Quiz Score</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m3:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">✅</div>
                <div class="analytics-metric-val">{overview['quiz_accuracy']}%</div>
                <div class="analytics-metric-lbl">Quiz Accuracy</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m4:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">📝</div>
                <div class="analytics-metric-val">{overview['total_quizzes']}</div>
                <div class="analytics-metric-lbl">Quizzes Done</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m5:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">❓</div>
                <div class="analytics-metric-val">{overview['total_questions_answered']}</div>
                <div class="analytics-metric-lbl">Questions Answered</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m6:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">💬</div>
                <div class="analytics-metric-val">{overview['questions_asked_to_ai']}</div>
                <div class="analytics-metric-lbl">AI Doubts</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_m7, col_m8, col_m9, col_m10, col_m11, col_m12 = st.columns(6)
    with col_m7:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">⏱️</div>
                <div class="analytics-metric-val">{overview['total_study_hours']} hrs</div>
                <div class="analytics-metric-lbl">Study Time</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m8:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">🔥</div>
                <div class="analytics-metric-val">{overview['current_streak']} days</div>
                <div class="analytics-metric-lbl">Current Streak</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m9:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">🪙</div>
                <div class="analytics-metric-val">{overview['coins_balance']}</div>
                <div class="analytics-metric-lbl">Coins Balance</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m10:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">💰</div>
                <div class="analytics-metric-val">+{overview['coins_earned']}</div>
                <div class="analytics-metric-lbl">Coins Earned</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m11:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">💡</div>
                <div class="analytics-metric-val">{overview['hints_used']}</div>
                <div class="analytics-metric-lbl">Hints Used</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m12:
        st.markdown(
            f"""
            <div class="analytics-metric-card">
                <div class="analytics-metric-icon">📚</div>
                <div class="analytics-metric-val">{overview['subjects_studied_count']}</div>
                <div class="analytics-metric-lbl">Subjects Studied</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ==============================================================================
    # 2. SUBJECT PERFORMANCE & TOPIC PERFORMANCE
    # ==============================================================================
    col_subj, col_top = st.columns([1, 1], gap="large")

    with col_subj:
        st.subheader("📚 Subject Performance")
        charts.render_subject_performance_chart(subject_perf)

        if subject_perf:
            st.markdown("**Subject Breakdown Table:**")
            subj_rows = []
            for s in subject_perf:
                subj_rows.append({
                    "Subject": s["subject"],
                    "Avg Score": f"{s['average_score']}%",
                    "Accuracy": f"{s['quiz_accuracy']}%",
                    "Quizzes": s["number_of_quizzes"],
                    "Study Time": f"{s['study_time_minutes']} min",
                    "Last Studied": s["last_studied_date"]
                })
            st.dataframe(subj_rows, use_container_width=True)

    with col_top:
        st.subheader("🧠 Topic & Subtopic Performance")
        charts.render_topic_performance_chart(topic_perf)

        if topic_perf:
            st.markdown("**Topic Mastery Breakdown:**")
            top_rows = []
            for t in topic_perf:
                top_rows.append({
                    "Topic": t["topic"],
                    "Subject": t["subject"],
                    "Avg Score": f"{t['average_score']}%",
                    "Attempts": t["attempt_count"],
                    "Mastery Level": t["status_tag"]
                })
            st.dataframe(top_rows, use_container_width=True)

    st.markdown("---")

    # ==============================================================================
    # 3. LEARNING TREND (Time-Series Chart with 7, 30, 90 Day selector)
    # ==============================================================================
    st.subheader("📈 Learning Progress & Activity Trends")
    days_option = st.selectbox(
        "Select Timeframe",
        options=[7, 30, 90],
        index=1,
        format_func=lambda d: f"Past {d} Days",
        key="trend_timeframe_select"
    )

    trend_data = analytics.get_learning_trends(user_id, days=days_option)

    col_t1, col_t2 = st.columns([1, 1], gap="large")
    with col_t1:
        charts.render_quiz_score_trend_chart(trend_data)
    with col_t2:
        charts.render_study_activity_chart(trend_data)

    st.markdown("---")

    # ==============================================================================
    # 4. QUIZ ANALYTICS & DIFFICULTY BREAKDOWN
    # ==============================================================================
    st.subheader("📝 Detailed Quiz Analytics")
    col_q_chart, col_q_stats = st.columns([1.2, 1], gap="large")

    with col_q_chart:
        charts.render_difficulty_performance_chart(quiz_stats.get("by_difficulty", {}))

    with col_q_stats:
        st.markdown(
            f"""
            <div class="analytics-box">
                <h4 style="margin-top:0; color:#F8FAFC;">Quiz Summary</h4>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.8rem;">
                    <span style="color:#94A3B8;">Average Quiz Score:</span>
                    <strong style="color:#60A5FA;">{quiz_stats['average_score']}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.8rem;">
                    <span style="color:#94A3B8;">Best Quiz Score:</span>
                    <strong style="color:#10B981;">{quiz_stats['best_score']}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.8rem;">
                    <span style="color:#94A3B8;">Lowest Quiz Score:</span>
                    <strong style="color:#EF4444;">{quiz_stats['lowest_score']}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.8rem;">
                    <span style="color:#94A3B8;">Total Quiz Attempts:</span>
                    <strong style="color:#F8FAFC;">{quiz_stats['total_attempts']}</strong>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#94A3B8;">Overall Accuracy:</span>
                    <strong style="color:#FEF08A;">{quiz_stats['accuracy']}%</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ==============================================================================
    # 5. WEAK TOPICS & STRONG TOPICS (Deterministic Detection)
    # ==============================================================================
    col_w, col_s = st.columns([1, 1], gap="large")

    with col_w:
        st.subheader("🔴 Weak Topics (Needs Revision / Practice)")
        if weak_topics:
            for w in weak_topics:
                st.markdown(
                    f"""
                    <div class="weak-topic-card">
                        <div style="font-weight:700; color:#F8FAFC; font-size:1.05rem;">{w['topic']} ({w['subject']})</div>
                        <div style="font-size:0.85rem; color:#FCA5A5; margin-top:0.3rem;">
                            Score: <strong>{w['score']}%</strong> | Attempts: {w['attempts']} | Wrong Answers: {w['wrong_answers']} | AI Doubts: {w['ai_doubts']}
                        </div>
                        <div style="font-size:0.82rem; color:#CBD5E1; margin-top:0.4rem; font-style:italic;">
                            💡 {w['reason']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.success("🎉 **No weak topics flagged!** Excellent job maintaining high mastery across all concepts.")

    with col_s:
        st.subheader("🟢 Strong Topics (Mastery >= 80%)")
        if strong_topics:
            for s in strong_topics:
                st.markdown(
                    f"""
                    <div class="strong-topic-card">
                        <div style="font-weight:700; color:#F8FAFC; font-size:1.05rem;">{s['topic']} ({s['subject']})</div>
                        <div style="font-size:0.85rem; color:#6EE7B7; margin-top:0.3rem;">
                            Score: <strong>{s['score']}%</strong> | Attempts: {s['attempts']} | Status: {s['status']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Complete quizzes with scores >= 80% to highlight your strong topics here.")

    st.markdown("---")

    # ==============================================================================
    # 6. AI PERSONALIZED RECOMMENDATIONS & ACHIEVEMENTS
    # ==============================================================================
    col_rec, col_ach = st.columns([1.2, 1], gap="large")

    with col_rec:
        st.subheader("🤖 AI Personalized Recommendations")
        for r in recommendations:
            st.markdown(
                f"""
                <div class="rec-card-item">
                    <div style="font-weight:700; color:#F8FAFC; font-size:1.05rem; display:flex; align-items:center; gap:0.5rem;">
                        <span>{r['icon']}</span> {r['title']}
                    </div>
                    <div style="font-size:0.88rem; color:#94A3B8; margin-top:0.4rem; line-height:1.4;">
                        {r['message']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"Action: {r['recommended_action']}", key=f"btn_rec_{r['title']}"):
                st.session_state.current_page = r.get("target_page", "🏠 Home / Individual Learning")
                st.rerun()

    with col_ach:
        st.subheader("🏆 Badges & Achievements")
        for ach in user_achievements:
            unlocked_class = "border-color: #10B981; background: rgba(16, 185, 129, 0.1);" if ach["unlocked"] else "border-color: rgba(148,163,184,0.15); background: rgba(30,41,59,0.4);"
            badge_text = "✅ Unlocked" if ach["unlocked"] else "🔒 Locked"
            badge_color = "#10B981" if ach["unlocked"] else "#94A3B8"
            st.markdown(
                f"""
                <div style="border: 1px solid; {unlocked_class} border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.6rem; display: flex; align-items: center; gap: 0.9rem;">
                    <span style="font-size: 1.8rem;">{ach['icon']}</span>
                    <div>
                        <div style="font-weight: 700; color: #F8FAFC; font-size: 0.95rem;">{ach['title']}</div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">{ach['desc']}</div>
                        <div style="font-size: 0.75rem; font-weight: 700; color: {badge_color}; margin-top: 0.2rem;">{badge_text}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
