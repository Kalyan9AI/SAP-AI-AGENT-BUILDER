from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "SAP AI Agent - Supplier Delivery Prediction"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # SAP Connection Settings
    SAP_ASHOST: str = os.getenv("SAP_ASHOST", "")
    SAP_SYSNR: str = os.getenv("SAP_SYSNR", "00")
    SAP_CLIENT: str = os.getenv("SAP_CLIENT", "100")
    SAP_USER: str = os.getenv("SAP_USER", "")
    SAP_PASSWD: str = os.getenv("SAP_PASSWD", "")

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External APIs
    WEATHER_API_KEY: Optional[str] = os.getenv("WEATHER_API_KEY")
    TRAFFIC_API_KEY: Optional[str] = os.getenv("TRAFFIC_API_KEY")

    # ML Model Settings
    MODEL_PATH: str = "models/supplier_delay_prediction.pkl"
    RETRAIN_SCHEDULE_HOURS: int = 24

    # Alert Settings
    ALERT_THRESHOLD_PROBABILITY: float = 0.7
    NOTIFICATION_EMAIL: Optional[str] = os.getenv("NOTIFICATION_EMAIL")

    class Config:
        case_sensitive = True

settings = Settings() 