"""
EduMind AI - Educational Learning Games Engine
Provides 10 Educational Games with 5 Genuine Cognitive Difficulty Levels (Beginner to Expert),
zero question reuse between levels, option randomization, Streamlit rerun safety,
and MongoDB per-user progress isolation.
"""

import uuid
import random
import copy
from typing import List, Dict, Any, Optional
import streamlit as st
import mongodb
from coin_manager import CoinManager

# Configurable questions per game session
QUESTIONS_PER_GAME = 5

# Level Rewards Mapping
LEVEL_REWARDS = {
    1: 5,   # Level 1: +5 coins
    2: 10,  # Level 2: +10 coins
    3: 15,  # Level 3: +15 coins
    4: 20,  # Level 4: +20 coins
    5: 25   # Level 5: +25 coins
}

# ==============================================================================
# 10 EDUCATIONAL GAMES LIST
# ==============================================================================
GAMES_LIST = [
    {
        "id": "quick_quiz",
        "name": "🧠 Quick Quiz",
        "desc": "Fast-paced general Computer Science and IT knowledge challenge."
    },
    {
        "id": "code_debug",
        "name": "💻 Code Debug Challenge",
        "desc": "Find bugs, memory leaks, and syntax errors in programming snippets."
    },
    {
        "id": "number_challenge",
        "name": "🔢 Number & Series Challenge",
        "desc": "Identify mathematical sequences, series, and binary patterns."
    },
    {
        "id": "logic_puzzle",
        "name": "🧩 Logic & Reasoning Puzzle",
        "desc": "Solve analytical reasoning riddles, syllogisms, and pattern logic."
    },
    {
        "id": "topic_challenge",
        "name": "📚 Computer Systems & DB",
        "desc": "Master DBMS, Operating Systems, Computer Networks, and Web concepts."
    },
    {
        "id": "mental_math",
        "name": "🧮 Mental Math",
        "desc": "Solve arithmetic equations quickly in your head."
    },
    {
        "id": "vocab_challenge",
        "name": "📝 CS & Academic Vocab",
        "desc": "Expand your technical CS and academic terminology mastery."
    },
    {
        "id": "speed_math",
        "name": "⚡ Speed Calculation",
        "desc": "Rapidly calculate powers, modulo, and binary conversions."
    }
]

