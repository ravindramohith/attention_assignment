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
    cookie_manager.delete("auth_token")
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.current_chat = None
    st.session_state.chats = []
    st.experimental_rerun()


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
    st.sidebar.title("Your Chats")

    if st.sidebar.button("🆕 New Chat"):
        st.session_state.current_chat = None
        st.session_state.messages = []
        st.rerun()

    for chat in st.session_state.chats:
        if st.sidebar.button(f"💬 {chat['title']}", key=f"chat_{chat['id']}"):
            st.session_state.current_chat = chat
            messages = (
                json.loads(chat["messages"])
                if isinstance(chat["messages"], str)
                else chat["messages"]
            )
            st.session_state.messages = messages
            st.rerun()


def render_chat_interface():
    st.title("Travel Planner Chat")

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

                    # Include current message history in the request
                    all_messages = []
                    if st.session_state.messages:
                        # Add existing messages from the chat
                        for msg in st.session_state.messages:
                            all_messages.append(
                                {"role": "user", "content": msg["user_input"]}
                            )
                            all_messages.append(
                                {"role": "assistant", "content": msg["bot_response"]}
                            )

                    # Add the new message
                    all_messages.append({"role": "user", "content": user_input})

                    response = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "username": st.session_state.username,
                            "chat_id": current_chat_id,
                            "message": user_input,
                            "title": (
                                user_input[:30] + "..." if not current_chat_id else None
                            ),
                            "messages": all_messages,  # Send full message history
                        },
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                    )

                    # Rest of the existing code remains same
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
    if st.session_state.messages:
        for msg in st.session_state.messages:
            with st.container():
                st.text(f"You: {msg['user_input']}")
                st.text(f"Assistant: {msg['bot_response']}")
                st.divider()


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
        username = st.text_input("Username", key="register_username")
        password = st.text_input("Password", type="password", key="register_password")
        if st.button("Register"):
            response = requests.post(
                f"{API_URL}/register", json={"username": username, "password": password}
            )
            if response.status_code == 200:
                st.success("Registration successful! Please login.")
            else:
                st.error("Registration failed. Username might be taken.")


def main():
    # st.set_page_config(page_title="Travel Planner", layout="wide")

    init_session_state()

    if st.session_state.authenticated:
        col1, col2 = st.columns([1, 3])

        with col1:
            render_chat_list()
            if st.button("Logout"):
                handle_logout()

        with col2:
            render_chat_interface()
    else:
        render_auth()


if __name__ == "__main__":
    main()
