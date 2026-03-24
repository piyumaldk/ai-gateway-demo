import streamlit as st
from datetime import datetime
from pathlib import Path

from config import GUARDRAIL_APIS, DEFAULT_MODEL
from apim_client import GatewayClient
from logger import log_request, log_guardrail_block, log_system


# ============================================================
# Page Config & CSS
# ============================================================

st.set_page_config(
    page_title="WSO2 AI Gateway — Guardrails Demo",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = Path("styles.css")
if css_path.exists():
    st.html(f"<style>{css_path.read_text()}</style>")


# ============================================================
# Session State
# ============================================================

if "client" not in st.session_state:
    st.session_state.client = GatewayClient()
if "selected_guardrail_index" not in st.session_state:
    st.session_state.selected_guardrail_index = 0
if "model" not in st.session_state:
    st.session_state.model = DEFAULT_MODEL
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Welcome to the **WSO2 AI Gateway Guardrails Demo**.\n\n"
                   "Select a guardrail from the sidebar, then send a test prompt to see it in action.",
        "timestamp": datetime.now().strftime("%H:%M"),
        "blocked": False,
    }]
if "logs" not in st.session_state:
    st.session_state.logs = [log_system("AI Gateway Guardrails Demo started")]
if "show_logs" not in st.session_state:
    st.session_state.show_logs = False


# ============================================================
# Helpers
# ============================================================

def current_guardrail():
    return GUARDRAIL_APIS[st.session_state.selected_guardrail_index]


def format_error(response):
    if response.status_code == 401:
        return "**401 Unauthorized** — Check API subscription and API key."
    if response.status_code == 404:
        return "**404 Not Found** — API path does not exist on the gateway. Check context/version in config."
    if response.status_code == 500 and "endpoint" in response.content.lower():
        return "**Endpoint Error** — API is missing its backend LLM endpoint. Deploy a new revision in Publisher."
    return response.content


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.markdown("## WSO2 AI Gateway Demo")
    st.caption("WSO2 API Manager — Guardrails")

    # Connection status
    gateway_ok = st.session_state.client.test_connection()
    if gateway_ok:
        st.success("🟢 Gateway connected")
    else:
        st.error("🔴 Gateway unreachable")

   

    # Guardrail selection
    st.markdown("##### Select Guardrail")
    guardrail_names = [g["name"] for g in GUARDRAIL_APIS]
    selected_name = st.selectbox(
        "Guardrail", guardrail_names,
        index=st.session_state.selected_guardrail_index,
        label_visibility="collapsed",
    )

    new_index = guardrail_names.index(selected_name)
    if new_index != st.session_state.selected_guardrail_index:
        old = GUARDRAIL_APIS[st.session_state.selected_guardrail_index]
        new = GUARDRAIL_APIS[new_index]
        st.session_state.selected_guardrail_index = new_index
        st.session_state.logs.append(log_system(f"Switched: {old['name']} → {new['name']}"))
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Switched to **{new['name']}**.\n\n{new['desc']}\n\n"
                       f"*Try the test prompts below to see this guardrail in action.*",
            "timestamp": datetime.now().strftime("%H:%M"),
            "blocked": False,
        }]
        st.rerun()

    g = current_guardrail()

    st.divider()

    # Model selection
    st.markdown("##### Model")
    st.session_state.model = st.text_input("Model ID", value=st.session_state.model, label_visibility="collapsed")

    st.divider()


# ============================================================
# Header
# ============================================================

g = current_guardrail()
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f"### {g['name']}")
    st.caption(g['desc'])
    api_context = GUARDRAIL_APIS[st.session_state.selected_guardrail_index]['context']
    api_version = GUARDRAIL_APIS[st.session_state.selected_guardrail_index]['version']
    st.caption(f"API: `{api_context}/{api_version}`")
with col2:
    if st.button("⌨️ Logs", use_container_width=True):
        st.session_state.show_logs = not st.session_state.show_logs
        st.rerun()