# ==============================================================================
# COMPREHENSIVE LEVEL-ISOLATED QUESTION DATABASE (LEVELS 1 - 5)
# Zero Question Overlap Between Levels!
# ==============================================================================
GAME_QUESTIONS_DB = {
    # --------------------------------------------------------------------------
    # 1. QUICK QUIZ
    # --------------------------------------------------------------------------
    "quick_quiz": {
        1: [
            {"id": "qq_l1_01", "q": "What component is known as the 'Brain' of a computer?", "opts": ["RAM", "CPU", "Hard Drive", "GPU"], "ans": 1, "exp": "The CPU (Central Processing Unit) performs all basic arithmetic and control logic."},
            {"id": "qq_l1_02", "q": "Which data structure follows FIFO (First In First Out)?", "opts": ["Queue", "Stack", "Tree", "Graph"], "ans": 0, "exp": "Queues operate on First In First Out (FIFO) order."},
            {"id": "qq_l1_03", "q": "What does CPU stand for?", "opts": ["Central Processing Unit", "Computer Power Unit", "Core Programming Utility", "Control Processing Unit"], "ans": 0, "exp": "CPU stands for Central Processing Unit."},
            {"id": "qq_l1_04", "q": "Which storage memory is volatile and loses data when powered off?", "opts": ["ROM", "SSD", "RAM", "Hard Disk"], "ans": 2, "exp": "RAM is primary volatile memory that requires electrical power to hold data."},
            {"id": "qq_l1_05", "q": "What is an array?", "opts": ["A collection of elements of same type stored contiguously", "A random file on disk", "A network protocol", "A database engine"], "ans": 0, "exp": "An array stores homogeneous elements in contiguous memory locations."}
        ],
        2: [
            {"id": "qq_l2_01", "q": "Which data structure is optimal for implementing function call stacks?", "opts": ["Queue", "Stack", "Linked List", "Binary Search Tree"], "ans": 1, "exp": "The system call stack uses Last In First Out (LIFO) order managed by a Stack."},
            {"id": "qq_l2_02", "q": "What is the time complexity to access an element by index in an array?", "opts": ["O(1)", "O(n)", "O(log n)", "O(n^2)"], "ans": 0, "exp": "Direct index offset calculation allows constant O(1) time array access."},
            {"id": "qq_l2_03", "q": "Which searching algorithm requires the input array to be sorted first?", "opts": ["Linear Search", "Binary Search", "Depth First Search", "Breadth First Search"], "ans": 1, "exp": "Binary Search relies on sorted order to divide the search space in half."},
            {"id": "qq_l2_04", "q": "What does SQL stand for?", "opts": ["Structured Query Language", "Simple Question Language", "Sequential Query Logic", "Server Query List"], "ans": 0, "exp": "SQL stands for Structured Query Language used in relational databases."},
            {"id": "qq_l2_05", "q": "In Python, which built-in data structure stores key-value pairs?", "opts": ["List", "Tuple", "Dictionary", "Set"], "ans": 2, "exp": "Python Dictionaries store unique key to value mappings using hash tables."}
        ],
        3: [
            {"id": "qq_l3_01", "q": "What is the worst-case time complexity of QuickSort algorithm?", "opts": ["O(n log n)", "O(n)", "O(n^2)", "O(log n)"], "ans": 2, "exp": "When bad pivots are selected repeatedly (e.g. already sorted array), QuickSort degrades to O(n^2)."},
            {"id": "qq_l3_02", "q": "Which data structure uses LIFO order for operations?", "opts": ["Queue", "Array", "Stack", "Tree"], "ans": 2, "exp": "Stack works on Last In First Out order."},
            {"id": "qq_l3_03", "q": "What is the main advantage of a doubly linked list over a singly linked list?", "opts": ["Uses less memory", "Allows bi-directional traversal (forward & backward)", "Faster element insertion at head", "Automatic sorting"], "ans": 1, "exp": "Doubly linked lists store both `next` and `prev` pointers, enabling backward traversal."},
            {"id": "qq_l3_04", "q": "In DBMS, what does the ACID property 'Atomicity' ensure?", "opts": ["Transactions execute simultaneously", "All operations in a transaction succeed or all fail together", "Data is encrypted at rest", "Database never crashes"], "ans": 1, "exp": "Atomicity guarantees an 'all or nothing' outcome for database transactions."},
            {"id": "qq_l3_05", "q": "Which network protocol operates at the Transport Layer of OSI model?", "opts": ["IP", "TCP", "HTTP", "Ethernet"], "ans": 1, "exp": "TCP (Transmission Control Protocol) and UDP operate at Layer 4 (Transport)."}
        ],
        4: [
            {"id": "qq_l4_01", "q": "Which page replacement algorithm suffers from Belady's Anomaly?", "opts": ["LRU (Least Recently Used)", "FIFO (First In First Out)", "Optimal Page Replacement", "LFU"], "ans": 1, "exp": "Belady's Anomaly occurs in FIFO where increasing page frames can increase page faults."},
            {"id": "qq_l4_02", "q": "What is the tight worst-case time complexity of inserting an element into a Min-Heap of size N?", "opts": ["O(1)", "O(log N)", "O(N)", "O(N log N)"], "ans": 1, "exp": "Heap insertion appends at bottom and heapifies up through tree height log(N)."},
            {"id": "qq_l4_03", "q": "In computer architecture, what is a cache hazard / coherence issue?", "opts": ["RAM speed mismatch", "Multiple processor caches holding stale copies of shared memory", "Power surge in CPU", "Disk fragmentation"], "ans": 1, "exp": "Cache coherence ensures multi-core CPUs maintain consistent memory state across local L1/L2 caches."},
            {"id": "qq_l4_04", "q": "Which condition is NOT one of Coffman's 4 necessary conditions for Deadlock?", "opts": ["Mutual Exclusion", "Hold and Wait", "Preemption allowed", "Circular Wait"], "ans": 2, "exp": "No Preemption is required for deadlock. If preemption IS allowed, deadlock is avoided."},
            {"id": "qq_l4_05", "q": "What is the height of a balanced AVL tree containing N nodes?", "opts": ["O(N)", "O(log N)", "O(N^2)", "O(1)"], "ans": 1, "exp": "AVL trees maintain strict balance factor (-1, 0, +1), guaranteeing O(log N) height."}
        ],
        5: [
            {"id": "qq_l5_01", "q": "What is the worst-case space complexity of Depth First Search (DFS) on a graph with V vertices and maximum depth D?", "opts": ["O(V)", "O(D)", "O(V + E)", "O(1)"], "ans": 1, "exp": "DFS recursive call stack grows up to maximum search tree depth O(D)."},
            {"id": "qq_l5_02", "q": "In distributed systems, what does the CAP Theorem state?", "opts": ["Systems can simultaneously provide Consistency, Availability, and Partition Tolerance", "Systems can provide at most TWO of Consistency, Availability, and Partition Tolerance", "Centralized servers are faster than peer-to-peer networks", "Async networks eliminate latencies"], "ans": 1, "exp": "CAP Theorem proves distributed databases must trade off between Consistency and Availability during network Partitions."},
            {"id": "qq_l5_03", "q": "Which time complexity represents the Master Theorem solution for T(n) = 2T(n/2) + O(n)?", "opts": ["O(n)", "O(n log n)", "O(n^2)", "O(2^n)"], "ans": 1, "exp": "By Master Theorem Case 2 (f(n) = Theta(n^(log_b a))), T(n) = O(n log n)."},
            {"id": "qq_l5_04", "q": "What is the main purpose of the B+ Tree index structure in production database engines like InnoDB?", "opts": ["Keep all data records only in leaf nodes and link leaves sequentially for fast range scans", "Encrypt table data", "Eliminate secondary keys", "Store data in random order"], "ans": 0, "exp": "B+ Trees store key-pointers in internal nodes and all actual data/pointers in linked leaf nodes for O(log N) point lookup and O(1) sequential range queries."},
            {"id": "qq_l5_05", "q": "In compiler design, what type of grammar is parsed by an LL(1) parser?", "opts": ["Context-Free Grammar without left recursion using 1 token lookahead", "Regular Expressions only", "Context-Sensitive Grammar", "Ambiguous Grammars"], "ans": 0, "exp": "LL(1) top-down parsers require non-left-recursive CFGs deterministically predictable with 1 lookahead token."}
        ]
    },

    # --------------------------------------------------------------------------
    # 2. CODE DEBUG CHALLENGE
    # --------------------------------------------------------------------------
    "code_debug": {
        1: [
            {"id": "cd_l1_01", "q": "Fix Python error: `def add(a, b) return a + b`", "opts": ["Add colon `:` after `b)`", "Change return to print", "Rename function", "Wrap in quotes"], "ans": 0, "exp": "Python function header requires a colon `:` at the end of the `def` line."},
            {"id": "cd_l1_02", "q": "Find bug in C array access: `int arr[5]; printf(\"%d\", arr[5]);`", "opts": ["arr[5] is out of bounds (indices are 0 to 4)", "Syntax error in printf", "Array must be float", "No error"], "ans": 0, "exp": "In C, a 5-element array has valid indices 0, 1, 2, 3, 4. Index 5 is out of bounds."},
            {"id": "cd_l1_03", "q": "What happens in Python if you execute `x = \"5\" + 5`?", "opts": ["TypeError: cannot concatenate 'str' and 'int'", "Result is 10", "Result is \"55\"", "Creates tuple"], "ans": 0, "exp": "Python does not implicitly coerce string and integer types for addition."},
            {"id": "cd_l1_04", "q": "How do you check equality in Java and C++?", "opts": ["=", "==", "===", "equals"], "ans": 1, "exp": "`=` is assignment; `==` is equality comparison."},
            {"id": "cd_l1_05", "q": "Identify infinite loop in C: `for(int i=0; i<10; i--)`", "opts": ["`i--` decrements i away from 10, looping infinitely until underflow", "Syntax error in for", "Loop runs 10 times", "No error"], "ans": 0, "exp": "Decrementing `i` starts at 0, going to -1, -2..., which remains `< 10` constantly."}
        ],
        2: [
            {"id": "cd_l2_01", "q": "What is the output of `print(type([]))` in Python?", "opts": ["<class 'list'>", "<class 'array'>", "<class 'tuple'>", "<class 'set'>"], "ans": 0, "exp": "Square brackets `[]` create a Python `list` instance."},
            {"id": "cd_l2_02", "q": "Identify error: `int *p = NULL; *p = 10;`", "opts": ["Dereferencing a NULL pointer causes segmentation fault", "Cannot assign integer to pointer", "NULL is undefined", "Syntax error"], "ans": 0, "exp": "Writing data to `*p` when `p` points to NULL attempts writing to invalid memory address 0."},
            {"id": "cd_l2_03", "q": "In Python, what is the output of `bool(\"\")`?", "opts": ["False", "True", "None", "Error"], "ans": 0, "exp": "An empty string `\"\"` evaluates to boolean `False` in Python."},
            {"id": "cd_l2_04", "q": "What is wrong with this C loop? `int i=10; while(i>0) { i++; }`", "opts": ["`i++` increments i away from 0, leading to integer overflow / infinite loop", "Syntax error in while", "Executes 10 times", "Valid exit condition"], "ans": 0, "exp": "Incrementing `i` from 10 increases its value, never satisfying `i <= 0` until overflow."},
            {"id": "cd_l2_05", "q": "What is the result of `5 // 2` in Python 3?", "opts": ["2", "2.5", "3", "2.0"], "ans": 0, "exp": "`//` is integer floor division operator in Python."}
        ],
        3: [
            {"id": "cd_l3_01", "q": "Predict output: `a = [1, 2]; b = a; b.append(3); print(len(a))`", "opts": ["3", "2", "1", "AttributeError"], "ans": 0, "exp": "In Python, `b = a` assigns reference to same list object. Mutating `b` modifies `a`."},
            {"id": "cd_l3_02", "q": "Find memory leak in C++ snippet: `int* arr = new int[100]; return 0;`", "opts": ["Memory allocated on heap with `new` is never freed with `delete[]`", "Syntax error in array declaration", "Index out of bounds", "Null pointer exception"], "ans": 0, "exp": "Dynamic heap memory allocated via `new[]` must be released using `delete[] arr`."},
            {"id": "cd_l3_03", "q": "What is the result of `list(set([1, 2, 2, 3, 1]))`?", "opts": ["A list with unique elements [1, 2, 3]", "Duplicated list [1, 2, 2, 3, 1]", "TypeError", "Set object"], "ans": 0, "exp": "Passing list to `set()` removes duplicates, and `list()` converts back to list."},
            {"id": "cd_l3_04", "q": "What will `print(\"a\" * 3)` output in Python?", "opts": ["aaa", "a3", "Error", "['a', 'a', 'a']"], "ans": 0, "exp": "Multiplying string by integer N repeats string N times."},
            {"id": "cd_l3_05", "q": "Fix C++ error: `class A { int x; }; A a; cout << a.x;`", "opts": ["Class members are private by default; `x` cannot be accessed outside class", "cout syntax error", "Class requires constructor", "Cannot instantiate A"], "ans": 0, "exp": "Members of C++ `class` default to `private`. Mark `x` as `public:` to access directly."}
        ],
        4: [
            {"id": "cd_l4_01", "q": "Predict Python output: `def foo(elem, lst=[]): lst.append(elem); return lst; print(foo(1)); print(foo(2))`", "opts": ["[1] then [1, 2]", "[1] then [2]", "[1, 2] then [1, 2]", "SyntaxError"], "ans": 0, "exp": "Default mutable arguments (`lst=[]`) are evaluated ONCE at function definition time, accumulating across calls."},
            {"id": "cd_l4_02", "q": "Identify problem with recursive function without base case: `void f() { f(); }`", "opts": ["Exhausts stack memory causing StackOverflow / Segmentation Fault", "Executes normally", "Returns 0", "Compiler error"], "ans": 0, "exp": "Infinite recursion pushes stack frames continuously until stack limit is exceeded."},
            {"id": "cd_l4_03", "q": "In Java, what does `String s1 = new String(\"hi\"); String s2 = new String(\"hi\"); System.out.println(s1 == s2);` print?", "opts": ["false", "true", "Compilation error", "NullPointerException"], "ans": 0, "exp": "`==` checks object reference identity. `new String` creates two distinct heap objects, so `==` is false."},
            {"id": "cd_l4_04", "q": "What is the output of Python snippet: `[x for x in range(5) if x % 2 == 0]`?", "opts": ["[0, 2, 4]", "[1, 3]", "[0, 1, 2, 3, 4]", "[2, 4]"], "ans": 0, "exp": "List comprehension filters even numbers 0, 2, 4 from range(5)."},
            {"id": "cd_l4_05", "q": "What causes dangling pointer in C?", "opts": ["Pointer referencing memory that has been deallocated with `free()`", "Pointer assigned NULL", "Uninitialized local variable", "Void pointer"], "ans": 0, "exp": "A dangling pointer stores the address of memory that was previously freed or out of scope."}
        ],
        5: [
            {"id": "cd_l5_01", "q": "Predict output of C code: `int x = 5; printf(\"%d %d\", x++, ++x);`", "opts": ["Undefined behavior due to multiple unsequenced modifications of x", "5 7", "6 7", "5 6"], "ans": 0, "exp": "Modifying same scalar variable multiple times without sequence points yields Undefined Behavior in C/C++."},
            {"id": "cd_l5_02", "q": "Analyze closure trap in JS/Python: `funcs = [lambda: i for i in range(3)]; print([f() for f in funcs])`", "opts": ["[2, 2, 2]", "[0, 1, 2]", "[0, 0, 0]", "TypeError"], "ans": 0, "exp": "Lambdas bind to variable `i` by reference (late binding). At invocation, `i` has final loop value 2."},
            {"id": "cd_l5_03", "q": "In C++, what occurs when an exception is thrown inside a destructor during stack unwinding?", "opts": ["`std::terminate()` is invoked immediately crashing the program", "Exception is ignored", "Handled by caller", "Compiler warning"], "ans": 0, "exp": "Throwing an exception while another exception is unwinding the stack calls `std::terminate()`."},
            {"id": "cd_l5_04", "q": "What is the flaw in double-checked locking singleton without `volatile` keyword in Java?", "opts": ["Instruction reordering may publish reference to partially initialized object", "Memory leak", "Thread deadlock", "ClassCastException"], "ans": 0, "exp": "Without `volatile`, compiler/CPU reordering may assign non-null reference before object constructor finishes."},
            {"id": "cd_l5_05", "q": "Predict result of Python slicing: `a = [0, 1, 2, 3, 4]; print(a[::-2])`", "opts": ["[4, 2, 0]", "[0, 2, 4]", "[4, 3, 2]", "[3, 1]"], "ans": 0, "exp": "Negative step `-2` reverses list and steps backwards by 2 starting from last element."}
        ]
    },

    # --------------------------------------------------------------------------
    # 3. NUMBER & SERIES CHALLENGE
    # --------------------------------------------------------------------------
    "number_challenge": {
        1: [
            {"id": "nc_l1_01", "q": "Find missing term in sequence: 2, 4, 6, 8, ___", "opts": ["10", "9", "12", "11"], "ans": 0, "exp": "Even numbers incrementing by +2. Next is 10."},
            {"id": "nc_l1_02", "q": "Find missing term: 5, 10, 15, 20, ___", "opts": ["25", "30", "22", "24"], "ans": 0, "exp": "Multiples of 5 incrementing by +5. Next is 25."},
            {"id": "nc_l1_03", "q": "What is binary representation of decimal 2?", "opts": ["10", "01", "11", "100"], "ans": 0, "exp": "Decimal 2 in binary is 10_2."},
            {"id": "nc_l1_04", "q": "Find missing term: 10, 20, 30, 40, ___", "opts": ["50", "45", "60", "55"], "ans": 0, "exp": "Simple sequence adding +10 each step."},
            {"id": "nc_l1_05", "q": "What is the square of 5?", "opts": ["25", "10", "15", "20"], "ans": 0, "exp": "5 * 5 = 25."}
        ],
        2: [
            {"id": "nc_l2_01", "q": "Find missing term: 3, 9, 27, 81, ___", "opts": ["243", "162", "324", "100"], "ans": 0, "exp": "Each number is multiplied by 3. 81 * 3 = 243."},
            {"id": "nc_l2_02", "q": "Find missing term: 1, 4, 9, 16, 25, ___", "opts": ["36", "30", "35", "49"], "ans": 0, "exp": "Sequence of perfect squares: 1^2, 2^2, 3^2, 4^2, 5^2, 6^2 = 36."},
            {"id": "nc_l2_03", "q": "What is binary representation of decimal 10?", "opts": ["1010", "1001", "1100", "1110"], "ans": 0, "exp": "10 in binary is 8 + 2 = 1010_2."},
            {"id": "nc_l2_04", "q": "Find missing term: 2, 3, 5, 7, 11, ___", "opts": ["13", "12", "14", "15"], "ans": 0, "exp": "Sequence of prime numbers. Next prime after 11 is 13."},
            {"id": "nc_l2_05", "q": "Find missing term: 100, 90, 80, 70, ___", "opts": ["60", "50", "65", "55"], "ans": 0, "exp": "Decrements by 10 each step."}
        ],
        3: [
            {"id": "nc_l3_01", "q": "Find missing term in Fibonacci: 0, 1, 1, 2, 3, 5, 8, ___", "opts": ["13", "11", "12", "15"], "ans": 0, "exp": "Each term is sum of preceding two: 5 + 8 = 13."},
            {"id": "nc_l3_02", "q": "Find missing term: 2, 6, 12, 20, 30, ___", "opts": ["42", "40", "36", "48"], "ans": 0, "exp": "Differences are +4, +6, +8, +10, +12. 30 + 12 = 42 (n*(n+1))."},
            {"id": "nc_l3_03", "q": "Convert binary 1111_2 to decimal:", "opts": ["15", "16", "14", "12"], "ans": 0, "exp": "8 + 4 + 2 + 1 = 15."},
            {"id": "nc_l3_04", "q": "Find missing term: 1, 8, 27, 64, ___", "opts": ["125", "100", "216", "144"], "ans": 0, "exp": "Sequence of perfect cubes: 1^3, 2^3, 3^3, 4^3, 5^3 = 125."},
            {"id": "nc_l3_05", "q": "What is hexadecimal 1A in decimal?", "opts": ["26", "16", "20", "28"], "ans": 0, "exp": "1 * 16 + 10 (A) = 26."}
        ],
        4: [
            {"id": "nc_l4_01", "q": "Find missing term: 7, 10, 8, 11, 9, 12, ___", "opts": ["10", "13", "11", "14"], "ans": 0, "exp": "Alternating pattern: (+3, -2, +3, -2, +3, -2). 12 - 2 = 10."},
            {"id": "nc_l4_02", "q": "What is two's complement of 8-bit binary 00000101 (+5)?", "opts": ["11111011", "11111010", "10000101", "11111100"], "ans": 0, "exp": "Invert bits (11111010) and add 1 = 11111011 (-5)."},
            {"id": "nc_l4_03", "q": "Find missing term: 2, 3, 6, 18, 108, ___", "opts": ["1944", "216", "972", "1296"], "ans": 0, "exp": "Each term is product of previous two terms: 18 * 108 = 1944."},
            {"id": "nc_l4_04", "q": "How many trailing zeros does 20! (20 factorial) have?", "opts": ["4", "3", "5", "2"], "ans": 0, "exp": "Trailing zeros = floor(20/5) = 4."},
            {"id": "nc_l4_05", "q": "What is the sum of first 50 positive integers (1 to 50)?", "opts": ["1275", "1250", "2550", "1300"], "ans": 0, "exp": "Sum = n(n+1)/2 = 50 * 51 / 2 = 1275."}
        ],
        5: [
            {"id": "nc_l5_01", "q": "Find missing term: 1, 2, 6, 24, 120, 720, ___", "opts": ["5040", "1440", "4320", "2520"], "ans": 0, "exp": "Sequence of factorials (1!, 2!, 3!, 4!, 5!, 6!, 7! = 5040)."},
            {"id": "nc_l5_02", "q": "Evaluate modulo expression: (7^3) mod 13", "opts": ["5", "3", "7", "1"], "ans": 0, "exp": "7^1=7, 7^2=49=10 (mod 13), 7^3 = 70 mod 13 = 5."},
            {"id": "nc_l5_03", "q": "What is the 10th Catalan Number formula C_n?", "opts": ["(1 / (n + 1)) * (2n choose n)", "n!", "2^n", "(n-1)!"], "ans": 0, "exp": "Catalan numbers are given by C_n = (1/(n+1)) * (2n choose n)."},
            {"id": "nc_l5_04", "q": "Find general solution exponent of recurrence T(n) = 3T(n/4) + n log n", "opts": ["O(n log n)", "O(n^(log_4 3))", "O(n^2)", "O(log n)"], "ans": 0, "exp": "Since log_4(3) < 1 and f(n) = n log n dominates, T(n) = O(n log n)."},
            {"id": "nc_l5_05", "q": "What is the GCD of 252 and 105 using Euclidean algorithm?", "opts": ["21", "7", "42", "63"], "ans": 0, "exp": "252 mod 105 = 42; 105 mod 42 = 21; 42 mod 21 = 0. GCD is 21."}
        ]
    },

    # --------------------------------------------------------------------------
    # 4. LOGIC & REASONING PUZZLE
    # --------------------------------------------------------------------------
    "logic_puzzle": {
        1: [
            {"id": "lp_l1_01", "q": "If A is taller than B, and B is taller than C, who is the shortest?", "opts": ["C", "B", "A", "Cannot tell"], "ans": 0, "exp": "A > B > C. Therefore C is the shortest."},
            {"id": "lp_l1_02", "q": "Light is to Darkness as Knowledge is to ___", "opts": ["Ignorance", "Books", "Intelligence", "Wisdom"], "ans": 0, "exp": "Ignorance is the absence of knowledge, just as darkness is absence of light."},
            {"id": "lp_l1_03", "q": "Which word does NOT belong with the others?", "opts": ["Apple", "Banana", "Carrot", "Mango"], "ans": 2, "exp": "Carrot is a vegetable; others are fruits."},
            {"id": "lp_l1_04", "q": "If all Dogs are Animals, and Barky is a Dog, is Barky an Animal?", "opts": ["Yes", "No", "Uncertain", "Only on weekends"], "ans": 0, "exp": "Direct categorical syllogism."},
            {"id": "lp_l1_05", "q": "What comes next in pattern: Up, Down, Left, Right, Up, Down, Left, ___", "opts": ["Right", "Up", "Down", "Left"], "ans": 0, "exp": "Repeating sequence of 4 directions."}
        ],
        2: [
            {"id": "lp_l2_01", "q": "Pointing to a photograph, a man says 'I have no brothers or sisters, but that man's father is my father's son.' Who is in the photo?", "opts": ["His son", "His father", "Himself", "His nephew"], "ans": 0, "exp": "'My father's son' with no siblings = Himself. 'That man's father is myself' -> That man is his son."},
            {"id": "lp_l2_02", "q": "If CAT is coded as 3120 (C=3, A=1, T=20), how is DOG coded?", "opts": ["4157", "4147", "3157", "4158"], "ans": 0, "exp": "D=4, O=15, G=7 -> 4157."},
            {"id": "lp_l2_03", "q": "Some A are B. All B are C. Therefore:", "opts": ["Some A are C", "All A are C", "No A are C", "All C are A"], "ans": 0, "exp": "Since some A overlap with B and all B are inside C, those overlapping A must be C."},
            {"id": "lp_l2_04", "q": "A clock shows 3:00. What is the angle between hour and minute hands?", "opts": ["90 degrees", "45 degrees", "180 degrees", "60 degrees"], "ans": 0, "exp": "Each hour tick represents 30 degrees. 3 * 30 = 90 degrees."},
            {"id": "lp_l2_05", "q": "If 5 workers build 5 tables in 5 days, how many days does 1 worker take to build 1 table?", "opts": ["5 days", "1 day", "25 days", "10 days"], "ans": 0, "exp": "Rate of 1 worker is 1 table per 5 days."}
        ],
        3: [
            {"id": "lp_l3_01", "q": "You have 8 balls. One is slightly heavier. Using a balance scale, minimum weighings to guarantee finding it?", "opts": ["2", "3", "4", "1"], "ans": 0, "exp": "Divide into 3-3-2. Weigh 3 vs 3. If equal, weigh 2 remaining. If unequal, weigh 1 vs 1 from heavy set. Total 2 weighings."},
            {"id": "lp_l3_02", "q": "If RED is coded as 27 and BLUE is coded as 40, what is GREEN coded as?", "opts": ["49", "45", "52", "40"], "ans": 0, "exp": "Sum of alphabetical positions: G(7)+R(18)+E(5)+E(5)+N(14) = 49."},
            {"id": "lp_l3_03", "q": "A is B's sister. C is B's mother. D is C's father. How is A related to D?", "opts": ["Granddaughter", "Daughter", "Grandmother", "Niece"], "ans": 0, "exp": "A is child of C. C is child of D. So A is granddaughter of D."},
            {"id": "lp_l3_04", "q": "If it takes 10 minutes to boil 1 egg, how long does it take to boil 4 eggs together in the same pot?", "opts": ["10 minutes", "40 minutes", "20 minutes", "5 minutes"], "ans": 0, "exp": "All eggs boil concurrently in the same pot."},
            {"id": "lp_l3_05", "q": "Statement: 'If it rains, the grass is wet.' The grass is NOT wet. What can be concluded?", "opts": ["It did not rain", "It rained", "Grass is dead", "No conclusion"], "ans": 0, "exp": "Modus Tollens: ~Q -> ~P. Not wet implies not rain."}
        ],
        4: [
            {"id": "lp_l4_01", "q": "Island of Knights (always tell truth) and Knaves (always lie). Person A says: 'At least one of us is a Knave.' What are A and B?", "opts": ["A is Knight, B is Knave", "Both are Knights", "Both are Knaves", "A is Knave, B is Knight"], "ans": 0, "exp": "If A were Knave, statement would be true (contradiction). So A is Knight (tells truth), making B a Knave."},
            {"id": "lp_l4_02", "q": "Four people cross a bridge at night with 1 flashlight (max 2 people at a time). Times: 1 min, 2 min, 5 min, 10 min. Minimum time?", "opts": ["17 minutes", "19 minutes", "15 minutes", "21 minutes"], "ans": 0, "exp": "1+2 cross (2m), 1 returns (1m), 5+10 cross (10m), 2 returns (2m), 1+2 cross (2m). Total = 2+1+10+2+2 = 17m."},
            {"id": "lp_l4_03", "q": "In a 6-player round-robin tournament where everyone plays everyone once, total matches?", "opts": ["15", "30", "12", "18"], "ans": 0, "exp": "N*(N-1)/2 = 6 * 5 / 2 = 15 matches."},
            {"id": "lp_l4_04", "q": "Statement: 'All programmers like coffee. Some coffee lovers are night owls.' Which MUST follow?", "opts": ["None of the above necessarily follow", "All programmers are night owls", "Some night owls are programmers", "All coffee lovers are programmers"], "ans": 0, "exp": "Venn diagrams show no mandatory overlap between programmers and night owls."},
            {"id": "lp_l4_05", "q": "What is the negation of 'For all x, P(x) is true'?", "opts": ["There exists x such that P(x) is false", "For all x, P(x) is false", "There exists x such that P(x) is true", "No x exists"], "ans": 0, "exp": "De Morgan's law for quantifiers: ~(forall x P(x)) == exists x ~P(x)."}
        ],
        5: [
            {"id": "lp_l5_01", "q": "3 hats (Red/Blue). 3 logicians see other hats, not their own. All 3 simultaneously guess their hat color correctly without communication. How?", "opts": ["They agreed beforehand: guess color that appears odd number of times (or majority)", "Pure luck 1/8 chance", "Optical reflection", "Telepathy"], "ans": 0, "exp": "Group strategy matching parity allows at least 3/4 or full deterministic recovery under parity agreement."},
            {"id": "lp_l5_02", "q": "Monty Hall Problem: 3 doors, 1 car, 2 goats. You pick Door 1. Host opens Door 3 revealing goat. Should you switch to Door 2?", "opts": ["Yes, switching gives 2/3 probability of winning", "No, probability is 1/2 either way", "Switching gives 1/3 probability", "No difference"], "ans": 0, "exp": "Initial choice has 1/3 probability. Remaining unchosen door inherits 2/3 probability after host elimination."},
            {"id": "lp_l5_03", "q": "Two envelopes contain money; one has TWICE as much as the other. You pick envelope with $100. Expected value of switching?", "opts": ["$125", "$100", "$150", "$200"], "ans": 0, "exp": "Other envelope is either $50 or $200 with equal 0.5 probability: 0.5(50) + 0.5(200) = $125. (Classic Envelope Paradox)."},
            {"id": "lp_l5_04", "q": "Which logical system handles statements with degree of truth between 0 and 1?", "opts": ["Fuzzy Logic", "Boolean Logic", "First Order Predicate Logic", "Propositional Logic"], "ans": 0, "exp": "Fuzzy logic accounts for continuous partial truth values ranging in [0, 1]."},
            {"id": "lp_l5_05", "q": "In Resolution Refutation proof, what is derived when a set of clauses is unsatisfiable?", "opts": ["Empty clause ()", "Tautology", "Universal quantifier", "Implication"], "ans": 0, "exp": "Resolution refutation derives an empty clause (contradiction) when input clauses are unsatisfiable."}
        ]
    },

    # --------------------------------------------------------------------------
    # 5. COMPUTER SYSTEMS & DB
    # --------------------------------------------------------------------------
    "topic_challenge": {
        1: [
            {"id": "tc_l1_01", "q": "What does HTML stand for?", "opts": ["HyperText Markup Language", "HighTech Machine Language", "Hyperlink Text Mark List", "Home Tool Markup Language"], "ans": 0, "exp": "HTML stands for HyperText Markup Language."},
            {"id": "tc_l1_02", "q": "Which component manages computer hardware and system resources?", "opts": ["Operating System", "Web Browser", "Text Editor", "Database Engine"], "ans": 0, "exp": "Operating Systems (OS) interface between hardware and application software."},
            {"id": "tc_l1_03", "q": "What does IP stand for in IP address?", "opts": ["Internet Protocol", "Internal Provider", "Interface Port", "Information Packet"], "ans": 0, "exp": "IP stands for Internet Protocol."},
            {"id": "tc_l1_04", "q": "What is a Primary Key in a database table?", "opts": ["A unique identifier for each row", "A key to unlock database software", "The first column in any table", "A password"], "ans": 0, "exp": "Primary key uniquely identifies each record/tuple in a relational table."},
            {"id": "tc_l1_05", "q": "Which protocol is used for secure web browsing?", "opts": ["HTTPS", "HTTP", "FTP", "SMTP"], "ans": 0, "exp": "HTTPS encrypts HTTP traffic using TLS/SSL."}
        ],
        2: [
            {"id": "tc_l2_01", "q": "Which OSI layer is responsible for routing packets across networks?", "opts": ["Network Layer", "Transport Layer", "Data Link Layer", "Application Layer"], "ans": 0, "exp": "Layer 3 (Network Layer) performs IP routing."},
            {"id": "tc_l2_02", "q": "In SQL, which clause filters rows AFTER aggregation?", "opts": ["HAVING", "WHERE", "GROUP BY", "ORDER BY"], "ans": 0, "exp": "`WHERE` filters individual rows before grouping; `HAVING` filters aggregated groups."},
            {"id": "tc_l2_03", "q": "What is virtual memory in an Operating System?", "opts": ["Memory management technique using disk space to extend physical RAM", "Graphics RAM", "ROM memory", "Cloud storage"], "ans": 0, "exp": "Virtual memory maps virtual addresses to physical RAM and secondary disk paging space."},
            {"id": "tc_l2_04", "q": "Which HTTP method is idempotent and used to retrieve data?", "opts": ["GET", "POST", "PATCH", "CONNECT"], "ans": 0, "exp": "GET requests fetch representations without side effects on server state."},
            {"id": "tc_l2_05", "q": "What does DNS stand for?", "opts": ["Domain Name System", "Digital Network Service", "Data Network Storage", "Domain Node Server"], "ans": 0, "exp": "DNS translates domain names (e.g. edumind.app) to IP addresses."}
        ],
        3: [
            {"id": "tc_l3_01", "q": "What is First Normal Form (1NF) requirement in relational databases?", "opts": ["All table attributes must contain atomic (indivisible) values", "Eliminate transitive dependencies", "Eliminate partial dependencies", "Use foreign keys"], "ans": 0, "exp": "1NF requires columns to contain atomic values with no repeating groups."},
            {"id": "tc_l3_02", "q": "In TCP 3-way handshake, what is the sequence of control flags sent?", "opts": ["SYN -> SYN-ACK -> ACK", "ACK -> SYN -> ACK", "FIN -> ACK -> FIN", "SYN -> ACK -> RST"], "ans": 0, "exp": "TCP connection setup exchanges SYN, SYN-ACK, and ACK."},
            {"id": "tc_l3_03", "q": "What is a Mutex (Mutual Exclusion object)?", "opts": ["Synchronization primitive that prevents concurrent access to a shared resource", "Disk buffer", "Network router", "CPU register"], "ans": 0, "exp": "Mutex locks allow only one thread at a time into a critical section."},
            {"id": "tc_l3_04", "q": "What is the subnet mask for a standard Class C IPv4 network (/24)?", "opts": ["255.255.255.0", "255.255.0.0", "255.0.0.0", "255.255.255.255"], "ans": 0, "exp": "/24 prefix leaves 8 bits for hosts, giving mask 255.255.255.0."},
            {"id": "tc_l3_05", "q": "Which SQL JOIN returns all matching rows plus unmatched rows from left table?", "opts": ["LEFT OUTER JOIN", "INNER JOIN", "RIGHT OUTER JOIN", "FULL OUTER JOIN"], "ans": 0, "exp": "LEFT JOIN keeps all rows from left table regardless of right table match."}
        ],
        4: [
            {"id": "tc_l4_01", "q": "What distinguishes 3NF (Third Normal Form) from BCNF (Boyce-Codd Normal Form)?", "opts": ["BCNF requires every determinant to be a super key for all functional dependencies", "3NF handles multi-valued dependencies", "BCNF allows transitive dependencies", "3NF is stricter than BCNF"], "ans": 0, "exp": "BCNF eliminates anomalies in tables with multiple overlapping candidate keys where 3NF falls short."},
            {"id": "tc_l4_02", "q": "In TCP, what mechanism prevents sender from overwhelming receiver's buffer?", "opts": ["Flow Control (Sliding Window)", "Congestion Control", "Checksum", "Time To Live (TTL)"], "ans": 0, "exp": "Flow control uses window size advertised by receiver to regulate data transmission rate."},
            {"id": "tc_l4_03", "q": "What is Thrashing in an operating system?", "opts": ["High page fault rate causing OS to spend more time swapping pages than executing processes", "Disk failure", "CPU overheating", "Deadlock condition"], "ans": 0, "exp": "Thrashing occurs when active working set size exceeds available physical memory frames."},
            {"id": "tc_l4_04", "q": "Which isolation level in ANSI SQL prevents Dirty Reads, Non-Repeatable Reads, AND Phantom Reads?", "opts": ["SERIALIZABLE", "REPEATABLE READ", "READ COMMITTED", "READ UNCOMMITTED"], "ans": 0, "exp": "SERIALIZABLE is highest isolation level providing complete transaction execution isolation."},
            {"id": "tc_l4_05", "q": "What is the main role of ARP (Address Resolution Protocol)?", "opts": ["Map IPv4 addresses to MAC (hardware) addresses", "Translate domain names to IP", "Assign dynamic IP addresses", "Filter firewall ports"], "ans": 0, "exp": "ARP resolves Layer 3 IP addresses to Layer 2 Ethernet MAC addresses."}
        ],
        5: [
            {"id": "tc_l5_01", "q": "How does Raft consensus protocol guarantee state machine safety across nodes?", "opts": ["Leader election with strict log matching property and committed entry validation", "By using central master database", "By broadcasting UDP packets", "Using round-robin scheduling"], "ans": 0, "exp": "Raft ensures log matching: if a leader commits an entry at index & term, all nodes mirror that exact entry."},
            {"id": "tc_l5_02", "q": "In Linux kernel, what is the key difference between `epoll` and `select` system calls for I/O multiplexing?", "opts": ["`epoll` is O(1) per event notification while `select` scans O(N) file descriptors", "`select` is faster", "`epoll` is deprecated", "`select` supports 1 million sockets"], "ans": 0, "exp": "`epoll` uses OS event callbacks (O(1)), avoiding `select`'s file descriptor array scanning overhead (O(N))."},
            {"id": "tc_l5_03", "q": "What causes Phantom Reads in database transactions despite REPEATABLE READ in standard SQL?", "opts": ["Another transaction inserts new rows matching a range query during execution", "Reading uncommitted updates", "Reading old cached data", "Foreign key constraint failure"], "ans": 0, "exp": "Phantom reads occur when a transaction re-executes a range query and sees new rows inserted by a committed transaction."},
            {"id": "tc_l5_04", "q": "Which BGP (Border Gateway Protocol) attribute is prioritized first in standard path selection algorithm?", "opts": ["LOCAL_PREF (Local Preference)", "MED (Multi-Exit Discriminator)", "AS-Path Length", "Origin Type"], "ans": 0, "exp": "BGP decision process first evaluates Highest Weight (Cisco) then Highest LOCAL_PREF."},
            {"id": "tc_l5_05", "q": "In distributed storage (e.g. DynamoDB/Cassandra), what does Consistent Hashing accomplish?", "opts": ["Minimizes key remapping when nodes are added or removed from ring", "Guarantees 100% ACID transactions", "Encrypts stored keys", "Forces single primary node"], "ans": 0, "exp": "Consistent hashing maps keys and nodes to a circular ring, requiring remapping of only K/N keys upon node changes."}
        ]
    },

    # --------------------------------------------------------------------------
    # 6. MENTAL MATH
    # --------------------------------------------------------------------------
    "mental_math": {
        1: [
            {"id": "mm_l1_01", "q": "Calculate: 12 + 15", "opts": ["27", "25", "30", "28"], "ans": 0, "exp": "12 + 15 = 27."},
            {"id": "mm_l1_02", "q": "Calculate: 50 - 18", "opts": ["32", "38", "30", "34"], "ans": 0, "exp": "50 - 18 = 32."},
            {"id": "mm_l1_03", "q": "Calculate: 6 * 7", "opts": ["42", "40", "48", "36"], "ans": 0, "exp": "6 * 7 = 42."},
            {"id": "mm_l1_04", "q": "Calculate: 64 / 8", "opts": ["8", "7", "9", "6"], "ans": 0, "exp": "64 / 8 = 8."},
            {"id": "mm_l1_05", "q": "Calculate: 9 + 14", "opts": ["23", "21", "25", "22"], "ans": 0, "exp": "9 + 14 = 23."}
        ],
        2: [
            {"id": "mm_l2_01", "q": "Calculate: 15 * 14", "opts": ["210", "200", "220", "190"], "ans": 0, "exp": "15 * 10 = 150; 15 * 4 = 60; 150 + 60 = 210."},
            {"id": "mm_l2_02", "q": "Calculate: 144 / 12 + 18", "opts": ["30", "28", "32", "26"], "ans": 0, "exp": "144 / 12 = 12. 12 + 18 = 30."},
            {"id": "mm_l2_03", "q": "Calculate: 25 * 16", "opts": ["400", "350", "450", "380"], "ans": 0, "exp": "25 * 4 * 4 = 100 * 4 = 400."},
            {"id": "mm_l2_04", "q": "Calculate: 250 - 85", "opts": ["165", "155", "175", "160"], "ans": 0, "exp": "250 - 80 = 170; 170 - 5 = 165."},
            {"id": "mm_l2_05", "q": "Calculate: 81 / 9 * 7", "opts": ["63", "54", "72", "65"], "ans": 0, "exp": "81 / 9 = 9; 9 * 7 = 63."}
        ],
        3: [
            {"id": "mm_l3_01", "q": "Calculate: 18 * 25", "opts": ["450", "400", "425", "475"], "ans": 0, "exp": "18 * 100 / 4 = 1800 / 4 = 450."},
            {"id": "mm_l3_02", "q": "Calculate: 17^2 (17 squared)", "opts": ["289", "279", "299", "269"], "ans": 0, "exp": "17 * 17 = 289."},
            {"id": "mm_l3_03", "q": "Calculate: 15% of 480", "opts": ["72", "68", "75", "80"], "ans": 0, "exp": "10% = 48, 5% = 24. 48 + 24 = 72."},
            {"id": "mm_l3_04", "q": "Calculate: 500 - 187", "opts": ["313", "323", "303", "317"], "ans": 0, "exp": "500 - 180 = 320; 320 - 7 = 313."},
            {"id": "mm_l3_05", "q": "Calculate: 720 / 16", "opts": ["45", "40", "50", "42"], "ans": 0, "exp": "720 / 8 = 90; 90 / 2 = 45."}
        ],
        4: [
            {"id": "mm_l4_01", "q": "Calculate: 35 * 45", "opts": ["1575", "1525", "1625", "1475"], "ans": 0, "exp": "(40-5)(40+5) = 1600 - 25 = 1575."},
            {"id": "mm_l4_02", "q": "Calculate: 31^2", "opts": ["961", "941", "951", "971"], "ans": 0, "exp": "(30+1)^2 = 900 + 60 + 1 = 961."},
            {"id": "mm_l4_03", "q": "Calculate: 27 * 11", "opts": ["297", "287", "307", "277"], "ans": 0, "exp": "27 * 10 + 27 = 270 + 27 = 297."},
            {"id": "mm_l4_04", "q": "Calculate: 35% of 640", "opts": ["224", "210", "230", "240"], "ans": 0, "exp": "30% (192) + 5% (32) = 224."},
            {"id": "mm_l4_05", "q": "Calculate: sqrt(1024)", "opts": ["32", "28", "34", "36"], "ans": 0, "exp": "32^2 = 1024 (2^10)."}
        ],
        5: [
            {"id": "mm_l5_01", "q": "Calculate: 98 * 97", "opts": ["9506", "9406", "9606", "9504"], "ans": 0, "exp": "Vedic Math: (100-2)(100-3) = (95 | 06) = 9506."},
            {"id": "mm_l5_02", "q": "Calculate cube root of 13824: cbrt(13824)", "opts": ["24", "22", "26", "28"], "ans": 0, "exp": "Ends in 4 (so unit digit 4). 13 is between 2^3 (8) and 3^3 (27). Answer 24."},
            {"id": "mm_l5_03", "q": "Calculate: 125 * 32", "opts": ["4000", "3800", "4200", "3600"], "ans": 0, "exp": "125 * 8 * 4 = 1000 * 4 = 4000."},
            {"id": "mm_l5_04", "q": "Calculate: 45^2 - 35^2", "opts": ["800", "750", "900", "700"], "ans": 0, "exp": "Algebraic identity: (45-35)(45+35) = 10 * 80 = 800."},
            {"id": "mm_l5_05", "q": "Calculate exact remainder: 2^20 mod 7", "opts": ["4", "1", "2", "3"], "ans": 0, "exp": "By Fermat's Little Theorem, 2^6 = 1 (mod 7). 2^18 = 1. 2^20 = 2^2 = 4 (mod 7)."}
        ]
    },

    # --------------------------------------------------------------------------
    # 7. VOCABULARY CHALLENGE
    # --------------------------------------------------------------------------
    "vocab_challenge": {
        1: [
            {"id": "vc_l1_01", "q": "Synonym of 'PERSEVERE':", "opts": ["Persist", "Quit", "Hesitate", "Falter"], "ans": 0, "exp": "'Persevere' means to continue steadfastly in a course of action."},
            {"id": "vc_l1_02", "q": "Antonym of 'LUCID':", "opts": ["Confusing", "Clear", "Bright", "Transparent"], "ans": 0, "exp": "'Lucid' means clear/intelligible. 'Confusing' is its opposite."},
            {"id": "vc_l1_03", "q": "What does 'CONCISE' mean?", "opts": ["Brief and comprehensive", "Extremely long", "Vague", "Noisy"], "ans": 0, "exp": "Concise means giving a lot of information clearly and in few words."},
            {"id": "vc_l1_04", "q": "Synonym of 'FAST':", "opts": ["Rapid", "Slow", "Heavy", "Calm"], "ans": 0, "exp": "Rapid means happening or moving with great speed."},
            {"id": "vc_l1_05", "q": "Antonym of 'OPTIMISTIC':", "opts": ["Pessimistic", "Hopeful", "Positive", "Joyful"], "ans": 0, "exp": "Pessimistic means expecting the worst outcome."}
        ],
        2: [
            {"id": "vc_l2_01", "q": "What does 'MUTABLE' mean in programming?", "opts": ["Subject to change or modification", "Read-only / Unchangeable", "Encrypted", "Static"], "ans": 0, "exp": "Mutable objects can have their state or contents changed after creation."},
            {"id": "vc_l2_02", "q": "Antonym of 'IMMUTABLE':", "opts": ["Variable / Changeable", "Fixed", "Permanent", "Constant"], "ans": 0, "exp": "Immutable means unchangeable; its antonym is changeable/mutable."},
            {"id": "vc_l2_03", "q": "What does 'DEPRECATED' mean in software development?", "opts": ["Feature marked for future removal and no longer recommended", "Newly added feature", "High speed execution", "Encrypted code"], "ans": 0, "exp": "Deprecated software features are discouraged because they will be removed in future releases."},
            {"id": "vc_l2_04", "q": "Synonym of 'AUGMENT':", "opts": ["Increase / Expand", "Reduce", "Cancel", "Hide"], "ans": 0, "exp": "To augment means to make something greater by adding to it."},
            {"id": "vc_l2_05", "q": "What does 'PARALLEL' mean in computation?", "opts": ["Executing multiple tasks simultaneously", "Executing tasks one by one sequentially", "Pausing execution", "Deleting threads"], "ans": 0, "exp": "Parallel processing performs multiple calculations at the exact same instant."}
        ],
        3: [
            {"id": "vc_l3_01", "q": "What does 'IDEMPOTENT' mean in computer science?", "opts": ["An operation produces the same result no matter how many times it is executed", "An operation runs in logarithmic time", "A function with side effects", "A non-blocking socket"], "ans": 0, "exp": "Idempotent operations can be applied multiple times without changing the result beyond initial application."},
            {"id": "vc_l3_02", "q": "What does 'DETERMINISTIC' mean for an algorithm?", "opts": ["Always produces identical output given identical input", "Produces random outputs", "Runs only on single core", "Never terminates"], "ans": 0, "exp": "Deterministic algorithms pass through the exact same sequence of states for given inputs."},
            {"id": "vc_l3_03", "q": "Synonym of 'EPHEMERAL':", "opts": ["Transient / Short-lived", "Permanent", "Durable", "Continuous"], "ans": 0, "exp": "Ephemeral means lasting for a very short time (e.g. ephemeral storage/ports)."},
            {"id": "vc_l3_04", "q": "What is 'HEURISTIC' in problem solving?", "opts": ["Practical technique not guaranteed optimal but sufficient for immediate goals", "Mathematically exact proof", "Brute force search", "Compiler optimization flag"], "ans": 0, "exp": "Heuristics speed up finding a satisfactory solution when optimal solutions are intractable."},
            {"id": "vc_l3_05", "q": "What does 'AMORTIZED' time complexity refer to?", "opts": ["Average time per operation over a sequence of operations", "Worst-case single step time", "Best-case setup time", "Disk seek latency"], "ans": 0, "exp": "Amortized analysis averages time taken over a worst-case sequence of operations (e.g. dynamic array resize)."}
        ],
        4: [
            {"id": "vc_l4_01", "q": "What does 'ASYMPTOTIC' mean in algorithm analysis?", "opts": ["Approaching a limiting value or behavior as input size grows to infinity", "Exact execution time in seconds", "CPU clock cycle duration", "Memory byte layout"], "ans": 0, "exp": "Asymptotic analysis evaluates performance limits of algorithms for large input sizes N -> infinity."},
            {"id": "vc_l4_02", "q": "Antonym of 'SYNCHRONOUS':", "opts": ["Asynchronous", "Sequential", "Monolithic", "Blocking"], "ans": 0, "exp": "Asynchronous operations run independently without blocking caller execution flow."},
            {"id": "vc_l4_03", "q": "What does 'POLYMORPHISM' mean in OOP?", "opts": ["Ability of different classes to respond to same method call in unique ways", "Data hiding", "Single class definition", "Static typing"], "ans": 0, "exp": "Polymorphism (many forms) allows objects of different types to be treated via common interface."},
            {"id": "vc_l4_04", "q": "Synonym of 'UBIQUITOUS':", "opts": ["Omnipresent / Present everywhere", "Rare", "Isolated", "Obsolete"], "ans": 0, "exp": "Ubiquitous means found everywhere (e.g. ubiquitous computing)."},
            {"id": "vc_l4_05", "q": "What is 'ORTHOGONALITY' in software architecture?", "opts": ["Designing components such that changing one does not affect others", "Coupling components tightly", "Using 90-degree vector graphics", "Duplicating code logic"], "ans": 0, "exp": "Orthogonal systems have independent components where changes stay isolated."}
        ],
        5: [
            {"id": "vc_l5_01", "q": "What does 'LINEARIZABILITY' guarantee in distributed systems?", "opts": ["Real-time global order where operations appear to execute atomically at a point between invocation and response", "Eventual consistency only", "No network latency", "Zero storage overhead"], "ans": 0, "exp": "Linearizability (strong consistency) imposes strict global real-time ordering on operations across nodes."},
            {"id": "vc_l5_02", "q": "What does 'BYZANTINE' fault tolerance address?", "opts": ["Arbitrary faults including malicious or traitorous node behavior sending conflicting messages", "Simple power outages", "Disk space exhaustion", "Single point network cable cuts"], "ans": 0, "exp": "Byzantine fault tolerance handles nodes that fail arbitrarily or act maliciously."},
            {"id": "vc_l5_03", "q": "What is 'REENTRANCY' in programming languages?", "opts": ["A routine can be safely interrupted and re-invoked before previous executions complete", "Recursive loops", "Dynamic linking", "Automatic garbage collection"], "ans": 0, "exp": "Reentrant functions hold no static unshared state and can be interrupted/re-entered safely."},
            {"id": "vc_l5_04", "q": "What does 'HOMOMORPHIC' encryption allow?", "opts": ["Performing computations directly on encrypted ciphertext without decrypting it first", "Decrypting without a key", "Symmetric key exchange", "Hashing passwords"], "ans": 0, "exp": "Homomorphic encryption produces an encrypted result matching operations performed on plaintext."},
            {"id": "vc_l5_05", "q": "What does 'SCAVENGING' refer to in garbage collection algorithms?", "opts": ["Copying live objects from nursery memory spaces (e.g. Eden) to survivor spaces", "Deleting all files", "Fragmenting heap", "Defragmenting swap disk"], "ans": 0, "exp": "Scavenger GCs evacuate live objects from young generation regions into compact survivor spaces."}
        ]
    },

    # --------------------------------------------------------------------------
    # 8. SPEED CALCULATION
    # --------------------------------------------------------------------------
    "speed_math": {
        1: [
            {"id": "sm_l1_01", "q": "What is 2^3?", "opts": ["8", "6", "9", "16"], "ans": 0, "exp": "2 * 2 * 2 = 8."},
            {"id": "sm_l1_02", "q": "What is 10 mod 3?", "opts": ["1", "3", "0", "2"], "ans": 0, "exp": "10 divided by 3 gives quotient 3 and remainder 1."},
            {"id": "sm_l1_03", "q": "What is 7 * 8?", "opts": ["56", "54", "64", "49"], "ans": 0, "exp": "7 * 8 = 56."},
            {"id": "sm_l1_04", "q": "What is 100 - 37?", "opts": ["63", "73", "53", "67"], "ans": 0, "exp": "100 - 37 = 63."},
            {"id": "sm_l1_05", "q": "What is 15 + 28?", "opts": ["43", "45", "41", "44"], "ans": 0, "exp": "15 + 28 = 43."}
        ],
        2: [
            {"id": "sm_l2_01", "q": "What is 2^8?", "opts": ["256", "128", "512", "1024"], "ans": 0, "exp": "2^8 = 256."},
            {"id": "sm_l2_02", "q": "What is 17 mod 5?", "opts": ["2", "3", "1", "4"], "ans": 0, "exp": "17 = 3 * 5 + 2. Remainder is 2."},
            {"id": "sm_l2_03", "q": "What is 16 * 6?", "opts": ["96", "86", "106", "92"], "ans": 0, "exp": "16 * 6 = 96."},
            {"id": "sm_l2_04", "q": "What is 225 / 15?", "opts": ["15", "25", "12", "18"], "ans": 0, "exp": "15 * 15 = 225."},
            {"id": "sm_l2_05", "q": "What is 8^2 + 6^2?", "opts": ["100", "96", "108", "84"], "ans": 0, "exp": "64 + 36 = 100."}
        ],
        3: [
            {"id": "sm_l3_01", "q": "What is 2^10?", "opts": ["1024", "512", "2048", "4096"], "ans": 0, "exp": "2^10 = 1024 (1 Kilobyte in binary)."},
            {"id": "sm_l3_02", "q": "What is 47 mod 9?", "opts": ["2", "4", "3", "5"], "ans": 0, "exp": "47 = 5 * 9 + 2. Remainder 2."},
            {"id": "sm_l3_03", "q": "What is 13 * 13?", "opts": ["169", "159", "179", "149"], "ans": 0, "exp": "13^2 = 169."},
            {"id": "sm_l3_04", "q": "What is 3^4?", "opts": ["81", "27", "243", "64"], "ans": 0, "exp": "3 * 3 * 3 * 3 = 81."},
            {"id": "sm_l3_05", "q": "What is 500 / 25 * 4?", "opts": ["80", "100", "20", "40"], "ans": 0, "exp": "500 / 25 = 20; 20 * 4 = 80."}
        ],
        4: [
            {"id": "sm_l4_01", "q": "What is 2^16?", "opts": ["65536", "32768", "131072", "64000"], "ans": 0, "exp": "2^16 = 65,536 (Max unsigned 16-bit int + 1)."},
            {"id": "sm_l4_02", "q": "What is 123 mod 11?", "opts": ["2", "1", "3", "4"], "ans": 0, "exp": "123 = 11 * 11 + 2. Remainder 2."},
            {"id": "sm_l4_03", "q": "What is 25^2 - 15^2?", "opts": ["400", "300", "500", "450"], "ans": 0, "exp": "625 - 225 = 400."},
            {"id": "sm_l4_04", "q": "What is log2(1024)?", "opts": ["10", "8", "12", "9"], "ans": 0, "exp": "2^10 = 1024."},
            {"id": "sm_l4_05", "q": "What is 14 * 16?", "opts": ["224", "214", "234", "204"], "ans": 0, "exp": "(15-1)(15+1) = 225 - 1 = 224."}
        ],
        5: [
            {"id": "sm_l5_01", "q": "What is 2^20?", "opts": ["1048576", "524288", "2097152", "1000000"], "ans": 0, "exp": "2^20 = 1,048,576 (1 Megabyte in binary)."},
            {"id": "sm_l5_02", "q": "Evaluate: (17^2) mod 7", "opts": ["2", "3", "1", "4"], "ans": 0, "exp": "17 mod 7 = 3. 3^2 = 9 mod 7 = 2."},
            {"id": "sm_l5_03", "q": "What is log2(65536)?", "opts": ["16", "14", "18", "15"], "ans": 0, "exp": "2^16 = 65536."},
            {"id": "sm_l5_04", "q": "Evaluate: 99^2", "opts": ["9801", "9901", "9701", "9811"], "ans": 0, "exp": "(100-1)^2 = 10000 - 200 + 1 = 9801."},
            {"id": "sm_l5_05", "q": "Evaluate bitwise XOR: 0b1010 ^ 0b1100", "opts": ["0b0110 (6)", "0b1110 (14)", "0b1000 (8)", "0b0010 (2)"], "ans": 0, "exp": "1010 ^ 1100 = 0110 in binary (decimal 6)."}
        ]
    }
}


