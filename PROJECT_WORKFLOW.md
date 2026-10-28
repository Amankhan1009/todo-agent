# Todo Agent: Complete Project Workflow and Technical Explanation

## 1. Executive summary

Todo Agent is a conversational task-management application. Instead of making a user fill out separate forms for creating, viewing, searching, editing, and deleting tasks, it lets the user describe an action in natural language, such as:

- `Add a task to learn Docker.`
- `Show me all my tasks.`
- `Find my Kubernetes task.`
- `Mark my Docker task as completed.`
- `Delete my Terraform task.`

The application uses a Groq-hosted language model through LangChain, LangGraph for agent orchestration, SQLite for task storage, a second SQLite database for persistent LangGraph checkpoints, and Streamlit for the web chat interface. A terminal CLI is also provided for development and testing.

The core idea is that the language model does not directly manipulate the database. It interprets the user's request, chooses one or more strongly defined tools, and the tools perform the actual database operations. The database result is then returned to the model so it can produce a truthful natural-language response.

## 2. What problem it solves

Traditional todo applications expose CRUD controls: a title field, a description field, a status selector, and buttons for saving or deleting. Todo Agent replaces much of that interaction with a conversation. The user can express intent naturally, while the application still performs structured and user-scoped database operations underneath.

The project demonstrates how to build a practical agentic AI system that combines:

- Natural-language understanding.
- Tool calling.
- A cyclic workflow that can execute multiple steps.
- Persistent conversation memory.
- Runtime context that carries trusted user information.
- Database-backed business operations.
- A simple multi-user application interface.

## 3. Main capabilities

The agent supports the following task operations:

1. **Create tasks** with a title and optional description.
2. **View all tasks** belonging to the active user.
3. **Search tasks** by text in the title or description.
4. **Update tasks** by changing the title, description, or status.
5. **Complete or reopen tasks** by changing their status.
6. **Delete tasks** by task ID or by a natural-language reference after searching.
7. **Persist conversation history** across application restarts through LangGraph's SQLite checkpointer.
8. **Separate users' task data** using a user ID on every task query.
9. **Separate conversations** using LangGraph thread IDs.
10. **Use either a Streamlit chat UI or a terminal CLI**.
11. **Display task timestamps in Indian Standard Time (IST)** after converting SQLite UTC timestamps.

## 4. Technology stack

- **Python:** Application language.
- **Streamlit:** Browser-based chat interface.
- **LangChain:** Message types, tool decorators, tool runtime integration, and model integration.
- **LangGraph:** Stateful agent workflow, conditional routing, cyclic execution, and checkpoint persistence.
- **Groq:** Hosted LLM inference provider.
- **Model:** `openai/gpt-oss-120b`, configured with temperature `0`.
- **SQLite:** Local task database and checkpoint database.
- **python-dotenv:** Loads `GROQ_API_KEY` from `.env`.
- **`langgraph.checkpoint.sqlite.SqliteSaver`:** Stores graph state and conversation checkpoints.

The pinned dependencies are listed in `requirements.txt`. The most important packages for the architecture are `langchain`, `langchain-core`, `langchain-groq`, `langgraph`, `langgraph-checkpoint-sqlite`, `streamlit`, `python-dotenv`, and `aiosqlite`/SQLite-related packages.

## 5. Repository structure

```text
.
├── app.py                         Streamlit web application entry point
├── cli.py                         Terminal application entry point
├── requirements.txt               Pinned Python dependencies
├── README.md                      Project overview and usage guide
├── .gitignore                     Secrets, local databases, and generated files
│
├── database/
│   ├── __init__.py
│   ├── schema.py                  Creates the task table and user index
│   ├── db.py                      Task CRUD/search functions and timestamp formatting
│   └── checkpointer.py            Persistent LangGraph SQLite checkpointer
│
├── graph/
│   ├── __init__.py
│   ├── state.py                   AgentState definition
│   ├── context.py                 Trusted runtime TodoContext definition
│   ├── nodes.py                   Groq model, system prompt, and agent node
│   ├── routing.py                 Tool-call conditional routing
│   └── builder.py                 LangGraph construction and compilation
│
├── tools/
│   ├── __init__.py
│   ├── add_task.py                LLM tool for creating tasks
│   ├── view_tasks.py              LLM tool for listing tasks
│   ├── search_tasks.py            LLM tool for searching tasks
│   ├── update_task.py             LLM tool for editing tasks
│   └── delete_task.py             LLM tool for deleting tasks
│
├── prompts/
│   ├── __init__.py
│   └── system_prompt.py           Agent behavior and safety instructions
│
└── tests/
    ├── __init__.py
    ├── test_threads.py            Manual thread-isolation demonstration
    ├── inspect_state.py           Checkpoint state inspection utility
    └── inspect_history.py          Checkpoint history inspection utility
```

