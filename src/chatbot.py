from typing import Optional

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    SYSTEM_PROMPT,
)


class ChatbotError(Exception):
    pass


def _has_openai() -> bool:
    return bool(OPENAI_API_KEY)


def _has_gemini() -> bool:
    return bool(GEMINI_API_KEY)


def get_provider_status() -> dict:
    provider = LLM_PROVIDER
    if provider == "openai" and not _has_openai() and _has_gemini():
        provider = "gemini"
    elif provider == "gemini" and not _has_gemini() and _has_openai():
        provider = "openai"

    if provider == "openai" and _has_openai():
        return {"provider": "openai", "mode": "live", "label": "OpenAI"}
    if provider == "gemini" and _has_gemini():
        return {"provider": "gemini", "mode": "live", "label": "Google Gemini"}
    return {"provider": "fallback", "mode": "demo", "label": "Demo (no API key)"}


def _fallback_response(user_message: str) -> str:
    msg = user_message.lower()
    if any(w in msg for w in ("price", "cost", "fee", "pricing")):
        return (
            "Our business courses range from foundational programs to advanced automation "
            "tracks. Pricing depends on the program and cohort size. Please submit the lead "
            "form on the **Lead Capture** page and our team will send a tailored quote within "
            "24 hours."
        )
    if any(w in msg for w in ("course", "program", "training", "learn")):
        return (
            "We offer courses in business automation, AI integration, lead management, and "
            "workflow design. Each program includes hands-on projects and mentor support. "
            "Use the lead form to tell us your goals — we will recommend the best fit."
        )
    if any(w in msg for w in ("hello", "hi", "hey")):
        return (
            "Hello! I am your business automation assistant. Ask me about courses, consulting, "
            "enrollment, or how we can help automate your business workflows."
        )
    return (
        "Thank you for your question. I can help with course information, enrollment, and "
        "business automation consulting. For specific pricing or scheduling, please use the "
        "**Lead Capture** tab so our team can follow up personally. "
        "(Demo mode: add OPENAI_API_KEY or GEMINI_API_KEY in `.env` for full AI responses.)"
    )


def _chat_openai(messages: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        max_tokens=600,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


def _chat_gemini(messages: list[dict]) -> str:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )
    history = []
    for m in messages[:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})
    chat = model.start_chat(history=history)
    last = messages[-1]["content"] if messages else ""
    response = chat.send_message(last)
    return response.text or ""


def generate_reply(messages: list[dict]) -> tuple[str, dict]:
    """Return (assistant_text, provider_status)."""
    status = get_provider_status()
    if not messages:
        raise ChatbotError("No messages provided")

    user_message = messages[-1].get("content", "")

    if status["mode"] == "demo":
        return _fallback_response(user_message), status

    try:
        if status["provider"] == "openai":
            return _chat_openai(messages), status
        if status["provider"] == "gemini":
            return _chat_gemini(messages), status
    except Exception as exc:
        err = str(exc).lower()
        if "quota" in err or "429" in err or "resource_exhausted" in err:
            fallback = _fallback_response(user_message)
            note = (
                "\n\n---\n*Gemini quota limit reached — showing a guided reply. "
                "Enable billing or wait for quota reset at [Google AI Studio](https://aistudio.google.com).*"
            )
            return fallback + note, {**status, "mode": "quota_fallback"}
        raise ChatbotError(f"LLM request failed: {exc}") from exc

    return _fallback_response(user_message), status
