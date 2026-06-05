from asyncio import to_thread
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, TokenResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self._user_repo = user_repository

    # ── Register ──

    async def register(self, data: RegisterRequest) -> RegisterResponse:
        existing = await self._user_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач із такою електронною поштою вже існує",
            )

        password_hash = await to_thread(pwd_context.hash, data.password)

        user = User(
            email=data.email,
            password_hash=password_hash,
        )

        try:
            created_user = await self._user_repo.create(user)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач із такою електронною поштою вже існує",
            ) from None

        return RegisterResponse.model_validate(created_user)

    # ── Login ──

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._user_repo.get_by_email(data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірна електронна пошта або пароль",
            )

        is_valid = await to_thread(pwd_context.verify, data.password, user.password_hash)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірна електронна пошта або пароль",
            )

        access_token = self._create_access_token(subject=str(user.id))
        return TokenResponse(
            access_token=access_token,
            needs_onboarding=user.average_cycle_length is None,
        )

    # ── JWT ──

    @staticmethod
    def _create_access_token(subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
