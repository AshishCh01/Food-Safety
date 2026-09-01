from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Checked-in fallback for local/dev only - the value is public (it's in git
# history), so a production boot must never be allowed to silently keep it.
# See the `_reject_insecure_production_secret` validator below.
_INSECURE_DEFAULT_JWT_SECRET = "insecure-development-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Food Safety Platform API"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: SecretStr = SecretStr(
        "postgresql+psycopg2://postgres:password@localhost:5432/postgres"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle_seconds: int = 1800

    cors_origins: str = "http://localhost:5173"

    jwt_secret_key: SecretStr = SecretStr(_INSECURE_DEFAULT_JWT_SECRET)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    # Tolerance window for concurrent refresh requests that both presented
    # the same (still-valid-at-request-time) refresh token - see
    # app/services/auth_service.py's reuse-detection logic. A losing
    # concurrent request is rejected either way; this only decides whether
    # it's treated as benign (no family-wide revocation) or as replay of a
    # stale token (revokes the whole session family).
    refresh_token_reuse_grace_seconds: int = 5
    # Retention for dead refresh_sessions rows (expired, or revoked for a
    # routine reason: rotated/logout/account_deactivated) before
    # scripts/cleanup_refresh_sessions.py deletes them - see
    # docs/SECURITY_AND_RBAC.md section 20.
    refresh_session_retention_days: int = 7
    # Longer retention specifically for reuse_detected revocations - the
    # strongest signal of a leaked/replayed token and the most valuable to
    # keep around for incident investigation.
    refresh_session_reuse_detected_retention_days: int = 90

    supabase_url: str = ""
    supabase_service_role_key: SecretStr = SecretStr("")
    supabase_storage_bucket: str = "complaint-evidence"

    gemini_api_key: SecretStr = SecretStr("")
    gemini_main_model: str = "gemini-3.7-flash"
    gemini_reasoning_model: str = "gemini-3.1-pro"
    gemini_embedding_model: str = "gemini-embedding-2-preview"
    gemini_embedding_dimensions: int = 768
    gemini_request_timeout_seconds: float = 60.0

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

    @model_validator(mode="after")
    def _reject_insecure_production_secret(self) -> "Settings":
        """Fail fast at startup rather than silently serving requests signed
        with a secret that's public in the repo's git history - a missing
        JWT_SECRET_KEY env var in any deployment path other than Render's own
        blueprint (which sets `generateValue: true`) would otherwise boot
        successfully and let anyone forge a valid token for any user/role."""
        if self.environment == "production" and self.jwt_secret_key.get_secret_value() == _INSECURE_DEFAULT_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a real secret in production - "
                "refusing to start with the insecure default."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
