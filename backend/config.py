import os
from dotenv import load_dotenv

# Explicitly load .env from the backend folder
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class Settings:
    SUPABASE_URL: str  = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str  = os.getenv("SUPABASE_KEY", "")
    ADMIN_TOKEN: str   = os.getenv("ADMIN_TOKEN", "cafe-admin-secret")
    JWT_SECRET: str    = os.getenv("JWT_SECRET", "changeme")
    SMTP_HOST: str     = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int     = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str     = os.getenv("SMTP_USER", "")
    SMTP_PASS: str     = os.getenv("SMTP_PASS", "")
    FROM_EMAIL: str    = os.getenv("FROM_EMAIL", "noreply@smartcafe.in")
    FROM_NAME: str     = os.getenv("FROM_NAME", "Smart Cafe")
    CLOUDINARY_CLOUD_NAME: str    = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str       = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str    = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_UPLOAD_PRESET: str = os.getenv("CLOUDINARY_UPLOAD_PRESET", "cafe_menu_images")
    ENVIRONMENT: str   = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL: str  = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")
    TAX_RATE: float    = float(os.getenv("TAX_RATE", "0.09"))

    @property
    def is_production(self):
        return self.ENVIRONMENT == "production"

    @property
    def allowed_origins(self):
        return [self.FRONTEND_URL] if self.is_production else ["*"]

settings = Settings()
