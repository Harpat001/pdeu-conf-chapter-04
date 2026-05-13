# Chapter 4: Deep Agent + MCP Tools

Moves ledger access behind an ERP MCP service.

## Setup

```bash
uv sync
cp .env.example .env
```

Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in `.env`.

## Run

```bash
uv run python main.py --self-check
uv run python main.py "Audit the account for Gujarat Steel Corp."
uv run pytest
```

Run the MCP server separately when demonstrating the service boundary:

```bash
uv run python erp_server.py
```
