from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_KEY = "dev-secret-change-me"


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG_SQL: bool = False

    @model_validator(mode="after")
    def _reject_insecure_key(self) -> "Settings":
        if self.SECRET_KEY == _INSECURE_KEY:
            raise ValueError(
                "SECRET_KEY is set to the insecure default. "
                "Provide a strong value via the SECRET_KEY environment variable."
            )
        return self

    class Config:
        env_file = ".env"


settings = Settings()
