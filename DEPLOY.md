# Deploy to Streamlit Cloud (public live URL)

## 1. Push to GitHub

Install [Git](https://git-scm.com/), then:

```powershell
cd d:\chatbot
git init
git add .
git commit -m "AI business automation assistant"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Do **not** commit `.env` — it is in `.gitignore`.

## 2. Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → select your repository.
3. **Main file path:** `app.py`
4. **Advanced settings → Secrets** — paste:

```toml
GEMINI_API_KEY = "your-key-here"
LLM_PROVIDER = "gemini"
GEMINI_MODEL = "gemini-2.5-flash"
ADMIN_PASSWORD = "choose-a-strong-password"
```

5. **Deploy** — copy the `https://....streamlit.app` URL for your submission.

## 3. Demo video checklist

- Home overview + architecture (README diagram)
- AI Assistant with a live Gemini question
- Lead Capture form submit → Admin dashboard
- Mention automation workflows tab
