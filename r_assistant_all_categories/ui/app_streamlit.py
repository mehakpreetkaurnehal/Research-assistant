# # ui/app_streamlit.py


import streamlit as st
import requests

st.set_page_config(
    page_title="AI Demo App",
    layout="centered"
)

# ---- Styles (unchanged) ----
st.markdown("""
<style>
    .title { font-size: 42px; font-weight: 800; text-align: center; color: #4A90E2; }
    .subtitle { text-align: center; font-size: 18px; color: #666; margin-bottom: 30px; }
    .chat-container { border-radius: 12px; padding: 15px; background: #F7F9FC; border: 1px solid #E0E6ED; }
    .user-msg { background: #D4E6FF; padding: 10px; border-radius: 10px; width: fit-content; max-width: 80%; }
    .bot-msg { background: #EFEFEF; padding: 10px; border-radius: 10px; width: fit-content; max-width: 80%; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>AI Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>A lightweight demo built with Streamlit 🌟</p>", unsafe_allow_html=True)

API_URL = "http://localhost:8000/ask"   # >>> FIX: Add API endpoint here

st.subheader("Ask something from research papers:")

user_input = st.text_input("Your question:")

if st.button("Send"):
    if user_input.strip() == "":
        st.warning("Please enter something!")
    else:

        # Display user message
        st.markdown(f"<div class='chat-container'><div class='user-msg'><b>You:</b> {user_input}</div>", unsafe_allow_html=True)

        # >>> FIX: Call FastAPI backend
        try:
            response = requests.post(API_URL, json={"question": user_input})
            data = response.json()

            bot_reply = data["answer"]
            sources   = data.get("sources", [])

        except Exception as e:
            bot_reply = f"Error: {e}"
            sources = []

        # Display assistant response
        st.markdown(f"<div class='bot-msg'><b>Assistant:</b> {bot_reply}</div>", unsafe_allow_html=True)

        # >>> FIX: Show clickable PDF links
        if sources:
            st.markdown("### 📚 Sources")
            for s in sources:
                st.markdown(f"- [{s['paper_id']}]({s['pdf_url']})")   # CLICKABLE PDF LINKS

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#aaa;'>© 2024 Demo App</p>", unsafe_allow_html=True)







# import streamlit as st
# import requests

# # Configuration — adjust if needed
# API_URL = "http://localhost:8000/ask"

# def main():
#     st.set_page_config(page_title="Research Paper Assistant", layout="wide")
#     st.title("📚 Research Paper Assistant")
#     st.write("Ask a question and get answers *from research papers* with clickable source links.")

#     question = st.text_area("Enter your question", height=150, placeholder="What is reinforcement learning?")
#     submit   = st.button("Ask")

#     if submit:
#         if not question.strip():
#             st.warning("Please write a question before submitting.")
#             return

#         with st.spinner("Processing..."):
#             try:
#                 resp = requests.post(API_URL, json={"question": question})
#                 resp.raise_for_status()
#                 data = resp.json()
#             except Exception as e:
#                 st.error(f"Error calling API: {e}")
#                 return

#         answer  = data.get("answer", "")
#         sources = data.get("sources", [])

#         st.markdown("### ✅ Answer")
#         st.markdown(answer)

#         if sources:
#             st.markdown("### 🔍 Sources")
#             for src in sources:
#                 title    = src.get("title") or src.get("paper_id")
#                 authors  = src.get("authors") or []
#                 pubdate  = src.get("published_date") or ""
#                 url      = src.get("url") or ""
#                 category = src.get("category") or ""
#                 paper_id = src.get("paper_id") or ""

#                 # Display title as a clickable link if URL available
#                 if url:
#                     st.markdown(f"**[{title}]({url})**")
#                 else:
#                     st.markdown(f"**{title}**")

#                 if authors:
#                     st.markdown(f"• Authors: {', '.join(authors)}  ")
#                 if pubdate:
#                     st.markdown(f"• Published: {pubdate}  ")
#                 if category:
#                     st.markdown(f"• Category: `{category}`  ")
#                 st.markdown(f"• Paper ID: {paper_id}  ")
#                 st.markdown("---")
#         else:
#             st.info("No sources found for this question.")

#     st.markdown("---")
#     st.caption("Powered by your Research Paper Assistant system")

# if __name__ == "__main__":
#     main()
