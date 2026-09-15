"""
EduMind AI - Authentication & Session Security Module
Manages secure password hashing, user registration, authentication, input validation,
and server-side session state tracking.
"""

import re
import logging
from typing import Tuple, Dict, Any, Optional
import streamlit as st
import config
import mongodb
import database

logger = logging.getLogger("auth")

# Password Hashing Utilities
try:
    import werkzeug
    from werkzeug.security import generate_password_hash, check_password_hash
    HAS_WERKZEUG = True
except ImportError:
    HAS_WERKZEUG = False

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

def hash_password(password: str) -> str:
    """Hash plaintext password securely using werkzeug, bcrypt, or pbkdf2_hmac."""
    if HAS_WERKZEUG:
        return generate_password_hash(password, method='pbkdf2:sha256')
    elif HAS_BCRYPT:
        salt = bcrypt.gensalt(12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    else:
        import hashlib
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), b'edumind_salt_2026', 100000).hex()

def verify_password(password: str, hashed: str) -> bool:
    """Verify plaintext password against stored password hash across all hashing engines."""
    if not password or not hashed:
        return False
    try:
        clean_pw = password
        clean_hash = hashed.strip()

        # 1. Check bcrypt hashes ($2a$, $2b$, $2y$)
        if clean_hash.startswith(('$2a$', '$2b$', '$2y$', '$2a', '$2b', '$2y')):
            if HAS_BCRYPT:
                return bcrypt.checkpw(clean_pw.encode('utf-8'), clean_hash.encode('utf-8'))
            elif HAS_WERKZEUG:
                try:
                    return check_password_hash(clean_hash, clean_pw)
                except Exception:
                    pass

        # 2. Check werkzeug hashes (pbkdf2, scrypt, sha256)
        if HAS_WERKZEUG and (':' in clean_hash or '$' in clean_hash):
            try:
                if check_password_hash(clean_hash, clean_pw):
                    return True
            except Exception:
                pass

        # 3. Check plain hashlib pbkdf2_hmac hex hash
        import hashlib
        computed = hashlib.pbkdf2_hmac('sha256', clean_pw.encode('utf-8'), b'edumind_salt_2026', 100000).hex()
        if computed == clean_hash:
            return True

        # 4. Fallback check_password_hash if HAS_WERKZEUG
        if HAS_WERKZEUG:
            try:
                return check_password_hash(clean_hash, clean_pw)
            except Exception:
                pass

        return False
    except Exception as e:
        logger.error("Error verifying password: %s", str(e))
        return False

