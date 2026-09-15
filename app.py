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
from coin_manager import CoinManager
import aptitude_engine
from aptitude_engine import AptitudeEngine, CATEGORIES
import games_engine
from games_engine import GamesEngine, GAMES_LIST
from gemini_client import (
    GeminiClientError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)

import auth
import mongodb
from ui.login import render_login_page
from ui.register import render_register_page
from ui.dashboard import render_dashboard_page
from ui.profile import render_profile_page
from ui.settings import render_settings_page
from ui.analytics import render_student_analytics_page
from ui.admin_analytics import render_admin_analytics_page

# ==============================================================================
# 1. STREAMLIT PAGE CONFIGURATION & THEME STYLES
# ==============================================================================
st.set_page_config(
    page_title="EduMind AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Unauthenticated User Gate: Show Login or Registration page
if not auth.is_authenticated():
    auth_mode = st.session_state.get("auth_mode", "login")
    if auth_mode == "register":
        render_register_page()
    else:
        render_login_page()
    st.stop()

# Theme-aware CSS styling for Light Mode & Dark Mode legibility
st.markdown(
    """
    <style>
    /* Hide default Streamlit automatic multipage navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Next-Gen AI Tutor Background & Particle Ambient Glow */
    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(30, 58, 138, 0.22) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(88, 28, 135, 0.22) 0%, transparent 50%),
                    #080B12 !important;
        animation: gradientShift 22s ease-in-out infinite alternate;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 0%; }
        50% { background-position: 50% 50%; }
        100% { background-position: 100% 100%; }
    }

    /* 3D NEURAL CORE HERO STYLING */
    .hero-ai-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 1.8rem 1rem 1rem 1rem;
        margin-bottom: 1.2rem;
        perspective: 1000px;
    }

    .neural-core-wrapper {
        position: relative;
        width: 220px;
        height: 220px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1.2rem;
        perspective: 1000px;
    }

    .core-shadow-3d {
        position: absolute;
        bottom: -15px;
        width: 140px;
        height: 18px;
        border-radius: 50%;
        background: radial-gradient(ellipse at center, rgba(15, 23, 42, 0.85) 0%, rgba(99, 102, 241, 0.25) 40%, transparent 75%);
        animation: shadowPulse 6s ease-in-out infinite;
        z-index: 0;
    }

    @keyframes shadowPulse {
        0%, 100% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(0.72); opacity: 0.45; }
    }

    .neural-core-3d {
        position: relative;
        width: 190px;
        height: 190px;
        display: flex;
        align-items: center;
        justify-content: center;
        transform-style: preserve-3d;
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        animation: coreFloat 6s ease-in-out infinite;
        z-index: 1;
    }

    @keyframes coreFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
    }

    .core-back-glow {
        position: absolute;
        width: 210px;
        height: 210px;
        border-radius: 50%;
        background: radial-gradient(circle at center, rgba(99, 102, 241, 0.4) 0%, rgba(139, 92, 246, 0.25) 45%, transparent 70%);
        filter: blur(15px);
        z-index: 0;
    }

    /* 3D Glass Sphere */
    .core-glass-sphere {
        position: relative;
        width: 155px;
        height: 155px;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 30%, rgba(96, 165, 250, 0.35) 0%, rgba(139, 92, 246, 0.3) 40%, rgba(15, 23, 42, 0.85) 90%);
        box-shadow: 
            inset -10px -10px 25px rgba(15, 23, 42, 0.9),
            inset 8px 8px 20px rgba(191, 219, 254, 0.5),
            0 0 35px rgba(99, 102, 241, 0.55),
            0 0 75px rgba(139, 92, 246, 0.3);
        border: 1px solid rgba(191, 219, 254, 0.4);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        transform-style: preserve-3d;
        overflow: hidden;
        z-index: 2;
    }

    /* Specular Light Reflection */
    .core-specular-light {
        position: absolute;
        top: 6px;
        left: 12px;
        width: 130px;
        height: 130px;
        border-radius: 50%;
        background: radial-gradient(circle at 25% 20%, rgba(255, 255, 255, 0.75) 0%, rgba(255, 255, 255, 0.15) 25%, transparent 60%);
        animation: specularMove 10s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: 4;
    }

    @keyframes specularMove {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(12px, 8px) scale(0.9); }
        100% { transform: translate(6px, 14px) scale(1.05); }
    }

    /* Inner Energy Flow */
    .core-inner-energy {
        position: absolute;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        z-index: 2;
    }

    .energy-stream {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px solid transparent;
    }

    .energy-stream-1 {
        border-top: 3px solid rgba(96, 165, 250, 0.85);
        border-right: 2px solid rgba(168, 85, 247, 0.6);
        animation: energyRotate1 7s linear infinite;
        filter: drop-shadow(0 0 6px #60A5FA);
    }

    .energy-stream-2 {
        border-bottom: 3px solid rgba(236, 72, 153, 0.85);
        border-left: 2px solid rgba(129, 140, 248, 0.6);
        animation: energyRotate2 10s linear infinite reverse;
        filter: drop-shadow(0 0 6px #EC4899);
    }

    .energy-stream-3 {
        border-right: 3px solid rgba(52, 211, 153, 0.8);
        border-top: 2px solid rgba(99, 102, 241, 0.7);
        animation: energyRotate3 13s ease-in-out infinite alternate;
        filter: drop-shadow(0 0 6px #34D399);
    }

    @keyframes energyRotate1 { 0% { transform: rotate(0deg) scale(0.9); } 100% { transform: rotate(360deg) scale(0.9); } }
    @keyframes energyRotate2 { 0% { transform: rotate(0deg) scale(1.05); } 100% { transform: rotate(-360deg) scale(1.05); } }
    @keyframes energyRotate3 { 0% { transform: rotate(0deg) scale(0.95); } 100% { transform: rotate(180deg) scale(1.1); } }

    /* Center Symbol */
    .core-center-symbol {
        position: relative;
        font-size: 2.2rem;
        color: #FFFFFF;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.9), 0 0 30px rgba(168, 85, 247, 0.85);
        animation: symbolPulse 3.5s ease-in-out infinite;
        z-index: 5;
    }

    @keyframes symbolPulse {
        0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.9; }
        50% { transform: scale(1.18) rotate(15deg); opacity: 1; filter: drop-shadow(0 0 12px #FFFFFF); }
    }

    /* 3D Particles */
    .core-particles-3d {
        position: absolute;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 3;
    }
    .p-3d {
        position: absolute;
        color: rgba(255, 255, 255, 0.85);
        font-size: 0.65rem;
        animation: pFloat 6s ease-in-out infinite alternate;
        text-shadow: 0 0 5px #60A5FA;
    }
    .p1 { top: 20%; left: 25%; animation-delay: 0s; font-size: 0.8rem; }
    .p2 { top: 70%; left: 30%; animation-delay: 1.2s; }
    .p3 { top: 35%; left: 75%; animation-delay: 0.5s; font-size: 0.75rem; }
    .p4 { top: 75%; left: 70%; animation-delay: 2.1s; }
    .p5 { top: 15%; left: 60%; animation-delay: 1.7s; }
    .p6 { top: 80%; left: 45%; animation-delay: 0.9s; }
    .p7 { top: 45%; left: 15%; animation-delay: 2.6s; font-size: 0.7rem; }
    .p8 { top: 60%; left: 80%; animation-delay: 3.1s; }

    @keyframes pFloat {
        0% { transform: translateY(0) scale(0.8); opacity: 0.3; }
        100% { transform: translateY(-10px) scale(1.2); opacity: 0.95; }
    }

    /* 3D Orbital Rings */
    .orbit-ring-3d {
        position: absolute;
        border-radius: 50%;
        pointer-events: none;
        transform-style: preserve-3d;
    }

    .orbit-ring-1 {
        width: 210px;
        height: 210px;
        border: 1.5px dashed rgba(96, 165, 250, 0.6);
        box-shadow: 0 0 12px rgba(96, 165, 250, 0.3);
        transform: rotateX(68deg) rotateY(-18deg);
        animation: orbit1Rotate 14s linear infinite;
        z-index: 1;
    }

    .orbit-ring-2 {
        width: 235px;
        height: 235px;
        border: 1.5px dotted rgba(168, 85, 247, 0.65);
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.35);
        transform: rotateX(75deg) rotateY(25deg);
        animation: orbit2Rotate 19s linear infinite reverse;
        z-index: 0;
    }

    .orbit-ring-3 {
        width: 185px;
        height: 185px;
        border: 1px solid rgba(52, 211, 153, 0.45);
        transform: rotateX(60deg) rotateY(45deg);
        animation: orbit1Rotate 24s linear infinite;
        z-index: 3;
    }

    @keyframes orbit1Rotate { 0% { transform: rotateX(68deg) rotateY(-18deg) rotateZ(0deg); } 100% { transform: rotateX(68deg) rotateY(-18deg) rotateZ(360deg); } }
    @keyframes orbit2Rotate { 0% { transform: rotateX(75deg) rotateY(25deg) rotateZ(0deg); } 100% { transform: rotateX(75deg) rotateY(25deg) rotateZ(-360deg); } }

    /* Thinking State Accelerated Rotations */
    .ai-orb-thinking .orbit-ring-1 { animation: orbit1Rotate 4s linear infinite !important; border-color: rgba(236, 72, 153, 0.8) !important; }
    .ai-orb-thinking .orbit-ring-2 { animation: orbit2Rotate 5s linear infinite reverse !important; border-color: rgba(245, 158, 11, 0.8) !important; }
    .ai-orb-thinking .core-center-symbol { animation: symbolPulse 1.2s ease-in-out infinite !important; }

    /* AI Status Pill */
    .ai-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.95rem;
        border-radius: 9999px;
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(99, 102, 241, 0.35);
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
        font-size: 0.82rem;
        font-weight: 600;
        color: #E2E8F0;
        margin-bottom: 0.75rem;
    }

    .status-pulse-dot {
        color: #10B981;
        font-size: 0.75rem;
        animation: dotPulse 2s ease-in-out infinite;
    }

    @keyframes dotPulse {
        0%, 100% { opacity: 0.4; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.2); }
    }

    .hero-ai-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 0.25rem;
        letter-spacing: -0.01em;
    }

    .hero-ai-name {
        background: linear-gradient(135deg, #60A5FA 0%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-ai-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        font-weight: 500;
    }

    /* Hover style for suggestion chips */
    div[data-testid="stHorizontalBlock"] button {
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(168, 85, 247, 0.6) !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.25) !important;
    }

    /* Message entrance animation */
    div[data-testid="stChatMessage"] {
        animation: messageIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
        border-radius: 14px !important;
    }

    @keyframes messageIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* Accessibility Fallback for Reduced Motion */
    @media (prefers-reduced-motion: reduce) {
        .neural-core-3d, .orbit-ring-3d, .energy-stream, .core-center-symbol, .p-3d, div[data-testid="stChatMessage"], .stApp {
            animation: none !important;
        }
    }

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

    /* THEME-AWARE QUIZ & CARD STYLES */
    .quiz-card {
        background-color: var(--background-secondary-color, rgba(128, 128, 128, 0.08));
        color: var(--text-color, inherit);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .unlock-card {
        background-color: var(--background-secondary-color, rgba(128, 128, 128, 0.08));
        color: var(--text-color, inherit);
        border: 2px dashed rgba(234, 179, 8, 0.6);
        border-radius: 14px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
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

    /* COMMAND CENTER GLASSMORPHISM STYLES */
    .command-center-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 16px;
        padding: 0.8rem 1.4rem;
        margin-bottom: 1.4rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.35);
    }
    
    .glass-panel {
        background: rgba(20, 27, 45, 0.65);
        border: 1px solid rgba(120, 110, 255, 0.25);
        backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 1.3rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
    }

    .vault-doc-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .vault-doc-card:hover {
        border-color: rgba(168, 85, 247, 0.55);
        transform: translateY(-2px);
    }
    .doc-card-title { font-weight: 700; color: #F8FAFC; font-size: 0.95rem; margin-bottom: 0.25rem; }
    .doc-card-meta { font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.35rem; }
    .doc-card-status { font-size: 0.78rem; color: #10B981; font-weight: 600; display: inline-flex; align-items: center; gap: 0.3rem; }

    .ai-context-pill {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 0.55rem 1rem;
        margin-bottom: 1.2rem;
        font-size: 0.85rem;
    }
    .context-badge {
        background: rgba(99, 102, 241, 0.18);
        color: #818CF8;
        padding: 0.22rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid rgba(99, 102, 241, 0.3);
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
    Loads authenticated user profile, user-specific documents, chat history, and progress from MongoDB.
    """
    user_id = st.session_state.get("user_id", "user_default")
    user_name = st.session_state.get("user_name", "Student")

    # Initialize Coin Engine State for current user
    CoinManager.initialize()

    # Load user documents
    user_docs = mongodb.get_user_documents(user_id) or database.get_documents_by_subject(config.DEFAULT_SUBJECT)

    # Load user chat messages
    current_subj = st.session_state.get("current_subject", config.DEFAULT_SUBJECT)
    user_msgs = mongodb.get_chat_messages(user_id, current_subj)
    if not user_msgs:
        user_msgs = [{"role": "assistant", "content": config.INITIAL_GREETING}]

    # Load user learned topics
    user_topics = mongodb.get_user_learned_topics(user_id)

    sample_groups = group_learning.create_sample_groups(user_name)
    first_group_id = list(sample_groups.keys())[0] if sample_groups else ""

    defaults = {
        "user_id": user_id,
        "user_name": user_name,
        "rewarded_questions": set(),
        "completed_quiz_ids": set(),
        "messages": user_msgs,
        "documents": user_docs,
        "learned_topics": user_topics,
        "current_subject": config.DEFAULT_SUBJECT,
        "quiz_mode": False,
        "current_quiz": None,
        "quiz_answers": {},
        "quiz_hints_used": {},
        "quiz_submitted": False,
        "quiz_index": 0,
        "selected_voice_gender": "Female",
        "my_groups": sample_groups,
        "active_group_id": first_group_id,
        "attached_image": None,

        # Feature Unlock State
        "aptitude_unlocked": False,
        "games_unlocked": False,

        # Aptitude State
        "aptitude_active": False,
        "aptitude_questions": [],
        "aptitude_index": 0,
        "aptitude_answers": {},
        "aptitude_submitted": False,
        "aptitude_report": None,

        # Games State
        "active_game_id": None,
        "active_game_level": 1,
        "game_questions": [],
        "game_index": 0,
        "game_score": 0,
        "game_submitted": False,
        "game_report": None
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
    st.session_state.learning_streak = st.session_state.current_streak


initialize_session_state()

# ==============================================================================
# 3. SIDEBAR: NAVIGATION, VOICE, SUBJECT, UPLOAD & CONTROLS
# ==============================================================================
with st.sidebar:
    st.image("https://api.iconify.design/lucide:graduation-cap.svg?color=%233B82F6", width=44)
    st.title("EduMind AI")
    st.caption(f"Powered by Gemini ({config.GEMINI_MODEL}) | SIH 2026")
    st.markdown("---")

    PAGE_OPTIONS = [
        "📊 Student Dashboard",
        "📊 My Analytics",
        "🏠 Home / Individual Learning",
        "🎯 Aptitude Practice",
        "🎮 Educational Games",
        "👥 Friends Dashboard",
        "👤 Profile & Analytics",
        "⚙️ Settings & Voice",
        "📊 Admin Analytics"
    ]

    if "current_page" not in st.session_state:
        st.session_state.current_page = "📊 Student Dashboard"

    try:
        current_nav_index = PAGE_OPTIONS.index(st.session_state.current_page)
    except (ValueError, KeyError):
        current_nav_index = 0
        st.session_state.current_page = PAGE_OPTIONS[0]

    def _on_nav_change():
        st.session_state.current_page = st.session_state.nav_radio_select

    nav_mode = st.radio(
        "📌 Navigation",
        options=PAGE_OPTIONS,
        index=current_nav_index,
        key="nav_radio_select",
        on_change=_on_nav_change
    )
    st.session_state.current_page = nav_mode
    st.markdown("---")

    # Compact Coin Balance in Sidebar
    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.7); border-radius: 10px; padding: 0.75rem; text-align: center; margin-bottom: 1rem; border: 1px solid rgba(234, 179, 8, 0.4);">
            <span style="font-size: 1.25rem; font-weight: 700; color: #FEF08A;">🪙 {st.session_state.coin_balance} Coins</span>
            <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 0.2rem;">Global Learning Wallet</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # API Connection Status (Secure Server-Side Secret / Env Var)
    if config.is_gemini_api_key_configured():
        st.markdown('<span class="status-badge status-active">● Gemini Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-missing">● Gemini API Key Missing</span>', unsafe_allow_html=True)
        st.error("⚠️ Set `GEMINI_API_KEY` in environment variables or Streamlit secrets.")

    st.markdown(f"**AI Model:** `{config.GEMINI_MODEL}`")
    st.markdown("---")

    # Authenticated Student Profile Card at Sidebar Bottom
    u_disp = st.session_state.get("display_name", st.session_state.get("user_name", "Student"))
    u_handle = st.session_state.get("username", "student")
    u_avatar = st.session_state.get("avatar", "🎓")

    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 0.8rem;">
            <div style="font-size: 1.8rem; background: rgba(99, 102, 241, 0.2); width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                {u_avatar}
            </div>
            <div>
                <div style="font-weight: 700; color: #F8FAFC; font-size: 0.95rem; line-height: 1.2;">{u_disp}</div>
                <div style="font-size: 0.8rem; color: #60A5FA;">@{u_handle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🚪 Logout Session", use_container_width=True, key="sidebar_logout_btn"):
        auth.logout_user()
        st.rerun()

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
    st.markdown("---")

    if "Home" in nav_mode:
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
                                subject=st.session_state.current_subject,
                                user_id=st.session_state.user_id
                            )
                            st.session_state.documents.append(doc_data)
                            st.success(f"✅ Indexed: {file.name} ({doc_data['total_units']} {doc_data['file_type']} units)")
                            # Reward for uploading study material (+5 coins)
                            CoinManager.claim_reward(
                                reward_id=f"upload_doc_{file.name}",
                                amount=5,
                                reason=f"Uploaded study material: {file.name}",
                                source="study"
                            )
                            CoinManager.record_study_activity("materials_uploaded")
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
            <span class="badge-pill badge-streak">🔥 {st.session_state.current_streak} Day Streak</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ==============================================================================
# 4.5. SHAREABLE GROUP INVITE LINK HELPER & INTERCEPTOR (?join_group=<token_or_code>)
# ==============================================================================
def render_share_invite_buttons(invite_token: str, group_name: str, key_suffix: str = ""):
    """Render interactive HTML/JS buttons for copying invite link and Web Share API."""
    html_code = f"""
    <script>
    function copyInviteLink_{key_suffix}() {{
        let hostUrl = window.location.origin + window.location.pathname;
        if (!hostUrl || hostUrl === 'null' || hostUrl === 'about:blank') {{
            hostUrl = 'http://localhost:8501/';
        }}
        const fullUrl = hostUrl.replace(/\\/?$/, '/') + '?join_group={invite_token}';
        
        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(fullUrl).then(() => {{
                alert('📋 Invite link copied to clipboard!\\n\\n' + fullUrl);
            }}).catch(() => {{
                prompt('Copy this invite link:', fullUrl);
            }});
        }} else {{
            prompt('Copy this invite link:', fullUrl);
        }}
    }}

    function shareGroup_{key_suffix}() {{
        let hostUrl = window.location.origin + window.location.pathname;
        if (!hostUrl || hostUrl === 'null' || hostUrl === 'about:blank') {{
            hostUrl = 'http://localhost:8501/';
        }}
        const fullUrl = hostUrl.replace(/\\/?$/, '/') + '?join_group={invite_token}';

        if (navigator.share) {{
            navigator.share({{
                title: 'Join my EduMind Study Group',
                text: 'Join my {group_name} study group on EduMind AI!',
                url: fullUrl
            }}).catch(err => console.log('Share canceled/error', err));
        }} else {{
            copyInviteLink_{key_suffix}();
        }}
    }}
    </script>
    <div style="display: flex; gap: 10px; margin-top: 6px; margin-bottom: 6px;">
        <button onclick="copyInviteLink_{key_suffix}()" style="background-color: #1E3A8A; color: #FFFFFF; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.88rem;">
            📋 Copy Invite Link
        </button>
        <button onclick="shareGroup_{key_suffix}()" style="background-color: #059669; color: #FFFFFF; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.88rem;">
            📤 Share Group
        </button>
    </div>
    """
    st.components.v1.html(html_code, height=60)


query_invite = st.query_params.get("join_group")
if query_invite:
    group_learning.init_group_state()
    target_group = group_learning.find_group_by_token_or_code(query_invite)

    if not target_group:
        st.markdown(
            """
            <div style="background-color: #FDE8E8; border: 1px solid #F87171; border-radius: 12px; padding: 1.4rem; margin-bottom: 1.5rem;">
                <h3 style="color: #9B1C1C; margin-top: 0;">❌ Invalid or Expired Group Invite</h3>
                <p style="color: #7F1D1D; font-size: 1rem; margin-bottom: 0.8rem;">
                    The study group invite link or code you opened is invalid or no longer active.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Dismiss & Continue to EduMind AI", type="primary"):
            if "join_group" in st.query_params:
                del st.query_params["join_group"]
            st.rerun()
    else:
        is_member = st.session_state.user_name in target_group.get("members", {})
        if is_member:
            st.markdown(
                f"""
                <div style="background-color: rgba(59, 130, 246, 0.1); border: 1.5px solid #3B82F6; border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem;">
                    <h3 style="color: #1E3A8A; margin-top: 0;">👥 You're already a member of {target_group['group_name']}</h3>
                    <p style="font-size: 1.05rem; margin-bottom: 0.8rem;">
                        Subject: <b>{target_group['subject']}</b> | Members: <b>{len(target_group['members'])}</b> | Created by: <b>{target_group['created_by']}</b>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            col_already1, col_already2 = st.columns([1, 1])
            with col_already1:
                if st.button("💬 Open Group Chat", type="primary", use_container_width=True):
                    st.session_state.active_group_id = target_group["group_id"]
                    st.session_state.current_page = "👥 Friends Dashboard"
                    if "join_group" in st.query_params:
                        del st.query_params["join_group"]
                    st.rerun()
            with col_already2:
                if st.button("Dismiss", use_container_width=True):
                    if "join_group" in st.query_params:
                        del st.query_params["join_group"]
                    st.rerun()
        else:
            st.markdown(
                f"""
                <div class="unlock-card" style="border: 2px solid #3B82F6; text-align: left; padding: 1.8rem;">
                    <h2 style="color: #1E3A8A; margin-top: 0; margin-bottom: 0.8rem;">👥 Join Study Group</h2>
                    <div style="font-size: 1.4rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.6rem;">
                        {target_group['group_name']}
                    </div>
                    <div style="font-size: 1.05rem; margin-bottom: 0.4rem;">📚 Subject: <b>{target_group['subject']}</b></div>
                    <div style="font-size: 1.05rem; margin-bottom: 0.4rem;">👤 Created by: <b>{target_group['created_by']}</b></div>
                    <div style="font-size: 1.05rem; margin-bottom: 1.2rem;">👥 Members: <b>{len(target_group['members'])}</b></div>
                </div>
                """,
                unsafe_allow_html=True
            )

            join_handle_val = st.text_input("Your Handle / Name", value=st.session_state.user_name, key="invite_handle_confirm_input")

            col_confirm1, col_confirm2 = st.columns([1, 1])
            with col_confirm1:
                if st.button("➕ Join Group", type="primary", use_container_width=True):
                    if join_handle_val.strip():
                        st.session_state.user_name = join_handle_val.strip()
                    ok, msg = group_learning.join_existing_group(target_group["group_id"], st.session_state.user_name)
                    if ok:
                        st.session_state.active_group_id = target_group["group_id"]
                        st.session_state.current_page = "👥 Friends Dashboard"
                        if "join_group" in st.query_params:
                            del st.query_params["join_group"]
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col_confirm2:
                if st.button("Cancel", use_container_width=True):
                    if "join_group" in st.query_params:
                        del st.query_params["join_group"]
                    st.rerun()

# ==============================================================================
# 5. APTITUDE SECTION RENDERER (COIN UNLOCK FLOW)
# ==============================================================================
def render_aptitude_section():
    st.subheader("🎯 Aptitude Practice")

    if not st.session_state.aptitude_unlocked:
        # LOCKED CARD UI
        st.markdown(
            f"""
            <div class="unlock-card">
                <h2>🎯 Aptitude Practice</h2>
                <p style="font-size:1.1rem; opacity:0.9;">
                    Test your skills in <b>Quantitative Aptitude, Logical Reasoning, Verbal Ability, Data Interpretation, Geometry, & Algebra</b>.
                </p>
                <div style="margin: 1.2rem 0;">
                    <span class="badge-pill badge-revision" style="font-size:1rem;">🔒 Locked</span>
                    <span class="badge-pill badge-coins" style="font-size:1rem;">🪙 30 Coins</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_left, col_btn, col_right = st.columns([1, 2, 1])
        with col_btn:
            if st.button("🔓 Unlock Aptitude (🪙 30 Coins)", type="primary", use_container_width=True, key="btn_unlock_aptitude"):
                if CoinManager.can_afford(30):
                    if CoinManager.spend_coins(30, "Unlocked Aptitude Practice", "feature_unlock", reference_id="aptitude_unlock"):
                        st.session_state.aptitude_unlocked = True
                        st.balloons()
                        st.success("🎯 Aptitude Practice unlocked!")
                        st.rerun()
                else:
                    needed = 30 - st.session_state.coin_balance
                    st.warning(f"🪙 You need {needed} more coins to unlock Aptitude Practice.")

    else:
        # UNLOCKED STATE - APTITUDE INTERFACE
        st.caption("✅ **Unlocked** | Practice Quantitative Aptitude, Logical Reasoning, Verbal Ability, & Data Interpretation.")

        if not st.session_state.aptitude_active:
            with st.form(key="aptitude_setup_form"):
                st.markdown("### ⚙️ Configure Aptitude Challenge")
                col_cat, col_diff, col_num = st.columns(3)
                with col_cat:
                    selected_cat = st.selectbox("Aptitude Category", options=["All Categories"] + CATEGORIES)
                with col_diff:
                    selected_diff = st.selectbox("Difficulty Level", options=["Mixed", "Easy", "Medium", "Hard"])
                with col_num:
                    num_q = st.radio("Number of Questions", options=[5, 10, 15], index=0, horizontal=True)

                start_btn = st.form_submit_button("🚀 Start Aptitude Test (0 Coins)", type="primary")

            if start_btn:
                questions = AptitudeEngine.get_questions(category=selected_cat, difficulty=selected_diff, count=num_q)
                st.session_state.aptitude_questions = questions
                st.session_state.aptitude_index = 0
                st.session_state.aptitude_answers = {}
                st.session_state.aptitude_submitted = False
                st.session_state.aptitude_report = None
                st.session_state.aptitude_active = True
                st.rerun()

        else:
            questions = st.session_state.aptitude_questions
            total_q = len(questions)
            curr_idx = st.session_state.aptitude_index

            if not st.session_state.aptitude_submitted:
                q = questions[curr_idx]
                st.progress((curr_idx + 1) / total_q, text=f"Question {curr_idx + 1} of {total_q}")

                st.markdown(
                    f"""
                    <div class="quiz-card">
                        <span class="topic-badge badge-learned">Category: {q['category']}</span>
                        <span class="topic-badge badge-practice">Difficulty: {q['difficulty']}</span>
                        <div class="quiz-question-heading">{q['question']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                existing_ans = st.session_state.aptitude_answers.get(q["id"])
                selected_opt = st.radio(
                    "Select your answer:",
                    options=q["options"],
                    index=existing_ans if existing_ans is not None else 0,
                    key=f"apt_q_radio_{q['id']}"
                )
                st.session_state.aptitude_answers[q["id"]] = q["options"].index(selected_opt)

                col_p, col_space, col_n = st.columns([1, 2, 1])
                with col_p:
                    if curr_idx > 0 and st.button("← Previous", key="btn_apt_prev"):
                        st.session_state.aptitude_index -= 1
                        st.rerun()
                with col_n:
                    if curr_idx < total_q - 1:
                        if st.button("Next Question →", key="btn_apt_next"):
                            st.session_state.aptitude_index += 1
                            st.rerun()
                    else:
                        if st.button("Submit Aptitude Test ✅", type="primary", key="btn_apt_submit"):
                            attempt_id = f"apt_{uuid.uuid4().hex[:8]}"
                            score = 0
                            details = []

                            for q_item in questions:
                                usr_ans = st.session_state.aptitude_answers.get(q_item["id"])
                                is_corr = (usr_ans is not None and usr_ans == q_item["correct_index"])
                                if is_corr:
                                    score += 1
                                details.append({
                                    "id": q_item["id"],
                                    "difficulty": q_item["difficulty"],
                                    "is_correct": is_corr
                                })

                            report = AptitudeEngine.process_test_completion(
                                attempt_id=attempt_id,
                                score=score,
                                total_questions=total_q,
                                question_details=details
                            )
                            st.session_state.aptitude_report = report
                            st.session_state.aptitude_submitted = True
                            st.balloons()
                            st.rerun()

            else:
                rep = st.session_state.aptitude_report or {}
                st.success("🎉 Aptitude Test Completed!")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Score", f"{rep.get('score', 0)} / {rep.get('total', 0)}")
                c2.metric("Percentage", f"{rep.get('percentage', 0)}%")
                c3.metric("Coins Earned", f"🪙 +{rep.get('coins_earned', 0)}")
                c4.metric("Wallet Balance", f"💰 {st.session_state.coin_balance}")

                st.markdown("---")
                st.markdown("### 📖 Detailed Review")
                for q_item in questions:
                    usr_ans = st.session_state.aptitude_answers.get(q_item["id"])
                    is_corr = (usr_ans is not None and usr_ans == q_item["correct_index"])
                    status = "✅ Correct" if is_corr else "❌ Incorrect"
                    st.markdown(f"**{q_item['question']}** ({status})")
                    st.caption(f"Category: {q_item['category']} | Difficulty: {q_item['difficulty']}")
                    st.info(f"💡 **Explanation:** {q_item['explanation']}")
                    st.markdown("---")

                if st.button("🔄 Take Another Aptitude Test", type="primary"):
                    st.session_state.aptitude_active = False
                    st.rerun()

# ==============================================================================
# 6. EDUCATIONAL GAMES SECTION RENDERER (COIN UNLOCK FLOW)
# ==============================================================================
def render_games_section():
    st.subheader("🎮 Educational Games Hub")
    user_id = st.session_state.get("user_id", "user_default")

    if not st.session_state.games_unlocked:
        # LOCKED CARD UI
        st.markdown(
            f"""
            <div class="unlock-card">
                <h2>🎮 Educational Games Hub</h2>
                <p style="font-size:1.1rem; opacity:0.9;">
                    Play interactive educational games across 5 cognitive difficulty levels (<b>Beginner, Easy, Intermediate, Advanced, Expert</b>).
                </p>
                <div style="margin: 1.2rem 0;">
                    <span class="badge-pill badge-revision" style="font-size:1rem;">🔒 Locked</span>
                    <span class="badge-pill badge-coins" style="font-size:1rem;">🪙 40 Coins</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_left, col_btn, col_right = st.columns([1, 2, 1])
        with col_btn:
            if st.button("🔓 Unlock Games (🪙 40 Coins)", type="primary", use_container_width=True, key="btn_unlock_games"):
                if CoinManager.can_afford(40):
                    if CoinManager.spend_coins(40, "Unlocked Educational Games", "feature_unlock", reference_id="games_unlock"):
                        st.session_state.games_unlocked = True
                        st.balloons()
                        st.success("🎮 Educational Games unlocked!")
                        st.rerun()
                else:
                    needed = 40 - st.session_state.coin_balance
                    st.warning(f"🪙 You need {needed} more coins to unlock Educational Games.")

    else:
        # UNLOCKED STATE - GAMES HUB INTERFACE
        st.caption("✅ **Unlocked** | 5 Progressive Cognitive Difficulty Levels • Zero Question Overlap • Scaled Coin Rewards")

        if not st.session_state.active_game_id:
            cols = st.columns(2)
            for idx, game in enumerate(GAMES_LIST):
                unlocked_lvl = GamesEngine.get_unlocked_level(game["id"], user_id=user_id)
                col_target = cols[idx % 2]

                with col_target:
                    st.markdown(
                        f"""
                        <div class="quiz-card">
                            <h3 style="margin-top:0;">{game['name']}</h3>
                            <p style="color:#94A3B8; font-size:0.92rem;">{game['desc']}</p>
                            <span class="topic-badge badge-strong">Highest Unlocked: Level {unlocked_lvl} / 5</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Select Level for this Game
                    level_choices = list(range(1, unlocked_lvl + 1))
                    selected_lvl = st.selectbox(
                        f"Choose Level for {game['name']}",
                        options=level_choices,
                        format_func=lambda l: f"Level {l} — {'Beginner ⭐' if l==1 else ('Easy ⭐⭐' if l==2 else ('Intermediate ⭐⭐⭐' if l==3 else ('Advanced ⭐⭐⭐⭐' if l==4 else 'Expert ⭐⭐⭐⭐⭐')))}",
                        key=f"select_lvl_{game['id']}"
                    )

                    if st.button(f"🎮 Play Level {selected_lvl}", key=f"btn_play_g_{game['id']}", use_container_width=True, type="primary"):
                        st.session_state.active_game_id = game["id"]
                        st.session_state.active_game_level = selected_lvl
                        st.session_state.game_questions = GamesEngine.get_game_questions(game["id"], selected_lvl)
                        st.session_state.game_index = 0
                        st.session_state.game_score = 0
                        st.session_state.game_answers = {}
                        st.session_state.game_submitted = False
                        st.session_state.game_report = None
                        st.rerun()

        else:
            game_id = st.session_state.active_game_id
            game_info = next((g for g in GAMES_LIST if g["id"] == game_id), GAMES_LIST[0])
            active_lvl = st.session_state.active_game_level

            # Rerun stability check
            if ("game_questions" not in st.session_state or
                not st.session_state.game_questions or
                st.session_state.get("game_level_cached") != active_lvl):
                st.session_state.game_questions = GamesEngine.get_game_questions(game_id, active_lvl)
                st.session_state.game_level_cached = active_lvl
                st.session_state.game_index = 0
                st.session_state.game_score = 0
                st.session_state.game_answers = {}
                st.session_state.game_submitted = False
                st.session_state.game_report = None

            questions = st.session_state.game_questions
            total_q = len(questions)
            curr_idx = st.session_state.game_index

            st.markdown(
                f"""
                <div style="display:flex; justify-between:space-between; align-items:center; background:rgba(30,41,59,0.7); border:1px solid rgba(99,102,241,0.3); border-radius:12px; padding:0.9rem 1.2rem; margin-bottom:1.2rem;">
                    <div>
                        <h3 style="margin:0; color:#F8FAFC;">{game_info['name']}</h3>
                        <div style="font-size:0.88rem; color:#60A5FA;">Level {active_lvl} Challenge ({'Beginner ⭐' if active_lvl==1 else ('Easy ⭐⭐' if active_lvl==2 else ('Intermediate ⭐⭐⭐' if active_lvl==3 else ('Advanced ⭐⭐⭐⭐' if active_lvl==4 else 'Expert ⭐⭐⭐⭐⭐')))})</div>
                    </div>
                    <div>
                        <span class="badge-pill badge-reward">Reward: 🪙 +{games_engine.LEVEL_REWARDS.get(active_lvl, 5)} Coins</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if not st.session_state.game_submitted:
                q = questions[curr_idx]
                st.progress((curr_idx + 1) / total_q, text=f"Question {curr_idx + 1} of {total_q}")

                st.markdown(
                    f"""
                    <div class="quiz-card">
                        <span class="topic-badge badge-learned">Level {active_lvl}</span>
                        <div class="quiz-question-heading">{q['q']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                existing_ans = st.session_state.game_answers.get(curr_idx)
                sel_opt = st.radio(
                    "Choose your answer:",
                    options=q["opts"],
                    index=existing_ans if existing_ans is not None else 0,
                    key=f"game_radio_{active_lvl}_{curr_idx}"
                )
                st.session_state.game_answers[curr_idx] = q["opts"].index(sel_opt)

                col_prev, col_space, col_next = st.columns([1, 2, 1])

                with col_prev:
                    if curr_idx > 0:
                        if st.button("← Previous", key=f"btn_g_prev_{curr_idx}"):
                            st.session_state.game_index -= 1
                            st.rerun()

                with col_next:
                    if curr_idx < total_q - 1:
                        if st.button("Next Question →", key=f"btn_g_next_{curr_idx}"):
                            st.session_state.game_index += 1
                            st.rerun()
                    else:
                        if st.button("Submit Game Level ✅", type="primary", key=f"btn_game_sub_level"):
                            score = 0
                            for idx_q, q_item in enumerate(questions):
                                u_ans = st.session_state.game_answers.get(idx_q)
                                if u_ans is not None and u_ans == q_item["ans"]:
                                    score += 1

                            rep = GamesEngine.process_game_results(
                                game_id=game_id,
                                level=active_lvl,
                                score=score,
                                total=total_q,
                                user_id=user_id
                            )
                            st.session_state.game_report = rep
                            st.session_state.game_submitted = True
                            st.rerun()

            else:
                rep = st.session_state.game_report or {}
                if rep.get("is_win"):
                    st.balloons()
                    st.success(f"🎉 Level {active_lvl} Complete! Victory achieved!")
                else:
                    st.warning(f"Level {active_lvl} Completed. Keep practicing to reach 60% accuracy and unlock Level {active_lvl + 1}!")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Score", f"{rep.get('score', 0)} / {rep.get('total', 0)}")
                c2.metric("Accuracy", f"{rep.get('percentage', 0)}%")
                c3.metric("Coins Earned", f"🪙 +{rep.get('coins_earned', 0)}")
                c4.metric("Best Score", f"{rep.get('best_score', 0)}%")

                st.markdown("---")
                st.markdown("### 📖 Detailed Question Review")
                for idx_q, q_item in enumerate(questions):
                    u_ans = st.session_state.game_answers.get(idx_q)
                    is_corr = (u_ans is not None and u_ans == q_item["ans"])
                    status_icon = "✅ Correct" if is_corr else "❌ Incorrect"
                    
                    st.markdown(f"**Question {idx_q + 1}: {q_item['q']}** ({status_icon})")
                    if u_ans is not None and u_ans < len(q_item["opts"]):
                        st.caption(f"Your Answer: **{q_item['opts'][u_ans]}**")
                    st.caption(f"Correct Answer: **{q_item['opts'][q_item['ans']]}**")
                    st.info(f"💡 **Explanation:** {q_item['exp']}")
                    st.markdown("---")

                btn_col1, btn_col2, btn_col3 = st.columns(3)

                with btn_col1:
                    if st.button("🔄 Play Again", use_container_width=True, type="secondary"):
                        st.session_state.game_questions = GamesEngine.get_game_questions(game_id, active_lvl)
                        st.session_state.game_index = 0
                        st.session_state.game_score = 0
                        st.session_state.game_answers = {}
                        st.session_state.game_submitted = False
                        st.session_state.game_report = None
                        st.rerun()

                with btn_col2:
                    if rep.get("unlocked_next") and active_lvl < 5:
                        if st.button("🚀 Play Next Level!", type="primary", use_container_width=True):
                            next_lvl = active_lvl + 1
                            st.session_state.active_game_level = next_lvl
                            st.session_state.game_level_cached = next_lvl
                            st.session_state.game_questions = GamesEngine.get_game_questions(game_id, next_lvl)
                            st.session_state.game_index = 0
                            st.session_state.game_score = 0
                            st.session_state.game_answers = {}
                            st.session_state.game_submitted = False
                            st.session_state.game_report = None
                            st.rerun()

                with btn_col3:
                    if st.button("🎮 Back to Games Hub", use_container_width=True):
                        st.session_state.active_game_id = None
                        st.rerun()

# ==============================================================================
# 7. FRIENDS & GROUP LEARNING DASHBOARD RENDERER
# ==============================================================================
def render_friends_dashboard():
    try:
        group_learning.init_group_state()

        st.subheader("👥 Friends & Group Learning System")
        st.caption("Learn together with friends, ask EduMind AI in group chat, share notes, take group quizzes, and compete on the group leaderboard!")

        # Newly Created Group Banner
        just_created_id = st.session_state.get("just_created_group_id")
        if just_created_id and just_created_id in st.session_state.my_groups:
            c_grp = st.session_state.my_groups[just_created_id]
            c_tok = c_grp.get("invite_token", c_grp["group_id"])
            c_link = f"http://localhost:8501/?join_group={c_tok}"

            st.markdown(
                f"""
                <div style="background-color: rgba(16, 185, 129, 0.1); border: 2px solid #10B981; border-radius: 14px; padding: 1.5rem; margin-bottom: 1.2rem;">
                    <h3 style="color: #065F46; margin-top: 0; margin-bottom: 0.5rem;">🎉 Study Group Created!</h3>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #047857; margin-bottom: 0.4rem;">
                        👥 {c_grp['group_name']}
                    </div>
                    <div style="margin-bottom: 0.3rem;">📚 Subject: <b>{c_grp['subject']}</b></div>
                    <div style="margin-bottom: 0.3rem;">👥 Members: <b>{len(c_grp['members'])}</b></div>
                    <div style="margin-bottom: 0.6rem;">🔑 Join Code: <code>{c_grp['join_code']}</code></div>
                    <div style="font-weight: 600; margin-bottom: 0.3rem;">🔗 Invite Link:</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.code(c_link, language=None)
            render_share_invite_buttons(c_tok, c_grp['group_name'], key_suffix="just_created")
            
            if st.button("Open Group", type="primary", key="btn_open_just_created"):
                st.session_state.active_group_id = just_created_id
                st.session_state.just_created_group_id = None
                st.rerun()

            st.markdown("---")

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
                        st.session_state.just_created_group_id = new_id
                        st.success(f"Study group created successfully! ID: `{new_id}`")
                        st.rerun()
                    else:
                        st.warning("Please enter Group Name, Subject, and Handle.")

        with col_join:
            with st.popover("🔗 Join Group"):
                st.markdown("### 🔗 Join Study Group")
                code_in = st.text_input("Enter Join Code or Invite Link", value="", key="pop_join_code")
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
                        st.warning("Please enter Group Code/Link and Handle.")

        active_group = st.session_state.my_groups.get(st.session_state.active_group_id)
        if not active_group:
            st.info("No active study group. Create or join one above!")
            return

        inv_token = active_group.get("invite_token", active_group["group_id"])
        inv_url = f"http://localhost:8501/?join_group={inv_token}"

        st.markdown(
            f"""
            <div class="quiz-card" style="margin-top: 0.4rem; margin-bottom: 0.8rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.25rem; font-weight: 700; color: #1E3A8A;">👥 {active_group['group_name']}</span>
                    <span class="badge-pill badge-coins">Created by: {active_group['created_by']}</span>
                </div>
                <span class="topic-badge badge-learned">Subject: <b>{active_group['subject']}</b></span>
                <span class="topic-badge badge-strong">🔑 Join Code: <code>{active_group['join_code']}</code></span>
                <span class="topic-badge badge-practice">Members: 👥 {len(active_group['members'])}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("🔗 Shareable Group Invite Link", expanded=False):
            st.markdown("Share this invite link with your friends to let them join this exact study group:")
            st.code(inv_url, language=None)
            render_share_invite_buttons(inv_token, active_group['group_name'], key_suffix=f"active_{active_group['group_id']}")
            
            if active_group.get("created_by") == st.session_state.user_name:
                st.markdown("---")
                if st.button("🔄 Regenerate Invite Link", key=f"btn_regen_{active_group['group_id']}"):
                    new_tok = group_learning.regenerate_invite_token(active_group["group_id"])
                    if new_tok:
                        st.success(f"New invite link generated! Old link is now invalid.")
                        st.rerun()

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
                                if not CoinManager.can_afford(config.HINT_COST):
                                    st.warning(f"💰 Not enough coins! You need {config.HINT_COST} coins to use a hint.")
                                else:
                                    if CoinManager.spend_coins(config.HINT_COST, "Group Quiz hint", "quiz", reference_id=f"g_hint_{q.id}"):
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

current_page = st.session_state.get("current_page", nav_mode)

if "Admin" in current_page:
    render_admin_analytics_page()
elif "My Analytics" in current_page:
    render_student_analytics_page()
elif "Dashboard" in current_page:
    render_dashboard_page()
elif "Friends" in current_page:
    render_friends_dashboard()
elif "Aptitude" in current_page:
    render_aptitude_section()
elif "Games" in current_page:
    render_games_section()
elif "Profile" in current_page:
    render_profile_page()
elif "Settings" in current_page:
    render_settings_page()
else:
    # --------------------------------------------------------------------------
    # MODE A: INDIVIDUAL CHAT INTERFACE & GROUNDED RAG DOUBT CLEARING
    # --------------------------------------------------------------------------
    if not st.session_state.quiz_mode:
        student_display_name = st.session_state.get("user_display_name", st.session_state.get("user_name", "Student"))
        
        # Command Center Top Header Status Bar
        top_header_html = f"""<div class="command-center-header">
<div style="display:flex; align-items:center; gap:0.6rem;">
<span style="font-size:1.5rem;">🎓</span>
<div>
<h3 style="margin:0; font-size:1.15rem; font-weight:800; color:#F8FAFC; letter-spacing:-0.01em;">EduMind AI — Command Center</h3>
<div style="font-size:0.78rem; color:#94A3B8;">Personalized RAG Reasoning Engine & Study Vault</div>
</div>
</div>
<div style="display:flex; align-items:center; gap:0.6rem;">
<span class="status-badge status-active">🟢 AI Ready</span>
<span class="badge-pill badge-streak">🔥 {st.session_state.get('user_streak', 1)} Days</span>
<span class="badge-pill badge-coins">🪙 {st.session_state.coin_balance} Coins</span>
</div>
</div>"""
        st.markdown(top_header_html, unsafe_allow_html=True)

        col_vault, col_tutor = st.columns([1, 1.85], gap="large")

        # ======================================================================
        # LEFT COLUMN (~35% Width) — 📚 STUDY VAULT & 👁 VISION LAB
        # ======================================================================
        with col_vault:
            # 📚 Study Vault Glass Panel
            vault_header_html = """<div class="glass-panel" style="margin-bottom:0.8rem;">
<h4 style="margin:0 0 0.3rem 0; color:#F8FAFC; display:flex; align-items:center; gap:0.5rem; font-size:1.05rem;">
📚 Study Vault
</h4>
<p style="color:#94A3B8; font-size:0.8rem; margin:0 0 0.6rem 0;">
Your private learning knowledge base • Private • Encrypted
</p>
<div style="font-size:0.75rem; color:#60A5FA; font-weight:600;">
PDF • PPT • PPTX (Max 100 MB per file)
</div>
</div>"""
            st.markdown(vault_header_html, unsafe_allow_html=True)

            uploaded_files = st.file_uploader(
                "Choose PDF, PPT or PPTX",
                type=config.SUPPORTED_FILE_TYPES,
                accept_multiple_files=True,
                key="vault_doc_uploader",
                help="Upload course notes or slides (up to 100 MB per file)"
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
                                    subject=st.session_state.current_subject,
                                    user_id=st.session_state.user_id
                                )
                                st.session_state.documents.append(doc_data)
                                st.success(f"✅ Indexed: {file.name} ({doc_data['total_units']} chunks)")
                                CoinManager.claim_reward(
                                    reward_id=f"upload_doc_{file.name}",
                                    amount=5,
                                    reason=f"Uploaded study material: {file.name}",
                                    source="study"
                                )
                                CoinManager.record_study_activity("materials_uploaded")
                            except document_processor.FileSizeExceededError as e:
                                st.error(f"❌ File too large: {str(e)}")
                            except Exception as e:
                                st.error(f"❌ Failed to process {file.name}: {str(e)}")

            if st.session_state.documents:
                st.markdown("<div style='font-weight: 700; color: #E2E8F0; margin-top: 0.8rem; margin-bottom: 0.4rem; font-size: 0.88rem;'>📄 Indexed Knowledge Files:</div>", unsafe_allow_html=True)
                for doc in st.session_state.documents:
                    doc_card_html = f"""<div class="vault-doc-card">
<div class="doc-card-title">📄 {doc['filename']}</div>
<div class="doc-card-meta">{doc.get('file_size_mb', 0)} MB • {doc.get('total_units', 0)} knowledge chunks</div>
<div class="doc-card-status">● Indexed</div>
</div>"""
                    st.markdown(doc_card_html, unsafe_allow_html=True)
            else:
                empty_vault_html = """<div style="text-align:center; padding:1.5rem 1rem; background:rgba(15,23,42,0.5); border:1px dashed rgba(99,102,241,0.3); border-radius:14px; margin-top:0.6rem;">
<div style="font-size:1.8rem; margin-bottom:0.4rem;">📚</div>
<div style="font-weight:700; color:#E2E8F0; font-size:0.9rem;">Your Study Vault is empty</div>
<div style="font-size:0.78rem; color:#94A3B8; margin-top:0.2rem;">Upload your first notes to build your private AI context.</div>
</div>"""
                st.markdown(empty_vault_html, unsafe_allow_html=True)

            st.markdown("---")

            # 👁 Vision Lab Glass Panel
            vision_header_html = """<div class="glass-panel" style="margin-bottom:0.8rem;">
<h4 style="margin:0 0 0.3rem 0; color:#F8FAFC; display:flex; align-items:center; gap:0.5rem; font-size:1.05rem;">
👁 Vision Lab
</h4>
<p style="color:#94A3B8; font-size:0.8rem; margin:0 0 0.6rem 0;">
Show EduMind what you're looking at (textbook question, handwritten problem, code error, math problem).
</p>
<div style="font-size:0.75rem; color:#C084FC; font-weight:600;">
Supported: JPG • PNG • WEBP (Max 15 MB)
</div>
</div>"""
            st.markdown(vision_header_html, unsafe_allow_html=True)

            img_file = st.file_uploader(
                "Upload Question Image",
                type=config.SUPPORTED_IMAGE_TYPES,
                key="vision_lab_uploader"
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
                st.markdown(f"""<div style="background:rgba(16,185,129,0.15); border:1px solid #10B981; border-radius:10px; padding:0.6rem; font-size:0.82rem; color:#D1FAE5; margin-bottom:0.5rem;">📷 Image Received • ● Attached for Analysis</div>""", unsafe_allow_html=True)
                if st.button("❌ Remove Attached Image", use_container_width=True, key="btn_remove_attached_img_vision"):
                    st.session_state.attached_image = None
                    st.rerun()

        # ======================================================================
        # RIGHT COLUMN (~65% Width) — 🧠 AI TUTOR & 3D NEURAL CORE
        # ======================================================================
        with col_tutor:
            # AI Context Pill Indicator
            doc_cnt = len(st.session_state.documents)
            context_status_text = f"● Connected ({doc_cnt} docs)" if doc_cnt > 0 else "○ No private material connected"
            ai_context_html = f"""<div class="ai-context-pill">
<span style="font-weight:700; color:#F8FAFC;">🧠 AI CONTEXT:</span>
<span class="context-badge">{context_status_text}</span>
<span class="context-badge">🎓 {st.session_state.current_subject}</span>
</div>"""
            st.markdown(ai_context_html, unsafe_allow_html=True)

            if len(st.session_state.messages) <= 1:
                hero_3d_html = f"""<div class="hero-ai-container" id="heroNeuralContainer">
<div class="neural-core-wrapper">
<div class="core-shadow-3d"></div>
<div class="neural-core-3d" id="neuralCore3D">
<div class="core-back-glow"></div>
<div class="orbit-ring-3d orbit-ring-1"></div>
<div class="orbit-ring-3d orbit-ring-2"></div>
<div class="orbit-ring-3d orbit-ring-3"></div>
<div class="core-glass-sphere">
<div class="core-specular-light"></div>
<div class="core-inner-energy">
<div class="energy-stream energy-stream-1"></div>
<div class="energy-stream energy-stream-2"></div>
<div class="energy-stream energy-stream-3"></div>
</div>
<div class="core-particles-3d">
<span class="p-3d p1">✦</span>
<span class="p-3d p2">•</span>
<span class="p-3d p3">✦</span>
<span class="p-3d p4">•</span>
<span class="p-3d p5">✦</span>
<span class="p-3d p6">•</span>
<span class="p-3d p7">✦</span>
<span class="p-3d p8">•</span>
</div>
<div class="core-center-symbol">✦</div>
</div>
</div>
</div>
<div class="ai-status-pill">
<span class="status-pulse-dot">●</span> READY TO LEARN
</div>
<div class="hero-ai-title">Hello, <span class="hero-ai-name">{student_display_name}</span> 👋</div>
<div class="hero-ai-subtitle">Your personal AI learning companion.</div>
<div style="color: #94A3B8; font-size: 0.9rem; margin-top: 0.3rem;">What would you like to master today? Ask any academic doubt, upload study material, or request a grounded quiz.</div>
</div>
<script>
(function() {{
    const container = document.getElementById('heroNeuralContainer');
    const core = document.getElementById('neuralCore3D');
    if (!container || !core) return;
    container.addEventListener('mousemove', (e) => {{
        const rect = container.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const deltaX = (e.clientX - centerX) / (rect.width / 2);
        const deltaY = (e.clientY - centerY) / (rect.height / 2);
        const tiltX = Math.max(-8, Math.min(8, -deltaY * 7));
        const tiltY = Math.max(-8, Math.min(8, deltaX * 7));
        core.style.transform = `rotateX(${{tiltX}}deg) rotateY(${{tiltY}}deg)`;
    }});
    container.addEventListener('mouseleave', () => {{
        core.style.transform = 'rotateX(0deg) rotateY(0deg)';
    }});
}})();
</script>"""
                st.markdown(hero_3d_html, unsafe_allow_html=True)

                st.markdown("<div style='margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 600; color: #94a3b8; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em;'>Quick Learning Actions</div>", unsafe_allow_html=True)
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                with s_col1:
                    if st.button("💡 Explain", key="ai_cmd_explain", use_container_width=True):
                        st.session_state["pending_prompt"] = f"Explain the fundamental concepts of {st.session_state.current_subject} with clear examples."
                        st.rerun()
                with s_col2:
                    if st.button("📄 Summarize", key="ai_cmd_summarize", use_container_width=True):
                        st.session_state["pending_prompt"] = f"Summarize the key concepts and definitions for {st.session_state.current_subject}."
                        st.rerun()
                with s_col3:
                    if st.button("🧠 Quiz Me", key="ai_cmd_quiz", use_container_width=True):
                        st.session_state["pending_prompt"] = "test my learning"
                        st.rerun()
                with s_col4:
                    if st.button("⚡ Practice", key="ai_cmd_practice", use_container_width=True):
                        st.session_state["pending_prompt"] = f"Provide 3 step-by-step practice problems with solutions for {st.session_state.current_subject}."
                        st.rerun()

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
                img_card_html = f"""<div class="image-preview-card"><div>📷 <b>Attached Question Image:</b> <code>{img_info['filename']}</code></div></div>"""
                st.markdown(img_card_html, unsafe_allow_html=True)
                st.image(img_info["bytes"], caption="Attached Question Image", width=220)

            user_prompt = st.chat_input("📎 Ask EduMind anything...")

            if not user_prompt and "pending_prompt" in st.session_state:
                user_prompt = st.session_state.pop("pending_prompt")

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
                                thinking_html = """<div class="ai-status-thinking"><span class="ai-status-pulse">◉</span> ANALYZING... Generating personalized quiz...</div>"""
                                st.markdown(thinking_html, unsafe_allow_html=True)
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
                                            vision_thinking_html = """<div class="ai-status-thinking"><span class="ai-status-pulse">◉</span> ANALYZING... Analyzing image with Gemini Vision...</div>"""
                                            st.markdown(vision_thinking_html, unsafe_allow_html=True)
                                            with st.spinner("Analyzing image with Gemini Vision..."):
                                                full_response = gemini_client.analyze_image_doubt(
                                                    image_bytes=img_bytes,
                                                    user_question=cleaned_prompt,
                                                    subject=st.session_state.current_subject
                                                )
                                                st.markdown(full_response)
                                                # Study reward for image doubt (+3 coins)
                                                CoinManager.claim_reward(
                                                    reward_id=f"img_doubt_{hash(img_payload['filename'])}",
                                                    amount=3,
                                                    reason="Asked question with image",
                                                    source="study"
                                                )
                                        else:
                                            # REAL RAG SEMANTIC RETRIEVAL PIPELINE
                                            matching_chunks = document_processor.search_documents(
                                                documents=st.session_state.documents,
                                                query=cleaned_prompt,
                                                subject=st.session_state.current_subject,
                                                top_k=config.TOP_K,
                                                user_id=st.session_state.user_id
                                            )

                                            # Check if student is asking about uploaded materials
                                            doc_keywords = ["notes", "pdf", "ppt", "document", "uploaded", "material", "slides", "page"]
                                            is_doc_query = any(k in prompt_lower for k in doc_keywords) or bool(st.session_state.documents)

                                            if is_doc_query and not matching_chunks:
                                                # Grounded Answer Policy
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

                                            # Claim study activity rewards
                                            CoinManager.claim_reward(
                                                reward_id=f"doubt_{hash(cleaned_prompt or 'img')}",
                                                amount=2,
                                                reason="Asked meaningful academic doubt",
                                                source="study"
                                            )
                                            CoinManager.claim_reward(
                                                reward_id=f"topic_complete_{topic_name}",
                                                amount=5,
                                                reason=f"Studied topic: {topic_name}",
                                                source="study"
                                            )
                                            CoinManager.record_study_activity("doubts")
                                            CoinManager.record_study_activity("topics_completed")

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
                            if not CoinManager.can_afford(config.HINT_COST):
                                st.warning(f"💰 **Not enough coins!** You need {config.HINT_COST} coins to use a hint. You have {st.session_state.coin_balance} coins.")
                            else:
                                if CoinManager.spend_coins(config.HINT_COST, "Quiz hint", "quiz", reference_id=f"hint_{q.id}"):
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
