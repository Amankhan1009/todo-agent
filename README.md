# 📋 Todo Agent

A conversational AI-powered task management agent built with **LangGraph**, **LangChain**, **Groq**, **SQLite**, and **Streamlit**.

Todo Agent allows users to manage tasks using natural-language conversations. Instead of interacting with traditional forms or CRUD interfaces, users can ask the agent to add, view, search, update, complete, and delete tasks.

The application uses **LLM tool calling**, **LangGraph-based agent orchestration**, **persistent checkpoint memory**, **runtime context injection**, and **user-scoped database operations** to provide persistent conversations and isolated task management for multiple users.

---

## ✨ Features

* 💬 Natural-language task management through a conversational interface
* ➕ Add new tasks with optional descriptions
* 📋 View all tasks belonging to the current user
* 🔎 Search tasks by title or description
* ✏️ Update task titles, descriptions, and status
* ✅ Mark tasks as completed or reopen them
* 🗑️ Delete tasks using task IDs or natural-language references
* 🧠 Persistent conversation memory using LangGraph checkpointing
* 💾 SQLite-backed task and checkpoint persistence
* 🧵 Thread-based conversation isolation
* 👥 User-scoped task isolation
* 🔐 Runtime context injection keeps `user_id` hidden from the LLM tool schema
* 🔧 Multi-step tool execution for requests such as finding a task before updating or deleting it
* 🎨 Streamlit chat interface
* 🖥️ Terminal CLI interface for development and testing
* 🕒 Task timestamps displayed in Indian Standard Time (IST)

---

## 🧠 How It Works

A user sends a natural-language request such as:

> Mark my Docker task as completed.

The request flows through the application as follows:

```text
User
  │
  ▼
Streamlit Chat Interface
  │
  ▼
LangGraph StateGraph
  │
  ▼
Agent Node
  │
  ▼
Groq LLM
(openai/gpt-oss-120b)
  │
  ├──────────── No Tool Call ────────────► Final Response
  │
  ▼
Conditional Routing
  │
  ▼
ToolNode
  │
  ▼
Todo Tools
  │
  ├── Add Task
  ├── View Tasks
  ├── Search Tasks
  ├── Update Task
  └── Delete Task
  │
  ▼
User-Scoped SQLite Database
  │
  ▼
Tool Result
  │
  └──────────────────────────────► Agent Node
                                      │
                                      ▼
                                  Final Response
```

LangGraph persists conversation state through a SQLite-backed checkpointer.

```text
Conversation
     │
     ▼
Thread ID
     │
     ▼
LangGraph SQLite Checkpointer
     │
     ▼
Persistent Conversation State
```

Each application user receives a separate runtime context and conversation thread.

```text
User
 │
 ├── user_id
 │      │
 │      ▼
 │   TodoContext
 │      │
 │      ▼
 │   ToolRuntime
 │      │
 │      ▼
 │   User-Scoped Database Operations
 │
 └── thread_id
        │
        ▼
   LangGraph Checkpointer
        │
        ▼
   Persistent Conversation History
```

This separates **task ownership** from **conversation memory**.

---

## 🛠️ Tech Stack

| Technology                    | Purpose                                                         |
| ----------------------------- | --------------------------------------------------------------- |
| Python                        | Core application language                                       |
| LangGraph                     | Agent workflow orchestration and checkpointing                  |
| LangChain                     | Tool definitions, message abstractions, and runtime integration |
| Groq                          | LLM inference API                                               |
| openai/gpt-oss-120b           | Language model used by the agent                                |
| SQLite                        | Persistent task storage                                         |
| LangGraph SQLite Checkpointer | Persistent conversation state                                   |
| Streamlit                     | Web-based conversational UI                                     |
| python-dotenv                 | Environment variable management                                 |

---

## 📂 Project Structure

