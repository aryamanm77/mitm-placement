"""
Student router – OTP login, personal dashboard, weakness analysis,
resources, and AI mock interview.
"""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json, os, asyncio
from groq import Groq
from dotenv import load_dotenv

from app.models import (
    get_db, Student, StudentEvaluation, PlacementRecord,
    OTPRecord, Resource, Faculty, MockInterviewSession
)
from app.auth import generate_otp, create_access_token, decode_token

load_dotenv()

router = APIRouter(prefix="/student")
templates = Jinja2Templates(directory="app/templates")
ROUNDS = ["Aptitude", "Group Discussion", "HR Round", "Coding - C", "Coding - Java", "Coding - DSA"]

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))


# ─────────────── helpers ────────────────────────────────────────────────────

def get_current_student(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("student_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("role") != "student":
        return None
    return db.query(Student).filter_by(id=payload["sub"]).first()


# ─────────────── OTP auth ───────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def student_login_page(request: Request):
    return templates.TemplateResponse("student_login.html", {"request": request, "step": "mobile"})


@router.post("/send-otp")
async def send_otp(request: Request, mobile: str = Form(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(mobile=mobile).first()
    if not student:
        return JSONResponse({"error": "Mobile number not registered. Contact your department."}, status_code=404)

    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # invalidate old OTPs
    db.query(OTPRecord).filter_by(student_id=student.id, is_used=False).update({"is_used": True})

    otp_record = OTPRecord(
        student_id=student.id, otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()

    # In production, send via SMS. For demo, return in response.
    print(f"\n📱 OTP for {student.name} ({mobile}): {otp_code}\n")

    return JSONResponse({
        "success": True,
        "message": "OTP sent successfully.",
        "demo_otp": otp_code,  # Remove in production
        "student_name": student.name
    })


@router.post("/verify-otp")
async def verify_otp(
    request: Request,
    mobile: str = Form(...),
    otp: str = Form(...),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter_by(mobile=mobile).first()
    if not student:
        return JSONResponse({"error": "Student not found."}, status_code=404)

    otp_record = db.query(OTPRecord).filter_by(
        student_id=student.id, otp_code=otp, is_used=False
    ).order_by(OTPRecord.created_at.desc()).first()

    if not otp_record:
        return JSONResponse({"error": "Invalid OTP."}, status_code=400)

    if datetime.utcnow() > otp_record.expires_at:
        return JSONResponse({"error": "OTP has expired. Please request a new one."}, status_code=400)

    otp_record.is_used = True
    db.commit()

    token = create_access_token({"sub": student.id, "role": "student"})
    response = JSONResponse({"success": True, "redirect": "/student/dashboard"})
    response.set_cookie("student_token", token, httponly=True, max_age=28800)
    return response


@router.get("/logout")
async def student_logout():
    response = RedirectResponse("/student/login", status_code=302)
    response.delete_cookie("student_token")
    return response


# ─────────────── dashboard ──────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db)):
    student = get_current_student(request, db)
    if not student:
        return RedirectResponse("/student/login", status_code=302)

    evals = db.query(StudentEvaluation).filter_by(student_id=student.id).all()
    placements = db.query(PlacementRecord).filter_by(student_id=student.id).all()
    mock_sessions = db.query(MockInterviewSession).filter_by(student_id=student.id)\
        .order_by(MockInterviewSession.started_at.desc()).limit(5).all()

    eval_map = {e.round_name: e for e in evals}
    failed_rounds = [e.round_name for e in evals if not e.passed]
    avg_score = round(sum(e.score for e in evals if e.score) / len(evals), 1) if evals else 0

    # resources for failed rounds
    resources = []
    for rnd in failed_rounds:
        res = db.query(Resource).filter_by(target_round=rnd).all()
        resources.extend(res)

    # faculty mentors
    faculty = db.query(Faculty).filter_by(branch=student.branch).all()

    # chart data – radar chart
    chart = {
        "rounds": ROUNDS,
        "scores": [eval_map.get(r, type("obj", (object,), {"score": 0})).score or 0 for r in ROUNDS],
        "pass_threshold": 60,
    }

    # sub-metrics breakdown
    sub_metrics = []
    for e in evals:
        sub_metrics.append({
            "round": e.round_name,
            "english": e.english_score,
            "technical": e.technical_score,
            "communication": e.communication_score,
            "problem_solving": e.problem_solving_score,
        })

    return templates.TemplateResponse("student_dashboard.html", {
        "request": request,
        "student": student,
        "evals": evals,
        "eval_map": eval_map,
        "placements": placements,
        "mock_sessions": mock_sessions,
        "failed_rounds": failed_rounds,
        "avg_score": avg_score,
        "resources": resources,
        "faculty": faculty,
        "chart": json.dumps(chart),
        "sub_metrics": json.dumps(sub_metrics),
        "rounds": ROUNDS,
    })


# ─────────────── AI Mock Interview ──────────────────────────────────────────

INTERVIEW_SYSTEM_PROMPTS = {
    "aptitude": """You are an aptitude test examiner for campus placements at top Indian IT companies. 
Generate exactly 5 timed MCQ questions covering: quantitative aptitude, logical reasoning, and verbal ability.
Format each as:
Q{n}: [question]
A) [option]  B) [option]  C) [option]  D) [option]
Answer: [correct option]
Explanation: [brief explanation]

Tailor difficulty to the student's weak areas if mentioned.""",

    "gd": """You are simulating a Group Discussion for campus placements. You play 3 co-participants with distinct personalities:
- Riya (assertive, data-driven)
- Karan (creative, tangential thinker)  
- Priya (balanced, structured)

Start by announcing the GD topic and giving the student 30 seconds to think.
Then each co-participant makes their opening statement (2 sentences each).
After the student responds, score on: Clarity (1-10), Assertiveness (1-10), Relevance (1-10), Communication (1-10).
Be realistic. Challenge the student's points politely.""",

    "hr": """You are a senior HR interviewer at {company}. Your style is {style}.
Conduct a realistic HR interview starting with "Tell me about yourself."
Ask follow-up questions based on answers. Cover: strengths/weaknesses, situational questions, career goals, culture fit.
After each answer, internally assess: Communication, Confidence, Professionalism.
After 6-8 questions, provide a final scorecard: 
- Communication: X/10
- Confidence: X/10  
- Professionalism: X/10
- Overall: X/10
- Key Feedback: [3 specific points]""",

    "coding": """You are a technical interviewer at {company}. 
Start by asking 1 coding problem appropriate for a fresher/campus hire (arrays, strings, basic DP, sorting).
Say: "Please write your solution and explain your approach."
When the student shares code, analyze it for: correctness, time complexity, space complexity, edge cases.
Ask follow-up probing questions: "What's your time complexity?", "Can you optimize this?", "What about edge case X?"
Be encouraging but rigorous. End with: Technical Score: X/10, Approach Score: X/10, Communication Score: X/10."""
}

COMPANY_STYLES = {
    "TCS": {"style": "structured, process-oriented, slightly formal"},
    "Infosys": {"style": "friendly but competency-based"},
    "Wipro": {"style": "technical, detail-oriented"},
    "Google": {"style": "open-ended, problem-solving focused, very technical"},
    "Amazon": {"style": "leadership principles heavy, bar-raiser culture"},
    "Startup": {"style": "casual, culture-fit focused, fast-paced"},
}


@router.get("/mock-interview", response_class=HTMLResponse)
async def mock_interview_page(request: Request, db: Session = Depends(get_db)):
    student = get_current_student(request, db)
    if not student:
        return RedirectResponse("/student/login", status_code=302)

    sessions = db.query(MockInterviewSession).filter_by(student_id=student.id)\
        .order_by(MockInterviewSession.started_at.desc()).limit(10).all()

    return templates.TemplateResponse("mock_interview.html", {
        "request": request,
        "student": student,
        "sessions": sessions,
        "companies": list(COMPANY_STYLES.keys()),
        "interview_types": ["aptitude", "gd", "hr", "coding"],
    })


@router.post("/mock-interview/start")
async def start_mock_session(
    request: Request,
    interview_type: str = Form(...),
    company: str = Form("TCS"),
    weak_areas: str = Form(""),
    db: Session = Depends(get_db)
):
    student = get_current_student(request, db)
    if not student:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    session = MockInterviewSession(
        student_id=student.id,
        session_type=interview_type,
        company_style=company,
    )
    db.add(session)
    db.commit()

    co_info = COMPANY_STYLES.get(company, COMPANY_STYLES["TCS"])
    system_prompt = INTERVIEW_SYSTEM_PROMPTS.get(interview_type, INTERVIEW_SYSTEM_PROMPTS["hr"])
    system_prompt = system_prompt.replace("{company}", company).replace("{style}", co_info["style"])

    if weak_areas:
        system_prompt += f"\n\nNote: This student's weak areas are: {weak_areas}. Adjust accordingly."

    return JSONResponse({
        "success": True,
        "session_id": session.id,
        "system_prompt": system_prompt,
        "company": company,
        "type": interview_type,
    })


@router.post("/mock-interview/chat")
async def mock_interview_chat(request: Request, db: Session = Depends(get_db)):
    student = get_current_student(request, db)
    if not student:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    body = await request.json()
    messages = body.get("messages", [])
    session_id = body.get("session_id")
    system_prompt = body.get("system_prompt", "You are a placement interview examiner.")

    async def stream_response():
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}] + messages,
                stream=True,
                max_tokens=1024,
                temperature=0.8,
            )
            full_response = ""
            for chunk in completion:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                yield f"data: {json.dumps({'content': delta})}\n\n"

            # save transcript
            if session_id:
                session = db.query(MockInterviewSession).filter_by(id=session_id).first()
                if session:
                    existing = json.loads(session.transcript or "[]")
                    existing.append({"role": "assistant", "content": full_response})
                    session.transcript = json.dumps(existing)
                    db.commit()

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.post("/mock-interview/{session_id}/complete")
async def complete_session(
    session_id: int,
    request: Request,
    overall_score: float = Form(0),
    scorecard: str = Form("{}"),
    db: Session = Depends(get_db)
):
    student = get_current_student(request, db)
    if not student:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    session = db.query(MockInterviewSession).filter_by(id=session_id, student_id=student.id).first()
    if session:
        session.completed_at = datetime.utcnow()
        session.overall_score = overall_score
        session.scorecard = scorecard
        db.commit()

    return JSONResponse({"success": True})
