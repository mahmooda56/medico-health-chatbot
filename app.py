"""Medico: an educational health-information chat interface."""
from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, UnidentifiedImageError

load_dotenv()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MAX_IMAGE_BYTES = 10 * 1024 * 1024
SYSTEM_INSTRUCTION = """You are Medico, an educational health-information assistant, not a clinician.
Never claim to diagnose, interpret an image as a confirmed finding, or replace professional care.
Offer general, cautious information; ask concise follow-up questions when needed; distinguish
possibilities from facts; and encourage the user to contact a licensed clinician for personal
medical decisions. Do not prescribe medication or recommend changing a prescribed treatment.
For possible emergencies, tell the user to contact local emergency services or go to an emergency
department now. Be empathetic, clear, and concise. Remind users that AI can be wrong."""

st.set_page_config(page_title="Medico | Health information", page_icon="🩺", layout="wide")
st.markdown(
    """
    <style>
      .block-container {max-width: 980px; padding-top: 2rem;}
      [data-testid="stSidebar"] {border-right: 1px solid rgba(120, 140, 160, .18);}
      .notice {padding: 1rem 1.1rem; border-radius: 12px; background: #eff6ff;
               border: 1px solid #bfdbfe; margin: .75rem 0 1.25rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("🩺 Medico")
    st.caption("General health information, with an AI assistant")
    st.divider()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        st.success("Gemini is configured on the server.")
    else:
        st.warning("Set GEMINI_API_KEY in the server environment or deployment secrets.")
    st.caption(f"Model: {MODEL_NAME}")
    st.divider()
    st.markdown("#### Optional image")
    uploaded_file = st.file_uploader(
        "Attach an image to your questions",
        type=["png", "jpg", "jpeg", "webp"],
        help="While attached, the image is sent to Google Gemini with each submitted question.",
    )
    image_acknowledged = st.checkbox(
        "I understand this image will be sent to Google Gemini when I submit my question.",
        disabled=uploaded_file is None,
    )
    if uploaded_file is not None:
        st.warning("Avoid images that show names, dates of birth, or other identifying details.")
        if uploaded_file.size > MAX_IMAGE_BYTES:
            st.error("This image is over the 10 MB limit. Choose a smaller file.")
            uploaded_file = None
            image = None
        elif image_acknowledged:
            try:
                image = Image.open(uploaded_file)
                image.verify()
                uploaded_file.seek(0)
                image = Image.open(uploaded_file).convert("RGB")
                st.image(image, caption="Attached to your questions", use_container_width=True)
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

st.title("A calmer place to ask health questions")
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

prompt = st.chat_input("What would you like general information about?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    if not api_key:
        st.error("The app owner must configure GEMINI_API_KEY on the server before chat is available.")
    elif uploaded_file is not None and not image_acknowledged:
        st.error("Confirm image sharing in the sidebar, or remove the image before submitting.")
    else:
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
            client = genai.Client(api_key=api_key)
            with st.chat_message("assistant"):
                with st.spinner("Preparing a general-information response…"):
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents,
                        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.3),
                    )
                answer = (response.text or "").strip()
                if not answer:
                    answer = "I couldn't prepare a response. Please rephrase your question and try again."
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception:
            st.error("I couldn't reach Gemini. Check the server key and model, then try again.")

st.caption(
    "Your questions and any attached image are sent to Google Gemini when submitted. "
    "Avoid sharing identifying or highly sensitive information."
)