# ==============================================================================
# GAMES ENGINE CLASS
# ==============================================================================
class GamesEngine:

    @staticmethod
    def get_unlocked_level(game_id: str, user_id: str = "user_default") -> int:
        """Get the highest level unlocked for user_id (1 to 5) from MongoDB."""
        if "game_levels" in st.session_state and game_id in st.session_state.game_levels:
            return st.session_state.game_levels[game_id]

        progress = mongodb.get_user_game_progress(user_id, game_id)
        highest = progress.get("highest_unlocked_level", 1)

        if "game_levels" not in st.session_state:
            st.session_state.game_levels = {}
        st.session_state.game_levels[game_id] = highest
        return highest

    @staticmethod
    def get_level_reward(level: int) -> int:
        """Retrieve level coin reward."""
        return LEVEL_REWARDS.get(level, 5)

    @staticmethod
    def get_game_questions(game_id: str, level: int = 1, count: int = QUESTIONS_PER_GAME) -> List[Dict[str, Any]]:
        """
        Retrieve question pool strictly for game_id and level.
        Enforces zero question overlap across levels.
        Applies option shuffling while preserving correct answer matching.
        """
        level = max(1, min(5, int(level)))
        game_dict = GAME_QUESTIONS_DB.get(game_id, GAME_QUESTIONS_DB["quick_quiz"])

        # Fallback to level 1 if requested level key is missing
        pool = game_dict.get(level)
        if not pool:
            pool = game_dict.get(1, GAME_QUESTIONS_DB["quick_quiz"][1])

        # Deep copy to avoid mutating global database
        raw_items = copy.deepcopy(pool)
        random.shuffle(raw_items)
        selected_raw = raw_items[:count]

        processed_questions = []
        for q_item in selected_raw:
            original_opts = q_item["opts"]
            correct_text = original_opts[q_item["ans"]]

            # Shuffle options
            shuffled_opts = copy.deepcopy(original_opts)
            random.shuffle(shuffled_opts)
            new_ans_idx = shuffled_opts.index(correct_text)

            q_item["opts"] = shuffled_opts
            q_item["ans"] = new_ans_idx
            q_item["level"] = level
            q_item["coins"] = LEVEL_REWARDS.get(level, 5)
            processed_questions.append(q_item)

        return processed_questions

    @staticmethod
    def process_game_results(game_id: str, level: int, score: int, total: int, user_id: str = "user_default") -> Dict[str, Any]:
        """
        Process game completion, update user MongoDB progress, award coins.
        """
        pct = round((score / total) * 100, 1) if total > 0 else 0.0
        session_id = str(uuid.uuid4())[:8]

        is_win = pct >= 60.0
        is_perfect = pct >= 100.0

        coins_awarded = 0
        level_reward = LEVEL_REWARDS.get(level, 5)

        # Base completion reward (+5)
        if CoinManager.claim_reward(
            reward_id=f"game_comp_{game_id}_l{level}_{session_id}",
            amount=5,
            reason=f"Completed {game_id} (Level {level})",
            source="games"
        ):
            coins_awarded += 5

        # Level victory reward (+ level_reward)
        if is_win:
            if CoinManager.claim_reward(
                reward_id=f"game_win_{game_id}_l{level}_{session_id}",
                amount=level_reward,
                reason=f"Cleared Level {level} of {game_id}!",
                source="games"
            ):
                coins_awarded += level_reward

        # Perfect score bonus (+15)
        if is_perfect:
            if CoinManager.claim_reward(
                reward_id=f"game_perfect_{game_id}_l{level}_{session_id}",
                amount=15,
                reason=f"Perfect Score on {game_id} (Level {level})!",
                source="games"
            ):
                coins_awarded += 15

        # Update MongoDB Game Progress per user_id
        progress_rec = mongodb.save_user_game_progress(
            user_id=user_id,
            game_id=game_id,
            level_played=level,
            score=score,
            total_questions=total,
            coins_earned=coins_awarded
        )

        # Update session state cache
        if "game_levels" not in st.session_state:
            st.session_state.game_levels = {}
        st.session_state.game_levels[game_id] = progress_rec.get("highest_unlocked_level", level)

        # Record activity for achievements & streaks
        CoinManager.record_study_activity("games_played")
        if is_win:
            CoinManager.record_study_activity("games_won")

        return {
            "score": score,
            "total": total,
            "percentage": pct,
            "is_win": is_win,
            "is_perfect": is_perfect,
            "coins_earned": coins_awarded,
            "level": level,
            "highest_unlocked": progress_rec.get("highest_unlocked_level", level),
            "unlocked_next": (is_win and level < 5),
            "best_score": progress_rec.get("best_score", pct)
        }
