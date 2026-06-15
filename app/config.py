from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    # CRITICAL: Add this so Pydantic exposes settings.SECRET_KEY
    SECRET_KEY: str 

    class Config:
        env_file = ".env"
        extra = "ignore" # Prevents crashing if extra vars are in .env

    # MariaDB Configuration
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        # Utilizing the pymysql dialect driver for MariaDB compatibility
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"

settings = Settings()
