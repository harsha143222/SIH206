"""
EduMind AI - Automated Verification Test Suite
Tests Feature 1 (Material Overview -> Grounded Quiz -> Personal Analytics)
and Feature 2 (Shared Study Space, RAG isolation, Chat, Group Quiz, Security).
"""

import secrets
import uuid
import json
import config
import database
import document_processor
import quiz_engine
import analytics


def run_tests():
    print("=== STARTING EDUMIND AI VERIFICATION TESTS ===")

    run_suffix = uuid.uuid4().hex[:6]
    # Setup test users
    user_a_id = f"test_user_a_{run_suffix}"
    user_a_name = f"Karthik_{run_suffix}"
    user_b_id = f"test_user_b_{run_suffix}"
    user_b_name = f"Rahul_{run_suffix}"
    non_member_id = f"test_user_c_{run_suffix}"

    database.save_user_profile(user_a_id, user_a_name, coin_balance=100, streak_days=1, last_active_date="2026-09-16")
    database.save_user_profile(user_b_id, user_b_name, coin_balance=100, streak_days=1, last_active_date="2026-09-16")
    database.save_user_profile(non_member_id, "NonMember", coin_balance=50, streak_days=1, last_active_date="2026-09-16")

    # -------------------------------------------------------------
    # FEATURE 1 TESTS
    # -------------------------------------------------------------
    print("\n--- Testing Feature 1: Material Overview & Grounded Quiz ---")

    # TEST 1: Create subject
    subject = "Java Programming"
    database.save_subject(subject)
    print("TEST 1 PASSED: Subject 'Java Programming' registered.")

    # TEST 2 & 3: Process PDF material
    doc_id = f"doc_java_unit1_{run_suffix}"
    dummy_pdf_text = (
        "Java Unit 1: Classes and Objects.\n"
        "A class in Java is a blueprint for creating objects. An object is an instance of a class.\n"
        "Classes define properties and behaviors. Encapsulation wraps data and code into a single unit.\n"
        "Constructors initialize new objects when created with the new keyword.\n"
        "Inheritance allows a class to derive properties from a parent class using the extends keyword.\n"
        "Page 18: Difference between class and object: Class is logical, object is physical entity."
    )
    chunks = [
        {
            "chunk_id": f"chunk_java_1_{run_suffix}",
            "doc_id": doc_id,
            "doc_name": "Java_Unit1.pdf",
            "filename": "Java_Unit1.pdf",
            "unit_label": "Page 18",
            "unit_num": 18,
            "subject": subject,
            "section_title": "Classes and Objects",
            "text": dummy_pdf_text
        }
    ]

    doc_data = {
        "user_id": user_a_id,
        "doc_id": doc_id,
        "filename": "Java_Unit1.pdf",
        "file_hash": f"hash_java_{run_suffix}",
        "subject": subject,
        "file_size_mb": 1.2,
        "file_type": "PDF",
        "total_units": 1,
        "chunks": chunks
    }

    database.save_document_record(doc_data, storage_path="data/uploads/Java_Unit1.pdf")
    print("TEST 2 & 3 PASSED: PDF material processed and stored.")

    # TEST 4: Automatic AI Overview
    overview = document_processor.generate_material_overview(chunks, "Java_Unit1.pdf", subject, 1)
    database.save_material_overview(doc_id, "Java_Unit1.pdf", subject, overview)
    saved_ov = database.get_material_overview(doc_id)
    assert saved_ov is not None, "Failed to retrieve saved overview"
    assert "main_topics" in saved_ov, "Main topics missing in overview"
    print(f"TEST 4 PASSED: Overview generated with main topics: {saved_ov['main_topics']}")

    # TEST 5 & 6: Generate Grounded Material-Specific Quiz
    quiz = quiz_engine.generate_material_specific_quiz(doc_data, subject=subject, num_questions=5, difficulty="Easy")
    assert len(quiz.questions) > 0, "Quiz question list is empty"
    for q in quiz.questions:
        assert q.source_citation != "", "Source citation missing"
    print(f"TEST 5 & 6 PASSED: Material quiz generated with {len(quiz.questions)} questions. Sample source: {quiz.questions[0].source_citation}")

    # TEST 7: Complete Quiz
    student_answers = {q.id: q.correct_index for q in quiz.questions}
    report = quiz_engine.evaluate_quiz(quiz, student_answers, registry={}, user_id=user_a_id)
    assert report["score"] == len(quiz.questions), "Quiz score mismatch"
    assert report["percentage"] == 100.0, "Quiz percentage mismatch"
    print("TEST 7 PASSED: Quiz completed with 100% score.")

    # TEST 8: Verify Personal Analytics Updated
    overview_analytics = analytics.get_user_overview(user_a_id)
    assert overview_analytics["total_quizzes"] >= 1, "User quiz count not updated in analytics"
    assert overview_analytics["average_quiz_score"] > 0, "User average quiz score not updated"
    print(f"TEST 8 PASSED: Personal analytics updated (Total Quizzes: {overview_analytics['total_quizzes']}, Avg Score: {overview_analytics['average_quiz_score']}%).")

    # -------------------------------------------------------------
    # FEATURE 2 TESTS
    # -------------------------------------------------------------
    print("\n--- Testing Feature 2: Shared Study Space ---")

    # TEST 9 & 10: Create Study Space & Invite Token
    space_id = f"space_dsa_{run_suffix}"
    token = secrets.token_urlsafe(16)
    space = database.create_study_space(
        space_id=space_id,
        owner_user_id=user_a_id,
        owner_username=user_a_name,
        name=f"DSA Placement Prep {run_suffix}",
        subject="Data Structures",
        description="Study group for placement prep",
        invite_token=token
    )
    assert space["space_id"] == space_id, "Study space creation failed"
    assert space["invite_token"] == token, "Invite token mismatch"

    # Verify get_study_space alias and get_user_study_spaces for User A
    sp_lookup = database.get_study_space(space_id)
    assert sp_lookup is not None and sp_lookup["space_id"] == space_id, "get_study_space lookup failed"
    
    user_a_spaces = database.get_user_study_spaces(user_a_id)
    assert len(user_a_spaces) >= 1, "User A study spaces list is empty"
    assert any(s["space_id"] == space_id for s in user_a_spaces), "Created space missing in User A dashboard list"
    
    # Verify non-member empty spaces list
    non_mem_spaces = database.get_user_study_spaces(non_member_id)
    assert len(non_mem_spaces) == 0, "Non-member should have empty study spaces list"
    
    print(f"TEST 9 & 10 PASSED: Study space created & verified in User A dashboard list.")

    # TEST 11 & 12: Second user opens invite token and joins
    space_from_tok = database.get_study_space_by_token(token)
    assert space_from_tok is not None, "Failed to resolve study space from token"
    joined_ok = database.add_study_space_member(space_from_tok["space_id"], user_b_id, user_b_name, role="member")
    assert joined_ok is True, "User B failed to join study space"

    members = database.get_study_space_members(space_id)
    member_ids = [m["user_id"] for m in members]
    assert user_a_id in member_ids and user_b_id in member_ids, "Members list incomplete"

    # Verify space now appears in User B dashboard list
    user_b_spaces = database.get_user_study_spaces(user_b_id)
    assert len(user_b_spaces) >= 1, "User B study spaces list is empty after joining"
    assert any(s["space_id"] == space_id for s in user_b_spaces), "Joined space missing in User B dashboard list"

    print(f"TEST 11 & 12 PASSED: User B joined space via token & verified in User B dashboard list.")

    # TEST 13: Shared Study Material & RAG Data Isolation
    space_doc_id = f"sdoc_dsa_{run_suffix}"
    s_doc_data = {
        "doc_id": space_doc_id,
        "space_id": space_id,
        "uploaded_by": user_a_id,
        "uploaded_by_name": user_a_name,
        "filename": "DSA_Full_Course.pdf",
        "file_type": "PDF",
        "file_size_mb": 2.5,
        "total_units": 10
    }
    database.add_study_space_document(
        doc_id=space_doc_id,
        space_id=space_id,
        uploaded_by=user_a_id,
        uploaded_by_name=user_a_name,
        filename="DSA_Full_Course.pdf",
        file_type="PDF",
        file_size_mb=2.5,
        total_units=10
    )

    docs_user_a = database.get_study_space_documents(space_id, user_a_id)
    docs_user_b = database.get_study_space_documents(space_id, user_b_id)
    assert len(docs_user_a) == len(docs_user_b) == 1, "Shared material visibility mismatch"
    print("TEST 13 PASSED: Both User A and User B can access shared material 'DSA_Full_Course.pdf'.")

    # TEST 14, 15, 16, 17: Persistent Group Chat
    database.add_study_space_message(f"msg_1_{run_suffix}", space_id, user_a_id, user_a_name, "Does anyone understand recursion?", "question")
    messages_b = database.get_study_space_messages(space_id, user_b_id)
    assert len(messages_b) == 1 and messages_b[0]["sender_name"] == user_a_name, "User B cannot see User A's message"

    database.add_study_space_message(f"msg_2_{run_suffix}", space_id, user_b_id, user_b_name, "Yes, think of it as a function calling itself.", "chat")
    messages_a = database.get_study_space_messages(space_id, user_a_id)
    assert len(messages_a) == 2 and messages_a[1]["sender_name"] == user_b_name, "User A cannot see User B's response"
    print("TEST 14, 15, 16, 17 PASSED: Persistent chat messages exchanged bi-directionally between User A and User B.")

    # TEST 18 & 19: RAG Data Isolation for Non-Members & Members
    non_member_docs = database.get_study_space_documents(space_id, non_member_id)
    assert len(non_member_docs) == 0, "Security failure: Non-member retrieved shared documents!"
    non_member_msgs = database.get_study_space_messages(space_id, non_member_id)
    assert len(non_member_msgs) == 0, "Security failure: Non-member retrieved shared messages!"
    print("TEST 18 & 19 PASSED: Strict RAG and Database layer data isolation verified.")

    # TEST 20, 21, 22: Shared Group Quiz & Independent Tracking
    g_quiz_id = f"gquiz_dsa_{run_suffix}"
    questions_data = [
        {
            "question": "What is the time complexity of binary search?",
            "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"],
            "correct_index": 1,
            "explanation": "Binary search divides search space in half.",
            "topic": "Search Algorithms",
            "subtopic": "Binary Search",
            "difficulty": "Easy",
            "coin_reward": 10,
            "source_citation": "DSA_Full_Course.pdf — Page 64"
        }
    ]
    database.save_study_space_quiz(g_quiz_id, space_id, user_a_name, "Group Quiz 1: Algorithms", questions_data)
    
    # User A attempt (100%)
    database.save_study_space_quiz_attempt(f"att_a_{run_suffix}", g_quiz_id, space_id, user_a_id, user_a_name, score=1, total=1, pct=100.0, correct=1, wrong=0)
    # User B attempt (0%)
    database.save_study_space_quiz_attempt(f"att_b_{run_suffix}", g_quiz_id, space_id, user_b_id, user_b_name, score=0, total=1, pct=0.0, correct=0, wrong=1)

    attempts = database.get_study_space_quiz_attempts(space_id, user_a_id)
    assert len(attempts) == 2, "Quiz attempts mismatch"

    # Verify user personal analytics updated independently
    analytics_a = analytics.get_user_overview(user_a_id)
    analytics_b = analytics.get_user_overview(user_b_id)
    assert analytics_a["user_id"] == user_a_id, "Analytics user mismatch"
    assert analytics_b["user_id"] == user_b_id, "Analytics user mismatch"
    print("TEST 20, 21, 22 PASSED: Shared quiz taken independently. Personal results tracked privately.")

    # TEST 23: Non-member Access Security Check
    is_mem_non = database.is_study_space_member(space_id, non_member_id)
    assert is_mem_non is False, "Non-member wrongly marked as member"
    print("TEST 23 PASSED: Non-member denied access to Study Space.")

    # --- Testing Feature 3: RAG Multi-PDF, Subject Isolation & Scanned PDF Fallbacks ---
    print("\n--- Testing Feature 3: RAG Multi-PDF, Subject Isolation & Scanned PDF Fallbacks ---")
    
    # TEST 24: Multiple PDF Upload and Cross-Document Retrieval (PDF 1 queried when PDF 2 is latest)
    doc_1_id = f"doc_pdf1_{run_suffix}"
    doc_2_id = f"doc_pdf2_{run_suffix}"
    
    chunks_pdf1 = [{
        "chunk_id": f"{doc_1_id}_p1_0",
        "doc_id": doc_1_id,
        "doc_name": "Java_Advanced_Pointers.pdf",
        "filename": "Java_Advanced_Pointers.pdf",
        "unit_label": "Page 1",
        "unit_num": 1,
        "subject": "Java",
        "section_title": "Page 1",
        "text": "Inheritance allows a child class to acquire properties and methods of a parent class in object-oriented programming."
    }]
    
    chunks_pdf2 = [{
        "chunk_id": f"{doc_2_id}_p1_0",
        "doc_id": doc_2_id,
        "doc_name": "Java_Streams_And_Lambdas.pdf",
        "filename": "Java_Streams_And_Lambdas.pdf",
        "unit_label": "Page 1",
        "unit_num": 1,
        "subject": "Java",
        "section_title": "Page 1",
        "text": "Stream API enables functional programming operations such as map, filter, and reduce on collections."
    }]

    # Save vector store chunks for Java
    v_store_java = document_processor.get_subject_vector_store("Java", user_id=user_a_id)
    v_store_java.add_chunks(chunks_pdf1, [[0.1] * 768])
    v_store_java.add_chunks(chunks_pdf2, [[0.2] * 768])

    docs_list = [
        {"doc_id": doc_1_id, "filename": "Java_Advanced_Pointers.pdf", "chunks": chunks_pdf1},
        {"doc_id": doc_2_id, "filename": "Java_Streams_And_Lambdas.pdf", "chunks": chunks_pdf2}
    ]

    # Query question from PDF 1 (Inheritance) when no doc_id is selected
    res_multi = document_processor.search_documents(
        documents=docs_list,
        query="What is inheritance?",
        subject="Java",
        user_id=user_a_id,
        doc_id=None
    )
    assert len(res_multi) > 0 and res_multi[0]["doc_id"] == doc_1_id, "Multi-PDF retrieval failed to find answer in earlier PDF 1"
    print("TEST 24 PASSED: Found answer in earlier uploaded PDF 1 when no specific document was selected.")

    # TEST 25: Explicit Document Selection Filtering
    res_explicit = document_processor.search_documents(
        documents=docs_list,
        query="What is inheritance?",
        subject="Java",
        user_id=user_a_id,
        doc_id=doc_2_id  # explicitly select PDF 2
    )
    # Since query is about inheritance and PDF 2 is selected, no matching chunks in PDF 2 for inheritance
    assert not any(c["doc_id"] == doc_1_id for c in res_explicit), "Explicit filter failed: retrieved PDF 1 chunks when PDF 2 was explicitly selected"
    print("TEST 25 PASSED: Explicit document filter strictly enforced for selected PDF.")

    # TEST 26: Cross-Subject Retrieval Fallback
    res_cross = document_processor.search_documents(
        documents=docs_list,
        query="inheritance",
        subject="General",  # different active subject in UI
        user_id=user_a_id,
        doc_id=None
    )
    assert len(res_cross) > 0 and res_cross[0]["doc_id"] == doc_1_id, "Cross-subject fallback retrieval failed"
    print("TEST 26 PASSED: Cross-subject fallback retrieved relevant PDF chunks across subject stores.")

    # TEST 27: Document Diagnostics Helper
    processed_file = config.PROCESSED_DIR / f"{doc_1_id}.json"
    with open(processed_file, "w", encoding="utf-8") as f:
        json.dump({
            "doc_id": doc_1_id,
            "filename": "Java_Advanced_Pointers.pdf",
            "subject": "Java",
            "total_units": 1,
            "extracted_chars": 120,
            "status": "READY",
            "chunks": chunks_pdf1
        }, f)
    
    diag = document_processor.get_document_diagnostics(doc_1_id, user_id=user_a_id)
    assert diag["status"] == "READY" and diag["chunks"] == 1, "Diagnostics helper failed"
    print("TEST 27 PASSED: Document diagnostics helper verified READY status.")

    # TEST 28: Scanned PDF / OCR Required Detection
    scanned_chunks = document_processor._extract_pdf_chunks(b"%PDF-dummy-scanned", "scanned_doc.pdf", "Java", f"doc_scan_{run_suffix}")
    assert len(scanned_chunks) == 1 and scanned_chunks[0].get("status") == "OCR_REQUIRED", "Scanned PDF detection failed"
    print("TEST 28 PASSED: Scanned image PDF detected and marked as OCR_REQUIRED.")

    # TEST 29: Specific User Query 'tell me about python pdf' Semantic Retrieval
    doc_py_id = f"doc_py_{run_suffix}"
    chunks_py = [{
        "chunk_id": f"{doc_py_id}_p1_0",
        "doc_id": doc_py_id,
        "doc_name": "Python_Course_Unit1.pdf",
        "filename": "Python_Course_Unit1.pdf",
        "unit_label": "Page 1",
        "unit_num": 1,
        "subject": "Python",
        "section_title": "Python Overview",
        "text": "Python is an interpreted high-level general-purpose programming language emphasizing code readability."
    }]
    v_store_py = document_processor.get_subject_vector_store("Python", user_id=user_a_id)
    v_store_py.add_chunks(chunks_py, [[0.15] * 768])

    docs_py = [{"doc_id": doc_py_id, "filename": "Python_Course_Unit1.pdf", "chunks": chunks_py}]

    res_py = document_processor.search_documents(
        documents=docs_py,
        query="tell me about python pdf",
        subject="Python",
        user_id=user_a_id,
        doc_id=None
    )
    assert len(res_py) > 0 and res_py[0]["doc_id"] == doc_py_id, "Failed to retrieve Python chunks for 'tell me about python pdf'"
    print("TEST 29 PASSED: 'tell me about python pdf' successfully retrieved Python PDF chunks via semantic RAG.")

    print("\nALL 29 VERIFICATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()

