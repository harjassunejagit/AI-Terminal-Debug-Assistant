# 🤖 AI Terminal Debug Assistant

> Paste an error. Get an instant explanation, root cause, and fix commands — powered by AI.

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

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repo
git clone https://github.com/yourusername/ai-terminal-debug-assistant
cd ai-terminal-debug-assistant

# Install (with OpenAI support)
pip install -e ".[openai]"

# Or install all extras
pip install -e ".[all]"
```

### 2. Configure

```bash
debugai config-init
```

Or set environment variables:

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Use it

```bash
# Run a command and debug any errors
debugai run "python app.py"

# Pipe errors directly
python app.py 2>&1 | debugai run

# Paste an error message
debugai explain "NameError: name 'x' is not defined"

# Paste via flag
debugai run --error "ModuleNotFoundError: No module named 'dotenv'"

# Auto-apply safe fixes (pip install, npm install, etc.)
debugai run "node index.js" --auto-fix

# View session history
debugai history
```

---

## ⚙️ Configuration

Config file lives at `~/.debugai/config.yaml`:

```yaml
provider: openai           # openai | ollama | anthropic
model: gpt-4o-mini
openai_api_key: sk-...     # or use OPENAI_API_KEY env var
verbose: false
auto_fix: false
```

### Using Ollama (local models, free)

```bash
# Install Ollama: https://ollama.com
ollama pull llama3

debugai run "python app.py" --provider ollama --model llama3
```

### Using Anthropic Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
debugai run "python app.py" --provider anthropic --model claude-3-haiku-20240307
```

---

## 🌐 API Server

```bash
# Start the REST API
python -m src.api.server

# Or
uvicorn src.api.server:app --reload
```

Swagger docs at: http://localhost:8000/docs

```bash
# Example API call
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"error_text": "ModuleNotFoundError: No module named dotenv"}'
```

---

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

## 🧪 Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

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
