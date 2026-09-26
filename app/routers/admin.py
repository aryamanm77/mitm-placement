"""
Admin router – handles department admin auth + student management + analytics.
"""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional
import json

from app.models import (
    get_db, DepartmentAdmin, Student, StudentEvaluation,
    PlacementRecord, Resource, Faculty
)
from app.auth import verify_password, create_access_token, decode_token, hash_password

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

ROUNDS = ["Aptitude", "Group Discussion", "HR Round", "Coding - C", "Coding - Java", "Coding - DSA"]
BRANCHES = ["Information Science", "Computer Science", "Electronics and Communication", "Mechanical Engineering"]


# ─────────────── helpers ────────────────────────────────────────────────────

def get_current_admin(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("admin_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("role") != "admin":
        return None
    admin = db.query(DepartmentAdmin).filter_by(id=payload["sub"]).first()
    return admin


def require_admin(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        raise HTTPException(status_code=307, headers={"Location": "/admin/login"})
    return admin


# ─────────────── auth ───────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})


@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = db.query(DepartmentAdmin).filter_by(email=email).first()
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "Invalid email or password."}
        )
    token = create_access_token({"sub": admin.id, "role": "admin", "branch": admin.branch})
    response = RedirectResponse("/admin/dashboard", status_code=302)
    response.set_cookie("admin_token", token, httponly=True, max_age=28800)
    return response


@router.get("/logout")
async def admin_logout():
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response


# ─────────────── dashboard ──────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    students = db.query(Student).filter_by(branch=admin.branch).all()
    student_ids = [s.id for s in students]

    # per-round pass rates
    round_stats = []
    for rnd in ROUNDS:
        evals = db.query(StudentEvaluation).filter(
            StudentEvaluation.student_id.in_(student_ids),
            StudentEvaluation.round_name == rnd
        ).all()
        total = len(evals)
        passed = sum(1 for e in evals if e.passed)
        round_stats.append({
            "round": rnd,
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "rate": round((passed / total * 100) if total else 0, 1)
        })

    # placements
    placed = db.query(PlacementRecord).filter(PlacementRecord.student_id.in_(student_ids)).count()

    # leaderboard: branch avg scores
    branch_scores = []
    for branch in BRANCHES:
        b_students = db.query(Student).filter_by(branch=branch).all()
        b_ids = [s.id for s in b_students]
        avg = db.query(func.avg(StudentEvaluation.score)).filter(
            StudentEvaluation.student_id.in_(b_ids)
        ).scalar() or 0
        branch_scores.append({"branch": branch, "avg": round(float(avg), 1)})
    branch_scores.sort(key=lambda x: x["avg"], reverse=True)
    top_branch = branch_scores[0] if branch_scores else None

    # Plotly chart data
    chart_data = {
        "rounds": [r["round"] for r in round_stats],
        "pass_rates": [r["rate"] for r in round_stats],
        "passed": [r["passed"] for r in round_stats],
        "failed": [r["failed"] for r in round_stats],
        "branch_names": [b["branch"] for b in branch_scores],
        "branch_avgs": [b["avg"] for b in branch_scores],
    }

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "admin": admin,
        "students": students,
        "round_stats": round_stats,
        "placed_count": placed,
        "total_count": len(students),
        "top_branch": top_branch,
        "branch_scores": branch_scores,
        "chart_data": json.dumps(chart_data),
        "rounds": ROUNDS,
        "branches": BRANCHES,
    })


# ─────────────── student management ─────────────────────────────────────────

