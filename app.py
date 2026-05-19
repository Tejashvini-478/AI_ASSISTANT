import uuid

import pandas as pd
import streamlit as st

from src.automation import email_configured, on_chat_interaction, send_lead_notification
from src.chatbot import ChatbotError, generate_reply, get_provider_status
from src.config import ADMIN_PASSWORD
from src.database import (
    get_all_leads,
    get_automation_events,
    get_chat_logs,
    get_stats,
    init_db,
    insert_lead,
    log_chat,
)

st.set_page_config(
    page_title="Business Automation Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

CUSTOM_CSS = """
<style>
    .main-header { font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem; }
    .sub-header { color: #6b7280; margin-bottom: 1.5rem; }
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        padding: 1rem 1.25rem;
        border-radius: 12px;
        color: white;
    }
    div[data-testid="stMetricValue"] { font-size: 1.75rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def sidebar_nav():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "AI Assistant", "Lead Capture", "Admin Dashboard"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    status = get_provider_status()
    st.sidebar.markdown("### System Status")
    mode_label = status["mode"].replace("_", " ")
    st.sidebar.info(f"**LLM:** {status['label']} ({mode_label})")
    st.sidebar.info(
        f"**Email automation:** {'Configured' if email_configured() else 'Logging only (set SMTP in .env)'}"
    )
    stats = get_stats()
    st.sidebar.metric("Total leads", stats["leads"])
    st.sidebar.metric("Chat messages", stats["chats"])
    return page


def page_home():
    st.markdown('<p class="main-header">AI-Powered Business Automation Assistant</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Chatbot · Lead capture · Automation workflows · Admin dashboard</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🤖 AI Assistant")
        st.write("Ask about courses, business programs, enrollment, and automation consulting.")
    with col2:
        st.markdown("#### 📋 Lead Capture")
        st.write("Submit your details — data is stored in SQLite and triggers automation workflows.")
    with col3:
        st.markdown("#### 📊 Admin Dashboard")
        st.write("View leads, chat history, and automation event logs (password protected).")

    st.divider()
    st.subheader("Automation workflows")
    st.markdown(
        """
| Workflow | Trigger | Action |
|----------|---------|--------|
| **Lead notification** | Form submission | SQLite storage + email to admin (if SMTP configured) + event log |
| **Chat logging** | Each chat message | Persist conversation + automation audit trail |
| **Auto-response** | User message in chat | LLM (or demo) generates reply and logs the interaction |
        """
    )


def page_chat():
    st.header("AI Business Assistant")
    status = get_provider_status()
    mode_label = status["mode"].replace("_", " ")
    st.caption(f"Provider: **{status['label']}** — {mode_label} mode")

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about courses, pricing, or business automation..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_chat(st.session_state.session_id, "user", prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    reply, _ = generate_reply(st.session_state.messages)
                except ChatbotError as e:
                    reply = f"Sorry, I could not generate a response: {e}"
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        log_chat(st.session_state.session_id, "assistant", reply)
        on_chat_interaction(st.session_state.session_id, prompt, reply)

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.rerun()


def page_lead():
    st.header("Lead Capture")
    st.write("Submit your details and our team will follow up. Your submission triggers automated logging and notification.")

    with st.form("lead_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full name *", placeholder="Jane Doe")
            email = st.text_input("Email *", placeholder="jane@company.com")
            phone = st.text_input("Phone", placeholder="+1 555 0100")
        with c2:
            company = st.text_input("Company", placeholder="Acme Inc.")
            interest = st.selectbox(
                "Area of interest",
                [
                    "Business Automation Course",
                    "AI Integration Consulting",
                    "Lead Management Setup",
                    "Custom Workflow Design",
                    "General Inquiry",
                ],
            )
        message = st.text_area("Message", placeholder="Tell us about your goals...")
        submitted = st.form_submit_button("Submit lead", type="primary")

    if submitted:
        if not name.strip() or not email.strip():
            st.error("Name and email are required.")
            return
        if "@" not in email:
            st.error("Please enter a valid email address.")
            return

        lead_id = insert_lead(
            name=name.strip(),
            email=email.strip(),
            phone=phone.strip(),
            company=company.strip(),
            interest=interest,
            message=message.strip(),
        )
        lead = {
            "id": lead_id,
            "name": name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "company": company.strip(),
            "interest": interest,
            "message": message.strip(),
        }
        automation_status = send_lead_notification(lead)
        st.success(f"Thank you, {name}! Your details have been saved (Lead #{lead_id}).")
        if automation_status == "email_sent":
            st.info("Our team has been notified by email.")
        elif automation_status == "email_skipped_no_smtp_config":
            st.info("Lead logged successfully. Email notification skipped — configure SMTP in `.env` to enable.")
        else:
            st.warning(f"Lead saved; notification status: {automation_status}")


def page_admin():
    st.header("Admin Dashboard")
    if not st.session_state.get("admin_authenticated"):
        pwd = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Invalid password.")
        st.caption("Default password: `admin123` (change via ADMIN_PASSWORD in .env)")
        return

    if st.button("Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()

    stats = get_stats()
    m1, m2, m3 = st.columns(3)
    m1.metric("Leads captured", stats["leads"])
    m2.metric("Chat messages", stats["chats"])
    m3.metric("Automation events", stats["automation_events"])

    tab1, tab2, tab3 = st.tabs(["Leads", "Chat logs", "Automation events"])

    with tab1:
        leads = get_all_leads()
        if leads:
            st.dataframe(pd.DataFrame(leads), use_container_width=True, hide_index=True)
            st.download_button(
                "Export leads CSV",
                pd.DataFrame(leads).to_csv(index=False).encode("utf-8"),
                "leads_export.csv",
                "text/csv",
            )
        else:
            st.info("No leads yet.")

    with tab2:
        logs = get_chat_logs()
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
        else:
            st.info("No chat logs yet.")

    with tab3:
        events = get_automation_events()
        if events:
            st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
        else:
            st.info("No automation events yet.")


def main():
    page = sidebar_nav()
    routes = {
        "Home": page_home,
        "AI Assistant": page_chat,
        "Lead Capture": page_lead,
        "Admin Dashboard": page_admin,
    }
    routes[page]()


if __name__ == "__main__":
    main()
