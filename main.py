"""
MITM Placement Dashboard — Main Application Entry Point
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.models import create_tables
from app.routers import admin, student

# ── Bootstrap ────────────────────────────────────────────────────────────────
create_tables()

app = FastAPI(
    title="MITM Placement & Training Dashboard",
    description="Maharaja Institute of Technology Mysore – Placement Tracking System",
    version="1.0.0",
)

# Static files & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(admin.router)
app.include_router(student.router)


# ── Root redirect ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "app": "MITM Placement Dashboard"}
