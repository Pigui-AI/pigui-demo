import io
import warnings
import requests
import streamlit as st
from datetime import datetime
from pathlib import Path
import base64

# Suppress warnings
warnings.filterwarnings("ignore")

# Page config to remove padding
st.set_page_config(
    page_title="Pigui AI Chat",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# API_URL_CHAT = "http://localhost:8000/ai/chat/branch"
# API_URL_ASR = "http://localhost:8000/ai/asr"
# API_URL_TTS = "http://localhost:8000/ai/tts"

API_URL_CHAT = "https://dev-apipiguibackend.pigui.ai/ai/chat/branch"
API_URL_ASR = "https://dev-apipiguibackend.pigui.ai/ai/asr"
API_URL_TTS = "https://dev-apipiguibackend.pigui.ai/ai/tts"


TOPICS = {
    "All topics": [
        "Who are my most valuable customers?",
        "What times they buy, where, and why?",
        "Purchase frequency and average ticket?",
    ],
    "Customers & Behavior": [
        "Who are my most valuable customers?",
        "What times they buy, where, and why?",
        "Purchase frequency and average ticket?",
    ],
    "Sales & Revenue": [
        "What drives my highest revenue days?",
        "Which products generate the most profit?",
        "How can I increase average ticket size?",
    ],
    "Marketing & Campaigns": [
        "Which campaigns bring the most visits?",
        "Best times to launch a new promo?",
        "Which channels drive repeat customers?",
    ],
    "Rewards & Loyalty": [
        "Which rewards improve repeat visits?",
        "Who redeems rewards the most?",
        "How can I optimize points usage?",
    ],
    "Products & Services": [
        "Which items are trending this month?",
        "What products should I discontinue?",
        "Which bundles could increase sales?",
    ],
    "Customer Experience": [
        "What are the top customer complaints?",
        "When do we receive the best feedback?",
        "How can we reduce churn rate?",
    ],
    "Operations & Branch Performance": [
        "Which hours are most efficient?",
        "Where are operational bottlenecks?",
        "How can we improve staff coverage?",
    ],
    "Growth & Strategy": [
        "Where should we expand next?",
        "What growth levers are underused?",
        "Which segments offer the most growth?",
    ],
}


def init_state():
    # Get IDs from URL query parameters
    query_params = st.query_params
    client_id = query_params.get("client_id", "")
    branch_id = query_params.get("branch_id", "")
    
    # Store in session state
    st.session_state.setdefault("client_id", client_id)
    st.session_state.setdefault("branch_id", branch_id)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("active_topic", "All topics")
    st.session_state.setdefault("context_loaded", False)
    st.session_state.setdefault("playing_audio", {})


def reset_chat():
    st.session_state.messages = []
    st.session_state.context_loaded = False


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


def validate_ids():
    """Validate that required IDs are present in URL parameters."""
    if not st.session_state.client_id or not st.session_state.branch_id:
        st.error("⚠️ Missing required parameters")
        st.markdown("""
        Please access this page with the required URL parameters:
        
        ```
        http://localhost:8501/?client_id=YOUR_CLIENT_ID&branch_id=YOUR_BRANCH_ID
        ```
        
        **Example:**
        ```
        http://localhost:8501/?client_id=939d59ae-43b0-4e21-89dd-d4aaed3d4fae&branch_id=6b90a72a-5aec-4da1-bfb9-eae3afd3395f
        ```
        """)
        st.stop()


def show_loading_screen():
    """Display custom loading screen with centered GIF."""
    import base64
    from pathlib import Path
    
    # Load GIF and encode to base64
    gif_path = Path(__file__).parent / "assets" / "Saludo-Media-resolucion.gif"
    with open(gif_path, "rb") as f:
        gif_data = base64.b64encode(f.read()).decode()
    
    loading_html = f"""
    <style>
        .loading-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: #F3F6FA;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }}
        .loading-gif {{
            max-width: 300px;
            max-height: 300px;
        }}
    </style>
    <div class="loading-container">
        <img src="data:image/gif;base64,{gif_data}" class="loading-gif" alt="Loading...">
    </div>
    """
    return st.markdown(loading_html, unsafe_allow_html=True)


def load_initial_context():
    """Load initial context from API endpoint on first load."""
    if st.session_state.context_loaded:
        return
    
    if not st.session_state.client_id or not st.session_state.branch_id:
        return
    
    # Show custom loading screen
    loading_placeholder = st.empty()
    with loading_placeholder.container():
        show_loading_screen()
    
    try:
        initial_message = "Provide a brief overview of this branch's performance."
        payload = {
            "client_id": st.session_state.client_id,
            "branch_id": st.session_state.branch_id,
            "messages": [{"role": "user", "content": initial_message}],
        }
        resp = requests.post(API_URL_CHAT, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        data = data.get("data") or {}
        answer = data.get("response") or "(No response)"
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.context_loaded = True
    except requests.RequestException as exc:
        st.warning(f"Could not load initial context: {exc}")
    finally:
        loading_placeholder.empty()


def send_prompt(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        try:
            answer, missing = send_chat()
            st.session_state.messages.append({"role": "assistant", "content": answer})
            if missing:
                st.caption(f"Missing: {missing}")
        except requests.RequestException as exc:
            st.error(f"Error calling API: {exc}")


def get_pigui_avatar():
    """Load Pigui SVG avatar as base64 data URL."""
    import base64
    from pathlib import Path
    
    svg_path = Path(__file__).parent / "assets" / "PuguiChat-ziCgELVp.svg"
    with open(svg_path, "rb") as f:
        svg_data = base64.b64encode(f.read()).decode()
    return f"data:image/svg+xml;base64,{svg_data}"


def chat_view():
    # Inject comprehensive CSS to fix all issues
    st.markdown("""
    <style>
    /* REMOVE ALL TOP SPACING - AGGRESSIVE */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
    }
    .stApp {
        margin-top: -100px !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }
    div[data-testid="stVerticalBlock"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* VERY SMALL BUTTON TEXT - FORCE OVERRIDE */
    .stButton > button,
    button[kind="secondary"],
    button[kind="primary"],
    div[data-testid="stHorizontalBlock"] button {
        font-size: 9px !important;
        padding: 0.25rem 0.35rem !important;
        min-height: 32px !important;
        height: auto !important;
        line-height: 1.0 !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    
    /* Transparent backgrounds */
    div[data-testid="column"]:last-child > div {
        background-color: transparent !important;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # This injects a custom class for the main container
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    
    # Load Pigui avatar
    pigui_avatar = get_pigui_avatar()

    st.title("Chat with Pigui about any topic related to your branch!")
    st.caption("Choose what Pigui should focus on to help you make better decisions for this branch.")

    # Topic selection
    topic_cols = st.columns(len(TOPICS))
    for i, topic_name in enumerate(TOPICS.keys()):
        with topic_cols[i]:
            is_active = st.session_state.active_topic == topic_name
            if st.button(
                topic_name,
                key=f"topic_{i}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_topic = topic_name
                st.rerun()

    st.markdown("<hr class='chat-divider'>", unsafe_allow_html=True)

    # Main layout for chat and suggestions
    main_cols = st.columns([4, 1])
    with main_cols[0]:
        # Chat History
        with st.container(height=400):
            if not st.session_state.messages:
                with st.chat_message("assistant", avatar=pigui_avatar):
                    st.write(
                        "Hi! I'm Pigui. I'm here to help you understand and "
                        "improve this branch. What would you like to explore today?"
                    )

            for i, msg in enumerate(st.session_state.messages):
                avatar = pigui_avatar if msg["role"] == "assistant" else None
                with st.chat_message(msg["role"], avatar=avatar):
                    st.write(msg["content"])
                    
                    # Add TTS button for assistant messages
                    if msg["role"] == "assistant":
                        audio_key = f"audio_{i}"
                        is_playing = st.session_state.playing_audio.get(audio_key, False)
                        
                        button_label = "⏸️ Stop" if is_playing else "🔊 Listen"
                        if st.button(button_label, key=f"tts_{i}"):
                            if is_playing:
                                st.session_state.playing_audio[audio_key] = False
                                st.rerun()
                            else:
                                st.session_state.playing_audio[audio_key] = True
                                synthesize_speech_streaming(msg["content"])
                                st.session_state.playing_audio[audio_key] = False

    with main_cols[1]:
        st.write("")  # Spacer for alignment
        active_questions = TOPICS.get(st.session_state.active_topic, [])
        for q in active_questions:
            if st.button(q, use_container_width=True, key=f"sugg_{q}"):
                send_prompt(q)
                st.rerun()

    # Close the custom class div
    st.markdown("</div>", unsafe_allow_html=True)

    # Audio input section
    with st.expander("🎤 Upload Audio (Optional)", expanded=False):
        audio_file = st.file_uploader(
            "Upload audio to transcribe",
            type=["wav", "mp3", "m4a", "ogg", "webm"],
            key="audio_uploader"
        )
        
        if audio_file is not None:
            with st.spinner("Transcribing audio..."):
                audio_bytes = audio_file.read()
                transcribed_text = transcribe_audio(
                    audio_bytes,
                    audio_file.name,
                    audio_file.type
                )
                
                if transcribed_text:
                    # Send transcribed text as message
                    st.session_state.messages.append({
                        "role": "user",
                        "content": transcribed_text
                    })
                    
                    with st.spinner("Pigui is thinking..."):
                        try:
                            answer, missing = send_chat()
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer
                            })
                            
                            if missing:
                                st.caption(f"Missing: {missing}")
                        except requests.RequestException as exc:
                            st.error(f"Error: {exc}")
                    
                    st.rerun()
    
    # Text input (always available)
    if user_prompt := st.chat_input("Ask Pigui anything you'd like - I'm here to help!"):
        send_prompt(user_prompt)
        st.rerun()


def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> str | None:
    files = {"file": (filename, audio_bytes, content_type)}
    try:
        resp = requests.post(API_URL_ASR, files=files, timeout=20)
        resp.raise_for_status()
        data = resp.json()
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
        with requests.post(API_URL_TTS, json=payload, timeout=60, stream=True) as resp:
            resp.raise_for_status()
            audio_buffer = io.BytesIO()
            for chunk in resp.iter_content(chunk_size=4096):
                if chunk:
                    audio_buffer.write(chunk)
            st.audio(audio_buffer.getvalue(), format="audio/mp3", autoplay=True)
    except requests.RequestException as e:
        st.error(f"Error during voice synthesis: {e}")


def synthesize_speech_streaming(text: str):
    """Streaming TTS that generates and plays audio progressively."""
    payload = {
        "text": text,
        "model": "tts-1-hd",
        "voice": "nova",
        "format": "mp3",
        "speed": 1.0,
    }
    try:
        with requests.post(API_URL_TTS, json=payload, timeout=60, stream=True) as resp:
            resp.raise_for_status()
            audio_buffer = io.BytesIO()
            
            # Stream chunks and build audio progressively
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    audio_buffer.write(chunk)
            
            # Play complete audio with autoplay
            audio_buffer.seek(0)
            st.audio(audio_buffer.getvalue(), format="audio/mp3", autoplay=True)
    except requests.RequestException as e:
        st.error(f"Error during streaming synthesis: {e}")


def send_chat(system_only_messages: list[str] | None = None):
    payload_messages = list(st.session_state.messages)
    if system_only_messages:
        payload_messages.append({"role": "user", "content": system_only_messages[0]})

    payload = {
        "client_id": st.session_state.client_id,
        "branch_id": st.session_state.branch_id,
        "messages": payload_messages,
    }
    resp = requests.post(API_URL_CHAT, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    data = data.get("data") or {}
    answer = data.get("response") or "(No response)"
    missing = data.get("missing")
    return answer, missing


def load_css():
    """Load CSS from external file."""
    from pathlib import Path
    
    # Try multiple possible paths for CSS file
    possible_paths = [
        Path(__file__).parent / "assets" / "styles.css",  # Local development
        Path("/app/streamlit_app/assets/styles.css"),     # Docker absolute path
        Path("streamlit_app/assets/styles.css"),          # Docker relative path
    ]
    
    css_file = None
    for path in possible_paths:
        if path.exists():
            css_file = path
            break
    
    if css_file is None:
        # CSS not found, continue without it
        return
    
    try:
        with open(css_file, encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not load CSS from {css_file}: {e}")


def main():
    st.set_page_config(layout="wide")
    load_css()

    init_state()
    validate_ids()
    load_initial_context()
    chat_view()


if __name__ == "__main__":
    main()
