import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from src.config import (
    LOG_PATH,
    NOTIFY_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_PASSWORD,
    SMTP_USER,
)
from src.database import log_automation


def _write_log(line: str) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def email_configured() -> bool:
    return bool(SMTP_USER and SMTP_PASSWORD and NOTIFY_EMAIL)


def send_lead_notification(lead: dict[str, Any]) -> str:
    """Automation: new lead → email notification + audit log."""
    payload = json.dumps(lead, default=str)
    subject = f"New Lead: {lead.get('name', 'Unknown')}"
    body = f"""New lead captured via Business Automation Assistant

Name: {lead.get('name')}
Email: {lead.get('email')}
Phone: {lead.get('phone') or '—'}
Company: {lead.get('company') or '—'}
Interest: {lead.get('interest') or '—'}
Message: {lead.get('message') or '—'}
Lead ID: {lead.get('id')}
"""

    if not email_configured():
        msg = "email_skipped_no_smtp_config"
        log_automation("lead_notification", payload, msg)
        _write_log(f"[LEAD] id={lead.get('id')} — notification skipped (SMTP not configured)")
        return msg

    try:
        mime = MIMEMultipart()
        mime["From"] = SMTP_USER
        mime["To"] = NOTIFY_EMAIL
        mime["Subject"] = subject
        mime.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, NOTIFY_EMAIL, mime.as_string())

        log_automation("lead_notification", payload, "email_sent")
        _write_log(f"[LEAD] id={lead.get('id')} — email sent to {NOTIFY_EMAIL}")
        return "email_sent"
    except Exception as exc:
        err = f"email_failed: {exc}"
        log_automation("lead_notification", payload, err)
        _write_log(f"[LEAD] id={lead.get('id')} — {err}")
        return err


def on_chat_interaction(session_id: str, user_msg: str, assistant_msg: str) -> str:
    """Automation: chatbot interaction → log + auto-response event."""
    payload = json.dumps(
        {
            "session_id": session_id,
            "user_preview": user_msg[:120],
            "assistant_preview": assistant_msg[:120],
        }
    )
    log_automation("chat_auto_response", payload, "logged")
    _write_log(f"[CHAT] session={session_id} — response generated and stored")
    return "logged"
