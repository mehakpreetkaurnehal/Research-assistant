
import streamlit as st
import requests
import time

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    .title {
        font-size: 46px;
        font-weight: 800;
        text-align: center;
        color: #2c82f7;
        margin-top: -10px;
    }
    .subtitle {
        text-align: center;
        font-size: 20px;
        color: #555;
        margin-top: -10px;
        margin-bottom: 25px;
    }
    .chat-box {
        padding: 15px;
        border-radius: 14px;
        margin-bottom: 12px;
        animation: fadeIn 0.4s ease;
    }
    .user-msg {
        background: #dbe7ff;
        border-left: 5px solid #2c82f7;
    }
    .bot-msg {
        background: #f0f0f0;
        border-left: 5px solid #34a853;
    }
    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(10px);}
        to   {opacity: 1; transform: translateY(0);}
    }
</style>
""", unsafe_allow_html=True)

# >>> NEW: Personalized greeting
st.markdown("<h1 class='title'>🤖 AI Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask anything from research papers!</p>", unsafe_allow_html=True)


with st.sidebar:
    st.header("👤 Personalize Experience")

    # >>> NEW: User name input — stored in session
    user_name = st.text_input("Enter your name:", value=st.session_state.get("name", ""))
    
    if user_name:
        st.session_state["name"] = user_name

    st.write("---")
    st.caption("✨ All responses are generated from your research paper database.")


if "name" in st.session_state and st.session_state["name"]:
    st.markdown(
        f"<h3>👋 Hello <b>{st.session_state['name']}</b>! How can I help you today?</h3>",
        unsafe_allow_html=True
    )
else:
    st.markdown("<h3>👋 Hello! What would you like to explore today?</h3>", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/ask"  # backend API

# Store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---- CHAT MESSAGE INPUT ----
user_input = st.text_input("Type your question:")

if st.button("Send"):
    if not user_input.strip():
        st.warning("Please type a question.")
    else:
        # Add user message to chat history
        st.session_state.messages.append(("user", user_input))

        # Send request to API
        try:
            response = requests.post(
                API_URL, json={"question": user_input}, timeout=20
            )

            if response.status_code != 200:
                bot_reply = f"⚠️ Backend error:\n{response.text}"
                sources = []
            else:
                data = response.json()
                bot_reply = data["answer"]
                sources = data.get("sources", [])

        except Exception as e:
            bot_reply = f"❌ Could not reach backend: {e}"
            sources = []

        # Save bot reply
        st.session_state.messages.append(("bot", bot_reply, sources))



for msg in st.session_state.messages:
    if msg[0] == "user":
        st.markdown(
            f"<div class='chat-box user-msg'><b>You:</b> {msg[1]}</div>",
            unsafe_allow_html=True
        )
    else:
        bot_text = msg[1]
        sources = msg[2]

        st.markdown(
            f"<div class='chat-box bot-msg'><b>Assistant:</b> {bot_text}</div>",
            unsafe_allow_html=True
        )

        # >>> NEW: Show sources as clickable links with icons
        if sources:
            st.markdown("#### 📚 Sources")
            for s in sources:
                st.markdown(
                    f"- 🔗 [{s['paper_id']}]({s['pdf_url']})",
                    unsafe_allow_html=True
                )

# Footer
st.markdown("<br><p style='text-align:center; color:#aaa;'>© 2025 AI Research Assistant</p>",
            unsafe_allow_html=True)















#working code
# import gradio as gr
# import requests
# from urllib.parse import quote_plus

# API_URL = "http://localhost:8000/ask"

# def ask_question_ui(question: str):
#     payload = {"question": question}
#     try:
#         resp = requests.post(API_URL, json=payload)
#         resp.raise_for_status()
#         data = resp.json()
#     except Exception as e:
#         # return a single string each for both outputs
#         return f"Error: {e}", ""

#     answer = data.get("answer", "")
#     sources = data.get("sources", [])

#     # Format markdown for sources
#     md = ""
#     for s in sources:
#         pid      = s.get("paper_id", "")
#         title    = s.get("title", "")
#         authors  = s.get("authors", [])
#         date     = s.get("published_date", "")
#         abstract = s.get("abstract", "")
#         url      = s.get("url", f"https://arxiv.org/pdf/{quote_plus(pid)}")

#         display_name = title or pid
#         md += f"**[{display_name}]({url})**  \n"
#         if authors:
#             md += f"*Authors:* {', '.join(authors)}  \n"
#         if date:
#             md += f"*Published:* {date}  \n"
#         if abstract:
#             md += f"*Abstract:* {abstract[:250]}…  \n"
#         md += "\n---\n\n"

#     # Return two strings: one for answer_output, one for sources_output
#     return answer, md

# with gr.Blocks() as demo:
#     gr.Markdown("# 🧠 Research Paper Assistant")
#     question_input = gr.Textbox(label="Question", placeholder="Enter your research question here", lines=2)
#     submit_btn = gr.Button("Ask")

#     answer_output  = gr.Markdown(label="Answer")
#     sources_output = gr.Markdown(label="Sources (click to open)")

#     submit_btn.click(fn=ask_question_ui,
#                      inputs=[question_input],
#                      outputs=[answer_output, sources_output])

# demo.launch()


#properly working code
# import gradio as gr
# import requests
# from urllib.parse import quote_plus

# API_URL = "http://localhost:8000/ask"

# def ask_question_ui(question: str, category: str = ""):
#     payload = {"question": question}
#     if category and category.strip():
#         payload["category"] = category.strip()
#     try:
#         resp = requests.post(API_URL, json=payload)
#         resp.raise_for_status()
#         data = resp.json()
#         answer = data.get("answer", "")
#         sources = data.get("sources", [])
#         # Remove duplicate paper_ids
#         seen = set()
#         unique_sources = []
#         for s in sources:
#             pid = s.get("paper_id")
#             if pid and pid not in seen:
#                 seen.add(pid)
#                 unique_sources.append(pid)
#         # Format clickable links
#         src_text = ""
#         for pid in unique_sources:
#             url = f"https://arxiv.org/pdf/{quote_plus(pid)}"
#             src_text += f"[{pid}]({url})\n"
#         return answer, src_text
#     except Exception as e:
#         return f"Error: {e}", ""

# with gr.Blocks() as demo:
#     gr.Markdown("# Research Paper Assistant")
#     question_input = gr.Textbox(label="Question", placeholder="Enter your research question here", lines=2)
#     # category_input = gr.Textbox(label="Category (optional)", placeholder="e.g. machine_learning or biology", lines=1)
#     answer_output = gr.Markdown(label="Answer")
#     sources_output = gr.Markdown(label="Sources (click to open)")

#     submit_btn = gr.Button("Ask")
#     submit_btn.click(fn=ask_question_ui, inputs=[question_input], outputs=[answer_output, sources_output])

# demo.launch()