## 6. End-to-end runtime workflow

The following is the complete workflow for a request made through Streamlit.

### Step 1: Streamlit starts

`app.py` is the web entry point. Streamlit executes the script from top to bottom whenever the page is loaded or the user submits a new chat message.

The application first configures the page title, icon, and centered layout.

### Step 2: The task database is initialized

`initialize_database()` from `database/schema.py` is called on every application run. It safely executes `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`, so repeated initialization does not destroy existing data.

The task database path is:

```text
database/todo.db
```

The table is named `tasks` and contains:

| Column | Meaning |
|---|---|
| `id` | Auto-incrementing task ID and primary key |
| `user_id` | Owner of the task |
| `title` | Required task title |
| `description` | Optional task details |
| `status` | Defaults to `pending` |
| `created_at` | SQLite creation timestamp |
| `updated_at` | Last-update timestamp |

An index named `idx_tasks_user_id` improves queries filtered by user.

### Step 3: The persistent checkpointer and graph are created

`initialize_agent()` in `app.py` is decorated with `st.cache_resource`, so the graph and checkpointer are reused by the Streamlit process rather than rebuilt for every interaction.

The function:

1. Calls `create_checkpointer()` from `database/checkpointer.py`.
2. Opens the checkpointer context.
3. Creates a `SqliteSaver` backed by `database/checkpoints.db`.
4. Passes that saver to `build_graph()`.
5. Returns the compiled graph and context manager.

The checkpoint database stores LangGraph state, including message history and intermediate graph checkpoints. It is separate from the task database; conversation memory and business data are intentionally stored separately.

### Step 4: The user enters a username

If `st.session_state` does not contain `user_id`, the application shows a login-like username form. This is not production authentication; it is an application-level identity selector.

`normalize_user_id()`:

1. Trims whitespace.
2. Converts the username to lowercase.
3. Replaces characters outside `a-z`, `0-9`, `_`, and `-` with `-`.
4. Removes leading and trailing hyphens.

The normalized value is stored in `st.session_state["user_id"]`. An empty result is rejected.

### Step 5: The application creates user-specific runtime identifiers

For an active user, `app.py` creates:

```text
USER_ID   = normalized username
THREAD_ID = user-{USER_ID}-main
```

For example:

```text
Username: Aman Khan
USER_ID:   aman-khan
THREAD_ID: user-aman-khan-main
```

The graph configuration is:

```python
{
    "configurable": {
        "thread_id": THREAD_ID,
    }
}
```

The trusted runtime context is:

```python
TodoContext(user_id=USER_ID)
```

The thread ID identifies conversation memory. The context user ID identifies task ownership. These are related by the application, but they serve different purposes.

### Step 6: Previous conversation messages are loaded

`get_conversation_messages()` calls `graph.get_state(config)`. If a checkpoint exists for the current thread, the saved `messages` list is read from the snapshot.

The Streamlit interface re-renders saved `HumanMessage` objects as user messages and saved `AIMessage` objects as assistant messages. This makes the conversation appear continuous after a page rerun or application restart, provided the same thread ID and checkpoint database are available.

### Step 7: The user submits natural language

The chat input accepts requests such as:

```text
Mark my Docker task as completed.
```

The message is immediately displayed in the UI and then sent to:

```python
graph.invoke(
    {"messages": [HumanMessage(content=user_input)]},
    config=config,
    context=context,
)
```

