from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    repository = UserRepository(session)
    return AuthService(repository)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
) -> RegisterResponse:
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    return await service.login(data)
