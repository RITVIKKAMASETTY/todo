from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Chess Backend"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./chess.db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Matchmaking
    MATCHMAKING_TIMEOUT_SECONDS: int = 10
    
    # Stockfish
    STOCKFISH_PATH: str = "/usr/local/bin/stockfish"  # Update based on your system
    STOCKFISH_DEPTH: int = 10
    
    # Points
    WIN_POINTS: int = 10
    DRAW_POINTS: int = 3
    LOSS_POINTS: int = 0
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
