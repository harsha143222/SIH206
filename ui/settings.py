"""
EduMind AI - Settings Page View
Manages account preferences, appearance theme, AI tutor voice settings, privacy controls, and secure session logout.
"""

import streamlit as st
import auth
import voice_engine

def render_settings_page():
    st.subheader("⚙️ Settings & Preferences")

    # Tabs for Settings Sections
    tab_acc, tab_voice, tab_app, tab_priv = st.tabs([
        "👤 Account",
        "🎙️ AI Tutor & Voice",
        "🎨 Appearance",
        "🔒 Privacy & Session"
    ])

    with tab_acc:
        st.markdown("### 👤 Account Details")
        st.write(f"**Display Name:** `{st.session_state.get('display_name', 'Student')}`")
        st.write(f"**Username:** `@{st.session_state.get('username', 'N/A')}`")
        st.write(f"**Registered Email:** `{st.session_state.get('user_email', 'N/A')}`")
        st.write(f"**User ID:** `{st.session_state.get('user_id', 'N/A')}`")

        st.markdown("---")
        st.markdown("### 🔑 Change Password")
        with st.form("change_password_form"):
            curr_pw = st.text_input("Current Password", type="password", key="settings_curr_pw")
            new_pw = st.text_input("New Password", type="password", key="settings_new_pw")
            conf_pw = st.text_input("Confirm New Password", type="password", key="settings_conf_pw")
            submit_pw_change = st.form_submit_button("Update Password 🔒", type="primary")

            if submit_pw_change:
                if not curr_pw or not new_pw or not conf_pw:
                    st.error("Please fill in all password fields.")
                elif new_pw != conf_pw:
                    st.error("New passwords do not match.")
                else:
                    user_id = st.session_state.get("user_id")
                    ok, msg = auth.change_password(user_id, curr_pw, new_pw)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

    with tab_voice:
        st.markdown("### 🎙️ AI Tutor Voice Settings")
        current_voice = st.session_state.get("selected_voice_gender", "Female")
        v_choice = st.radio(
            "Default AI Tutor Voice",
            options=["👩 Female Voice", "👨 Male Voice"],
            index=0 if current_voice == "Female" else 1,
            key="settings_voice_radio"
        )
        st.session_state.selected_voice_gender = "Female" if "Female" in v_choice else "Male"

        st.markdown("---")
        st.markdown("**Test Selected Browser Voice:**")
        # Single voice test button location in the application
        voice_engine.render_voice_test_button(st.session_state.selected_voice_gender)

    with tab_app:
        st.markdown("### 🎨 Appearance & Theme")
        st.info("🌙 **EduMind SaaS Dark Mode** is active by default for maximum visual contrast and legibility during long study sessions.")

    with tab_priv:
        st.markdown("### 🔒 Privacy & Data Isolation")
        st.success("✅ **MongoDB Multi-Tenant Isolation Active**: All your notes, chat history, quiz attempts, and coin balances are strictly isolated under your authenticated user account.")

        st.markdown("---")
        st.markdown("### 🚪 Account Session")
        st.warning("Signing out will clear your active dashboard session. Your notes, coins, and progress remain securely saved in MongoDB.")

        if st.button("🚪 Logout from EduMind AI", type="primary", use_container_width=True, key="btn_settings_logout"):
            auth.logout_user()
            st.success("Successfully logged out!")
            st.rerun()
