from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "ap_ledger.db"
mcp = FastMCP("shree-erp")


@mcp.tool
def get_vendor_financials(vendor_id: str) -> dict[str, Any]:
    """Return summarized accounts payable information for one vendor."""
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            """
            select v.Vendor_ID, v.Vendor_Name, i.Invoice_ID, i.Amount as Invoice_Amount,
                   i.Status, p.Amount as Payment_Amount, p.Payment_Date
            from Vendors v
            join Invoices i on i.Vendor_ID = v.Vendor_ID
            left join Payments p on p.Invoice_ID = i.Invoice_ID
            where v.Vendor_ID = ?
            """,
            (vendor_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Unknown vendor_id: {vendor_id}")
    return {
        "vendor_id": row["Vendor_ID"],
        "vendor_name": row["Vendor_Name"],
        "invoice_id": row["Invoice_ID"],
        "invoice_amount": float(row["Invoice_Amount"]),
        "payment_amount": float(row["Payment_Amount"]),
        "payment_status": row["Status"],
        "payment_date": row["Payment_Date"],
    }


if __name__ == "__main__":
    mcp.run()
