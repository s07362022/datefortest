from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    app_env: str = "development"
    app_name: str = "Dating App MVP"
    app_version: str = "0.1.0"

    # Database
    database_url: str = "postgresql://postgres:devpassword123@localhost:5432/datingapp"

    # JWT
    secret_key: str = "change_this_to_a_long_random_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Upload
    upload_dir: str = "uploads"
    max_photo_size_mb: int = 5
    max_photos_per_user: int = 6

    # Limits
    daily_like_limit: int = 50
    like_limit_enabled: bool = True

    # Docker / seed (用於 docker-compose 與初始資料，不對外暴露)
    postgres_password: str = "devpassword123"
    admin_email: str = "admin@example.com"
    admin_password: str = "change_this_admin_password"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
