"""
Databricks DE Associate — Intern Study Hub (hosted version)

Run locally:   streamlit run streamlit_app.py
Deploy free:   push this repo to GitHub -> share.streamlit.io -> add a
               GITHUB_TOKEN secret (see README).

Architecture
------------
* The full study hub (notes, quizzes, flashcards, games, Feed-the-Duck XP,
  local progress) is the self-contained HTML, embedded here unchanged.
* The AI Tutor is a NATIVE Streamlit sidebar panel so the GitHub Models token
  stays server-side (st.secrets) and there are no browser CORS issues. It is in
  an st.fragment, so chatting with it does NOT reload/reset the study hub.
* If no token is set, the tutor shows a friendly setup note and everything
  else keeps working.
"""
import json
from pathlib import Path

import streamlit as st

import ai_tutor

HERE = Path(__file__).parent
TEMPLATE = HERE / "app_template.html"

st.set_page_config(page_title="Databricks DE Associate — Study Hub",
                   page_icon="🦆", layout="wide")


@st.cache_data
def build_html() -> str:
    content = json.loads((HERE / "content.json").read_text(encoding="utf-8"))
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(content).replace("</", "<\\/")  # safe inside <script>
    html = html.replace("__CONTENT_JSON__", payload)
    # tell the in-page tutor entry points we're in the hosted environment
    html = html.replace(
        "<body>",
        "<body><script>window.STUDYHUB_AI={mode:'hosted'};</script>",
    )
    return html


@st.cache_data
def get_content() -> dict:
    return ai_tutor.load_content()


content = get_content()
config = ai_tutor.get_config(dict(st.secrets) if hasattr(st, "secrets") else {})

# ----------------------------- AI TUTOR (sidebar) -------------------------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "prefill" not in st.session_state:
    st.session_state.prefill = ""


def run_tutor(user_text: str):
    st.session_state.chat.append({"role": "user", "content": user_text})
    msgs = [{"role": "system", "content": ai_tutor.system_prompt(content)}]
    msgs += st.session_state.chat[-8:]  # keep recent context
    with st.spinner("Tutor is thinking…"):
        answer = ai_tutor.ask(msgs, config)
    st.session_state.chat.append({"role": "assistant", "content": answer})


@st.fragment
def tutor_panel():
    st.markdown("### 🤖 AI Tutor")
    if not config.get("token"):
        st.info(
            "**AI tutor not configured.**\n\n"
            "Add a free **GitHub Models** token to switch it on:\n"
            "1. Create a GitHub token (it just needs Models access).\n"
            "2. In Streamlit Cloud → **Settings → Secrets**, add:\n"
            "   `GITHUB_TOKEN = \"ghp_…\"`\n\n"
            "Everything else in the hub works without it.",
            icon="🔑",
        )
        return

    st.caption("Grounded in the exam notes · says when it's unsure")

    # Explain a specific quiz question
    with st.expander("📌 Explain a quiz question"):
        titles = [s["title"] for s in content["sections"]]
        sec = st.selectbox("Section", titles, key="exp_sec")
        n_q = len(next(s for s in content["sections"]
                       if s["title"] == sec)["quiz"])
        qnum = st.number_input("Question #", 1, n_q, 1, key="exp_q")
        if st.button("Explain it", use_container_width=True):
            prompt = ai_tutor.question_lookup(content, sec, int(qnum))
            if prompt:
                run_tutor(prompt)

    # Conversation
    for m in st.session_state.chat:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.markdown(m["content"])

    if st.session_state.chat:
        if st.button("🧹 Clear chat", use_container_width=True):
            st.session_state.chat = []
            st.rerun(scope="fragment")

    user_text = st.chat_input("Ask anything about the exam…")
    if user_text:
        run_tutor(user_text)
        st.rerun(scope="fragment")


with st.sidebar:
    tutor_panel()
    st.divider()
    st.caption(
        "Tip: in the study hub, click **🤖 Explain this** under any answer to "
        "copy the question, then paste it here."
    )

# ----------------------------- STUDY HUB (main) ---------------------------
st.components.v1.html(build_html(), height=920, scrolling=True)
