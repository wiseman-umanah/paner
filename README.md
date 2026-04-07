# Paner

Paner is a terminal-based PDF analysis assistant. It ingests one or more PDFs, embeds their contents into an in-memory Chroma vector store, and answers follow-up questions with Groq’s `openai/gpt-oss-120b` model. When local documents can’t answer a question, Paner can optionally search the web and fold those snippets back into the same prompt flow.

## Features

- **Fast ingestion:** Drag-and-drop or paste a PDF path to index it. All chunking and embedding happens locally with `SentenceTransformer("all-MiniLM-L6-v2")`.
- **Multi-document focus:** Load as many PDFs as you need, list them with `list`, and scope queries with `use <id|name|all>`.
- **Rich answers:** Responses preserve Markdown formatting and cite the source file/page in each chunk.
- **Smart fallbacks:** If a question can’t be answered from your docs, Paner offers to run a DuckDuckGo search and summarizes the best hits.
- **Secure API handling:** Groq API keys are validated and stored in your platform-specific config directory.

## Requirements

- Python 3.11+
- Groq API key (starts with `gsk_…`)
- Internet access for Groq, initial model downloads, and optional web search

## Installation

Paner is published as a standard Python package, so you can install it via `pip`/`pipx`/`uv` once the wheel/sdist is available:

```bash
pip install paner
```

For local development clone the repo and install in editable mode:

```bash
git clone https://github.com/wiseman-umanah/paner.git
cd paner
pip install -e .
```

## Getting Started

1. Run the CLI:
   ```bash
   paner
   ```
2. On first launch Paner prompts for your Groq API key. It validates the key and stores it under `platformdirs.user_config_dir("paner", "wiseman-umanah")`.
3. When you see `paner>>>`, paste a PDF path (drag-and-drop works in most terminals). Paner will parse and index the document.
4. Ask questions in natural language. Answers reference the matched PDF chunks and respect the currently active document.

### Session Commands

| Command | Description |
|---------|-------------|
| `list`  | Show every PDF loaded this session with an index, path, and active status. |
| `use <n>` | Focus questions on document `n` from the `list` output. |
| `use <name>` | Focus by file name (case-insensitive). |
| `use all` | Query across every ingested PDF. |
| `quit` / `exit` | Leave the CLI. |

The prompt automatically updates to `paner[filename]>>>` when a specific document is active.

### Web Search Fallback

If a question can’t be answered locally Paner displays a Rich confirmation prompt:

```
I couldn't find this in your documents. Search the web? (y/N)
```

- Accept (`y`) to run a DuckDuckGo query and summarize the top results.
- Decline (`n`) to keep the conversation offline.

Make sure the `duckduckgo-search` dependency is installed (it ships with Paner) and that your environment permits outbound requests.

## Development

Useful tasks while hacking on Paner:

- Lint / format: configure `ruff` or `black` as desired.
- Run the CLI against sample PDFs to exercise chunking, vector search, and the Groq integration.
- Update `pyproject.toml` whenever dependencies or metadata change.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution workflow and pull-request expectations.

## License

MIT License. See the `LICENSE` section in `pyproject.toml` for details. Feel free to adapt Paner for your own workflows.
