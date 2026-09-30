# Codebase Understanding Agent 🔍

An autonomous agentic AI application designed to investigate unfamiliar software repositories, inspect code with exact line numbers, analyze dependencies, trace execution flows across files, and synthesize evidence-backed answers for developer queries.

---

## 🚀 Architecture & Core Principles

Unlike simple prompt-based chatbots, this system is an **agentic system**:
1. **Dynamic Tool Calling Loop**: Determines what information it needs, calls tools dynamically, evaluates tool outputs, and loops until sufficient evidence is collected.
2. **Strict Sandboxing**: All tools verify paths against the repository boundary to prevent unauthorized directory traversal (`../../`).
3. **Evidence-Backed**: Every finding is grounded in actual source files with 1-based line numbers.
4. **No Hallucination Rule**: If evidence is insufficient, it explicitly communicates what is missing rather than inventing code.

```
codebase-understanding-agent/
│
├── backend/
│   ├── main.py          # FastAPI application & REST endpoints
│   ├── agent.py         # Autonomous LLM investigation loop
│   ├── tools.py         # Core repository inspection tools
│   ├── analyzer.py      # Dependency parsers & sandboxing security
│   └── models.py        # Pydantic data schemas
│
├── frontend/
│   ├── index.html       # Clean Hackathon Demo UI
│   ├── style.css        # Modern dark-mode glassmorphic interface
│   └── app.js           # Client-side agent controller & playground
│
├── repositories/        # Folder holding repositories to inspect
│   ├── sample-auth-service/       # Node.js / Express / JWT example
│   └── sample-python-task-api/    # Python / FastAPI example
│
├── test_tools.py        # Standalone tool verification test suite
├── requirements.txt     # Minimal Python backend dependencies
├── .env                 # Local API keys (GEMINI_API_KEY)
└── README.md
```

---

## 🛠️ Repository Inspection Tools

The system provides 4 primary inspection tools in [`backend/tools.py`](file:///C:/Users/SHRAVANI/.gemini/antigravity-ide/scratch/codebase-understanding-agent/backend/tools.py):

| Tool | Purpose | Output Format |
|---|---|---|
| `list_files` | Recursively lists repository files while filtering out build/cache folders (`.git`, `node_modules`, `__pycache__`, `dist`, etc.) | File paths, sizes, and line counts |
| `search_code` | Case-insensitive regex or literal code search across all source text files | Exact matching file paths, line numbers, and trimmed code |
| `read_file` | Sandboxed file reader supporting line windows (`start_line`, `end_line`) | 1-based line-numbered code lines |
| `get_dependencies` | Multi-ecosystem manifest parser (`package.json`, `requirements.txt`, `pyproject.toml`, `pom.xml`, `go.mod`, `Cargo.toml`) | Structured dependency list with versions & ecosystems |
| `read_documentation` | Discovers architecture notes, `README.md`, and docs | Documentation files list & preview |

---

## 🧪 Testing Tools Independently

You can verify all tools without running an LLM or starting a server:

```bash
python test_tools.py
```

This test suite executes all 4 tools against the sample repositories and verifies:
- File tree discovery
- Keyword search and line-matching
- File reading with 1-based line numbers
- Multi-ecosystem dependency extraction
- Sandbox security (traversal prevention)

---

## ⚡ Quick Start & Running the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key (Optional)
Add your Google Gemini API key to `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: If no API key is provided, the agent runs in autonomous heuristic mode, allowing full UI demonstration immediately).*

### 3. Start Backend & UI Server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Open in Browser
Visit **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🖥️ Hackathon Demo Features

- **Repository Selector**: Switch between sample repositories or specify any custom local path.
- **Quick Question Pills**: Pre-loaded questions to demonstrate token generation, auth middleware, and registration flow.
- **Investigation Activity Timeline**: Real-time visibility into the agent's actions (e.g. *Searching code for 'jwt'*, *Reading authService.js*).
- **Evidence Cards**: Visual cards with clickable file references, line ranges, findings, and code snippets.
- **Execution Flow Diagram**: Step-by-step trace through routes, controllers, services, and models.
- **Interactive Tools Playground**: Dedicated modal to execute and test each tool individually on any repository.
