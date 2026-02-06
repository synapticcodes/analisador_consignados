"""
Configurações da aplicação usando Pydantic Settings.
Todas as configurações são carregadas de variáveis de ambiente.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_SECRET_KEY = "dev-insecure-secret-key-change-me-32chars"
DEFAULT_OPENAI_API_KEY = "test-openai-key"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_S3_ACCESS_KEY = "minioadmin"
DEFAULT_S3_SECRET_KEY = "minioadmin123"
DEFAULT_LOCAL_STORAGE_PATH = "storage"


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
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = True
    secret_key: str = Field(default=DEFAULT_SECRET_KEY, min_length=32)

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
    redis_url: RedisDsn = DEFAULT_REDIS_URL

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
    local_storage_path: str = DEFAULT_LOCAL_STORAGE_PATH
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = DEFAULT_S3_ACCESS_KEY
    s3_secret_key: str = DEFAULT_S3_SECRET_KEY
    s3_bucket_name: str = "pdf-uploads"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False

    # ==============================================
    # OpenAI Settings
    # ==============================================
    openai_api_key: str = DEFAULT_OPENAI_API_KEY
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
    # Feature Flags (Relatório PDF v2)
    # ==============================================
    feature_pdf_v2_enabled: bool = True
    feature_pdf_v2_phase2_enabled: bool = True
    feature_pdf_v2_phase3_enabled: bool = True
    taxa_referencia_mensal: float = 1.50

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

    @model_validator(mode="after")
    def validate_required_secrets(self):
        if self.environment in {"production", "staging"}:
            missing = []
            if self.secret_key == DEFAULT_SECRET_KEY:
                missing.append("SECRET_KEY")
            if self.openai_api_key == DEFAULT_OPENAI_API_KEY:
                missing.append("OPENAI_API_KEY")
            if self.redis_url == DEFAULT_REDIS_URL:
                missing.append("REDIS_URL")
            if self.s3_access_key == DEFAULT_S3_ACCESS_KEY:
                missing.append("S3_ACCESS_KEY")
            if self.s3_secret_key == DEFAULT_S3_SECRET_KEY:
                missing.append("S3_SECRET_KEY")
            if missing:
                raise ValueError(
                    "Configuração inválida em produção/staging. "
                    f"Defina variáveis: {', '.join(missing)}"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Retorna instância singleton das configurações.
    Usa lru_cache para evitar recarregar a cada chamada.
    """
    return Settings()


# Instância global das configurações
settings = get_settings()
