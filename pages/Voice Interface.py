import io
import json
import os
import time
import wave
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

st.set_page_config(page_title="Voice Assistant", page_icon="🎙️", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TTS_VOICES = ["Kore", "Puck", "Charon", "Aoede", "Fenrir", "Leda", "Orus", "Zephyr"]
MAX_RESULT_CHARS = 4000
HISTORY_TURNS = 6
TEXT_MODELS = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-flash-lite-latest"]
TTS_MODELS = ["gemini-3.8-flash-tts", "gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts-preview"]


# Setup
@st.cache_resource
def get_client():
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=90_000))  # ms


@st.cache_data
def load_data():
    df = pd.read_csv(ROOT / "cleaned_data.csv", parse_dates=["order_date", "delivery_date"])
    return df


def describe_dataset(df):
    """Compact schema description that is sent to Gemini instead of the full data."""
    lines = [f"Rows: {len(df)}, Columns: {df.shape[1]}", "", "Columns (dtype -> info):"]
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            info = f"min={s.min()}, max={s.max()}, mean={round(s.mean(), 2)}"
        elif pd.api.types.is_datetime64_any_dtype(s):
            info = f"from {s.min().date()} to {s.max().date()}"
        elif s.nunique() <= 30:
            info = f"values={sorted(s.dropna().unique().tolist())}"
        else:
            info = f"{s.nunique()} unique values, e.g. {s.dropna().unique()[:3].tolist()}"
        lines.append(f"- {col} ({s.dtype}) -> {info}")
    lines += ["", "Sample rows:", df.head(3).to_string()]
    return "\n".join(lines)


client = get_client()
df = load_data()
DATA_DESCRIPTION = describe_dataset(df)


# Prompts
CODE_SYSTEM_PROMPT = f"""You are a data analyst assistant for an e-commerce shopping-cart dataset.
The user speaks (audio) or writes in Egyptian Arabic or English and asks questions about the data.

A pandas DataFrame named `df` is already loaded. Its description:
{DATA_DESCRIPTION}

Notes:
- Each row is one sales line (a product inside an order). An order_id can appear in several rows,
  so count orders with df['order_id'].nunique(), and customers with df['customer_id'].nunique().
- Revenue / sales = total_price.

Your task: return JSON with these keys:
- "question": the user's question transcribed/rewritten clearly (keep the user's language).
- "is_data_question": true if answering needs the data, false for greetings / small talk.
- "code": Python code (pandas) that computes the answer. Rules:
    * `df`, `pd`, `np`, `px`, `go` are available. Do NOT import anything, read files, or modify files.
    * Store the final answer in a variable named `result` (number, string, Series or small DataFrame).
    * Keep `result` small (aggregate / use head(20)).
    * If a chart would help (trends, comparisons, distributions) or the user asks for one,
      also create a Plotly figure in a variable named `fig` with a clear title.
    * Empty string if is_data_question is false.
"""

ANSWER_SYSTEM_PROMPT = """You are "Nour", a friendly Egyptian data assistant.
Always answer in Egyptian Arabic dialect (العامية المصرية), e.g. use "ده، دي، عشان، كده، إزاي، أكتر، بتاع".
Your answer will be read aloud, so:
- Keep it short and conversational: 1 to 4 sentences.
- No markdown, no tables, no bullet points, no code, no emojis.
- Write numbers as digits copied exactly from the analysis result (e.g. 427 or 45,376), never spell them
  out in words. You may round large numbers (e.g. 131 ألف). Mention units (e.g. دولار، قطعة، طلب، عميل).
- If a chart was created, mention briefly that the chart is shown on the screen.
- If the analysis failed, apologize briefly and ask the user to rephrase.
Base your answer ONLY on the analysis result provided; do not invent numbers."""


# Gemini helpers
def call_gemini(model, fallbacks, **kwargs):
    """generate_content with retries; on overload/timeout (429/5xx) fall back to other models."""
    last_error = None
    for m in [model] + [f for f in fallbacks if f != model]:
        for attempt in range(2):
            try:
                return client.models.generate_content(model=m, **kwargs)
            except genai_errors.APIError as e:
                last_error = e
                if e.code == 404:
                    break  # model not available for this key -> try the next one
                if e.code not in (429, 500, 503, 504):
                    raise
                time.sleep(1 + attempt * 2)
    raise last_error


def history_as_text():
    turns = st.session_state.messages[-HISTORY_TURNS * 2:]
    if not turns:
        return "No previous conversation."
    return "\n".join(f"{m['role']}: {m['content']}" for m in turns)


def generate_code(user_part, model, error_feedback=None):
    prompt = f"Previous conversation (for context of follow-up questions):\n{history_as_text()}\n\n"
    if error_feedback:
        prompt += f"Your previous code failed:\n{error_feedback}\nFix it.\n\n"
    prompt += "Current user question:"

    response = call_gemini(
        model, TEXT_MODELS,
        contents=[prompt, user_part],
        config=types.GenerateContentConfig(
            system_instruction=CODE_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING"},
                    "is_data_question": {"type": "BOOLEAN"},
                    "code": {"type": "STRING"},
                },
                "required": ["question", "is_data_question", "code"],
            },
            temperature=0.1,
        ),
    )
    return json.loads(response.text)


