from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mitm_placement.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class BranchEnum(str, enum.Enum):
    IS = "Information Science"
    CS = "Computer Science"
    EC = "Electronics and Communication"
    ME = "Mechanical Engineering"
    CV = "Civil Engineering"


class RoundEnum(str, enum.Enum):
    APTITUDE = "Aptitude"
    GD = "Group Discussion"
    HR = "HR Round"
    CODING_C = "Coding - C"
    CODING_JAVA = "Coding - Java"
    CODING_DSA = "Coding - DSA"


# ─────────────────────────── Department Admin ───────────────────────────────
class DepartmentAdmin(Base):
    __tablename__ = "department_admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    branch = Column(String(60), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ──────────────────────────── Student ───────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    usn = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    mobile = Column(String(15), unique=True, nullable=False)
    branch = Column(String(60), nullable=False)
    email = Column(String(150), nullable=True)
    photo_url = Column(String(255), nullable=True)
    cgpa = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(Integer, ForeignKey("department_admins.id"), nullable=True)

    evaluations = relationship("StudentEvaluation", back_populates="student", cascade="all, delete-orphan")
    placements = relationship("PlacementRecord", back_populates="student", cascade="all, delete-orphan")
    otp_records = relationship("OTPRecord", back_populates="student", cascade="all, delete-orphan")
    mock_sessions = relationship("MockInterviewSession", back_populates="student", cascade="all, delete-orphan")


# ─────────────────────────── Evaluation Rounds ──────────────────────────────
class StudentEvaluation(Base):
    __tablename__ = "student_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    round_name = Column(String(60), nullable=False)          # RoundEnum value
    score = Column(Float, nullable=True)                      # 0–100
    passed = Column(Boolean, nullable=True)
    feedback = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    evaluated_by = Column(Integer, ForeignKey("department_admins.id"), nullable=True)

    # Sub-metrics (for granular tracking)
    english_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    problem_solving_score = Column(Float, nullable=True)

    student = relationship("Student", back_populates="evaluations")


# ─────────────────────────── Placement Record ───────────────────────────────
class PlacementRecord(Base):
    __tablename__ = "placement_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    company_name = Column(String(150), nullable=False)
    role = Column(String(100), nullable=True)
    package_lpa = Column(Float, nullable=True)            # in LPA
    offer_date = Column(DateTime, nullable=True)
    placement_type = Column(String(50), default="Campus")  # Campus / Off-Campus / Internship

    student = relationship("Student", back_populates="placements")


# ─────────────────────────── OTP ────────────────────────────────────────────
class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    otp_code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="otp_records")


# ─────────────────────────── Mock Interview ─────────────────────────────────
class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_type = Column(String(30), nullable=False)       # aptitude / gd / hr / coding
    company_style = Column(String(50), nullable=True)       # startup / MNC / product
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    overall_score = Column(Float, nullable=True)
    scorecard = Column(Text, nullable=True)                 # JSON blob
    transcript = Column(Text, nullable=True)                # full conversation JSON

    student = relationship("Student", back_populates="mock_sessions")


# ────────────────────────── Resource / Course ───────────────────────────────
class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    resource_type = Column(String(30), nullable=False)      # video / course / article
    url = Column(String(500), nullable=False)
    target_round = Column(String(60), nullable=False)       # maps to RoundEnum
    tags = Column(String(300), nullable=True)               # comma-separated
    added_at = Column(DateTime, default=datetime.utcnow)


# ────────────────────────── Faculty Contact ─────────────────────────────────
class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    branch = Column(String(60), nullable=False)
    specialization = Column(String(150), nullable=True)
    email = Column(String(150), nullable=True)
    mobile = Column(String(15), nullable=True)
    cabin = Column(String(50), nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
