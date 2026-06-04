from fastapi import FastAPI

from app.controllers import auth_router, onboarding_router

app = FastAPI(
    title="Estro API",
    description="Бекенд для трекера менструального циклу та жіночого здоров'я",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(onboarding_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
