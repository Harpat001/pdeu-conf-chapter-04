from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from deepagents import create_deep_agent
from loguru import logger

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
DEFAULT_MODEL = "openrouter:inclusionai/ring-2.6-1t:free"
DB_PATH = ROOT / "ap_ledger.db"

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


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _vendor_id_by_name() -> dict[str, str]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("select Vendor_Name, Vendor_ID from Vendors").fetchall()
    return {row["Vendor_Name"]: row["Vendor_ID"] for row in rows}


def _find_vendor_in_prompt(prompt: str) -> tuple[str, str] | None:
    normalized_prompt = _normalize(prompt)
    vendors = sorted(_vendor_id_by_name().items(), key=lambda item: len(item[0]), reverse=True)
    for vendor_name, vendor_id in vendors:
        if _normalize(vendor_name) in normalized_prompt:
            return vendor_name, vendor_id
    return None


def build_augmented_prompt(prompt: str) -> str:
    match = _find_vendor_in_prompt(prompt)
    if match is None:
        return prompt

    vendor_name, vendor_id = match
    return (
        f"{prompt}\n\n"
        "LOCAL MCP REFERENCE DATA\n"
        f"Vendor: {vendor_name}\n"
        f"Vendor ID: {vendor_id}\n"
        f"Tool Guidance: call get_vendor_financials(\"{vendor_id}\") for this vendor. "
        "Do not pass the vendor name to get_vendor_financials; it expects a vendor_id. "
        "Do not write raw SQL or request direct database access.\n"
    )


def load_model_name() -> str:
    load_dotenv(ENV_PATH)
    return os.getenv("OPENROUTER_MODEL") or os.getenv("MODEL_NAME") or DEFAULT_MODEL


def invoke_agent(prompt: str) -> str:
    agent = build_agent(load_model_name())
    result = agent.invoke({"messages": [{"role": "user", "content": build_augmented_prompt(prompt)}]})
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