Three kinds of information are passed to the graph:

- **State update:** The new human message.
- **Config:** The conversation `thread_id` used by the checkpointer.
- **Runtime context:** The trusted `TodoContext` containing the active `user_id`.

## 7. LangGraph workflow

The graph is built in `graph/builder.py` using `StateGraph`.

```text
START
  │
  ▼
agent node
  │
  ▼
Does the latest model message contain tool calls?
  │
  ├── No ──► END
  │
  └── Yes
        │
        ▼
      ToolNode
        │
        ▼
      agent node
        │
        └── Repeat until the model produces a final response
```

### State

`graph/state.py` defines `AgentState` as a typed dictionary with one field:

```python
messages: Annotated[list[BaseMessage], add_messages]
```

The `add_messages` reducer appends new messages to the existing conversation state instead of replacing the complete message list. This enables the graph to preserve the full interaction history inside a thread.

### Context

`graph/context.py` defines an immutable dataclass:

```python
@dataclass(frozen=True)
class TodoContext:
    user_id: str
```

The context is supplied by the application, not generated by the model. Tool functions receive it through `ToolRuntime[TodoContext]`.

### Agent node

`graph/nodes.py` creates a `ChatGroq` instance after loading environment variables. The model configuration is:

```python
ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=groq_api_key,
)
```

The module fails early with a `ValueError` if `GROQ_API_KEY` is missing.

The five task tools are bound to the model with `llm.bind_tools(tools)`.

When `agent_node()` runs, it creates a message list containing:

1. A `SystemMessage` containing `SYSTEM_PROMPT`.
2. All messages currently in `state["messages"]`.

The model then decides whether to:

- Answer without a tool call.
- Call one task tool.
- Call a tool such as search first and then, after receiving its result, call another tool such as update or delete.

The node returns the model response as a new message.

### Conditional routing

`route_after_agent()` examines the latest message. If `last_message.tool_calls` is non-empty, it returns `"tools"`; otherwise it returns `"__end__"`.

This produces the cyclic behavior:

```text
agent → tools → agent → tools → ... → final agent response → END
```

### Tool execution

`ToolNode(tools)` is a LangGraph prebuilt node. It reads the tool calls produced by the model, invokes the corresponding Python functions, and appends tool results to the graph message state. The next agent iteration receives those results and can decide what to do next.

## 8. System prompt behavior

`prompts/system_prompt.py` defines the agent's operating rules. These rules are important because they constrain an otherwise general-purpose language model.

The prompt requires the model to:

- Use tools for every task create, read, update, delete, or search operation.
- Never claim success unless the relevant tool succeeded.
- Treat tool results and the database as the source of truth.
- Never invent task information.
- Extract a short title when creating a task.
- Only include a description when the user provided additional details.
- Preserve unspecified fields during updates by passing `null`.
- Search before updating or deleting when the user gives a title or topic rather than an ID.
- Update or delete automatically only when exactly one matching task is found.
- Ask for clarification when multiple tasks match.
- Explain accurately when no task matches.
- Format displayed tasks as a Markdown table with exactly `ID`, `Title`, `Description`, and `Status` columns.
- Use `—` when a description is missing.
- Avoid exposing internal tool names, tool-call IDs, and database queries.
- Stay focused on todo management for unrelated questions.

## 9. Tool-by-tool behavior

All tools use the `@tool` decorator, which exposes their signatures and descriptions to the model. All tools obtain the active user from `runtime.context.user_id`; the LLM does not provide the user ID as a model-generated argument.

### 9.1 Add task

File: `tools/add_task.py`

Model-visible inputs:

- `title: str`
- `description: Optional[str] = None`

Execution:

1. Reads `runtime.context.user_id`.
2. Calls `database.db.add_task(user_id, title, description)`.
3. Serializes the created task to JSON.
4. Returns the JSON string to the ToolNode and then to the agent.

The database creates a new task with the default status `pending`.

### 9.2 View tasks

File: `tools/view_tasks.py`

The tool has no user-supplied task arguments. It reads the active user from runtime context, calls `get_all_tasks(user_id)`, serializes the list to JSON, and returns it.

