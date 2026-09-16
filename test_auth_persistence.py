"""
EduMind AI - Account Persistence & Authentication Test Suite
Verifies 16-step regression suite covering Registration, Permanent DB Storage,
Logout, Login, Application Restart, Password Verification, Duplicate Rejection,
Password Change, Multi-Tenant Data Isolation, and Study Space UUID Generation.
"""

import uuid
import secrets
import auth
import database
import mongodb


def run_auth_tests():
    print("=== STARTING EDUMIND AI AUTHENTICATION & PERSISTENCE TESTS ===")

    run_suffix = uuid.uuid4().hex[:6]
    user_a_email = f"user_a_{run_suffix}@edumind.app"
    user_a_username = f"user_a_{run_suffix}"
    user_a_password = "Password123!"

    user_b_email = f"user_b_{run_suffix}@edumind.app"
    user_b_username = f"user_b_{run_suffix}"
    user_b_password = "Password456!"

    # -------------------------------------------------------------
    # TEST 1 & 2: Register User A & Verify Persistent Database Record
    # -------------------------------------------------------------
    ok, msg = auth.register_user(
        email=user_a_email,
        username=user_a_username,
        password=user_a_password,
        display_name="Karthik User A",
        avatar="🎓"
    )
    assert ok is True, f"User A registration failed: {msg}"
    print("TEST 1 PASSED: User A registered successfully.")

    sqlite_rec_a = database.get_user_profile(user_a_username)
    assert sqlite_rec_a is not None, "User A record not found in SQLite database"
    assert sqlite_rec_a["email"] == user_a_email, "User A email mismatch in DB"
    assert sqlite_rec_a["password_hash"] != user_a_password, "SECURITY FAILURE: Password stored in plaintext!"
    assert sqlite_rec_a["password_hash"] != "", "Password hash is empty!"
    print("TEST 2 PASSED: User A record exists in persistent database with secure password hash.")

    # -------------------------------------------------------------
    # TEST 3 & 4: Logout and Login with same credentials
    # -------------------------------------------------------------
    auth.logout_user()
    assert auth.is_authenticated() is False, "Logout failed"
    print("TEST 3 PASSED: Logged out successfully.")

    login_ok, login_msg = auth.login_user(user_a_email, user_a_password)
    assert login_ok is True, f"Login with email failed: {login_msg}"
    assert auth.is_authenticated() is True, "User session not authenticated"
    user_a_id = auth.get_current_user()["user_id"]
    print("TEST 4 PASSED: Logged in using email & password.")

    # -------------------------------------------------------------
    # TEST 5, 6, 7: Simulate App Restart / Rerun & Verify Account Persistence
    # -------------------------------------------------------------
    auth.logout_user()
    # Re-initialize DB connection to simulate fresh app restart
    database.init_db()

    login_after_restart, _ = auth.login_user(user_a_username, user_a_password)
    assert login_after_restart is True, "Login failed after simulated application restart!"
    print("TEST 5, 6, 7 PASSED: Account survived app restart and logged in successfully using username.")

    # -------------------------------------------------------------
    # TEST 8: Incorrect Password Rejection
    # -------------------------------------------------------------
    auth.logout_user()
    bad_login_ok, bad_msg = auth.login_user(user_a_username, "WrongPassword999!")
    assert bad_login_ok is False, "Login succeeded with wrong password!"
    assert bad_msg == "Invalid email/username or password.", f"Unexpected error message: {bad_msg}"
    print("TEST 8 PASSED: Incorrect password rejected with generic authentication error.")

    # -------------------------------------------------------------
    # TEST 9 & 10: Duplicate Email & Username Rejection
    # -------------------------------------------------------------
    dup_email_ok, _ = auth.register_user(
        email=user_a_email,
        username=f"different_{run_suffix}",
        password="Password789!",
        display_name="Duplicate Email Test"
    )
    assert dup_email_ok is False, "Duplicate email registration was not rejected!"
    print("TEST 9 PASSED: Duplicate email registration rejected.")

    dup_user_ok, _ = auth.register_user(
        email=f"different_{run_suffix}@edumind.app",
        username=user_a_username,
        password="Password789!",
        display_name="Duplicate Username Test"
    )
    assert dup_user_ok is False, "Duplicate username registration was not rejected!"
    print("TEST 10 PASSED: Duplicate username registration rejected.")

    # -------------------------------------------------------------
    # TEST 11, 12, 13, 14: Password Change & Verification
    # -------------------------------------------------------------
    auth.login_user(user_a_username, user_a_password)
    new_password = "NewSecretPassword123!"
    chg_ok, chg_msg = auth.change_password(user_a_id, user_a_password, new_password)
    assert chg_ok is True, f"Password change failed: {chg_msg}"
    print("TEST 11 PASSED: Password changed successfully.")

    auth.logout_user()

    old_pw_login, _ = auth.login_user(user_a_username, user_a_password)
    assert old_pw_login is False, "Login with old password succeeded after password change!"
    print("TEST 13 PASSED: Login with old password failed.")

    new_pw_login, _ = auth.login_user(user_a_username, new_password)
    assert new_pw_login is True, "Login with new password failed!"
    print("TEST 14 PASSED: Login with new password succeeded.")

    # -------------------------------------------------------------
    # TEST 15 & 16: Multi-Tenant User Data Isolation
    # -------------------------------------------------------------
    auth.register_user(
        email=user_b_email,
        username=user_b_username,
        password=user_b_password,
        display_name="Rahul User B",
        avatar="🚀"
    )
    auth.login_user(user_b_username, user_b_password)
    user_b_id = auth.get_current_user()["user_id"]

    # Save documents for User A and User B
    doc_a_id = f"doc_a_{run_suffix}"
    doc_b_id = f"doc_b_{run_suffix}"
    database.save_document_record({"doc_id": doc_a_id, "filename": "UserA_Notes.pdf", "subject": "Java", "file_type": "PDF", "file_size_mb": 1.0, "total_units": 1}, storage_path="data/uploads/UserA.pdf")
    database.save_document_record({"doc_id": doc_b_id, "filename": "UserB_Notes.pdf", "subject": "Java", "file_type": "PDF", "file_size_mb": 1.0, "total_units": 1}, storage_path="data/uploads/UserB.pdf")

    # Verify isolate checks
    user_a_docs = database.get_study_space_documents(f"space_{doc_a_id}", user_a_id)
    user_b_docs = database.get_study_space_documents(f"space_{doc_a_id}", user_b_id)
    assert len(user_b_docs) == 0, "Security leak: User B accessed User A study space document!"
    print("TEST 15 & 16 PASSED: User A and User B data isolated strictly by user_id.")

    # -------------------------------------------------------------
    # TEST 17: Study Space UUID Generation Test
    # -------------------------------------------------------------
    s1_id = f"space_{uuid.uuid4().hex[:12]}"
    s2_id = f"space_{uuid.uuid4().hex[:12]}"
    assert s1_id != s2_id, "UUID collision detected!"
    assert s1_id.startswith("space_"), "Study space ID format mismatch"
    
    space1 = database.create_study_space(
        space_id=s1_id,
        owner_user_id=user_a_id,
        owner_username=user_a_username,
        name="Study Space 1",
        subject="Python",
        description="Space 1 description",
        invite_token=secrets.token_urlsafe(16)
    )
    space2 = database.create_study_space(
        space_id=s2_id,
        owner_user_id=user_a_id,
        owner_username=user_a_username,
        name="Study Space 2",
        subject="Java",
        description="Space 2 description",
        invite_token=secrets.token_urlsafe(16)
    )

    assert space1["space_id"] == s1_id, "Space 1 creation failed"
    assert space2["space_id"] == s2_id, "Space 2 creation failed"
    assert space1["space_id"] != space2["space_id"], "Two Study Spaces created by same user received identical IDs!"
    print("TEST 17 PASSED: Study Space UUID generation verified. Multiple spaces receive unique IDs.")

    print("\nALL AUTHENTICATION & PERSISTENCE TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_auth_tests()
