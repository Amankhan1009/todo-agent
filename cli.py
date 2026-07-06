from langchain_core.messages import HumanMessage

from database.checkpointer import create_checkpointer
from graph.builder import build_graph
from graph.context import TodoContext


USER_ID = "aman"
THREAD_ID = "default-thread"


def main() -> None:
    """Run the Todo Agent terminal application."""

    config = {
        "configurable": {
            "thread_id": THREAD_ID,
        }
    }

    context = TodoContext(
        user_id=USER_ID,
    )

    with create_checkpointer() as checkpointer:
        graph = build_graph(checkpointer)

        print("Todo Agent started.")
        print(f"User ID: {USER_ID}")
        print(f"Thread ID: {THREAD_ID}")
        print("Type 'exit' or 'quit' to stop the application.")

        while True:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit"}:
                print("Todo Agent stopped.")
                break

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

            print(f"\nAssistant: {assistant_message.content}")


if __name__ == "__main__":
    main()