```text
Todo-Agent/
│
├── app.py
├── cli.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
│
├── database/
│   ├── schema.py
│   ├── db.py
│   └── checkpointer.py
│
├── graph/
│   ├── __init__.py
│   ├── builder.py
│   ├── context.py
│   ├── nodes.py
│   ├── routing.py
│   └── state.py
│
├── tools/
│   ├── __init__.py
│   ├── add_task.py
│   ├── view_tasks.py
│   ├── search_tasks.py
│   ├── update_task.py
│   └── delete_task.py
│
├── prompts/
│   └── system_prompt.py
│
└── tests/
    ├── __init__.py
    ├── inspect_state.py
    ├── inspect_history.py
    └── test_threads.py
```

### Directory Responsibilities

**`database/`**

Handles SQLite task persistence and the persistent LangGraph SQLite checkpointer.

**`graph/`**

Contains the LangGraph state definition, runtime context, agent node, routing logic, and graph construction.

**`tools/`**

Contains the tools available to the LLM for performing task CRUD operations.

**`prompts/`**

Contains the system instructions that define the behavior of the Todo Agent.

**`tests/`**

Contains development utilities for inspecting checkpoint state, checkpoint history, and thread isolation.

---

## 🤖 Agent Workflow

The agent uses a cyclic LangGraph workflow:

```text
START
  │
  ▼
AGENT
  │
  ▼
Does the LLM request a tool?
  │
  ├── NO ─────────────► END
  │
  └── YES
        │
        ▼
      TOOLS
        │
        ▼
      AGENT
        │
        └── Repeat until no tool call remains
```

The agent can perform multi-step operations automatically.

For example:

```text
User:
"Mark my Docker task as completed."

Agent:
Search Docker task
      │
      ▼
Receive matching task ID
      │
      ▼
Update task status
      │
      ▼
Generate final response
```

---

## 🔧 Available Tools

### `add_task_tool`

Creates a new task for the active user.

Example:

```text
Add a task to learn Docker.
```

### `view_tasks_tool`

Returns all tasks belonging to the active user.

Example:

```text
Show me all my tasks.
```

### `search_tasks_tool`

Searches the active user's tasks by title or description.

Example:

```text
Find my Kubernetes task.
```

### `update_task_tool`

Updates an existing task belonging to the active user.

Example:

```text
Mark my Docker task as completed.
```

### `delete_task_tool`

Deletes an existing task belonging to the active user.

Example:

```text
Delete my Terraform task.
```

---

## 🧠 Persistent Conversation Memory

Todo Agent uses a SQLite-backed LangGraph checkpointer.

Conversation state is persisted inside:

```text
database/checkpoints.db
```

Every conversation uses a `thread_id`.

Example:

```text
user-aman-main
user-rahul-main
```

When the application restarts, LangGraph loads the stored checkpoint associated with the same thread ID.

This allows conversations to continue across application restarts.

---

## 👥 User Isolation

Tasks are stored with a `user_id`.

Example:

```text
id | user_id | title            | status
---|---------|------------------|----------
1  | aman    | Learn Docker     | completed
2  | rahul   | Learn Kubernetes | pending
```

Every database query includes the active `user_id`.

For example:

```text
get_all_tasks(user_id)

get_task_by_id(user_id, task_id)

search_tasks(user_id, query)

update_task(user_id, task_id)

delete_task(user_id, task_id)
```

Therefore, one user cannot access another user's tasks through normal application operations.

> **Important:** The current username screen provides application-level user isolation, not production authentication. Anyone who knows another username could enter it. Password authentication, OAuth, or an external identity provider would be required for production use.

---

## 🔐 Runtime Context Injection

The application passes the active user's identity through LangGraph runtime context.

```text
TodoContext
    │
    ▼
ToolRuntime
    │
    ▼
runtime.context.user_id
    │
    ▼
Database Operation
```

The `user_id` is not exposed as a parameter that the LLM can generate.

For example, the model-visible schema of the add-task tool contains only:

```text
title
description
```

Internally, the tool retrieves the user identity from trusted runtime context:

```text
runtime.context.user_id
```

