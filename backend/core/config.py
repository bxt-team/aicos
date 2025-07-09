import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application configuration settings"""
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    PEXELS_API_KEY: Optional[str] = os.getenv("PEXELS_API_KEY")
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_BUSINESS_ACCOUNT_ID: Optional[str] = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    RUNWAY_API_KEY: Optional[str] = os.getenv("RUNWAY_API_KEY")
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    
    # Paths
    ADB_PATH: str = os.getenv("ADB_PATH", "adb")
    
    # CORS Settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", 
        "http://127.0.0.1:8000",
    ]
    
    # File Storage Settings
    STORAGE_BASE_PATH: str = "storage"
    GENERATED_DIR: str = "generated"
    COMPOSED_DIR: str = "composed"
    INSTAGRAM_MEDIA_DIR: str = "instagram_media"
    VOICE_OVERS_DIR: str = "voice_overs"
    VIDEO_DIR: str = "videos"
    ANDROID_RESULTS_DIR: str = "android_test_results"
    
    @classmethod
    def get_storage_path(cls, *paths) -> str:
        """Get full storage path"""
        return os.path.join(cls.STORAGE_BASE_PATH, *paths)

settings = Settings()