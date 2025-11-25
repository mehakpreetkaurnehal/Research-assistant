#implemented simple code to know how to use Streamlit
import streamlit as st

st.set_page_config(
    page_title="AI Demo App",
    # page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    .title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        color: #4A90E2;
        margin-bottom: -5px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }
    .chat-container {
        border-radius: 12px;s
        padding: 15px;
        background: #F7F9FC;
        border: 1px solid #E0E6ED;
        margin-bottom: 10px;
    }
    .user-msg {
        background: #D4E6FF;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 6px;
        width: fit-content;
        max-width: 80%;
    }
    .bot-msg {
        background: #EFEFEF;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 6px;
        width: fit-content;
        max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>AI Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>A lightweight demo built with Streamlit 🌟</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Settings")
    st.radio("Mode", ["Chat", "Q&A", "Summary"])
    st.text_input("API Key (optional)")
    # st.write("---")
    # st.caption("Created with ❤️ using Streamlit")


st.subheader("Try Asking Something:")

# Input field
user_input = st.text_input("Your message:")

# Button
if st.button("Send"):
    if user_input.strip() == "":
        st.warning("Please enter a message!")
    else:
        # User bubble
        st.markdown(f"<div class='chat-container'><div class='user-msg'><b>You:</b> {user_input}</div>", unsafe_allow_html=True)
        
        # Fake assistant response (you can replace it with your model)
        bot_reply = "🤖 This is a demo response. You can replace this with your backend model output."
        
        # Bot bubble
        st.markdown(f"<div class='bot-msg'><b>Assistant:</b> {bot_reply}</div></div>", unsafe_allow_html=True)

# Footer
st.markdown("<br><br><br><br><p style='text-align:center; color:#aaa;'>© 2024 Demo App</p>", unsafe_allow_html=True)
