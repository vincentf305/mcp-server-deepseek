from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()