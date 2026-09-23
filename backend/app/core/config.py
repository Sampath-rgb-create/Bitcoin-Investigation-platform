from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bitcoin Investigation Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Offline & Network controls
    OFFLINE_MODE: bool = True
    
    # Storage and paths (strictly D: drive)
    DATA_DIR: str = "d:/Bitcoin-Investigation-platform/data"
    DATABASE_URL: str = "sqlite:///d:/Bitcoin-Investigation-platform/data/app.db"
    
    # Security & Auth
    SECRET_KEY: str = "prototype-insecure-secret-key-change-in-production-env-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Pipeline & Scoring Configuration Defaults
    WEIGHT_ANOMALY: float = 0.40
    WEIGHT_BEHAVIOR: float = 0.30
    WEIGHT_GRAPH: float = 0.20
    WEIGHT_NETWORK: float = 0.10
    
    # Correlation defaults
    ALLOW_TEMPORAL_CORRELATION: bool = False
    CORRELATION_WINDOW_SECONDS: int = 30
    
    # Monetary epsilon for checking total_input == total_output + fee
    MONEY_EPSILON: float = 1e-8
    
    # Optional GeoIP MMDB Path (offline file)
    GEOIP_DATABASE_PATH: Optional[str] = "d:/Bitcoin-Investigation-platform/data/GeoLite2-City.mmdb"
    
    # AI Adapters (Disabled by default in offline MVP)
    ENABLE_LAYA: bool = False
    ENABLE_OLLAMA: bool = False
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3:latest"
    LAYA_MODEL_PATH: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file="d:/Bitcoin-Investigation-platform/.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
