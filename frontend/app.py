import streamlit as st
import extra_streamlit_components as stx
import requests
import json
import time
from datetime import datetime, timedelta

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Travel Planner", layout="wide")
cookie_manager = stx.CookieManager()


def init_session_state():
    defaults = {
        "authenticated": False,
        "username": "",
        "token": None,
        "current_chat": None,
        "chats": [],
        "messages": [],
    }

    # Initialize defaults if not present
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # Check for existing token in cookies
    token = cookie_manager.get("auth_token")
    if token and not st.session_state.authenticated:
        try:
            response = requests.post(
                f"{API_URL}/verify", headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                auth_data = response.json()
                st.session_state.token = token
                st.session_state.authenticated = True
                st.session_state.username = auth_data["username"]
                load_chats()
            else:
                handle_logout()
        except Exception as e:
            cookie_manager.delete("auth_token")


def handle_login(username: str, password: str):
    try:
        response = requests.post(
            f"{API_URL}/login", json={"username": username, "password": password}
        )
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["access_token"]

            # Set cookie with secure flags
            cookie_manager.set(
                "auth_token", token, expires_at=datetime.now() + timedelta(days=7)
            )

            # Update session state
            st.session_state.token = token
            st.session_state.authenticated = True
            st.session_state.username = auth_data["username"]

            st.success("Login successful!")
            load_chats()
            time.sleep(1)  # Give time for success message
            st.rerun()
        else:
            st.error("Invalid credentials")
    except Exception as e:
        st.error(f"Login failed: {str(e)}")


def handle_logout():
    for key in [
        "authenticated",
        "username",
        "token",
        "current_chat",
        "chats",
        "messages",
    ]:
        st.session_state[key] = (
            None
            if key == "token"
            else (
                []
                if key in ["chats", "messages"]
                else False if key == "authenticated" else ""
            )
        )

    # Clear cookie after state
    if cookie_manager.get("auth_token"):
        cookie_manager.delete("auth_token")

    # Force reload without cache
    st.markdown(
        """
        <script>
            window.parent.location.reload();
        </script>
        """,
        unsafe_allow_html=True,
    )


def load_chats():
    if st.session_state.token:
        try:
            response = requests.get(
                f"{API_URL}/chats/{st.session_state.username}",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
            )
            if response.status_code == 200:
                st.session_state.chats = response.json()
                # Sync current chat messages if needed
                if st.session_state.current_chat:
                    current = next(
                        (
                            c
                            for c in st.session_state.chats
                            if c["id"] == st.session_state.current_chat["id"]
                        ),
                        None,
                    )
                    if current:
                        st.session_state.current_chat = current
                        messages = (
                            json.loads(current["messages"])
                            if isinstance(current["messages"], str)
                            else current["messages"]
                        )
                        st.session_state.messages = messages
        except Exception as e:
            st.error(f"Error loading chats: {e}")


def render_chat_list():
    st.markdown(
        """
        <style>
            .stButton > button {
                width: 100%;
                margin-bottom: 5px;
                padding: 10px;
                border-radius: 5px;
            }
            section[data-testid="stSidebar"] .block-container {
                padding-bottom: 40px;
            }
            .new-chat-btn {
                background-color: #4CAF50 !important;
                color: white !important;
            }
            .chat-btn {
                text-align: left !important;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .logout-btn {
                position: fixed;
                bottom: 20px;
                width: calc(100% - 40px) !important;
                background-color: #ff4b4b !important;
                color: white !important;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("Your Chats")

    if st.sidebar.button("⨁ New Chat", key="new_chat", use_container_width=True):
        st.session_state.current_chat = None
        st.session_state.messages = []
        st.rerun()

    for chat in st.session_state.chats:
        title = chat["title"][:30] + "..." if len(chat["title"]) > 30 else chat["title"]
        if st.sidebar.button(
            f"💬 {title}", key=f"chat_{chat['id']}", use_container_width=True
        ):
            st.session_state.current_chat = chat
            messages = (
                json.loads(chat["messages"])
                if isinstance(chat["messages"], str)
                else chat["messages"]
            )
            st.session_state.messages = messages
            st.rerun()

    st.sidebar.markdown(
        '<div style="position: fixed; bottom: 20px; width: 100%;">',
        unsafe_allow_html=True,
    )
    if st.sidebar.button(
        "Logout",
        type="primary",
        key="logout_btn",
        help="Click to logout",
        use_container_width=True,
        on_click=handle_logout,
    ):
        pass
    st.sidebar.markdown("</div>", unsafe_allow_html=True)


def render_chat_interface():
    st.title("Travel Planner Chat")

    if st.session_state.messages:
        for msg in sorted(st.session_state.messages, key=lambda x: x["timestamp"]):
            with st.container():
                st.text(f"You: {msg['user_input']}")
                st.text(f"Assistant: {msg['bot_response']}")
                st.divider()

    with st.form(key="chat_form"):
        user_input = st.text_area("Your message:")
        if st.form_submit_button("Send"):
            if user_input:
                try:
                    current_chat_id = (
                        st.session_state.current_chat.get("id")
                        if st.session_state.current_chat
                        else None
                    )

                    # Build and sort message history by timestamp
                    all_messages = []
                    if st.session_state.messages:
                        # Sort existing messages by timestamp
                        sorted_messages = sorted(
                            st.session_state.messages,
                            key=lambda x: datetime.fromisoformat(x["timestamp"]),
                        )
                        # Add sorted messages to history
                        for msg in sorted_messages:
                            all_messages.append(
                                {
                                    "role": "user",
                                    "content": msg["user_input"],
                                    "timestamp": msg["timestamp"],
                                }
                            )
                            all_messages.append(
                                {
                                    "role": "assistant",
                                    "content": msg["bot_response"],
                                    "timestamp": msg["timestamp"],
                                }
                            )

                    # Add current message
                    current_timestamp = datetime.now().isoformat()
                    all_messages.append(
                        {
                            "role": "user",
                            "content": user_input,
                            "timestamp": current_timestamp,
                        }
                    )

                    response = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "username": st.session_state.username,
                            "chat_id": current_chat_id,
                            "message": user_input,
                            "title": (
                                user_input[:30] + "..." if not current_chat_id else None
                            ),
                            "messages": all_messages,
                        },
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        new_message = {
                            "user_input": user_input,
                            "bot_response": data["response"],
                            "timestamp": datetime.now().isoformat(),
                        }

                        if not st.session_state.messages:
                            st.session_state.messages = []
                        st.session_state.messages.append(new_message)

                        if not current_chat_id:
                            st.session_state.current_chat = {
                                "id": data["chat_id"],
                                "title": user_input[:30] + "...",
                                "messages": st.session_state.messages,
                            }

                        load_chats()
                        time.sleep(0.5)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error sending message: {e}")


def render_auth():
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            handle_login(username, password)

    with tab2:
        st.subheader("Register")
        reg_username = st.text_input("Username", key="register_username")
        reg_password = st.text_input(
            "Password", type="password", key="register_password"
        )

        if st.button("Register"):
            if not reg_username or not reg_password:
                st.error("Please enter both username and password")
                return

            try:
                response = requests.post(
                    f"{API_URL}/register",
                    json={"username": reg_username, "password": reg_password},
                )

                if response.status_code == 200:
                    st.success("Registration successful! Please login.")
                    time.sleep(1)
                    st.rerun()
                elif response.status_code == 400:
                    st.error("Username already exists. Please choose another.")
                else:
                    st.error("Registration failed. Please try again.")
            except Exception as e:
                st.error(f"Registration error: {str(e)}")


def main():
    init_session_state()

    if st.session_state.authenticated:
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            render_chat_list()
        with col2:
            render_chat_interface()
    else:
        render_auth()


if __name__ == "__main__":
    main()
