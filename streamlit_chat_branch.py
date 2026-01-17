import io
import json
import requests
import streamlit as st


def log_to_browser_console(message):
    js_code = f"<script>console.log({json.dumps(message)});</script>"
    st.components.v1.html(js_code, height=0)


#API_URL_CHAT = "http://localhost:8000/ai/chat/branch"
#API_URL_ASR = "http://localhost:8000/ai/asr"
#API_URL_TTS = "http://localhost:8000/ai/tts"

API_URL_CHAT = "https://dev-apipiguibackend.pigui.ai/ai/chat/branch"
API_URL_ASR = "https://dev-apipiguibackend.pigui.ai/ai/asr"
API_URL_TTS = "https://dev-apipiguibackend.pigui.ai/ai/tts"


def init_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "ids"
    st.session_state.setdefault("client_id", "")
    st.session_state.setdefault("branch_id", "")
    st.session_state.setdefault("messages", [])


def reset_chat():
    st.session_state.messages = []
    st.session_state.stage = "ids"


def process_audio_and_chat():
    uploaded_file = st.session_state.get("audio_uploader")
    if not uploaded_file:
        return

    with st.spinner("Processing uploaded audio..."):
        audio_bytes = uploaded_file.read()
        user_prompt = transcribe_audio(audio_bytes, uploaded_file.name, uploaded_file.type)

    if user_prompt:
        st.info(f"Transcribed from audio: {user_prompt}")
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        # Immediately get response
        with st.spinner("Thinking..."):
            try:
                answer, missing = send_chat()
                st.session_state.messages.append({"role": "assistant", "content": answer})
                if missing:
                    st.caption(f"Missing: {missing}")
            except requests.RequestException as exc:
                st.error(f"Error calling API: {exc}")


def ids_view():
    st.title("Contextual Chat - Pigui AI")
    st.caption("First, enter the IDs to personalize the context")

    st.session_state.client_id = st.text_input("Client ID (UUID)", st.session_state.client_id)
    st.session_state.branch_id = st.text_input("Branch ID (UUID)", st.session_state.branch_id)

    if st.button("Continue"):
        if not all([st.session_state.client_id.strip(), st.session_state.branch_id.strip()]):
            st.warning("All IDs are required")
        else:
            st.session_state.stage = "chat"
            st.session_state.messages = []
            st.rerun()


def chat_view():
    st.title("Contextual Chat - Pigui AI")
    st.caption("Using client and branch context (30 days)")

    with st.sidebar:
        st.subheader("Context")
        st.text_input("Client ID", st.session_state.client_id, disabled=True)
        st.text_input("Branch ID", st.session_state.branch_id, disabled=True)
        if st.button("Change IDs"):
            reset_chat()
            st.rerun()

    # Display chat history
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                if st.button("Play", key=f"play_{i}"):
                    with st.spinner("Generating audio..."):
                        synthesize_speech(msg["content"])

    # Get initial greeting if chat is empty
    if not st.session_state.messages:
        with st.spinner("Loading greeting..."):
            try:
                initial_answer, _ = send_chat(["Hello"])
                if initial_answer:
                    st.session_state.messages.append({"role": "assistant", "content": initial_answer})
                    st.rerun()
            except requests.RequestException as exc:
                st.error(f"Error getting greeting: {exc}")

    # --- User Input Section ---
    st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"], key="audio_uploader", on_change=process_audio_and_chat)

    if user_prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.spinner("Thinking..."):
            try:
                answer, missing = send_chat()
                st.session_state.messages.append({"role": "assistant", "content": answer})
                if missing:
                    st.caption(f"Missing: {missing}")
                st.rerun()  # Rerun to display the new messages
            except requests.RequestException as exc:
                st.error(f"Error calling API: {exc}")


def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> str | None:
    files = {"file": (filename, audio_bytes, content_type)}
    try:
        log_to_browser_console(f"POST: {API_URL_ASR}")
        print("--- ASR REQUEST ---")
        print(f"File: {filename}, Type: {content_type}, "
              f"Size: {len(audio_bytes)} bytes")
        resp = requests.post(API_URL_ASR, files=files, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        print("--- ASR RESPONSE ---")
        print(data)
        data = data.get("data") or {}
        return data.get("text")
    except requests.RequestException as e:
        st.error(f"Error during transcription: {e}")
        return None


def synthesize_speech(text: str):
    payload = {
        "text": text,
        "model": "tts-1-hd",
        "voice": "nova",
        "format": "mp3",
        "speed": 1.0,
    }
    try:
        log_to_browser_console(f"POST: {API_URL_TTS}")
        print("--- TTS REQUEST ---")
        print(payload)
        with requests.post(API_URL_TTS, json=payload, timeout=60, stream=True) as resp:
            print(f"--- TTS RESPONSE STATUS: {resp.status_code} ---")
            resp.raise_for_status()
            audio_buffer = io.BytesIO()
            for chunk in resp.iter_content(chunk_size=4096):
                if chunk:
                    audio_buffer.write(chunk)
            st.audio(audio_buffer.getvalue(), format="audio/mp3", autoplay=True)
    except requests.RequestException as e:
        st.error(f"Error during voice synthesis: {e}")


def send_chat(system_only_messages: list[str] | None = None):
    payload_messages = list(st.session_state.messages)
    if system_only_messages:
        payload_messages.append({"role": "user", "content": system_only_messages[0]})

    payload = {
        "client_id": st.session_state.client_id,
        "branch_id": st.session_state.branch_id,
        "messages": payload_messages,
    }
    log_to_browser_console(f"POST: {API_URL_CHAT}")
    print("--- CHAT REQUEST ---")
    print(payload)
    resp = requests.post(API_URL_CHAT, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print("--- CHAT RESPONSE ---")
    print(data)
    data = data.get("data") or {}
    answer = data.get("response") or "(No response)"
    missing = data.get("missing")
    return answer, missing


def main():
    init_state()
    if st.session_state.stage == "ids":
        ids_view()
    else:
        chat_view()


if __name__ == "__main__":
    main()
