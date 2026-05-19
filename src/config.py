import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "business_assistant.db"
LOG_PATH = DATA_DIR / "automation.log"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "").strip()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

SYSTEM_PROMPT = """You are an AI-powered business automation assistant for a training and consulting company.

Your role:
- Answer questions about business courses, programs, pricing, enrollment, and consulting services
- Help users understand offerings clearly and professionally
- Encourage interested users to fill out the lead capture form for follow-up
- Keep responses concise, helpful, and business-appropriate

If you do not know specific pricing or dates, say so and suggest they submit their contact details for a personalized follow-up.
"""
