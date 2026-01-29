import io
import requests
import streamlit as st
from typing import Optional


def hide_streamlit_elements():
    """Ocultar elementos de Streamlit UI (Deploy button y opciones del menú)"""
    hide_style = """
        <style>
        /* Ocultar el botón Deploy */
        [data-testid="stToolbar"] button[kind="header"]:first-child,
        button[data-testid="baseButton-header"]:has(span:contains("Deploy")),
        header button:has([data-testid="stDeployButton"]),
        [data-testid="stDeployButton"],
        button[kind="header"][data-testid*="deploy"],
        button[title="Deploy this app"] {
            display: none !important;
        }

        /* Ocultar opciones específicas del menú hamburger excepto Print y Record screencast */
        [data-testid="stMainMenu"] li:has(a[href*="settings"]),
        [data-testid="stMainMenu"] li:has(a[href*="about"]),
        [data-testid="stMainMenu"] li:has(span:contains("Settings")),
        [data-testid="stMainMenu"] li:has(span:contains("About")),
        [data-testid="stMainMenu"] li:has(span:contains("Clear cache")),
        [data-testid="stMainMenu"] li:has(span:contains("Rerun")),
        [data-testid="stMainMenu"] li:has(span:contains("Report a bug")),
        [data-testid="stMainMenu"] li:has(span:contains("Get help")) {
            display: none !important;
        }

        /* Reducir tamaño de fuente en el sidebar */
        [data-testid="stSidebar"] {
            font-size: 0.85rem !important;
        }

        [data-testid="stSidebar"] h2 {
            font-size: 1.1rem !important;
        }

        [data-testid="stSidebar"] h3 {
            font-size: 1rem !important;
        }

        [data-testid="stSidebar"] .stButton button {
            font-size: 0.75rem !important;
            padding: 0.3rem 0.5rem !important;
            min-height: 2rem !important;
        }

        [data-testid="stSidebar"] .stCaption {
            font-size: 0.75rem !important;
        }

        [data-testid="stSidebar"] p {
            font-size: 0.85rem !important;
        }

        /* Reducir tamaño del título principal */
        h1 {
            font-size: 1.8rem !important;
        }
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)


# API URLs
API_BASE_URL = "https://dev-apipiguibackend.pigui.ai"
API_URL_CONVERSATIONS = f"{API_BASE_URL}/ai/conversations"
API_URL_ASR = f"{API_BASE_URL}/ai/asr"
API_URL_TTS = f"{API_BASE_URL}/ai/tts"


def init_state():
    """Inicializar estado de la sesión"""
    query_params = st.query_params

    # IDs desde URL
    if "client_id" not in st.session_state:
        st.session_state.client_id = query_params.get("client_id", "")
    if "branch_id" not in st.session_state:
        st.session_state.branch_id = query_params.get("branch_id", "")

    # User ID (en producción vendría del sistema de auth)
    if "user_id" not in st.session_state:
        st.session_state.user_id = query_params.get("user_id", st.session_state.client_id)

    # Conversación actual
    st.session_state.setdefault("current_conversation_id", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("conversations_list", [])
    st.session_state.setdefault("conversations_loaded", False)


def fetch_conversations(user_id: str, page: int = 1, page_size: int = 20):
    """Obtener lista de conversaciones del usuario"""
    try:
        params = {"user_id": user_id, "status": "active", "page": page, "page_size": page_size}
        resp = requests.get(API_URL_CONVERSATIONS, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {})
    except Exception as e:
        st.error(f"Error loading conversations: {e}")
        return None


def fetch_conversation_detail(conversation_id: str):
    """Obtener detalle completo de una conversación"""
    try:
        url = f"{API_URL_CONVERSATIONS}/{conversation_id}"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {})
    except Exception as e:
        st.error(f"Error loading conversation: {e}")
        return None


def start_new_conversation(user_id: str, message: str, client_id: str, branch_id: str):
    """Iniciar una nueva conversación"""
    try:
        url = f"{API_URL_CONVERSATIONS}/start"
        params = {
            "user_id": user_id,
            "message": message,
            "context_type": "contextual",
            "client_id": client_id,
            "branch_id": branch_id,
        }
        resp = requests.post(url, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {})
    except Exception as e:
        st.error(f"Error starting conversation: {e}")
        return None


def continue_conversation(conversation_id: str, message: str):
    """Continuar una conversación existente"""
    try:
        url = f"{API_URL_CONVERSATIONS}/{conversation_id}/continue"
        payload = {
            "conversation_id": conversation_id,
            "message": message,
            "model": "gpt-4-1106-preview",
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {})
    except Exception as e:
        st.error(f"Error continuing conversation: {e}")
        return None


def load_conversation(conversation_id: str):
    """Cargar una conversación y actualizar el estado"""
    conversation = fetch_conversation_detail(conversation_id)
    if conversation:
        st.session_state.current_conversation_id = conversation_id
        st.session_state.messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation.get("messages", [])]
        return True
    return False


def update_conversation_title(conversation_id: str, new_title: str):
    """Actualizar el título de una conversación"""
    try:
        url = f"{API_URL_CONVERSATIONS}/{conversation_id}"
        payload = {"title": new_title}
        resp = requests.patch(url, json=payload, timeout=60)
        resp.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error updating title: {e}")
        return False


def archive_conversation(conversation_id: str):
    """Archivar una conversación (marcarla como inactiva)"""
    try:
        url = f"{API_URL_CONVERSATIONS}/{conversation_id}"
        payload = {"status": "archived"}
        resp = requests.patch(url, json=payload, timeout=60)
        resp.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error archiving conversation: {e}")
        return False


def start_new_chat():
    """Archivar conversación actual e iniciar una nueva"""
    # Archivar conversación actual si existe
    if st.session_state.current_conversation_id:
        archive_conversation(st.session_state.current_conversation_id)

    # Limpiar estado para nueva conversación
    st.session_state.messages = []
    st.session_state.current_conversation_id = None
    st.session_state.conversations_loaded = False


def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
    """Transcribir audio a texto"""
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
    """Sintetizar texto a voz"""
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


def process_message(message: str):
    """Procesar un mensaje (iniciar o continuar conversación)"""
    user_id = st.session_state.user_id
    client_id = st.session_state.client_id
    branch_id = st.session_state.branch_id

    if st.session_state.current_conversation_id:
        # Continuar conversación existente
        result = continue_conversation(st.session_state.current_conversation_id, message)
        if result:
            return result.get("response"), result.get("conversation_id")
    else:
        # Iniciar nueva conversación
        result = start_new_conversation(user_id, message, client_id, branch_id)
        if result:
            st.session_state.current_conversation_id = result.get("conversation_id")
            return result.get("response"), result.get("conversation_id")

    return None, None


def chat_view():
    """Vista principal del chat"""
    st.title("Business Intelligence Chat - Pigui AI")
    st.caption("Ask about your products, sales, customer feedback, and business performance")

    # Cargar avatar personalizado - buscar en múltiples ubicaciones
    import os

    possible_paths = [
        "scripts/assets/PuguiChat-ziCgELVp.svg",  # Local
        "assets/PuguiChat-ziCgELVp.svg",  # Docker
        "./assets/PuguiChat-ziCgELVp.svg",  # Docker alternativo
    ]
    avatar_path = None
    for path in possible_paths:
        if os.path.exists(path):
            avatar_path = path
            break

    with st.sidebar:
        # Cargar conversaciones si no están cargadas
        if not st.session_state.conversations_loaded:
            with st.spinner("Loading conversations..."):
                conv_data = fetch_conversations(st.session_state.user_id)
                if conv_data:
                    st.session_state.conversations_list = conv_data.get("conversations", [])
                    st.session_state.conversations_loaded = True

        # Botón para nueva conversación (siempre visible)
        if st.button("➕ New Conversation", use_container_width=True, type="primary"):
            start_new_chat()
            st.rerun()

        st.divider()

        # Sección 1: Historial de Conversaciones (colapsable)
        total_convs = len(st.session_state.conversations_list)
        # Mantener abierto si alguna conversación está en modo edición
        is_editing = any(st.session_state.get(f"edit_{conv['id']}", False) for conv in st.session_state.conversations_list)
        with st.expander(f"📜 Conversation History ({total_convs})", expanded=is_editing):
            # Mostrar lista de conversaciones
            if st.session_state.conversations_list:
                for conv in st.session_state.conversations_list:
                    conv_id = conv["id"]
                    title = conv.get("title") or "Untitled conversation"
                    message_count = conv.get("message_count", 0)

                    # Indicador si es la conversación actual
                    is_current = conv_id == st.session_state.current_conversation_id
                    button_type = "primary" if is_current else "secondary"

                    # Formatear título con info (asegurar que title no sea None)
                    title_str = str(title) if title else "Untitled"
                    truncated_title = title_str[:40] if len(title_str) > 40 else title_str
                    display_title = f"{'🔵 ' if is_current else ''}{truncated_title}"
                    if len(title_str) > 40:
                        display_title += "..."
                    display_caption = f"{message_count} msgs"

                    # Verificar si está en modo edición
                    edit_key = f"edit_{conv_id}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    if st.session_state[edit_key]:
                        # Modo edición: mostrar input y botones
                        new_title = st.text_input(
                            "New title", value=title_str, key=f"input_{conv_id}", label_visibility="collapsed"
                        )
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("✓", key=f"save_{conv_id}", use_container_width=True):
                                if new_title and new_title != title_str:
                                    if update_conversation_title(conv_id, new_title):
                                        st.session_state[edit_key] = False
                                        st.session_state.conversations_loaded = False
                                        st.rerun()
                        with col2:
                            if st.button("✗", key=f"cancel_{conv_id}", use_container_width=True):
                                st.session_state[edit_key] = False
                                st.rerun()
                    else:
                        # Modo normal: mostrar botón de conversación
                        col1, col2, col3 = st.columns([5, 1, 1])
                        with col1:
                            if st.button(
                                display_title,
                                key=f"conv_{conv_id}",
                                use_container_width=True,
                                type=button_type,
                                help=f"{message_count} messages",
                            ):
                                if load_conversation(conv_id):
                                    st.rerun()
                        with col2:
                            st.caption(display_caption)
                        with col3:
                            if st.button("✏️", key=f"edit_btn_{conv_id}", help="Edit title"):
                                st.session_state[edit_key] = True
                                st.rerun()
            else:
                st.info("No previous conversations")

        st.divider()

        # Sección 2: Customers & Behavior
        with st.expander("� Customers & Behavior", expanded=False):
            st.caption("Help me to understand my customers")

            customer_questions = [
                "Who are my most valuable customers?",
                "What do they buy, when and why?",
                "Purchase frequency and average ticket",
                "Behavior before and after a reward",
                "New vs recurring customers",
                "Preferences by product, service or branch",
            ]

            for question in customer_questions:
                if st.button(question, key=f"customer_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

        # Sección 3: Sales & Revenue
        with st.expander("💰 Sales & Revenue", expanded=False):
            st.caption("Help me sell more and better")

            sales_questions = [
                "Sales by product / service",
                "Sales by campaign",
                "Real impact of promotions and rewards",
                "Best and worst performing products",
                "Upsell and cross-sell opportunities",
            ]

            for question in sales_questions:
                if st.button(question, key=f"sales_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

        # Sección 4: Marketing & Campaigns
        with st.expander("📢 Marketing & Campaigns", expanded=False):
            st.caption("Optimize your marketing strategy and ROI")

            marketing_questions = [
                "Which campaign type works best? (discount, gift, coupon, promo)",
                "When to launch a campaign?",
                "Who to target?",
                "Campaign ROI analysis",
                "Best channels: email, push notifications, QR",
            ]

            for question in marketing_questions:
                if st.button(question, key=f"marketing_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

        # Sección 5: Rewards & Loyalty
        with st.expander("🎁 Rewards & Loyalty", expanded=False):
            st.caption("Maximize customer loyalty and retention")

            rewards_questions = [
                "Which rewards work best?",
                "How much incentive without affecting margin?",
                "Activation vs retention strategies",
                "Customer loyalty analysis",
                "Pigui Points usage and effectiveness",
            ]

            for question in rewards_questions:
                if st.button(question, key=f"rewards_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

        # Sección 6: Products & Services
        with st.expander("📦 Products & Services", expanded=False):
            st.caption("Optimize your product portfolio and pricing")

            products_questions = [
                "Most and least profitable products",
                "Margin by product",
                "Products that attract new customers",
                "Services that generate recurrence",
                "Data-driven pricing adjustments",
            ]

            for question in products_questions:
                if st.button(question, key=f"products_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

        # Sección 7: Operations & Branch Performance
        with st.expander("🏪 Operations & Branch Performance", expanded=False):
            st.caption("Optimize branch efficiency and performance")

            operations_questions = [
                "Performance by branch",
                "Comparison between branches",
                "Peak sales hours",
                "Capacity vs demand analysis",
                "Operational efficiency metrics",
            ]

            for question in operations_questions:
                if st.button(question, key=f"operations_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

        # Sección 8: Customer Experience
        with st.expander("⭐ Customer Experience", expanded=False):
            st.caption("Enhance customer satisfaction and loyalty")

            experience_questions = [
                "Customer feedback analysis",
                "Friction points in customer journey",
                "Rewards as part of the experience",
                "Personalization by customer",
                "Brand perception and sentiment",
            ]

            for question in experience_questions:
                if st.button(question, key=f"experience_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

        # Sección 9: Growth & Strategy
        with st.expander("📈 Growth & Strategy", expanded=False):
            st.caption("Scale your business with data-driven decisions")

            growth_questions = [
                "New customer activation strategies",
                "Retention and churn analysis",
                "Organic growth opportunities",
                "What to scale and what to optimize",
                "Data-driven decisions, not intuition",
            ]

            for question in growth_questions:
                if st.button(question, key=f"growth_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response, conv_id = process_message(question)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.session_state.conversations_loaded = False
                    st.rerun()

    # Mostrar historial de mensajes
    for i, msg in enumerate(st.session_state.messages):
        avatar = avatar_path if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Play", key=f"play_{i}"):
                    with st.spinner("Generating audio..."):
                        synthesize_speech(msg["content"])

    # Saludo inicial solo si no hay mensajes Y no hay conversación activa
    if not st.session_state.messages and not st.session_state.current_conversation_id:
        with st.spinner("Loading greeting..."):
            response, conv_id = process_message("Hello")
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_conversation_id = conv_id
                st.session_state.conversations_loaded = False
                st.rerun()

    # Input del usuario
    if user_prompt := st.chat_input("Ask me anything..."):
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.chat_message("user"):
            st.write(user_prompt)

        # Procesar mensaje
        with st.spinner("Thinking..."):
            response, conv_id = process_message(user_prompt)
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.conversations_loaded = False  # Recargar lista
                st.rerun()


def main():
    """Función principal"""
    hide_streamlit_elements()
    init_state()

    # Validar parámetros requeridos
    if not st.session_state.client_id or not st.session_state.branch_id:
        st.error("⚠️ Missing required parameters")
        st.markdown("""
        Please provide both `client_id` and `branch_id` in the URL.

        **Example:**
        ```
        http://localhost:8501/?client_id=939d59ae-43b0-4e21-89dd-d4aaed3d4fae&branch_id=905d26a6-b946-4dd6-8b20-f0ae04d182ac
        ```
        """)
        st.stop()

    chat_view()


if __name__ == "__main__":
    main()