The SQL query filters by `user_id` and orders tasks by newest creation timestamp first, with task ID as a secondary descending order.

### 9.3 Search tasks

File: `tools/search_tasks.py`

Model-visible input:

- `query: str`

The database function searches the active user's `title` and `description` using SQL `LIKE` with a `%query%` pattern. Results are returned as JSON.

This tool is especially important for natural-language references such as `my Docker task`, because the model can search first to discover the real task ID.

### 9.4 Update task

File: `tools/update_task.py`

Model-visible inputs:

- `task_id: int`
- `title: Optional[str] = None`
- `description: Optional[str] = None`
- `status: Optional[str] = None`

The database function first confirms that the task belongs to the active user. It then uses the existing value for every field whose new value is `None`. It updates `updated_at` with `CURRENT_TIMESTAMP`, commits the change, reads the updated row, converts timestamps, and returns the task as JSON.

A request like `Mark task 4 as completed` normally results in a call with `task_id=4`, `status="completed"`, and null for the title and description.

### 9.5 Delete task

File: `tools/delete_task.py`

Model-visible input:

- `task_id: int`

The database function executes a delete restricted by both task ID and active user ID. The tool returns JSON containing the requested task ID and a Boolean `deleted` value. The system prompt specifically prevents the agent from claiming deletion unless that value is true.

## 10. Database layer

### Task database connection

`database/db.py` opens a new SQLite connection for each operation. Connections use `sqlite3.Row`, allowing rows to be converted into dictionaries. Each operation closes its connection in a `finally` block.

### User isolation

Every task query includes both:

```sql
WHERE id = ? AND user_id = ?
```

or:

```sql
WHERE user_id = ?
```

This applies to create follow-up reads, list, get-by-ID, update, delete, and search operations. As a result, a task ID alone is not enough to access another user's task through the normal database functions.

### Timestamp handling

SQLite stores timestamps using `CURRENT_TIMESTAMP`, which is UTC. The application parses the UTC value, converts it to `Asia/Kolkata` using `zoneinfo.ZoneInfo`, and returns a formatted timestamp ending in `IST`.

This conversion occurs in `serialize_task()`, so tools receive task dictionaries with user-facing local timestamps.

### Separate persistence responsibilities

There are two SQLite files:

```text
database/todo.db         Task records

database/checkpoints.db  LangGraph state and conversation checkpoints
```

This separation keeps the task data model independent from LangGraph's internal checkpoint schema.

## 11. Streamlit interface workflow

The Streamlit application provides:

- A centered `Todo Agent` heading.
- A username form before a user becomes active.
- A sidebar showing the normalized user ID and thread ID.
- A logout button that removes `user_id` from Streamlit session state and reruns the page.
- A chat history rendered from persisted graph state.
- A chat input placeholder encouraging add, view, search, update, and delete requests.
- A `Thinking...` spinner while the graph executes.
- Error messages if checkpoint history cannot be loaded or graph execution fails.

The interface itself does not directly call the database. It delegates requests to the compiled LangGraph graph.

## 12. CLI workflow

`cli.py` provides a simpler terminal entry point.

It currently uses fixed development identifiers:

```text
USER_ID:   aman
THREAD_ID: default-thread
```

The CLI:

1. Creates a graph configuration for `default-thread`.
2. Creates `TodoContext(user_id="aman")`.
3. Opens the persistent checkpointer with a context manager.
4. Builds the graph.
5. Reads lines from standard input.
6. Ignores blank input.
7. Exits on `exit` or `quit`.
8. Sends every other line to `graph.invoke()`.
9. Prints the final assistant message.

Unlike the Streamlit app, the CLI does not currently initialize the task schema itself. Running `python -m database.schema` first is the safe setup path for a fresh checkout.

## 13. Example multi-step request

Consider:

```text
Mark my Docker task as completed.
```

The complete reasoning/execution pattern is:

