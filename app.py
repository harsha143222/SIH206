"""
EduMind AI - Streamlit Application
Powered by Gemini AI Model Integration (google-genai SDK)
Smart Education Assistant | Smart India Hackathon 2026 (Problem Statement ID 26207)
"""

import os
import datetime
import secrets
import time
import uuid
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
        "👥 Study Spaces",
        "🎯 Aptitude Practice",
        "🎮 Educational Games",
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
# FEATURE 1 — AUTOMATIC MATERIAL OVERVIEW & MATERIAL-SPECIFIC QUIZ UI
# ==============================================================================
def strip_html_tags(text: str) -> str:
    """Strip raw HTML/script tags from string to extract plain text."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    text = re.sub(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'<[^>]+>', '', text)
    cleaned = cleaned.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    return cleaned.strip()


def render_material_overview_card(doc_data: Dict[str, Any]):
    """
    Render Feature 1: Automatic Material Overview + Grounded Material Quiz buttons.
    Renders styled HTML UI without raw HTML tags visible on screen.
    """
    if not doc_data or not isinstance(doc_data, dict):
        return

    ov = doc_data.get("overview")
    if not ov:
        ov = database.get_material_overview(doc_data.get("doc_id", ""))

    if isinstance(ov, str):
        try:
            import json
            ov = json.loads(ov)
        except Exception:
            ov = None

    if not isinstance(ov, dict):
        ov = {
            "document_title": doc_data.get("filename", "Uploaded Material"),
            "subject": doc_data.get("subject", config.DEFAULT_SUBJECT),
            "total_units": doc_data.get("total_units", 1),
            "main_topics": ["General Overview"],
            "key_concepts": ["Course Notes"],
            "recommended_order": ["1. Review material"],
            "exam_points": ["Key concepts in document"]
        }

    title = strip_html_tags(str(ov.get("document_title") or doc_data.get("filename", "Study Material")))
    subject = strip_html_tags(str(ov.get("subject") or doc_data.get("subject", config.DEFAULT_SUBJECT)))
    total_units = ov.get("total_units") or doc_data.get("total_units", 1)
    file_type = doc_data.get("file_type", "PDF/PPT")
    unit_label = "Slides" if str(file_type).upper() in ["PPT", "PPTX"] else "Pages"

    def clean_items(raw_data: Any, fallback: List[str]) -> List[str]:
        if isinstance(raw_data, list):
            res = [strip_html_tags(str(x)) for x in raw_data if strip_html_tags(str(x))]
            return res if res else fallback
        elif isinstance(raw_data, str) and raw_data.strip():
            clean = strip_html_tags(raw_data)
            return [clean] if clean else fallback
        return fallback

    main_topics = clean_items(ov.get("main_topics"), ["General Overview"])
    key_concepts = clean_items(ov.get("key_concepts"), ["Course Notes"])
    rec_order = clean_items(ov.get("recommended_order"), ["1. Review material"])
    exam_points = clean_items(ov.get("exam_points"), ["Key concepts in document"])

    import html
    topics_html = "".join(f"<li style='margin-bottom: 0.35rem;'><b>{html.escape(t)}</b></li>" for t in main_topics)
    concepts_html = "".join(f"<li style='margin-bottom: 0.35rem;'>{html.escape(c)}</li>" for c in key_concepts)
    order_html = "".join(f"<li style='margin-bottom: 0.35rem;'>{html.escape(o)}</li>" for o in rec_order)
    exam_html = "".join(f"<li style='margin-bottom: 0.35rem;'>{html.escape(p)}</li>" for p in exam_points)

    card_html = f"""
    <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%); border: 1.5px solid rgba(99, 102, 241, 0.45); border-radius: 16px; padding: 1.4rem; margin-bottom: 1.2rem; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.35);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.9rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); padding-bottom: 0.6rem; flex-wrap: wrap; gap: 0.5rem;">
            <div>
                <h3 style="color: #60A5FA; margin: 0; font-size: 1.3rem;">📄 {html.escape(title)}</h3>
                <div style="font-size: 0.88rem; color: #94A3B8; margin-top: 0.2rem;">Subject: <b>{html.escape(subject)}</b> • <b>{total_units} {unit_label}</b> parsed & indexed</div>
            </div>
            <div>
                <span class="badge-pill badge-strong">● AI Overview Generated</span>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-bottom: 0.8rem;">
            <div style="background: rgba(30, 41, 59, 0.7); padding: 1rem; border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.15);">
                <h4 style="color: #818CF8; margin-top: 0; margin-bottom: 0.4rem; font-size: 0.95rem;">📌 Main Topics:</h4>
                <ul style="margin: 0; padding-left: 1.1rem; color: #E2E8F0; font-size: 0.88rem; line-height: 1.4;">
                    {topics_html}
                </ul>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); padding: 1rem; border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.15);">
                <h4 style="color: #34D399; margin-top: 0; margin-bottom: 0.4rem; font-size: 0.95rem;">💡 Key Concepts:</h4>
                <ul style="margin: 0; padding-left: 1.1rem; color: #E2E8F0; font-size: 0.88rem; line-height: 1.4;">
                    {concepts_html}
                </ul>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
            <div style="background: rgba(30, 41, 59, 0.7); padding: 1rem; border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.15);">
                <h4 style="color: #FBBF24; margin-top: 0; margin-bottom: 0.4rem; font-size: 0.95rem;">🗺️ Recommended Learning Order:</h4>
                <ol style="margin: 0; padding-left: 1.1rem; color: #E2E8F0; font-size: 0.88rem; line-height: 1.4;">
                    {order_html}
                </ol>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); padding: 1rem; border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.15);">
                <h4 style="color: #F87171; margin-top: 0; margin-bottom: 0.4rem; font-size: 0.95rem;">🎯 Important Exam Points:</h4>
                <ul style="margin: 0; padding-left: 1.1rem; color: #E2E8F0; font-size: 0.88rem; line-height: 1.4;">
                    {exam_html}
                </ul>
            </div>
        </div>

        <div style="background: rgba(99, 102, 241, 0.18); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 14px; padding: 0.9rem; text-align: center;">
            <h4 style="color: #F8FAFC; margin: 0 0 0.3rem 0;">Ready to test your understanding?</h4>
            <div style="color: #CBD5E1; font-size: 0.85rem;">Generate a personalized quiz grounded ONLY in this uploaded material.</div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    doc_key = doc_data.get("doc_id", f"doc_{hash(title)}")

    col_q1, col_q2 = st.columns([1, 1])
    with col_q1:
        num_q_sel = st.selectbox("Number of Questions", options=[5, 10, 20], index=0, key=f"num_q_sel_{doc_key}")
    with col_q2:
        diff_sel = st.selectbox("Difficulty Level", options=["Mixed", "Easy", "Medium", "Hard"], index=0, key=f"diff_sel_{doc_key}")

    btn_cq1, btn_cq2, btn_cq3 = st.columns(3)
    with btn_cq1:
        if st.button("📝 Start Quiz From This Material", type="primary", use_container_width=True, key=f"btn_quiz_mat_{doc_key}"):
            with st.spinner("Generating grounded material quiz via Gemini..."):
                try:
                    mat_quiz = quiz_engine.generate_material_specific_quiz(
                        doc_data=doc_data,
                        subject=subject,
                        num_questions=num_q_sel,
                        difficulty=diff_sel
                    )
                    st.session_state.current_quiz = mat_quiz
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

    with btn_cq2:
        if st.button("Start 5 Question Quiz", use_container_width=True, key=f"btn_q5_{doc_key}"):
            with st.spinner("Generating 5-question quiz..."):
                try:
                    mat_quiz = quiz_engine.generate_material_specific_quiz(
                        doc_data=doc_data,
                        subject=subject,
                        num_questions=5,
                        difficulty=diff_sel
                    )
                    st.session_state.current_quiz = mat_quiz
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

    with btn_cq3:
        if st.button("Ask AI Doubts", use_container_width=True, key=f"btn_ask_doubts_{doc_key}"):
            st.session_state.quiz_mode = False
            st.session_state.pending_prompt = f"I have a doubt regarding the uploaded material '{title}'."
            st.rerun()


