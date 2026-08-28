from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Food Safety Platform API"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://postgres:password@localhost:5432/postgres"

    cors_origins: str = "http://localhost:5173"

    jwt_secret_key: str = "insecure-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "complaint-evidence"

    gemini_api_key: str = ""
    gemini_main_model: str = "gemini-3.7-flash"
    gemini_reasoning_model: str = "gemini-3.1-pro"
    gemini_embedding_model: str = "gemini-embedding-2-preview"
    gemini_embedding_dimensions: int = 768
    gemini_request_timeout_seconds: float = 20.0

    rag_storage_bucket: str = "rag-documents"
    rag_max_upload_size_mb: int = 20
    rag_retrieval_top_k: int = 6
    rag_chunk_target_chars: int = 1200
    rag_chunk_overlap_chars: int = 150

    enable_reverse_geocoding: bool = True
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "food-safety-platform/1.0 (contact: ops@foodsafety.local)"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
