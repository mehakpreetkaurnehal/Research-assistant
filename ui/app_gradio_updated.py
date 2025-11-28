import streamlit as st
import requests
import html

st.set_page_config(
    page_title="AI Research Assistant",
    layout="centered",
)

st.markdown("""
<style>
    .title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        color: #2c82f7;
        margin-bottom: -5px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }
    .chat-box {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        animation: fadeIn 0.3s ease;
    }
    .user-msg {
        background: #d5e5ff;
        border-left: 5px solid #2c82f7;
    }
    .bot-msg {
        background: #efefef;
        border-left: 5px solid #34a853;
    }
    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(6px);}
        to   {opacity: 1; transform: translateY(0);}
    }
    .source-link a {
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("<div id='top'></div>", unsafe_allow_html=True)

st.markdown("<h1 class='title'>AI Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask anything from your research papers 📚</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Personalize Experience")

    user_name = st.text_input("Enter your name:", value=st.session_state.get("name", ""))
    if user_name:
        st.session_state["name"] = user_name


if "name" in st.session_state and st.session_state["name"]:
    st.markdown(
        f"<h3>👋 Hello <b>{st.session_state['name']}</b>! How can I help you today?</h3>",
        unsafe_allow_html=True,
    )
else:
    st.markdown("<h3>👋 Hello! What would you like to explore today?</h3>", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/ask"


# messages: list of tuples
# ("user", text) OR ("bot", text, sources)
if "messages" not in st.session_state:
    st.session_state.messages = []


if "input_key" not in st.session_state:
    st.session_state.input_key = 0

input_key = f"chat_input_{st.session_state.input_key}"

user_input = st.text_input(
    "Type your question:",
    key=input_key,
    placeholder="Ask something about your research papers..."
)


if st.button("Send"):
    if not user_input.strip():
        st.warning("Please enter a message.")
    else:
        # Save user message
        st.session_state.messages.append(("user", user_input))

        # Call backend API
        try:
            response = requests.post(API_URL, json={"question": user_input}, timeout=40)
            if response.status_code == 200:
                data = response.json()
                bot_reply = data.get("answer", "No answer returned.")
                sources = data.get("sources", [])
            else:
                bot_reply = f"Backend error: {response.text}"
                sources = []
        except Exception as e:
            bot_reply = f"⚠️ Error contacting backend: {e}"
            sources = []

        # Save bot reply
        st.session_state.messages.append(("bot", bot_reply, sources))

        # Rotate input key so next rerun creates a fresh empty text_input
        st.session_state.input_key += 1

        # Rerun the app to show updated chat + cleared input
        st.rerun()

for msg in st.session_state.messages:
    if msg[0] == "user":
        st.markdown(
            f"<div class='chat-box user-msg'><b>You:</b> {html.escape(msg[1])}</div>",
            unsafe_allow_html=True,
        )
    else:
        bot_text = msg[1]
        sources = msg[2] if len(msg) > 2 else []

        # Just show plain answer (no highlighting)
        safe_answer = html.escape(bot_text).replace("\n", "<br>")

        st.markdown(
            f"<div class='chat-box bot-msg'><b>Assistant:</b> {safe_answer}</div>",
            unsafe_allow_html=True,
        )

        # Display sources (each opens arXiv PDF in new tab)
        if sources:
            st.markdown("#### 📚 Sources")
            for s in sources:
                pid = s.get("paper_id", "")
                url = s.get("pdf_url", "#")
                st.markdown(
                    f"<div class='source-link'>- 🔗 <a href='{url}' target='_blank'>{pid}</a></div>",
                    unsafe_allow_html=True,
                )

st.markdown("<div id='bottom'></div>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center; margin-top:20px;'>
    <a href="#top">⬆️ Scroll to Top</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="#bottom">⬇️ Scroll to Bottom</a>
</div>
""", unsafe_allow_html=True)

# # Footer
# st.markdown(
#     "<br><p style='text-align:center; color:#aaa;'>© 2025 AI Research Assistant</p>",
#     unsafe_allow_html=True
# )
