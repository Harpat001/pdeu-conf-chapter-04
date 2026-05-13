from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from deepagents import create_deep_agent
from loguru import logger

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
DEFAULT_MODEL = "openrouter:inclusionai/ring-2.6-1t:free"

from erp_server import get_vendor_financials

SYSTEM_PROMPT = """
You are the Senior Financial Auditor for Shree Manufacturing Pvt. Ltd.
Use write_todos to plan the audit, read_file for legal contracts, check_delivery_log for warehouse receipts, and get_vendor_financials for ledger/payment data exposed by the ERP MCP service.
Do not write raw SQL or request direct database access.
""".strip()


def build_agent(model_name: str):
    return create_deep_agent(
        model=model_name,
        tools=[get_vendor_financials],
        system_prompt=SYSTEM_PROMPT,
    )


def run_self_check() -> str:
    return json.dumps(get_vendor_financials("VEN-1000"), indent=2)


def load_model_name() -> str:
    load_dotenv(ENV_PATH)
    return os.getenv("OPENROUTER_MODEL") or os.getenv("MODEL_NAME") or DEFAULT_MODEL


def invoke_agent(prompt: str) -> str:
    agent = build_agent(load_model_name())
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    messages = result.get("messages", [])
    if not messages:
        return ""
    final = messages[-1]
    return str(getattr(final, "content", final))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", default="What is your job?")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)

    if args.self_check:
        print(run_self_check())
        return 0

    print(invoke_agent(args.prompt))
    return 0