@router.get("/students", response_class=HTMLResponse)
async def list_students(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    students = db.query(Student).filter_by(branch=admin.branch).all()
    student_data = []
    for s in students:
        evals = db.query(StudentEvaluation).filter_by(student_id=s.id).all()
        avg_score = round(sum(e.score for e in evals if e.score) / len(evals), 1) if evals else 0
        failed_rounds = [e.round_name for e in evals if not e.passed]
        student_data.append({
            "student": s,
            "avg_score": avg_score,
            "failed_rounds": failed_rounds,
            "placed": db.query(PlacementRecord).filter_by(student_id=s.id).first() is not None
        })

    return templates.TemplateResponse("admin_students.html", {
        "request": request,
        "admin": admin,
        "student_data": student_data,
        "rounds": ROUNDS,
    })


@router.post("/students/add")
async def add_student(
    request: Request,
    usn: str = Form(...),
    name: str = Form(...),
    mobile: str = Form(...),
    email: str = Form(""),
    cgpa: float = Form(0.0),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    existing = db.query(Student).filter(
        (Student.usn == usn) | (Student.mobile == mobile)
    ).first()
    if existing:
        return JSONResponse({"error": "Student with this USN or mobile already exists."}, status_code=400)

    student = Student(
        usn=usn, name=name, mobile=mobile,
        email=email, cgpa=cgpa,
        branch=admin.branch, added_by=admin.id
    )
    db.add(student)
    db.commit()
    return JSONResponse({"success": True, "student_id": student.id})


@router.get("/students/{student_id}", response_class=HTMLResponse)
async def student_detail(student_id: int, request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    student = db.query(Student).filter_by(id=student_id, branch=admin.branch).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    evals = db.query(StudentEvaluation).filter_by(student_id=student_id).all()
    placements = db.query(PlacementRecord).filter_by(student_id=student_id).all()

    # spider/radar chart data
    scores = {e.round_name: e.score for e in evals if e.score}
    chart = {
        "rounds": ROUNDS,
        "scores": [scores.get(r, 0) for r in ROUNDS],
    }

    return templates.TemplateResponse("admin_student_detail.html", {
        "request": request,
        "admin": admin,
        "student": student,
        "evals": evals,
        "placements": placements,
        "chart": json.dumps(chart),
        "rounds": ROUNDS,
    })


@router.post("/students/{student_id}/evaluate")
async def save_evaluation(
    student_id: int,
    request: Request,
    round_name: str = Form(...),
    score: float = Form(...),
    feedback: str = Form(""),
    english_score: float = Form(0),
    technical_score: float = Form(0),
    communication_score: float = Form(0),
    problem_solving_score: float = Form(0),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # upsert
    existing = db.query(StudentEvaluation).filter_by(
        student_id=student_id, round_name=round_name
    ).first()

    if existing:
        existing.score = score
        existing.passed = score >= 60
        existing.feedback = feedback
        existing.english_score = english_score
        existing.technical_score = technical_score
        existing.communication_score = communication_score
        existing.problem_solving_score = problem_solving_score
        existing.evaluated_at = datetime.utcnow()
    else:
        ev = StudentEvaluation(
            student_id=student_id, round_name=round_name,
            score=score, passed=score >= 60, feedback=feedback,
            english_score=english_score, technical_score=technical_score,
            communication_score=communication_score,
            problem_solving_score=problem_solving_score,
            evaluated_by=admin.id
        )
        db.add(ev)

    db.commit()
    return JSONResponse({"success": True})


@router.post("/students/{student_id}/placement")
async def add_placement(
    student_id: int,
    request: Request,
    company_name: str = Form(...),
    role: str = Form(""),
    package_lpa: float = Form(0),
    placement_type: str = Form("Campus"),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    pr = PlacementRecord(
        student_id=student_id, company_name=company_name,
        role=role, package_lpa=package_lpa,
        offer_date=datetime.utcnow(), placement_type=placement_type
    )
    db.add(pr)
    db.commit()
    return JSONResponse({"success": True})


# ─────────────── analytics API ──────────────────────────────────────────────

@router.get("/api/analytics")
async def analytics_api(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    students = db.query(Student).filter_by(branch=admin.branch).all()
    ids = [s.id for s in students]

    data = {}
    for rnd in ROUNDS:
        evals = db.query(StudentEvaluation).filter(
            StudentEvaluation.student_id.in_(ids),
            StudentEvaluation.round_name == rnd
        ).all()
        total = len(evals)
        passed = sum(1 for e in evals if e.passed)
        data[rnd] = {"passed": passed, "failed": total - passed, "rate": round(passed / total * 100 if total else 0, 1)}

    return JSONResponse(data)
