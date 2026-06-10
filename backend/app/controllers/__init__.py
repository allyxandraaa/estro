from app.controllers.auth_controller import router as auth_router
from app.controllers.onboarding_controller import router as onboarding_router
from app.controllers.profile_controller import router as profile_router

__all__ = ["auth_router", "onboarding_router", "profile_router"]