```text
1. Human message enters the graph.
2. Agent node adds the system prompt and sends the conversation to Groq.
3. The model recognizes that the task is referred to by topic, not ID.
4. The model calls search_tasks_tool with query="Docker".
5. ToolRuntime supplies the trusted active user ID.
6. SQLite searches only that user's title and description fields.
7. The search result is added to graph state.
8. The agent node runs again with the search result.
9. If exactly one task matches, the model calls update_task_tool with its real ID and status="completed".
10. SQLite verifies the task belongs to the active user and updates it.
11. The update result is added to graph state.
12. The agent node runs again.
13. The model produces a final confirmation based on the actual database result.
14. The graph reaches END.
15. The final assistant message is displayed and checkpointed.
```

If multiple Docker tasks match, the prompt instructs the model to ask the user which one to update. If none match, it must report that no task was found.

## 14. Persistence and memory model

There are two forms of persistence:

### Application data persistence

Tasks are stored in `database/todo.db`. They remain available across graph invocations and application restarts as long as the SQLite file is retained.

### Conversation persistence

LangGraph stores state snapshots in `database/checkpoints.db`, keyed by the configured thread ID. The same `user-{user_id}-main` thread lets the Streamlit application reload prior messages for that user.

The repository also includes inspection utilities:

- `tests/inspect_state.py` prints the current values, next nodes, configuration, and metadata for `default-thread`.
- `tests/inspect_history.py` prints every checkpoint, including step, source, next nodes, checkpoint ID, message count, and last message.
- `tests/test_threads.py` demonstrates that two different thread IDs can retain different conversational facts.

## 15. What the project demonstrates architecturally

This project is useful as a learning and portfolio example because it demonstrates several patterns used in production-oriented AI applications:

1. **Separation of concerns:** UI, graph orchestration, prompts, tools, and database code are in separate modules.
2. **Tool-mediated side effects:** The model requests operations, but Python tools perform them.
3. **Stateful workflows:** LangGraph manages a message state and routes execution conditionally.
4. **Cyclic agent behavior:** Tool results return to the model for additional decisions.
5. **Trusted context injection:** Identity is passed through runtime context rather than exposed as a model-controlled tool argument.
6. **Data/memory separation:** Task records and conversation checkpoints use separate persistence layers.
7. **Defensive prompting:** The system prompt specifies what the model may claim and how it should handle ambiguity.
8. **Deterministic inference configuration:** Temperature `0` is used for more predictable task operations.
9. **Testability through a CLI:** The graph can be exercised without the browser UI.
10. **Operational inspection:** Checkpoint state and history can be examined with dedicated scripts.

## 16. Real-world value

A system like this can help people manage personal tasks, study plans, engineering work, household responsibilities, or small-team action items with less friction than a traditional interface.

Possible real-world scenarios include:

- A student saying `Add a task to revise operating systems before Friday`.
- A developer asking `Show my tasks related to Docker`.
- A project coordinator saying `Mark the API documentation task as completed`.
- A support engineer asking `Find all tasks mentioning deployment`.
- A household user saying `Delete the grocery task`.

The same architecture can be extended beyond todos. The important general pattern is: natural-language intent is interpreted by an LLM, validated through tool schemas and instructions, executed by deterministic application code, and persisted in a stateful workflow.

## 17. Security and correctness boundaries

The runtime context design is a meaningful safety improvement. The model-visible schemas do not contain `user_id`, so the model cannot choose an arbitrary owner as part of a normal tool call. The tools always read the active user from `runtime.context.user_id`, and database queries include that value.

However, the current username screen is **not production authentication**. Anyone who knows another username could enter it. There are no passwords, sessions backed by an identity provider, OAuth, access tokens, roles, or server-side authorization middleware.

Other correctness boundaries:

- The model can produce verbose or malformed language even though the task operation is tool-backed.
- Delete operations do not include a confirmation step.
- Status values are not enforced by a database constraint; the model is instructed to use meaningful values such as pending and completed.
- SQLite is appropriate for a small local or single-instance application, but larger distributed deployments need a stronger shared database design.
- The CLI uses fixed user and thread IDs and is intended for development/testing.
- There is no automated unit/integration test runner; the scripts are manual inspection and demonstration utilities.

## 18. Setup and execution