# ============================================================
# Test Prompts (dynamic per guardrail)
# ============================================================

prompts = g["test_prompts"]
st.caption("**Test prompts** — click to try:")
cols = st.columns(len(prompts))
for i, p in enumerate(prompts):
    with cols[i]:
        if st.button(p["label"], key=f"tp_{i}", use_container_width=True):
            st.session_state["pending_prompt"] = p["text"]
            st.rerun()


# ============================================================
# Chat Display
# ============================================================

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else ("🛡️" if msg.get("blocked") else "🤖")
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("blocked"):
            st.error(f"🛡️ **GUARDRAIL INTERVENED** — {msg.get('guardrail_type', '')}")
            st.markdown(msg["content"])
        elif msg.get("error"):
            st.error(msg["content"])
        else:
            st.markdown(msg["content"])
        ts = msg.get("timestamp", "")
        latency = msg.get("latency_ms", 0)
        caption = f"🕐 {ts}"
        if latency:
            caption += f" · {latency}ms"
        st.caption(caption)


# ============================================================
# Process Message
# ============================================================

def process_message(user_text: str):
    now = datetime.now().strftime("%H:%M")
    g = current_guardrail()

    st.session_state.messages.append({
        "role": "user", "content": user_text, "timestamp": now, "blocked": False,
    })

    response = st.session_state.client.send_chat(
        message=user_text,
        context=g["context"],
        version=g["version"],
        chat_path=g["chat_path"],
        model=st.session_state.model,
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": response.content if (response.success or response.blocked) else format_error(response),
        "timestamp": now,
        "latency_ms": response.latency_ms,
        "blocked": response.blocked,
        "guardrail_type": response.guardrail_type if response.blocked else "",
        "error": not response.success and not response.blocked,
    })

    # Logging
    if response.blocked:
        st.session_state.logs.append(log_guardrail_block(
            guardrail=response.guardrail_type or g["name"],
            reason=f"Guardrail enforced on {g['context']}",
            score=1.0, direction="REQUEST",
        ))
    elif response.success:
        st.session_state.logs.append(log_request(
            api=g["name"], provider="azure_openai",
            model=st.session_state.model, tokens=response.tokens_used,
        ))
    else:
        st.session_state.logs.append(log_system(
            f"ERROR [{response.status_code}] {response.content[:200]}"
        ))

    st.rerun()


# Handle pending prompts
if "pending_prompt" in st.session_state:
    text = st.session_state.pending_prompt
    del st.session_state["pending_prompt"]
    process_message(text)

# Clear Chat button near chatbox
col_input, col_clear = st.columns([8, 1])
with col_clear:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        g = current_guardrail()
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Chat cleared. Active: **{g['name']}**\n\n{g['desc']}",
            "timestamp": datetime.now().strftime("%H:%M"),
            "blocked": False,
        }]
        st.rerun()

# Chat input
user_input = st.chat_input("Type a message...")
if user_input:
    process_message(user_input)


# ============================================================
# Log Console
# ============================================================

if st.session_state.show_logs:
    st.markdown("---")
    with st.expander("⌨️ AI Gateway Logs", expanded=True):
        log_html = '<div class="log-console">'
        log_html += (
            '<span style="color:#58a6ff;font-weight:600;">▶ Gateway Logs</span>'
            ' <span style="background:#238636;color:#fff;font-size:9px;'
            'padding:1px 6px;border-radius:4px;">LIVE</span><br><br>'
        )
        for entry in st.session_state.logs[-50:]:
            if "WARN" in entry or "GUARDRAIL" in entry:
                color = "#f0883e"
            elif "ERROR" in entry:
                color = "#f85149"
            else:
                color = "#8b949e"
            safe = entry.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            log_html += f'<div style="color:{color};padding:1px 0;word-break:break-all;">{safe}</div>'
        log_html += "</div>"
        st.html(log_html)
        if st.button("🗑️ Clear Logs"):
            st.session_state.logs = [log_system("Logs cleared")]
            st.rerun()