This prevents the LLM from choosing arbitrary user IDs when calling task-management tools.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Amankhan1009/todo-agent.git
cd Todo-Agent
```

### 2. Create a Virtual Environment 

```bash
python -m venv venv
```

Activate it on macOS/Linux:

```bash
source venv/bin/activate
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key
```

Do not commit the `.env` file to GitHub.

### 5. Initialize the Task Database

```bash
python -m database.schema
```

### 6. Run the Streamlit Application

```bash
streamlit run app.py
```

Open the local Streamlit URL displayed in your terminal.

### 7. Run the CLI Application

```bash
python cli.py
```

---

## 🧪 Testing and Inspection

Compile the project:

```bash
python -m compileall app.py cli.py database graph tools prompts tests
```

Test conversation thread isolation:

```bash
python -m tests.test_threads
```

Inspect the current checkpoint state:

```bash
python -m tests.inspect_state
```

Inspect checkpoint history:

```bash
python -m tests.inspect_history
```

---

## 💬 Example Conversation

```text
User:
Add a task to learn Docker.

Assistant:
Task added successfully: Learn Docker.

User:
Add a task to learn LangGraph.

Assistant:
Task added successfully: Learn LangGraph.

User:
Show me all my tasks.

Assistant:
1. Learn LangGraph — pending
2. Learn Docker — pending

User:
Mark my Docker task as completed.

Assistant:
Your Docker task has been marked as completed.

User:
Delete my LangGraph task.

Assistant:
Your LangGraph task has been deleted successfully.
```

---

## 🗄️ Database Design

The application uses two SQLite databases.

### Task Database

```text
database/todo.db
```

Stores user-owned tasks.

The `tasks` table contains:

```text
id
user_id
title
description
status
created_at
updated_at
```

An index on `user_id` improves user-scoped task queries.

### Checkpoint Database

```text
database/checkpoints.db
```

Stores LangGraph conversation checkpoints and intermediate writes.

The checkpointer automatically creates and manages its required tables.

---

## 🔒 Environment and Git Safety

The following files and directories should not be committed:

```gitignore
.env
venv/
__pycache__/
*.pyc
database/todo.db
database/checkpoints.db
.DS_Store
.streamlit/
```

Before pushing the repository, verify tracked files:

```bash
git status
```

You can also verify that `.env` is ignored:

```bash
git check-ignore .env
```

---

## ⚠️ Current Limitations

* Username-based access is not production authentication
* No password hashing, OAuth, or external identity provider
* One primary conversation thread is used per user
* No task deadlines or reminders
* No priority or category system
* No streaming LLM responses
* No automated unit or integration test suite yet
* SQLite is suitable for this project but would need reconsideration for larger distributed deployments
* LLM responses can occasionally be verbose or malformed depending on model behavior

---

## 🔮 Future Improvements

Potential improvements include:

* Real authentication and authorization
* Multiple conversations per user
* New conversation and conversation history management
* Human-in-the-loop confirmation for destructive actions
* Task deadlines and reminders
* Task priorities, tags, and categories
* Structured final responses
* LLM response-length safeguards
* Streaming responses
* Automated unit and integration testing
* LangSmith tracing, observability, and evaluation
* PostgreSQL-backed task persistence
* Production deployment architecture

---

## 🎯 Key Learning Outcomes

This project demonstrates practical understanding of:

* Building tool-calling AI agents
* Designing cyclic agent workflows with LangGraph
* Creating nodes, edges, and conditional routing
* Executing tools through LangGraph `ToolNode`
* Maintaining conversational state
* Persisting state with checkpoint savers
* Separating conversation memory from application data
* Injecting trusted user identity through runtime context
* Designing user-scoped database operations
* Building multi-step agent behavior
* Integrating an agent backend with a Streamlit UI
* Structuring an Agentic AI project into modular components

---

## 👨‍💻 Author

**Md Aman Alam**

Information Technology undergraduate interested in **Machine Learning, Generative AI, Agentic AI, MLOps, DevOps, DevSecOps, Cloud, and Platform Engineering**.

---

## ⭐ Support

If you found this project useful, consider giving the repository a ⭐.

Contributions, suggestions, and feedback are welcome.