### Requirements

- Python installed.
- A Groq API key.
- Network access to the Groq API when invoking the agent.

### Installation

```bash
git clone https://github.com/Amankhan1009/todo-agent.git
cd todo-agent
python -m venv venv
```

Activate the virtual environment:

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\\Scripts\\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` in the project root:

```text
GROQ_API_KEY=your_groq_api_key
```

Initialize the task database:

```bash
python -m database.schema
```

Run the web application:

```bash
streamlit run app.py
```

Run the terminal application:

```bash
python cli.py
```

Compile-check the Python files:

```bash
python -m compileall app.py cli.py database graph tools prompts tests
```

Run the thread demonstration:

```bash
python -m tests.test_threads
```

Inspect the current default-thread checkpoint:

```bash
python -m tests.inspect_state
```

Inspect checkpoint history:

```bash
python -m tests.inspect_history
```

## 19. Files intentionally excluded from Git

The `.gitignore` excludes:

```text
.env
venv/
__pycache__/
*.pyc
database/todo.db
database/checkpoints.db
.DS_Store
.streamlit/
```

This prevents API secrets, local environments, generated Python files, and local SQLite data from being committed.

## 20. Current limitations

The implementation is a strong demonstration project, but it is not yet a full production task-management platform. Current limitations are:

- Username selection is not real authentication.
- There is no password hashing, OAuth, or external identity provider.
- Each user has one primary conversation thread: `user-{user_id}-main`.
- There are no deadlines, reminders, priorities, tags, or categories.
- LLM responses are not streamed.
- There is no human confirmation step before deletion.
- There is no automated unit or integration test suite.
- SQLite may become unsuitable for a distributed multi-instance deployment.
- Status values are not constrained at the database layer.
- The CLI has hard-coded development identity values.
- The local filesystem is used for persistence, so deployment storage durability matters.

## 21. Recommended future improvements

The repository README identifies several natural next steps:

1. Add real authentication and authorization.
2. Use multiple conversations per user.
3. Add conversation creation and history management.
4. Require human confirmation before destructive actions.
5. Add deadlines, reminders, priorities, tags, and categories.
6. Return structured final responses and validate model output.
7. Add response-length safeguards.
8. Stream model responses.
9. Add automated unit and integration tests.
10. Add LangSmith tracing, observability, and evaluation.
11. Move task persistence to PostgreSQL for larger deployments.
12. Design a production deployment architecture.
13. Add database constraints and validation for allowed task statuses.
14. Add concurrency and migration handling for multi-user deployments.
15. Add authorization tests proving that one user cannot read, update, or delete another user's tasks.

## 22. How to explain the project in one minute

> Todo Agent is a conversational todo application built with Python, Streamlit, LangGraph, LangChain, Groq, and SQLite. A user types a natural-language request instead of filling out CRUD forms. LangGraph sends the conversation to a Groq language model with five task-management tools: add, view, search, update, and delete. The model selects the right tool, and if necessary it can perform multiple steps—for example, search for a task by title and then update it. The tools execute real user-scoped SQLite operations, so the model does not invent or directly modify data. LangGraph persists the conversation in a SQLite checkpoint database, while the active user ID is passed through trusted runtime context and kept out of the model-generated tool arguments. The project demonstrates how to build a stateful, tool-calling AI agent with persistent memory and a practical user interface.

## 23. Short technical explanation

```text
Streamlit or CLI
    │
    ├── user_id → TodoContext → ToolRuntime → user-scoped SQL
    ├── thread_id → LangGraph SQLite checkpointer → conversation memory
    └── user message → AgentState.messages
                              │
                              ▼
                       LangGraph agent node
                              │
                              ▼
                       Groq Chat model
                              │
             ┌────────────────┴────────────────┐
             │                                 │
       No tool call                       Tool call
             │                                 │
             ▼                                 ▼
            END                           ToolNode
                                               │
                                               ▼
                                        SQLite task operation
                                               │
                                               ▼
                                      Agent node again
```

The central design principle is that the LLM chooses actions, but deterministic Python tools and SQLite remain the source of truth for task data.
