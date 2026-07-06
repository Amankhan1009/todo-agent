import re

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from database.checkpointer import create_checkpointer
from database.schema import initialize_database
from graph.builder import build_graph
from graph.context import TodoContext


st.set_page_config(
    page_title="Todo Agent",
    page_icon="📋",
    layout="centered",
)


@st.cache_resource
def initialize_agent():
    """Create and cache the checkpointer and compiled LangGraph agent."""

    checkpointer_context = create_checkpointer()
    checkpointer = checkpointer_context.__enter__()

    graph = build_graph(checkpointer)

    return graph, checkpointer_context


def normalize_user_id(username: str) -> str:
    """Create a normalized user ID from the entered username."""

    normalized_username = username.strip().lower()

    normalized_username = re.sub(
        r"[^a-z0-9_-]+",
        "-",
        normalized_username,
    )

    normalized_username = normalized_username.strip("-")

    return normalized_username


def get_thread_id(user_id: str) -> str:
    """Create the main conversation thread ID for a user."""

    return f"user-{user_id}-main"


def get_config(thread_id: str) -> dict:
    """Return LangGraph configuration for the current conversation."""

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def get_context(user_id: str) -> TodoContext:
    """Return trusted runtime context for the current user."""

    return TodoContext(
        user_id=user_id,
    )


def get_conversation_messages(graph, config: dict) -> list:
    """Load persisted conversation messages from checkpoint state."""

    snapshot = graph.get_state(config)

    if not snapshot.values:
        return []

    return snapshot.values.get("messages", [])


def render_project_header(subtitle: str) -> None:
    """Render the centered project heading and subtitle."""

    st.markdown(
        """
        <h1 style="text-align: center; margin-bottom: 0;">
            📋 Todo Agent
        </h1>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <p style="
            text-align: center;
            color: gray;
            margin-top: 0;
            margin-bottom: 2rem;
        ">
            {subtitle}
        </p>
        """,
        unsafe_allow_html=True,
    )


def logout() -> None:
    """Clear the active user from the Streamlit session."""

    st.session_state.pop("user_id", None)

    st.rerun()


# ---------------------------------------------------------
# Database initialization
# ---------------------------------------------------------

# Streamlit Community Cloud starts with a fresh filesystem.
# The SQLite database file may be created automatically, but
# the tasks table must also be initialized before the agent
# tries to access it.
initialize_database()


# ---------------------------------------------------------
# Agent initialization
# ---------------------------------------------------------

graph, checkpointer_context = initialize_agent()


# ---------------------------------------------------------
# Login screen
# ---------------------------------------------------------

if "user_id" not in st.session_state:
    render_project_header(
        "Your intelligent AI-powered task management assistant."
    )

    with st.form("user_login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
        )

        submitted = st.form_submit_button(
            "Continue",
            use_container_width=True,
        )

    if submitted:
        user_id = normalize_user_id(username)

        if not user_id:
            st.error(
                "Please enter a valid username."
            )

        else:
            st.session_state["user_id"] = user_id

            st.rerun()

    st.stop()


# ---------------------------------------------------------
# Active user configuration
# ---------------------------------------------------------

USER_ID = st.session_state["user_id"]

THREAD_ID = get_thread_id(USER_ID)

config = get_config(THREAD_ID)

context = get_context(USER_ID)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("📋 Todo Agent")

    st.write(f"**User:** `{USER_ID}`")

    st.write(f"**Thread:** `{THREAD_ID}`")

    st.divider()

    st.caption(
        "Tasks are isolated by user ID."
    )

    st.caption(
        "Conversation memory is persisted using the "
        "LangGraph SQLite checkpointer."
    )

    st.divider()

    if st.button(
        "Logout",
        use_container_width=True,
    ):
        logout()


# ---------------------------------------------------------
# Main chat interface
# ---------------------------------------------------------

render_project_header(
    f"Manage your todo tasks using natural language, {USER_ID}."
)


try:
    conversation_messages = get_conversation_messages(
        graph=graph,
        config=config,
    )

except Exception as error:
    st.error(
        f"Could not load conversation history: {error}"
    )

    conversation_messages = []


for message in conversation_messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)

    elif isinstance(message, AIMessage):
        if message.content:
            with st.chat_message("assistant"):
                st.markdown(message.content)


user_input = st.chat_input(
    "Add, view, search, update, or delete a task..."
)


if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        with st.spinner("Thinking..."):
            result = graph.invoke(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },
                config=config,
                context=context,
            )

        assistant_message = result["messages"][-1]

        with st.chat_message("assistant"):
            st.markdown(assistant_message.content)

    except Exception as error:
        st.error(
            f"Something went wrong while processing your request: {error}"
        )