from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import (
    auth_router,
    cycles_router,
    daily_logs_router,
    notifications_router,
    onboarding_router,
    profile_router,
)

app = FastAPI(
    title="Estro API",
    description="Бекенд для трекера менструального циклу та жіночого здоров'я",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(profile_router)
app.include_router(cycles_router)
app.include_router(daily_logs_router)
app.include_router(notifications_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
