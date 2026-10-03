"""Medico: multilingual, educational health information with optional image input."""
from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, UnidentifiedImageError

load_dotenv()


def setting(name: str, default: str = "") -> str:
    """Read Streamlit Cloud secrets first, then local environment variables."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default) or default).strip()


MODEL_NAME = setting("GEMINI_MODEL", "gemini-3.8-flash")
API_KEY = setting("GEMINI_API_KEY")
MAX_IMAGE_BYTES = 10 * 1024 * 1024
SYSTEM_INSTRUCTION = """You are Medico, an educational health-information assistant, not a clinician.
Never claim to diagnose, interpret an image as a confirmed finding, or replace professional care.
Offer general, cautious information; distinguish possibilities from facts; and encourage users to
contact a licensed clinician for personal medical decisions. Do not prescribe medication or
recommend changing a prescribed treatment. For possible emergencies, tell the user to contact
local emergency services or go to an emergency department now. Be empathetic. Remind users that AI
can be wrong. Reply in the same language as the user's latest question by default, and support any
language you can communicate in. If a response language is specified in the app, use that language.
Do not change languages unless the user asks."""

st.set_page_config(page_title="Medico | Health information", page_icon="🩺", layout="wide")
st.markdown(
    """
    <style>
      .stApp {background: linear-gradient(180deg, #f5fbfa 0%, #f8fafc 55%, #ffffff 100%);}
      .block-container {max-width: 1060px; padding-top: 2rem; padding-bottom: 3rem;}
      [data-testid="stSidebar"] {background: #edf6f4; border-right: 1px solid #d7e8e5;}
      [data-testid="stChatMessage"] {border: 1px solid #e4eeee; border-radius: 16px; padding: .35rem .7rem;}
      .notice {padding: 1rem 1.2rem; border-radius: 14px; background: #eaf6f4;
               border: 1px solid #c6e4de; margin: .75rem 0 1.25rem; color: #173b3a;}
      div.stButton > button {border-radius: 12px; border-color: #b9d8d2;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("🩺 Medico")
    st.caption("Clear, caring health information for everyone")
    st.divider()
    if API_KEY:
        st.success("Gemini is configured securely on the server.")
    else:
        st.warning("The owner needs to add GEMINI_API_KEY in Streamlit app Secrets.")
    st.caption(f"Model: {MODEL_NAME}")
    st.divider()
    st.markdown("#### Personalize your answer")
    language_preference = st.text_input(
        "Reply language (optional)",
        placeholder="Auto-match my question",
        help="Leave blank to answer in the language you use, or enter any language name.",
    ).strip()
    advanced_mode = st.toggle(
        "Advanced explanations",
        value=False,
        help="Free option for more context and technical terms with plain-language explanations.",
    )
    st.divider()
    st.markdown("#### Optional image")
    uploaded_file = st.file_uploader(
        "Attach a picture to your question",
        type=["png", "jpg", "jpeg", "webp"],
        help="The picture is sent to Google Gemini only when you submit your question.",
    )
    image_acknowledged = st.checkbox(
        "I understand this picture will be sent to Google Gemini when I submit my question.",
        disabled=uploaded_file is None,
    )
    if uploaded_file is not None:
        st.warning("Avoid pictures showing names, dates of birth, or other identifying details.")
        if uploaded_file.size > MAX_IMAGE_BYTES:
            st.error("This picture exceeds the 10 MB limit. Choose a smaller image.")
            uploaded_file = None
            image = None
        elif image_acknowledged:
            try:
                image = Image.open(uploaded_file)
                image.verify()
                uploaded_file.seek(0)
                image = Image.open(uploaded_file).convert("RGB")
                st.image(image, caption="Picture attached to your question", use_container_width=True)
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
                st.error("That file could not be opened as a safe image. Try another PNG, JPG, or WEBP.")
                uploaded_file = None
                image = None
        else:
            image = None
    else:
        image = None
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("Medico")
st.subheader("A calmer place to ask health questions")
st.markdown(
    '<div class="notice"><strong>For information only.</strong> Medico is an AI tool, not a '
    "doctor or diagnostic service. It can be wrong. Don't use it for emergencies or to make "
    'treatment decisions.</div>',
    unsafe_allow_html=True,
)
with st.expander("When to get urgent help", expanded=False):
    st.write(
        "If someone may be in immediate danger—for example, trouble breathing, severe chest pain, "
        "stroke symptoms, a severe allergic reaction, or loss of consciousness—contact your local "
        "emergency number or go to an emergency department now."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask in any language—for general health information")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    if not API_KEY:
        st.error("The app owner must add GEMINI_API_KEY in Streamlit app Secrets before answers are available.")
    elif uploaded_file is not None and not image_acknowledged:
        st.error("Please confirm picture sharing in the sidebar, or remove the picture before submitting.")
    else:
        language_rule = (
            f"Respond in {language_preference}."
            if language_preference
            else "Detect the language of the latest question and answer in that same language."
        )
        detail_rule = (
            "Give a detailed, well-structured explanation. Explain medical terms in plain language, "
            "include useful context and sensible next steps, while following all medical safety rules."
            if advanced_mode
            else "Give a clear, concise answer in everyday language, with practical next steps."
        )
        try:
            contents: list[types.Content] = []
            for previous in st.session_state.messages[:-1]:
                role = "model" if previous["role"] == "assistant" else "user"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=previous["content"])]))
            final_parts = []
            if uploaded_file is not None:
                final_parts.append(types.Part.from_bytes(data=uploaded_file.getvalue(), mime_type=uploaded_file.type or "image/jpeg"))
            final_parts.append(types.Part.from_text(text=prompt))
            contents.append(types.Content(role="user", parts=final_parts))
            client = genai.Client(api_key=API_KEY)
            with st.chat_message("assistant"):
                with st.spinner("Preparing a general-information response…"):
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=f"{SYSTEM_INSTRUCTION}\n{language_rule}\n{detail_rule}",
                            temperature=0.3,
                        ),
                    )
                answer = (response.text or "").strip()
                if not answer:
                    answer = "I couldn't prepare a response. Please rephrase your question and try again."
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception:
            st.error("I couldn't reach Gemini. Check the server key and model, then try again.")

st.caption(
    "Your questions and any attached picture are sent to Google Gemini when submitted. "
    "Avoid sharing identifying or highly sensitive information."
)
