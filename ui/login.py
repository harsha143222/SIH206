"""
EduMind AI - Futuristic Login Page View
Renders modern glassmorphism AI EdTech login screen.
"""

import streamlit as st
import auth

def render_login_page():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0A0F1D 0%, #0F172A 50%, #1E1B4B 100%) !important;
            color: #F8FAFC !important;
        }

        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 20px;
            padding: 2.2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            margin-bottom: 1.5rem;
        }

        .gradient-title {
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(90deg, #60A5FA 0%, #A855F7 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }

        .feature-item {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.8rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .feature-icon {
            font-size: 1.5rem;
            background: rgba(99, 102, 241, 0.2);
            padding: 0.5rem;
            border-radius: 10px;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.65rem 1.5rem !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        st.markdown(
            """<div style="padding-top: 1rem;">
<div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">
<span style="font-size: 2.6rem;">🎓</span>
<span class="gradient-title">EduMind AI</span>
</div>
<h2 style="font-size: 1.6rem; color: #E2E8F0; font-weight: 600; margin-bottom: 1.2rem;">
Learn Smarter. Learn Your Way.
</h2>
<p style="color: #94A3B8; font-size: 1.05rem; line-height: 1.6; margin-bottom: 1.8rem;">
Your personalized Gemini AI-powered tutor for Smart India Hackathon 2026. Instant grounded doubt resolution, grounded quizzes, interactive aptitude, educational games, and collaborative study groups.
</p>
<div class="feature-item">
<span class="feature-icon">🧠</span>
<div>
<div style="font-weight: 700; color: #F1F5F9;">AI Personal Tutor</div>
<div style="font-size: 0.88rem; color: #94A3B8;">Instant grounded doubt clearing powered by Gemini.</div>
</div>
</div>
<div class="feature-item">
<span class="feature-icon">📚</span>
<div>
<div style="font-weight: 700; color: #F1F5F9;">Learn From Your Notes</div>
<div style="font-size: 0.88rem; color: #94A3B8;">Upload PDF, PPT, and PPTX notes with private RAG retrieval.</div>
</div>
</div>
<div class="feature-item">
<span class="feature-icon">🎯</span>
<div>
<div style="font-weight: 700; color: #F1F5F9;">Smart Assessments & Games</div>
<div style="font-size: 0.88rem; color: #94A3B8;">Interactive quizzes, aptitude practice, and gamified reward coins.</div>
</div>
</div>
<div class="feature-item">
<span class="feature-icon">🔥</span>
<div>
<div style="font-weight: 700; color: #F1F5F9;">Track Progress & Study Groups</div>
<div style="font-size: 0.88rem; color: #94A3B8;">Maintain study streaks, share group links, and learn together.</div>
</div>
</div>
</div>""",
            unsafe_allow_html=True
        )

    with col_right:
        st.markdown(
            """
            <div class="glass-card">
                <h2 style="color: #F8FAFC; font-weight: 700; margin-top: 0; margin-bottom: 0.3rem;">Welcome back 👋</h2>
                <div style="color: #94A3B8; font-size: 0.95rem; margin-bottom: 1.4rem;">
                    Enter your student credentials to access your personal dashboard.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form(key="login_form", clear_on_submit=False):
            identifier = st.text_input("Email or Username", placeholder="student@example.com or username", key="login_id_input")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pw_input")
            remember_me = st.checkbox("Remember me", value=True, key="login_remember_check")
            submit_login = st.form_submit_button("🚀 Sign In to EduMind", type="primary", use_container_width=True)

        if submit_login:
            with st.spinner("Authenticating credentials..."):
                ok, msg = auth.login_user(identifier, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        st.markdown("---")
        col_reg, col_forgot = st.columns([1, 1])
        with col_reg:
            if st.button("✨ Create Account", use_container_width=True, key="btn_goto_register"):
                st.session_state.auth_mode = "register"
                st.rerun()
        with col_forgot:
            if st.button("🔑 Forgot Password?", use_container_width=True, key="btn_forgot_pw"):
                st.info("💡 Password reset instructions will be sent to your registered email.")
