from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import ensure_schema
from .routers import (
    auth,
    members,
    committees,
    activities,
    attendance,
    tasks,
    notifications,
    ai,
    stats,
    chat,
)
import os

# Tạo bảng còn thiếu + bổ sung cột mới cho DB cũ (social login, ...)
ensure_schema()

app = FastAPI(
    title="Hệ thống Quản lý Câu lạc bộ Sinh viên tích hợp AI",
    description="Quản lý thành viên, ban chuyên môn, hoạt động, điểm danh, nhiệm vụ, thông báo và tích hợp AI",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(members.router)
app.include_router(committees.router)
app.include_router(activities.router)
app.include_router(attendance.router)
app.include_router(tasks.router)
app.include_router(notifications.router)
app.include_router(ai.router)
app.include_router(stats.router)
app.include_router(chat.router)

# Keep the original routes for the existing frontend and expose the documented
# /api/activities paths as aliases.
app.include_router(activities.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


# Serve the frontend (built with pure HTML/CSS/JS).
# MUST be declared last so API routes above take precedence in Starlette routing.
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")