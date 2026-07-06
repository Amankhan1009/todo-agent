import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq

from graph.state import AgentState
from prompts.system_prompt import SYSTEM_PROMPT
from tools.add_task import add_task_tool

from tools.view_tasks import view_tasks_tool
from tools.search_tasks import search_tasks_tool
from tools.update_task import update_task_tool
from tools.delete_task import delete_task_tool


load_dotenv()


groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY is not set in the environment.")


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=groq_api_key,
)


tools = [
    add_task_tool,
    view_tasks_tool,
    search_tasks_tool,
    update_task_tool,
    delete_task_tool,
]


llm_with_tools = llm.bind_tools(tools)


def agent_node(state: AgentState) -> dict:
    """Call the LLM with system instructions and conversation messages."""

    messages_for_llm = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages_for_llm)

    return {
        "messages": [response]
    }