# ==============================================================================
# FEATURE 2 — SHARED STUDY SPACE DASHBOARD RENDERER
# ==============================================================================
def render_study_spaces_page():
    """
    Feature 2 — Shared Study Space UI Implementation.
    """
    user_id = st.session_state.get("user_id", "user_default")
    user_name = st.session_state.get("display_name", st.session_state.get("user_name", "Student"))
    username = st.session_state.get("username", "student")

    st.subheader("👥 Shared Study Spaces")
    st.caption("Collaborate with peers, share study materials, ask the AI Tutor doubts, participate in group discussions, and take shared quizzes!")

    # Check for invite token in URL or session state
    invite_param = st.query_params.get("invite") or st.query_params.get("join_group")
    if invite_param and "active_invite_processed" not in st.session_state:
        space_inv = database.get_study_space_by_token(invite_param)
        if space_inv:
            is_mem = database.is_study_space_member(space_inv["space_id"], user_id)
            if is_mem:
                st.session_state["active_space_id"] = space_inv["space_id"]
                st.session_state["active_invite_processed"] = True
            else:
                st.markdown(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.95); border: 2px solid #60A5FA; border-radius: 16px; padding: 1.8rem; margin-bottom: 1.5rem;">
                        <h2 style="color: #60A5FA; margin-top: 0;">👥 You've been invited to join a Study Space!</h2>
                        <h3 style="color: #F8FAFC; margin-bottom: 0.4rem;">{space_inv['name']}</h3>
                        <div style="color: #94A3B8; margin-bottom: 0.4rem;">📚 Subject: <b>{space_inv['subject']}</b></div>
                        <div style="color: #94A3B8; margin-bottom: 0.4rem;">👤 Created by: <b>{space_inv['owner_username']}</b></div>
                        <div style="color: #94A3B8; margin-bottom: 1rem;">📝 Description: {space_inv.get('description') or 'No description provided.'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                c_j1, c_j2 = st.columns(2)
                with c_j1:
                    if st.button("➕ Join Study Space Now", type="primary", use_container_width=True):
                        database.add_study_space_member(space_inv["space_id"], user_id, user_name, role="member")
                        st.session_state["active_space_id"] = space_inv["space_id"]
                        st.session_state["active_invite_processed"] = True
                        if "invite" in st.query_params:
                            del st.query_params["invite"]
                        if "join_group" in st.query_params:
                            del st.query_params["join_group"]
                        st.success(f"🎉 Successfully joined '{space_inv['name']}'!")
                        st.rerun()
                with c_j2:
                    if st.button("Dismiss", use_container_width=True):
                        st.session_state["active_invite_processed"] = True
                        st.rerun()
                return

    # Load User's Study Spaces from persistent SQLite DB
    user_spaces = database.get_user_study_spaces(user_id)

    # Top action bar: Create New Space / Join via Token
    col_act1, col_act2 = st.columns([1, 1])
    with col_act1:
        with st.expander("➕ Create New Study Space", expanded=(len(user_spaces) == 0)):
            with st.form("create_study_space_form"):
                space_name = st.text_input("Study Space Name", placeholder="e.g. DSA Placement Preparation")
                space_subj = st.text_input("Academic Subject", value=st.session_state.current_subject)
                space_desc = st.text_area("Description (Optional)", placeholder="What is this study space for?")
                submit_create = st.form_submit_button("Create Study Space ✅", type="primary", use_container_width=True)

                if submit_create:
                    if not space_name.strip():
                        st.error("Please enter a study space name.")
                    else:
                        new_space_id = f"space_{uuid.uuid4().hex[:12]}"
                        new_invite_token = secrets.token_urlsafe(16)
                        space_data = database.create_study_space(
                            space_id=new_space_id,
                            owner_user_id=user_id,
                            owner_username=user_name,
                            name=space_name.strip(),
                            subject=space_subj.strip(),
                            description=space_desc.strip(),
                            invite_token=new_invite_token
                        )
                        st.session_state["active_space_id"] = new_space_id
                        st.session_state["just_created_token"] = new_invite_token
                        st.success(f"✅ Study Space '{space_name}' created successfully!")
                        st.rerun()

    with col_act2:
        with st.expander("🔑 Join via Invite Token / Link"):
            with st.form("join_study_space_token_form"):
                input_token = st.text_input("Enter Invite Token or Full Link", placeholder="e.g. 7f4a8c9d...")
                submit_join_tok = st.form_submit_button("Join Space 🚀", use_container_width=True)

                if submit_join_tok and input_token.strip():
                    raw = input_token.strip()
                    tok = raw.split("invite=")[-1].split("join_group=")[-1].split("/")[-1].strip()
                    sp = database.get_study_space_by_token(tok)
                    if sp:
                        database.add_study_space_member(sp["space_id"], user_id, user_name, role="member")
                        st.session_state["active_space_id"] = sp["space_id"]
                        st.success(f"🎉 Successfully joined '{sp['name']}'!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid or expired invite token.")

    st.markdown("---")

    if not user_spaces:
        st.info("💡 You haven't joined or created any study spaces yet. Create your first Study Space or join one using an invite link above!")
        return

    # Select Active Study Space
    space_options = {s["space_id"]: f"👥 {s['name']} ({s['subject']})" for s in user_spaces}
    active_space_id = st.session_state.get("active_space_id")
    if active_space_id not in space_options:
        active_space_id = user_spaces[0]["space_id"]
        st.session_state["active_space_id"] = active_space_id

    selected_space_id = st.selectbox(
        "Select Active Study Space:",
        options=list(space_options.keys()),
        format_func=lambda sid: space_options[sid],
        index=list(space_options.keys()).index(active_space_id),
        key="space_selector_box"
    )
    st.session_state["active_space_id"] = selected_space_id

    space = database.get_study_space_by_id(selected_space_id)
    if not space:
        st.error("Study space not found or has been deleted.")
        return

    # BACKEND SECURITY GATE: Enforce Membership Validation
    if not database.is_study_space_member(selected_space_id, user_id):
        st.error("🔒 Security Gate: You are not authorized to view this Study Space.")
        return

    is_owner = database.is_study_space_owner(selected_space_id, user_id)
    members = database.get_study_space_members(selected_space_id)

    # Shareable Invite Token link display
    invite_token = space["invite_token"]
    invite_url = f"http://localhost:8501/?invite={invite_token}"

    st.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 16px; padding: 1.4rem; margin-bottom: 1.2rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="color: #F8FAFC; margin:0 0 0.3rem 0;">👥 {space['name']}</h2>
                    <div style="color: #94A3B8; font-size: 0.95rem;">
                        Subject: <b>{space['subject']}</b> | Members: <b>{len(members)}</b> | Owner: <b>{space['owner_username']}</b> {'👑' if is_owner else ''}
                    </div>
                    {f"<div style='color: #CBD5E1; font-size: 0.88rem; margin-top: 0.4rem;'>{space['description']}</div>" if space.get('description') else ''}
                </div>
                <div>
                    <span class="badge-pill badge-strong">● Persistent Storage</span>
                </div>
            </div>
            <div style="margin-top: 1rem; background: rgba(30, 41, 59, 0.7); border-radius: 10px; padding: 0.8rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
                <div style="font-size: 0.85rem; color: #E2E8F0;">
                    🔗 <b>Shareable Invite Link:</b> <code>{invite_url}</code>
                </div>
                <div>
                    <button onclick="navigator.clipboard.writeText('{invite_url}'); alert('📋 Invite link copied!');" style="background:#3B82F6; color:#FFF; border:none; padding:6px 14px; border-radius:6px; font-weight:600; cursor:pointer;">
                        📋 Copy Link
                    </button>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # TABS FOR STUDY SPACE
    tab_mats, tab_ai, tab_chat, tab_quiz, tab_mems, tab_act = st.tabs([
        "📚 Materials",
        "🤖 AI Tutor",
        "💬 Discussion",
        "📝 Quiz",
        "👥 Members",
        "📈 Space Activity"
    ])

    # 1. TAB: SHARED MATERIALS
    with tab_mats:
        st.markdown("### 📚 Shared Study Materials")
        st.caption("Upload course materials into this Study Space. Materials uploaded here are isolated specifically to this Study Space.")

        col_up1, col_up2 = st.columns([1.5, 1])
        with col_up1:
            shared_files = st.file_uploader(
                "Upload PDF/PPT/PPTX to Study Space",
                type=config.SUPPORTED_FILE_TYPES,
                accept_multiple_files=True,
                key=f"space_file_uploader_{selected_space_id}"
            )
            if shared_files:
                for sf in shared_files:
                    existing_docs = database.get_study_space_documents(selected_space_id, user_id)
                    already = any(d["filename"] == sf.name for d in existing_docs)
                    if not already:
                        with st.spinner(f"📖 Parsing & indexing '{sf.name}' into Study Space..."):
                            try:
                                file_bytes = sf.read()
                                sdoc_data = document_processor.process_study_space_file(
                                    file_bytes=file_bytes,
                                    filename=sf.name,
                                    space_id=selected_space_id,
                                    subject=space["subject"],
                                    uploaded_by=user_id,
                                    uploaded_by_name=user_name
                                )
                                st.success(f"✅ Shared: '{sf.name}' ({sdoc_data['total_units']} chunks)")
                                database.log_study_space_activity(
                                    f"act_{selected_space_id}_{sf.name}",
                                    selected_space_id,
                                    user_id,
                                    user_name,
                                    "upload",
                                    f"{user_name} uploaded shared material '{sf.name}'"
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Upload failed: {str(e)}")

        space_docs = database.get_study_space_documents(selected_space_id, user_id)
        if space_docs:
            st.markdown("#### 📄 Shared Files List:")
            for d in space_docs:
                with st.expander(f"📄 {d['filename']} ({d['file_size_mb']} MB, {d['total_units']} units) — Uploaded by {d['uploaded_by_name']}"):
                    ov = database.get_material_overview(d["doc_id"])
                    if ov:
                        st.markdown(f"**Main Topics:** {', '.join(ov.get('main_topics', []))}")
                        st.markdown(f"**Key Concepts:** {', '.join(ov.get('key_concepts', []))}")
                        st.markdown(f"**Exam Focus:** {', '.join(ov.get('exam_points', []))}")

                    if is_owner or str(d["uploaded_by"]) == str(user_id):
                        if st.button(f"🗑️ Delete {d['filename']}", key=f"del_doc_{d['doc_id']}"):
                            database.delete_study_space_document(d["doc_id"], selected_space_id, user_id)
                            st.success("Document deleted.")
                            st.rerun()
        else:
            st.info("No shared study materials uploaded to this space yet.")

    # 2. TAB: AI STUDY ASSISTANT (ISOLATED RAG)
    with tab_ai:
        st.markdown("### 🤖 AI Study Assistant (Space Grounded)")
        st.caption("Ask any academic doubt about the shared materials in this Study Space. EduMind AI will answer grounded ONLY in this space's materials.")

        space_chats_key = f"space_ai_chats_{selected_space_id}"
        if space_chats_key not in st.session_state:
            st.session_state[space_chats_key] = [
                {"role": "assistant", "content": f"Hello! I am your AI Study Assistant for **{space['name']}**. Ask me any doubt about your shared materials!"}
            ]

        for m in st.session_state[space_chats_key]:
            avatar = "🎓" if m["role"] == "assistant" else "👤"
            with st.chat_message(m["role"], avatar=avatar):
                st.markdown(m["content"])

        ai_input = st.chat_input("Ask AI doubt regarding shared space materials...", key=f"space_ai_input_{selected_space_id}")
        if ai_input and ai_input.strip():
            cleaned_q = ai_input.strip()
            st.session_state[space_chats_key].append({"role": "user", "content": cleaned_q})
            with st.chat_message("user", avatar="👤"):
                st.markdown(cleaned_q)

            with st.chat_message("assistant", avatar="🎓"):
                with st.spinner("Searching shared materials & thinking..."):
                    space_user_id = f"space_{selected_space_id}"
                    matching_chunks = document_processor.search_documents(
                        documents=None,
                        query=cleaned_q,
                        subject=space["subject"],
                        top_k=config.TOP_K,
                        user_id=space_user_id
                    )

                    doc_context = document_processor.format_context_for_prompt(matching_chunks) if matching_chunks else ""
                    
                    if not doc_context:
                        resp_text = "I couldn't find relevant information in the shared materials of this Study Space."
                        st.markdown(resp_text)
                    else:
                        stream = gemini_client.generate_chat_response_stream(
                            messages=st.session_state[space_chats_key],
                            document_context=doc_context,
                            subject=space["subject"]
                        )
                        resp_text = st.write_stream(stream)
                        if matching_chunks:
                            cite_str = "\n\n📚 **Source:** " + ", ".join(
                                f"`{c.get('filename', 'Doc')} — {c.get('unit_label', 'Page 1')}`" for c in matching_chunks
                            )
                            st.markdown(cite_str)
                            resp_text += cite_str

                    st.session_state[space_chats_key].append({"role": "assistant", "content": resp_text})
                    
                    database.log_study_space_activity(
                        f"act_ai_{selected_space_id}_{int(time.time())}",
                        selected_space_id,
                        user_id,
                        user_name,
                        "doubt",
                        f"{user_name} asked AI doubt: '{cleaned_q[:50]}...'"
                    )

    # 3. TAB: PERSISTENT GROUP CHAT WITH THOUGHT TAGS & REACTIONS & POLLING
    with tab_chat:
        st.markdown("### 💬 Persistent Group Discussion & Thought Box")

        col_ref1, col_ref2 = st.columns([4, 1])
        with col_ref2:
            if st.button("🔄 Refresh Messages", key=f"btn_ref_msg_{selected_space_id}"):
                st.rerun()

        # Load persistent messages from SQLite DB
        messages_list = database.get_study_space_messages(selected_space_id, user_id, limit=100)

        # Container for chat messages stream
        chat_box_container = st.container()

        with chat_box_container:
            if not messages_list:
                st.caption("No discussion messages yet. Start the conversation below!")
            else:
                for m in messages_list:
                    m_type = m.get("message_type", "chat")
                    tag_prefix = ""
                    card_style = "background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(148, 163, 184, 0.2);"
                    if m_type == "thought":
                        tag_prefix = "💡 <b>Thought:</b> "
                        card_style = "background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.4);"
                    elif m_type == "question":
                        tag_prefix = "❓ <b>Question:</b> "
                        card_style = "background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.4);"
                    elif m_type == "helpful":
                        tag_prefix = "✅ <b>Helpful Tip:</b> "
                        card_style = "background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4);"
                    elif m_type == "important":
                        tag_prefix = "📌 <b>Important:</b> "
                        card_style = "background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.4);"

                    reactions = m.get("reactions", {})
                    react_html_parts = []
                    for emo, uids in reactions.items():
                        react_html_parts.append(f"<span style='background:rgba(99,102,241,0.2); padding:2px 6px; border-radius:6px; font-size:0.8rem; margin-right:4px;'>{emo} {len(uids)}</span>")
                    react_html = "".join(react_html_parts)

                    st.markdown(
                        f"""
                        <div style="{card_style} border-radius: 12px; padding: 0.9rem 1.1rem; margin-bottom: 0.75rem;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.3rem;">
                                <div style="font-weight:700; color:#F8FAFC; font-size:0.92rem;">👤 {m['sender_name']}</div>
                                <div style="font-size:0.75rem; color:#94A3B8;">{m['created_at']}</div>
                            </div>
                            <div style="color:#E2E8F0; font-size:0.95rem; line-height:1.4;">
                                {tag_prefix}{m['message_text']}
                            </div>
                            {f"<div style='margin-top:0.4rem;'>{react_html}</div>" if react_html else ''}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Reaction Buttons
                    r_col1, r_col2, r_col3, r_col_space = st.columns([1, 1, 1, 7])
                    with r_col1:
                        if st.button("👍", key=f"react_like_{m['message_id']}"):
                            database.toggle_message_reaction(m['message_id'], selected_space_id, user_id, "👍")
                            st.rerun()
                    with r_col2:
                        if st.button("❤️", key=f"react_heart_{m['message_id']}"):
                            database.toggle_message_reaction(m['message_id'], selected_space_id, user_id, "❤️")
                            st.rerun()
                    with r_col3:
                        if st.button("💡", key=f"react_idea_{m['message_id']}"):
                            database.toggle_message_reaction(m['message_id'], selected_space_id, user_id, "💡")
                            st.rerun()

        st.markdown("---")
        with st.form(f"send_message_form_{selected_space_id}"):
            col_in1, col_in2 = st.columns([4, 1])
            with col_in1:
                new_msg = st.text_input("Type message...", placeholder="Share thoughts, ask questions...", label_visibility="collapsed")
            with col_in2:
                msg_category = st.selectbox("Type", options=["💬 Chat", "💡 Thought", "❓ Question", "✅ Helpful", "📌 Important"], label_visibility="collapsed")

            submit_msg = st.form_submit_button("Send 📤", type="primary", use_container_width=True)
            if submit_msg and new_msg.strip():
                cat_type = "chat"
                if "Thought" in msg_category:
                    cat_type = "thought"
                elif "Question" in msg_category:
                    cat_type = "question"
                elif "Helpful" in msg_category:
                    cat_type = "helpful"
                elif "Important" in msg_category:
                    cat_type = "important"

                msg_id = f"msg_{selected_space_id}_{uuid.uuid4().hex[:10]}"
                database.save_study_space_message(
                    message_id=msg_id,
                    space_id=selected_space_id,
                    user_id=user_id,
                    sender_name=user_name,
                    message_text=new_msg.strip(),
                    message_type=cat_type
                )
                database.log_study_space_activity(
                    f"act_msg_{msg_id}",
                    selected_space_id,
                    user_id,
                    user_name,
                    "chat",
                    f"{user_name} posted a {cat_type}"
                )
                st.rerun()

    # 4. TAB: SHARED GROUP QUIZ
    with tab_quiz:
        st.markdown("### 📝 Shared Group Quiz")
        st.caption("Generate a shared quiz derived strictly from shared Study Space materials. Each member takes an independent attempt.")

        if st.button("✨ Generate New Group Quiz", type="primary", key=f"btn_gen_group_quiz_{selected_space_id}"):
            with st.spinner("Generating shared group quiz from space materials..."):
                try:
                    g_quiz = quiz_engine.generate_study_space_quiz(selected_space_id, subject=space["subject"], num_questions=5, difficulty="Mixed", user_id=user_id)
                    database.save_study_space_quiz(
                        quiz_id=g_quiz.quiz_id,
                        space_id=selected_space_id,
                        created_by=user_name,
                        title=g_quiz.title,
                        questions=[q.to_dict() for q in g_quiz.questions]
                    )
                    st.success(f"✅ Generated Group Quiz: '{g_quiz.title}'!")
                    st.rerun()
                except quiz_engine.GroundedQuizError as e:
                    st.warning(f"⚠️ {str(e)}")
                except Exception as e:
                    st.error(f"Failed to generate group quiz: {str(e)}")

        space_quizzes = database.get_study_space_quizzes(selected_space_id, user_id)
        if space_quizzes:
            st.markdown("#### 📝 Available Group Quizzes:")
            for gq in space_quizzes:
                st.markdown(f"**{gq['title']}** (Created by {gq['created_by']} on {gq['created_at']})")
                if st.button(f"▶️ Take Quiz ({gq['quiz_id'][:8]})", key=f"take_gq_{gq['quiz_id']}"):
                    questions_objs = []
                    for idx, qd in enumerate(gq["questions"], 1):
                        questions_objs.append(
                            quiz_engine.QuizQuestion(
                                q_id=idx,
                                subject=space["subject"],
                                topic=qd.get("topic", space["subject"]),
                                subtopic=qd.get("subtopic", ""),
                                difficulty=qd.get("difficulty", "Medium"),
                                coin_reward=qd.get("coin_reward", 10),
                                question=qd["question"],
                                options=qd["options"],
                                correct_index=qd["correct_index"],
                                explanation=qd.get("explanation", ""),
                                source_citation=qd.get("source_citation", "")
                            )
                        )
                    active_g_quiz = quiz_engine.Quiz(
                        subject=space["subject"],
                        title=gq["title"],
                        topics_covered=[space["subject"]],
                        questions=questions_objs
                    )
                    active_g_quiz.quiz_id = gq["quiz_id"]
                    st.session_state.current_quiz = active_g_quiz
                    st.session_state.quiz_mode = True
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_hints_used = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_index = 0
                    st.rerun()
                st.markdown("---")
        else:
            st.info("No group quizzes created in this Study Space yet.")

    # 5. TAB: MEMBERS MANAGEMENT
    with tab_mems:
        st.markdown("### 👥 Study Space Members")
        for m in members:
            r_tag = "👑 Owner" if m["role"] == "owner" else "👤 Member"
            st.markdown(f"- **{m['username']}** ({r_tag}) — Joined {m['joined_at']}")
            if is_owner and m["role"] != "owner":
                if st.button(f"❌ Remove {m['username']}", key=f"btn_rem_mem_{m['user_id']}"):
                    database.remove_study_space_member(selected_space_id, user_id, m["user_id"])
                    st.success(f"Removed {m['username']}")
                    st.rerun()

        if is_owner:
            st.markdown("---")
            st.markdown("#### ⚙️ Owner Settings")
            col_ow1, col_ow2 = st.columns(2)
            with col_ow1:
                if st.button("🔄 Regenerate Invite Link", key=f"btn_regen_tok_{selected_space_id}"):
                    new_tok = secrets.token_urlsafe(16)
                    database.regenerate_invite_token(selected_space_id, user_id, new_tok)
                    st.success("Regenerated invite token!")
                    st.rerun()
            with col_ow2:
                if st.button("🗑️ Delete Study Space", type="primary", key=f"btn_del_space_{selected_space_id}"):
                    database.delete_study_space(selected_space_id, user_id)
                    st.success("Study Space deleted.")
                    st.rerun()

    # 6. TAB: SPACE ACTIVITY & AGGREGATE ANALYTICS
    with tab_act:
        st.markdown("### 📈 Space Aggregate Analytics")
        agg = database.get_study_space_aggregate_analytics(selected_space_id, user_id)

        a_col1, a_col2, a_col3, a_col4, a_col5 = st.columns(5)
        a_col1.metric("Members", agg.get("member_count", 0))
        a_col2.metric("Shared Materials", agg.get("shared_documents_count", 0))
        a_col3.metric("Shared Quizzes", agg.get("shared_quizzes_count", 0))
        a_col4.metric("Messages", agg.get("messages_count", 0))
        a_col5.metric("Avg Quiz Score", f"{agg.get('average_group_quiz_score', 0)}%")

        st.markdown("---")
        st.markdown("### 📋 Recent Space Activity Feed")
        activities = database.get_study_space_activity(selected_space_id, user_id, limit=30)
        if activities:
            for act in activities:
                st.markdown(f"• **{act['username']}** {act['description']} <span style='font-size:0.75rem; color:#94A3B8;'>({act['created_at']})</span>", unsafe_allow_html=True)
        else:
            st.caption("No recorded activities yet.")


def render_friends_dashboard():
    render_study_spaces_page()


current_page = st.session_state.get("current_page", nav_mode)

if "Admin" in current_page:
    render_admin_analytics_page()
elif "My Analytics" in current_page:
    render_student_analytics_page()
elif "Dashboard" in current_page:
    render_dashboard_page()
elif "Study Spaces" in current_page or "Friends" in current_page:
    render_study_spaces_page()
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
</div>"""
            st.markdown(ai_context_html, unsafe_allow_html=True)

            if st.session_state.documents:
                latest_doc = st.session_state.documents[-1]
                with st.expander(f"📖 Automatic Material Overview & Grounded Quiz: {latest_doc['filename']}", expanded=True):
                    render_material_overview_card(latest_doc)

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
