from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    port: int = 8000
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    request_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
