"""
Seed the database with realistic dummy data for MITM Mysore – IS branch.
Run once: python app/seed.py
"""
import sys, os, random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import (
    create_tables, SessionLocal,
    DepartmentAdmin, Student, StudentEvaluation,
    PlacementRecord, Resource, Faculty
)
from passlib.hash import bcrypt

BRANCHES = [
    "Information Science",
    "Computer Science",
    "Electronics and Communication",
    "Mechanical Engineering",
]

ROUNDS = [
    "Aptitude", "Group Discussion",
    "HR Round", "Coding - C", "Coding - Java", "Coding - DSA"
]

IS_STUDENTS = [
    ("1MS21IS001", "Aditya Sharma",     "9876543210"),
    ("1MS21IS002", "Bhavana Reddy",     "9876543211"),
    ("1MS21IS003", "Chandan Kumar",     "9876543212"),
    ("1MS21IS004", "Deepika Nair",      "9876543213"),
    ("1MS21IS005", "Eshan Patel",       "9876543214"),
    ("1MS21IS006", "Farida Begum",      "9876543215"),
    ("1MS21IS007", "Ganesh Rao",        "9876543216"),
    ("1MS21IS008", "Harini Iyer",       "9876543217"),
    ("1MS21IS009", "Ishaan Verma",      "9876543218"),
    ("1MS21IS010", "Janvi Mehta",       "9876543219"),
    ("1MS21IS011", "Karthik Shetty",    "9876543220"),
    ("1MS21IS012", "Lavanya Gowda",     "9876543221"),
    ("1MS21IS013", "Manoj Hegde",       "9876543222"),
    ("1MS21IS014", "Namrata Kulkarni",  "9876543223"),
    ("1MS21IS015", "Om Prakash",        "9876543224"),
]

CS_STUDENTS = [
    ("1MS21CS001", "Pranav Singh",      "9876544100"),
    ("1MS21CS002", "Rashmi Patil",      "9876544101"),
    ("1MS21CS003", "Sagar Joshi",       "9876544102"),
    ("1MS21CS004", "Tanvi Desai",       "9876544103"),
    ("1MS21CS005", "Uday Kumar",        "9876544104"),
]

EC_STUDENTS = [
    ("1MS21EC001", "Varun Shetty",      "9876544200"),
    ("1MS21EC002", "Vidya Gowda",       "9876544201"),
    ("1MS21EC003", "Wishal Nair",       "9876544202"),
]

ME_STUDENTS = [
    ("1MS21ME001", "Yash Thakkar",      "9876544300"),
    ("1MS21ME002", "Zara Ali",          "9876544301"),
]

RESOURCES = [
    # Aptitude
    ("IndiaBix Aptitude Practice", "video",   "https://www.indiabix.com/aptitude/questions-and-answers/",          "Aptitude",         "quant,logical"),
    ("TCS NQT Aptitude Masterclass", "video", "https://www.youtube.com/watch?v=kFBr5CY4uts",                       "Aptitude",         "TCS,quant"),
    # GD
    ("Group Discussion Tips – IIM",  "video", "https://www.youtube.com/watch?v=yXjxFV6nAMw",                       "Group Discussion",  "communication,soft-skills"),
    ("GD Topics 2024 – InsideIIM",   "article","https://insideiim.com/gd-topics",                                  "Group Discussion",  "topics"),
    # HR
    ("Top 50 HR Interview Qs – NPTEL","video","https://www.youtube.com/watch?v=HG68Ymazo18",                       "HR Round",          "behavioral,hr"),
    ("CareerVidz HR Interview",       "video", "https://www.youtube.com/watch?v=wAeqxL2NKCY",                       "HR Round",          "hr,star-method"),
    # Coding C
    ("C Programming – Apna College",  "video","https://www.youtube.com/watch?v=ZSPZob_1TOk",                       "Coding - C",        "C,basics"),
    ("GeeksForGeeks C Practice",      "course","https://practice.geeksforgeeks.org/explore?category%5B%5D=C",       "Coding - C",        "C,problems"),
    # Coding Java
    ("Java Full Course – Kunal K",    "video","https://www.youtube.com/watch?v=rZ41y93P2Qo",                       "Coding - Java",     "Java,OOP"),
    ("LeetCode Java Problems",        "course","https://leetcode.com/problemset/all/?topicSlugs=java",               "Coding - Java",     "Java,leetcode"),
    # DSA
    ("DSA Full Course – Love Babbar", "video","https://www.youtube.com/watch?v=WQoB2z67hvY",                       "Coding - DSA",      "DSA,arrays,trees"),
    ("Striver's A2Z DSA Sheet",       "course","https://takeuforward.org/strivers-a2z-dsa-course/strivers-a2z-dsa-course-sheet-2/","Coding - DSA","DSA,sheet"),
]

