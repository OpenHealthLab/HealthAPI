from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Healthcare AI Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    database_url: str = "sqlite:///./healthcare_ai.db"
    
    model_path: str = "./ml_models/chest_xray_model.pth"
    upload_dir: str = "./uploads"
    max_upload_size: int = 10485760
    
    api_key: str = "your-secret-api-key"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