def run_code(code):
    namespace = {"df": df.copy(), "pd": pd, "np": np, "px": px, "go": go}
    exec(code, namespace)
    result = namespace.get("result")
    fig = namespace.get("fig")
    if isinstance(result, (pd.DataFrame, pd.Series)):
        result_text = result.to_string()
    else:
        result_text = str(result)
    return result_text[:MAX_RESULT_CHARS], fig if isinstance(fig, go.Figure) else None


def generate_answer(question, result_text, has_chart, model):
    prompt = (
        f"Previous conversation:\n{history_as_text()}\n\n"
        f"User question: {question}\n\n"
        f"Analysis result:\n{result_text}\n\n"
        f"Chart shown on screen: {'yes' if has_chart else 'no'}"
    )
    response = call_gemini(
        model, TEXT_MODELS,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=ANSWER_SYSTEM_PROMPT, temperature=0.6),
    )
    return response.text.strip()


def text_to_speech(text, model, voice):
    response = call_gemini(
        model, TTS_MODELS,
        contents=f"{text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )
    pcm = response.candidates[0].content.parts[0].inline_data.data
    # Gemini TTS returns raw 16-bit mono PCM at 24 kHz -> wrap it as WAV
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)
    return buffer.getvalue()


def handle_turn(user_part, model, tts_model, voice, speak):
    """Full pipeline: question -> pandas code -> result -> Egyptian answer -> speech."""
    with st.status("بفكر... 🤔", expanded=False) as status:
        status.update(label="بفهم السؤال وبكتب الكود...")
        plan = generate_code(user_part, model)
        question = plan["question"]

        result_text, fig, code = "", None, ""
        if plan["is_data_question"] and plan["code"].strip():
            code = plan["code"]
            status.update(label="بحلل الداتا...")
            try:
                result_text, fig = run_code(code)
            except Exception as e:
                status.update(label="في غلطة، بحاول تاني...")
                plan = generate_code(user_part, model, error_feedback=f"{code}\n\nError: {e!r}")
                code = plan["code"]
                try:
                    result_text, fig = run_code(code)
                except Exception as e2:
                    result_text = f"Analysis failed: {e2!r}"

        status.update(label="بجهز الرد...")
        answer = generate_answer(question, result_text or "(small talk, no analysis needed)", fig is not None, model)

        audio = None
        if speak:
            status.update(label="بسجل الرد الصوتي...")
            try:
                audio = text_to_speech(answer, tts_model, voice)
            except Exception as e:
                st.warning(f"Text-to-speech failed: {e}")
        status.update(label="خلصت ✅", state="complete")

    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "fig": fig, "audio": audio, "code": code}
    )


# UI
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Settings")
    model = st.selectbox("Analysis model", TEXT_MODELS)
    tts_model = st.selectbox("Voice model", TTS_MODELS)
    voice = st.selectbox("Voice", TTS_VOICES)
    speak = st.toggle("Speak answers", value=True)
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🎙️ Voice Data Assistant")
st.caption("اسأل عن بيانات المبيعات بصوتك أو بالكتابة، والمساعد هيرد عليك بالمصري. "
           "Click the mic 🎤 in the box below to record, or type your question.")

if client is None:
    st.error("GEMINI_API_KEY was not found in the .env file.")
    st.stop()

if not st.session_state.messages:
    st.info("جرب تسأل: \"إيه أكتر نوع منتج اتباع؟\" أو \"ارسملي المبيعات في كل شهر\" أو \"مين أكتر ولاية بتشتري؟\"")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        if msg.get("fig") is not None:
            st.plotly_chart(msg["fig"], use_container_width=True, key=f"fig_{i}")
        if msg.get("audio"):
            is_latest = i == len(st.session_state.messages) - 1
            st.audio(msg["audio"], format="audio/wav", autoplay=is_latest and st.session_state.get("autoplay", False))
        if msg.get("code"):
            with st.expander("Code"):
                st.code(msg["code"], language="python")
st.session_state.autoplay = False

if st.session_state.get("last_error"):
    st.error(st.session_state.last_error)

prompt = st.chat_input("اكتب سؤالك أو دوس على المايك 🎤", accept_audio=True)

if prompt:
    if prompt.audio is not None:
        user_part = types.Part.from_bytes(data=prompt.audio.getvalue(), mime_type="audio/wav")
    elif prompt.text.strip():
        user_part = prompt.text.strip()
    else:
        user_part = None

    if user_part is not None:
        try:
            handle_turn(user_part, model, tts_model, voice, speak)
            st.session_state.autoplay = True
            st.session_state.last_error = None
        except genai_errors.APIError as e:
            if e.code in (429, 500, 503, 504):
                st.session_state.last_error = "Gemini مشغول أوي دلوقتي 😅 جرب تسأل تاني كمان شوية."
            else:
                st.session_state.last_error = f"Gemini error: {e}"
        except Exception as e:
            st.session_state.last_error = f"Something went wrong: {e!r}"
        st.rerun()
