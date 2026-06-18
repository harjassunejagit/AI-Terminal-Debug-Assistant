# 🤖 AI Terminal Debug Assistant

> Paste an error. Get an instant explanation, root cause, and fix commands — powered by AI.Supports multiple AI providers including Gemini, OpenAI, Anthropic, and Ollama.

```
$ debugai run "python app.py"

ModuleNotFoundError: No module named 'dotenv'

📦 Error Type : ModuleNotFound
🌐 Language   : Python
⚠️  Severity   : Medium

📖 What happened
  Python couldn't find the 'dotenv' package because it isn't installed
  in your current environment.

🔍 Root Cause
  The script imports 'dotenv' (python-dotenv) but it was never installed.

🔧 Suggested Fixes
  ┌─ Fix 1 ──────────────────────────────────────┐
  │  pip install python-dotenv                    │
  │  Installs the missing python-dotenv library  │
  └──────────────────────────────────────────────┘

💡 Prevention
  Add python-dotenv to requirements.txt and run pip install -r requirements.txt
  when setting up new environments.
```

---

## ✨ Features

- **Multi-language** — Python, JS/TS, Java, Go, Rust, C/C++, Ruby, Bash, Docker, Git, SQL
- **Smart classification** — 17+ error types detected via regex + heuristics
- **AI-powered explanations** — OpenAI, Anthropic Claude, or local Ollama
- **Auto-fix** — safely runs `pip install`, `npm install`, etc.
- **Session history** — tracks all past debug sessions
- **REST API** — FastAPI backend for IDE integrations
- **Knowledge base** — ChromaDB for semantic retrieval of past fixes
- **Config file + environment variable support** 


---

## 🚀 Quick Start

Get DebugAI running in under 2 minutes.

---

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/harjassunejagit/AI-Terminal-Debug-Assistant.git

# Enter project
cd AI-Terminal-Debug-Assistant
```

Create virtual environment:

Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

Linux / Mac

```bash
python -m venv .venv

source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Or install editable package:

```bash
pip install -e .
```

---

### 2. Configure AI Provider

Initialize configuration:

```bash
python -m src.core.config
```

Example config:

```yaml
provider: gemini
model: gemini-2.5-flash

verbose: false
auto_fix: false
```

Set API key.

Gemini (Windows)

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

Gemini (Linux / Mac)

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

Verify:

```bash
echo $env:GEMINI_API_KEY
```

---

### 3. Start Debugging

Analyze an error directly:

```bash
python -m src.cli.main explain "NameError: name 'x' is not defined"
```

Example output:

```text
📖 What happened
Variable x was used before being created.

🔍 Root Cause
Undefined variable reference.

🔧 Suggested Fix
Initialize x before usage.
```

---

### 4. Run & Capture Errors Automatically

Run a script:

```bash
python -m src.cli.main run "python app.py"
```

Pipe terminal output:

```bash
python app.py 2>&1 | python -m src.cli.main run
```

Pass raw error:

```bash
python -m src.cli.main run \
--error "ModuleNotFoundError: No module named 'dotenv'"
```

Enable auto-fix:

```bash
python -m src.cli.main run \
"node index.js" \
--auto-fix
```

View previous sessions:

```bash
python -m src.cli.main history
```

---

## ⚙️ Configuration

Configuration file:

```text
~/.debugai/config.yaml
```

Example:

```yaml
provider: gemini
model: gemini-2.5-flash

gemini_api_key: YOUR_KEY

verbose: false
auto_fix: false

max_history: 50
theme: dark
```

Supported providers:

| Provider  | Example Model    |
| --------- | ---------------- |
| Gemini    | gemini-2.5-flash |
| OpenAI    | gpt-4o-mini      |
| Anthropic | claude-3-haiku   |
| Ollama    | llama3           |

---

### Using Ollama (Local AI)

Install Ollama:

```bash
https://ollama.com
```

Pull model:

```bash
ollama pull llama3
```

Run:

```bash
python -m src.cli.main explain \
"ImportError" \
--provider ollama \
--model llama3
```

---

### Using Anthropic

```bash
export ANTHROPIC_API_KEY="YOUR_KEY"

python -m src.cli.main explain \
"TypeError" \
--provider anthropic \
--model claude-3-haiku
```

---

## 🌐 REST API

Start API server:

```bash
python -m src.api.server
```

OR

```bash
uvicorn src.api.server:app --reload
```

Open Swagger:

```text
http://localhost:8000/docs
```

Analyze via API:

```bash
curl -X POST \
http://localhost:8000/analyze \
-H "Content-Type: application/json" \
-d '{
"error_text":
"ModuleNotFoundError: No module named dotenv"
}'
```

Example response:

```json
{
  "explanation": "...",
  "root_cause": "...",
  "fix_commands": [],
  "prevention": "..."
}
```

---

✅ Setup complete.

Start debugging directly from your terminal.


## 🗂️ Project Structure

```
ai-terminal-debug-assistant/
├── src/
│   ├── cli/
│   │   └── main.py          # Typer CLI entry point
│   ├── core/
│   │   ├── debugger.py      # Main debug session orchestrator
│   │   ├── config.py        # Config management
│   │   └── history.py       # Session history
│   ├── parsers/
│   │   └── error_parser.py  # Regex + heuristic error parser
│   ├── ai/
│   │   └── llm_client.py    # OpenAI / Ollama / Anthropic client
│   ├── retrieval/
│   │   └── knowledge_base.py # ChromaDB knowledge base
│   └── api/
│       └── server.py        # FastAPI REST server
├── tests/
│   ├── test_parser.py
│   └── test_api.py
├── .vscode/
│   ├── settings.json
│   └── launch.json
├── pyproject.toml
├── requirements.txt
└── README.md
```

---


## ⚠️ Troubleshooting

### Command not found

Run:

```bash
python -m src.cli.main
```

instead of:

```bash
debugai
```

---

### Missing API Key

Verify:

```bash
echo $env:GEMINI_API_KEY
```

---

### Gemini 503 Error

Try:

```yaml
model: gemini-2.5-flash
```

Retry after a few seconds.

---

## 🛣️ Roadmap

- [ ] VSCode Extension
- [ ] Auto Fix Mode
- [ ] Knowledge Retrieval
- [ ] Web Dashboard
- [ ] Offline Debug Mode
- [ ] Better Error Classification

---


## 🤝 Contributing

Contributions welcome! Ideas:

- [ ] Add more language parsers (PHP, Swift, Kotlin)
- [ ] VSCode extension
- [ ] Shell plugin (zsh/bash hook — auto-trigger on non-zero exit)
- [ ] StackOverflow / GitHub Issues retrieval
- [ ] Error database / offline mode
- [ ] Web dashboard

---

## 📄 License

MIT — see [LICENSE](LICENSE)
