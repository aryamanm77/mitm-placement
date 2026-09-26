
# MITM Placement & Training Dashboard

> **Maharaja Institute of Technology Mysore** — Placement Tracking, Training & AI Mock Interview Platform

---

## 🎓 Project Overview

A full-stack web application for MITM Mysore that provides:

- **Department Admin Module** — Manage students, track performance across 6 placement rounds, view analytics
- **Student Portal** — Personalized dashboard, weakness analysis, resources, OTP login
- **AI Mock Interviews** — Powered by Groq (LLaMA 3.3-70B): Aptitude MCQs, GD simulation, HR interview, Live coding
- **Design** — Exact replica of [mitmysore.in](https://mitmysore.in) (Open Sans font, #046BD2 blue, same layout)

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11 or higher
- A Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Add your Groq API Key

Edit `.env` file:
```
GROQ_API_KEY=your_actual_groq_key_here
```

### 2. Run the app

**Windows (double-click or CMD):**
```
run.bat
```

**Or manually:**
```bash
pip install -r requirements.txt
python -m app.seed
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open in browser

```
http://127.0.0.1:8000
```

---

## 🔑 Demo Credentials

| Role | Credentials |
|------|-------------|
| **IS Admin** | Email: `admin.in@mitm.ac.in` / Pass: `Admin@1234` |
| **CS Admin** | Email: `admin.co@mitm.ac.in` / Pass: `Admin@1234` |
| **EC Admin** | Email: `admin.el@mitm.ac.in` / Pass: `Admin@1234` |
| **ME Admin** | Email: `admin.me@mitm.ac.in` / Pass: `Admin@1234` |
| **Student OTP** | Mobile: `9876543210` (Aditya Sharma, IS Branch) |

---

## 🏗️ Project Structure

```
mitm-placement/
├── main.py                      # FastAPI app entry point
├── requirements.txt             # Python dependencies
├── .env                         # 🔑 Add your GROQ_API_KEY here
├── run.bat                      # Windows launcher script
├── app/
│   ├── models.py                # SQLAlchemy database models
│   ├── auth.py                  # JWT + OTP utilities
│   ├── seed.py                  # Database seeder (MITM demo data)
│   ├── routers/
│   │   ├── admin.py             # Dept admin routes
│   │   └── student.py           # Student routes + AI interview
│   ├── templates/
│   │   ├── base.html            # MITM-styled base template
│   │   ├── landing.html         # Homepage
│   │   ├── admin_login.html     # Admin login page
│   │   ├── admin_dashboard.html # Admin analytics dashboard
│   │   ├── admin_students.html  # Student management
│   │   ├── admin_student_detail.html
│   │   ├── student_login.html   # OTP login
│   │   ├── student_dashboard.html
│   │   └── mock_interview.html  # AI interview interface
│   └── static/
│       ├── images/
│       │   ├── mitm_logo.jpg    # ✅ Real MITM logo (from mitmysore.in)
│       │   ├── dept_logo.jpg    # ✅ Real MITM dept logo (from mitmysore.in)
│       │   ├── logo_is.jpg      # IS dept logo
│       │   ├── logo_cs.jpg      # CS dept logo
│       │   ├── logo_ec.jpg      # EC dept logo
│       │   └── logo_me.jpg      # ME dept logo
│       ├── css/
│       └── js/
```

---

## 🤖 AI Mock Interview Modes

| Mode | Description |
|------|-------------|
| **Aptitude** | LLaMA generates 5 timed MCQs scaled to student's weak areas |
| **GD (Group Discussion)** | LLM plays 3 co-participants (Riya, Karan, Priya) with different personalities |
| **HR Round** | Full conversational HR interview, company style selectable (TCS/Infosys/Google/Amazon/Startup) |
| **Coding Round** | Live Monaco Editor + AI interviewer who asks follow-ups, checks complexity |

---

## 📊 Evaluation Rounds Tracked

1. Aptitude
2. Group Discussion (GD)
3. HR Round
4. Coding — C
5. Coding — Java
6. Coding — DSA

Each round tracks: Score, Pass/Fail, English Score, Technical Score, Communication Score, Problem-Solving Score

---

## 🎨 Design System (from mitmysore.in)

| Token | Value | Usage |
|-------|-------|-------|
| Primary Blue | `#046BD2` | Buttons, links, accents |
| Primary Dark | `#045CB4` | Hover states |
| Dark Text | `#1E293B` | Headings |
| Body Text | `#334155` | Paragraphs |
| Background | `#F0F5FA` | Page background |
| Border | `#D1D5DB` | Dividers, inputs |
| Font | Open Sans 300–800 | All text |

---

## 🚀 Future Enhancements

- [ ] Real SMS OTP via Fast2SMS/Twilio
- [ ] Voice-based GD round (Web Speech API)
- [ ] Company-wise placement analytics
- [ ] Resume builder module
- [ ] Bulk student import via Excel/CSV
- [ ] Email notifications for interview results
- [ ] Mobile app (PWA)
