"""Application settings loaded from environment variables / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── GCP / Gemini ──────────────────────────────────────────────────────────
    gcp_project_id: str = Field(default="my-gcp-project", alias="GCP_PROJECT_ID")
    gcp_location_id: str = Field(default="us-central1", alias="GCP_LOCATION_ID")
    gcp_gemini_model: str = Field(default="gemini-1.5-pro-002", alias="GCP_GEMINI_MODEL")

    # ── Corporate proxy (optional) ────────────────────────────────────────────
    https_proxy: str | None = Field(default=None, alias="HTTPS_PROXY")

    # ── Development / testing flags ───────────────────────────────────────────
    mock_llm: bool = Field(default=False, alias="MOCK_LLM")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── Pipeline behaviour ────────────────────────────────────────────────────
    max_attachment_size_mb: int = Field(default=20, alias="MAX_ATTACHMENT_SIZE_MB")
    max_email_size_mb: int = Field(default=50, alias="MAX_EMAIL_SIZE_MB")
    vulnerability_llm_confirm_threshold: int = Field(
        default=1,
        alias="VULNERABILITY_LLM_CONFIRM_THRESHOLD",
        description="Minimum keyword hits before sending to LLM for confirmation",
    )

    # ── Local data paths ──────────────────────────────────────────────────────
    mock_policies_path: Path = Field(
        default=Path(__file__).parent.parent / "data" / "mock_policies.json",
        alias="MOCK_POLICIES_PATH",
    )
    lodged_claims_path: Path = Field(
        default=Path(__file__).parent.parent / "data" / "lodged_claims.jsonl",
        alias="LODGED_CLAIMS_PATH",
    )
    exceptions_path: Path = Field(
        default=Path(__file__).parent.parent / "data" / "exceptions_queue.jsonl",
        alias="EXCEPTIONS_PATH",
    )
    vulnerability_phrases_path: Path = Field(
        default=Path(__file__).parent.parent / "data" / "vulnera_phrases.csv",
        alias="VULNERABILITY_PHRASES_PATH",
    )

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return v.upper()


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
