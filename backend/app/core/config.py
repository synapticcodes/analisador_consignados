"""
Configurações da aplicação usando Pydantic Settings.
Todas as configurações são carregadas de variáveis de ambiente.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações globais da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==============================================
    # Application Settings
    # ==============================================
    app_name: str = "Calculadora de Consignados"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = Field(min_length=32)

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001"
    )

    @field_validator("allowed_origins", mode="after")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ==============================================
    # Database Settings
    # ==============================================
    database_url: PostgresDsn

    # Pool settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # ==============================================
    # Redis Settings
    # ==============================================
    redis_url: RedisDsn

    # Cache TTL (seconds)
    cache_ttl: int = 900  # 15 minutes

    # ==============================================
    # Celery Settings
    # ==============================================
    celery_broker_url: str = Field(default="")
    celery_result_backend: str = Field(default="")

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def set_celery_broker(cls, v, info):
        if not v:
            return str(info.data.get("redis_url")).replace("/0", "/1")
        return v

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def set_celery_backend(cls, v, info):
        if not v:
            return str(info.data.get("redis_url")).replace("/0", "/2")
        return v

    # ==============================================
    # S3/MinIO Settings
    # ==============================================
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str = "pdf-uploads"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False

    # ==============================================
    # OpenAI Settings
    # ==============================================
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.0
    openai_max_tokens: int = 4096

    # Embedding model
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # ==============================================
    # AWS Textract Settings (Optional)
    # ==============================================
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    # ==============================================
    # Qdrant Settings
    # ==============================================
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "document_chunks"

    # ==============================================
    # Job Processing Settings
    # ==============================================
    max_file_size_mb: int = 10
    max_total_upload_size_mb: int = 25
    max_files_per_job: int = 3
    job_timeout_seconds: int = 300  # 5 minutes

    # OCR threshold
    ocr_quality_threshold: float = 0.6

    # ==============================================
    # Rate Limiting
    # ==============================================
    rate_limit_per_user_per_hour: int = 10
    rate_limit_per_ip_per_minute: int = 100

    # ==============================================
    # File Retention
    # ==============================================
    pdf_retention_days: int = 30
    audit_retention_days: int = 90

    # ==============================================
    # Observability Settings
    # ==============================================
    enable_metrics: bool = True
    enable_tracing: bool = False

    # Sentry (optional)
    sentry_dsn: str | None = None

    # ==============================================
    # Security Settings
    # ==============================================
    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Password hashing
    pwd_schemes: list[str] = Field(default_factory=lambda: ["bcrypt"])
    pwd_deprecated: str = "auto"

    # ==============================================
    # Helper Properties
    # ==============================================
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def max_total_upload_size_bytes(self) -> int:
        return self.max_total_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """
    Retorna instância singleton das configurações.
    Usa lru_cache para evitar recarregar a cada chamada.
    """
    return Settings()


# Instância global das configurações
settings = get_settings()