FACULTY = [
    ("Dr. Suresh Kumar",      "Information Science",          "Algorithms & Data Structures",   "suresh.k@mitm.ac.in",   "9845001001", "Room 301, CS Block"),
    ("Prof. Anitha Rao",      "Information Science",          "Aptitude & Reasoning",            "anitha.r@mitm.ac.in",   "9845001002", "Room 208, IS Block"),
    ("Dr. Ravi Shankar",      "Computer Science",             "Machine Learning & AI",           "ravi.s@mitm.ac.in",     "9845001003", "Room 401, CS Block"),
    ("Prof. Meera Bhat",      "Electronics and Communication","VLSI & Embedded Systems",         "meera.b@mitm.ac.in",    "9845001004", "Room 110, EC Block"),
    ("Dr. Nagaraj Hegde",     "Mechanical Engineering",        "CAD & Manufacturing",            "nagaraj.h@mitm.ac.in",  "9845001005", "Room 210, ME Block"),
    ("Prof. Kavitha S",       "Information Science",          "Communication & Soft Skills",     "kavitha.s@mitm.ac.in",  "9845001006", "Room 305, IS Block"),
    ("Prof. Arun Prasad",     "Computer Science",             "Java & Web Technologies",         "arun.p@mitm.ac.in",     "9845001007", "Room 402, CS Block"),
]


def seed():
    create_tables()
    db = SessionLocal()

    try:
        if db.query(DepartmentAdmin).count() > 0:
            print("Database already seeded. Skipping.")
            return

        # ── Admins ──────────────────────────────────────────────────────────
        admins = {}
        for branch in BRANCHES:
            code = branch.split()[0][:2].upper()
            admin = DepartmentAdmin(
                name=f"{branch} Dept. Admin",
                email=f"admin.{code.lower()}@mitm.ac.in",
                password_hash=bcrypt.hash("Admin@1234"),
                branch=branch,
            )
            db.add(admin)
            db.flush()
            admins[branch] = admin
        db.commit()

        # ── Students ─────────────────────────────────────────────────────────
        all_student_data = (
            [(d[0], d[1], d[2], "Information Science")          for d in IS_STUDENTS] +
            [(d[0], d[1], d[2], "Computer Science")             for d in CS_STUDENTS] +
            [(d[0], d[1], d[2], "Electronics and Communication")for d in EC_STUDENTS] +
            [(d[0], d[1], d[2], "Mechanical Engineering")        for d in ME_STUDENTS]
        )

        student_objs = {}
        for usn, name, mobile, branch in all_student_data:
            s = Student(
                usn=usn, name=name, mobile=mobile,
                branch=branch,
                email=f"{usn.lower()}@mitm.ac.in",
                cgpa=round(random.uniform(6.5, 9.5), 2),
                added_by=admins[branch].id,
            )
            db.add(s)
            db.flush()
            student_objs[usn] = s

        db.commit()

        # ── Evaluations ──────────────────────────────────────────────────────
        round_weights = {
            "Aptitude":         (65, 90),
            "Group Discussion": (55, 85),
            "HR Round":         (60, 92),
            "Coding - C":       (50, 88),
            "Coding - Java":    (45, 85),
            "Coding - DSA":     (40, 82),
        }

        for usn, s in student_objs.items():
            for rnd, (lo, hi) in round_weights.items():
                score = round(random.uniform(lo, hi), 1)
                passed = score >= 60
                ev = StudentEvaluation(
                    student_id=s.id,
                    round_name=rnd,
                    score=score,
                    passed=passed,
                    english_score=round(random.uniform(50, 95), 1),
                    technical_score=round(random.uniform(40, 95), 1),
                    communication_score=round(random.uniform(45, 92), 1),
                    problem_solving_score=round(random.uniform(40, 90), 1),
                    evaluated_by=admins[s.branch].id if s.branch in admins else None,
                )
                db.add(ev)

        db.commit()

        # ── Placements ───────────────────────────────────────────────────────
        placed_students = random.sample(list(student_objs.values()), k=min(10, len(student_objs)))
        companies = [
            ("Infosys", "Systems Engineer", 3.6),
            ("Flipkart", "Software Development Engineer", 19.0),
            ("Tata Consultancy Services (TCS)", "Assistant System Engineer", 3.9),
            ("IBM", "Associate System Engineer", 4.5),
            ("Kaynes Technology", "Hardware Engineer", 3.5),
            ("Tech Mahindra", "Software Engineer", 3.8),
            ("VI (Vodafone Idea)", "Graduate Engineer Trainee", 4.0),
            ("Dyashin Technosoft Pvt. Ltd.", "Software Developer", 3.6),
            ("Mphasis", "Associate Software Engineer", 3.25),
            ("Infosys", "Power Programmer", 8.0),
        ]
        for i, s in enumerate(placed_students):
            co = companies[i % len(companies)]
            db.add(PlacementRecord(
                student_id=s.id,
                company_name=co[0],
                role=co[1],
                package_lpa=co[2],
                offer_date=datetime(2024, random.randint(1, 12), random.randint(1, 28)),
                placement_type="Campus",
            ))
        db.commit()

        # ── Resources ────────────────────────────────────────────────────────
        for title, rtype, url, target, tags in RESOURCES:
            db.add(Resource(title=title, resource_type=rtype, url=url,
                            target_round=target, tags=tags))
        db.commit()

        # ── Faculty ─────────────────────────────────────────────────────────
        for name, branch, spec, email, mobile, cabin in FACULTY:
            db.add(Faculty(name=name, branch=branch, specialization=spec,
                           email=email, mobile=mobile, cabin=cabin))
        db.commit()

        print("Database seeded successfully!")
        print("\n   Admin credentials:")
        for branch, admin in admins.items():
            print(f"   [{branch}] Email: {admin.email}  |  Password: Admin@1234")
        print("\n   Sample student mobile for OTP login: 9876543210 (Aditya Sharma - IS)")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