# Input Validation
def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address format."""
    if not email or not email.strip():
        return False, "Email address is required."
    clean = email.strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, clean):
        return False, "Please enter a valid email address."
    return True, "Valid email"

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format (min 3 chars, alphanumeric or underscore)."""
    if not username or not username.strip():
        return False, "Username is required."
    clean = username.strip()
    if len(clean) < 3:
        return False, "Username must be at least 3 characters long."
    if not re.match(r"^[a-zA-Z0-9_]+$", clean):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, "Valid username"

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength (min 8 chars, 1 uppercase, 1 lowercase, 1 number)."""
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, "Strong password"

# Authentication Operations
def register_user(email: str, username: str, password: str, display_name: str = "", avatar: str = "🎓") -> Tuple[bool, str]:
    """Register a new student account."""
    val_e, msg_e = validate_email(email)
    if not val_e:
        return False, msg_e

    val_u, msg_u = validate_username(username)
    if not val_u:
        return False, msg_u

    val_p, msg_p = validate_password(password)
    if not val_p:
        return False, msg_p

    clean_email = email.strip().lower()
    clean_username = username.strip()
    clean_display_name = display_name.strip() if display_name and display_name.strip() else clean_username

    # Check MongoDB for duplicate email or username
    existing = mongodb.find_user_by_email_or_username(clean_email)
    if not existing:
        existing = mongodb.find_user_by_email_or_username(clean_username)

    if existing:
        return False, "An account with this email address or username already exists."

    # Also check SQLite fallback
    sqlite_user = database.get_user_profile(clean_username)
    if not sqlite_user:
        sqlite_user = database.get_user_profile(clean_email)

    if sqlite_user:
        return False, "An account with this email address or username already exists."

    pw_hash = hash_password(password)

    # Insert into MongoDB
    user_doc = mongodb.create_user(clean_email, clean_username, pw_hash)
    if user_doc:
        user_id = str(user_doc["_id"])
    else:
        user_id = f"usr_{clean_username}"

    # Initialize Profile with 100 coins & 1-day streak
    mongodb.create_or_update_profile(
        user_id=user_id,
        display_name=clean_display_name,
        avatar=avatar,
        bio="EduMind AI Scholar",
        coins=100,
        streak_days=1
    )

    # Sync with SQLite for dual compatibility
    database.save_user_profile(user_id, clean_username, 100, 1, "", email=clean_email, password_hash=pw_hash, display_name=clean_display_name)

    return True, "Account created successfully. Welcome to EduMind AI!"

def login_user(identifier: str, password: str) -> Tuple[bool, str]:
    """Authenticate user with email/username and password."""
    if not identifier or not password:
        return False, "Please enter both email/username and password."

    clean_id = identifier.strip()

    # Search MongoDB Atlas
    user = mongodb.find_user_by_email_or_username(clean_id)

    # Generic error message to prevent account enumeration
    invalid_msg = "Invalid email/username or password."

    if not user:
        # Fallback check SQLite if user created locally or MongoDB offline
        sqlite_user = database.get_user_profile(clean_id)
        if not sqlite_user:
            return False, invalid_msg
        
        # Check password hash if present
        stored_hash = sqlite_user.get("password_hash")
        if stored_hash:
            if not verify_password(password, stored_hash):
                return False, invalid_msg
        
        # Verify fallback
        user_id = sqlite_user["user_id"]
        username = sqlite_user.get("username", clean_id)
        display_name = sqlite_user.get("display_name") or username
        coins = sqlite_user.get("coin_balance", 100)
        streak = sqlite_user.get("streak_days", 1)
        email = sqlite_user.get("email") or f"{clean_id}@edumind.app"
        
        # Set session state
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.user_email = email
        st.session_state.username = username
        st.session_state.user_name = display_name
        st.session_state.display_name = display_name
        st.session_state.avatar = "🎓"
        st.session_state.user_bio = "EduMind AI Scholar"
        st.session_state.member_since = "September 2026"
        st.session_state.coin_balance = coins
        st.session_state.current_streak = streak
        return True, f"Welcome back, {display_name}!"

    # Verify password hash
    if not verify_password(password, user.get("password_hash", "")):
        return False, invalid_msg

    user_id = str(user["_id"])
    username = user["username"]
    email = user["email"]

    # Update last login timestamp
    mongodb.update_user_last_login(user_id)

    # Fetch profile and user details
    profile = mongodb.get_profile(user_id) or {}
    display_name = profile.get("display_name", username) or username
    coins = profile.get("coins", 100)
    streak = profile.get("streak_days", 1)
    avatar = profile.get("avatar", "🎓")
    bio = profile.get("bio", "EduMind AI Scholar")
    created_at = user.get("created_at") or profile.get("created_at") or "September 2026"

    # Format created_at to readable month-year
    if hasattr(created_at, "strftime"):
        member_since = created_at.strftime("%B %Y")
    else:
        member_since = str(created_at)

    # Populate server-side Streamlit session state
    st.session_state.authenticated = True
    st.session_state.user_id = user_id
    st.session_state.user_email = email
    st.session_state.username = username
    st.session_state.user_name = display_name
    st.session_state.display_name = display_name
    st.session_state.avatar = avatar
    st.session_state.user_bio = bio
    st.session_state.member_since = member_since
    st.session_state.coin_balance = coins
    st.session_state.current_streak = streak

    return True, f"Welcome back, {display_name}!"

def logout_user():
    """Clear authentication and user-specific session state."""
    keys_to_clear = [
        "authenticated", "user_id", "user_email", "username", "user_name",
        "display_name", "avatar", "user_bio", "member_since", "coin_balance",
        "rewarded_events", "coin_transactions", "messages", "documents",
        "learned_topics", "current_quiz", "quiz_mode", "active_group_id",
        "attached_image", "learning_streak", "current_streak", "coins",
        "aptitude_active", "game_score", "active_game_id"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.authenticated = False

def is_authenticated() -> bool:
    """Check if current session is authenticated."""
    return bool(st.session_state.get("authenticated", False) and st.session_state.get("user_id"))

def get_current_user() -> Dict[str, Any]:
    """Return dictionary of current authenticated user info."""
    if not is_authenticated():
        return {}
    return {
        "user_id": st.session_state.get("user_id"),
        "username": st.session_state.get("username"),
        "email": st.session_state.get("user_email"),
        "display_name": st.session_state.get("display_name", st.session_state.get("username")),
        "avatar": st.session_state.get("avatar", "🎓"),
        "bio": st.session_state.get("user_bio", "EduMind AI Scholar"),
        "member_since": st.session_state.get("member_since", "September 2026"),
        "coins": st.session_state.get("coin_balance", 100),
        "streak": st.session_state.get("current_streak", 1)
    }

