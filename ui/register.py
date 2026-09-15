"""
EduMind AI - Futuristic Registration Page View
Renders modern glassmorphism account creation screen with real-time validation.
"""

import streamlit as st
import auth

def render_register_page():
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
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #60A5FA 0%, #A855F7 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.65rem 1.5rem !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    col_center = st.columns([1, 2, 1])[1]

    with col_center:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 1.2rem; padding-top: 1rem;">
                <span style="font-size: 2.8rem;">🎓</span>
                <div class="gradient-title">Join EduMind AI</div>
                <div style="color: #94A3B8; font-size: 1.05rem;">
                    Create your student account to unlock your personalized Gemini AI Tutor
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form(key="register_form", clear_on_submit=False):
            st.markdown("### 📝 Create your EduMind account")

            col_names1, col_names2 = st.columns(2)
            with col_names1:
                full_name = st.text_input("Full Name", placeholder="Harsha Gudivada", key="reg_name_input")
            with col_names2:
                username = st.text_input("Username", placeholder="harsha_dev", key="reg_user_input")

            email = st.text_input("Email Address", placeholder="student@example.com", key="reg_email_input")

            col_pw1, col_pw2 = st.columns(2)
            with col_pw1:
                password = st.text_input("Password", type="password", placeholder="••••••••", key="reg_pw_input")
            with col_pw2:
                confirm_pw = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="reg_cpw_input")

            avatar_choice = st.selectbox(
                "Profile Avatar",
                options=["🎓 Student", "🚀 Hacker", "🧠 Scholar", "⭐ Star Scholar", "💻 Dev"],
                index=0,
                key="reg_avatar_select"
            )

            # Real-time password strength indicators
            if password:
                val_ok, val_msg = auth.validate_password(password)
                if val_ok:
                    st.success("🟢 Strong password")
                else:
                    st.warning(f"🟡 Password requirement: {val_msg}")

            submit_reg = st.form_submit_button("✨ Complete Registration & Sign In", type="primary", use_container_width=True)

        if submit_reg:
            if not full_name.strip() or not username.strip() or not email.strip() or not password:
                st.error("❌ Please fill in all required fields.")
            elif password != confirm_pw:
                st.error("❌ Passwords do not match.")
            else:
                with st.spinner("Creating your account & initializing wallet..."):
                    ok, msg = auth.register_user(
                        email=email,
                        username=username,
                        password=password,
                        display_name=full_name,
                        avatar=avatar_choice.split()[0]
                    )
                    if ok:
                        st.success(f"🎉 {msg}")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        st.markdown("---")
        if st.button("← Already have an account? Sign In", use_container_width=True, key="btn_goto_login"):
            st.session_state.auth_mode = "login"
            st.rerun()
