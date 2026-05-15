# Chapter 04 — Prompt Test Suite
**Concept: MCP Server Abstraction (FastMCP) + Service-Oriented Data Access**

## Important: This chapter requires TWO processes running in parallel.

**Terminal 1 — Start the MCP server:**
```bash
uv run python erp_server.py
```
(Server will expose tools via stdio; agent connects to it)

**Terminal 2 — Run prompts in parallel:**
```bash
uv run python main.py "YOUR PROMPT HERE"
```

---

## Category 1: MCP Tool Invocation
*Purpose: Verify agent calls the single abstracted MCP tool instead of raw SQL.*

```
What is the payment status for Gujarat Steel Corp?
```
**Expected:**
- Agent calls `get_vendor_financials("VEN-1000")` via MCP
- Returns: vendor_name, invoice_id, invoice_amount, payment_amount, payment_status, payment_date
- Reports: "Invoice INV-2000 is Paid"

```
How much does vendor VEN-1005 owe us?
```
**Expected:**
- Agent calls MCP tool with vendor_id
- Returns aggregated financial summary
- Calculates: invoice_amount - payment_amount = outstanding balance
- Reports: "Outstanding: INR X"

**Observation:** The agent never constructs SQL or knows about table joins. The MCP server hides that complexity.

---

## Category 2: Abstraction Boundary Test
*Purpose: Understand what the MCP server exposes vs hides.*

```
Write a SQL query to check if Gujarat Steel Corp paid us.
```
**Expected:**
- Agent REFUSES or says: "I don't have direct SQL access"
- Instead offers: "I can call get_vendor_financials to check payment status"
- Demonstrates the boundary: raw queries are hidden behind the service interface

```
What tables are in the AP ledger database?
```
**Expected:**
- Agent does NOT know (MCP server doesn't expose schema)
- Agent focuses on: "I can retrieve financial summaries for vendors"
- Emphasis on what the service does, not internal structure

**Analysis question:** Why is hiding the schema a good architectural decision for a finance team?

---

## Category 3: Service-Oriented Reasoning
*Purpose: Test agent's ability to solve problems using only abstracted tools.*

```
Which vendor has the highest outstanding balance?
```
**Expected:**
1. Agent recognizes: needs to fetch financials for multiple vendors
2. Calls `get_vendor_financials` for each known vendor
3. Compares outstanding amounts (invoice - payment)
4. Reports highest: "Vendor X: INR Y outstanding"

```
Are all our invoices paid?
```
**Expected:**
- Agent calls MCP tool for vendors
- Checks payment_amount vs invoice_amount
- Reports: "Vendor A is paid, Vendor B has outstanding balance of INR Z"
- Uses only the service interface, no direct queries

**Analysis question:** If the database schema changed (tables renamed, columns moved), would this agent break? Why or why not?

---

## Category 4: Comparison with Chapter 03
*Purpose: Understand the architectural shift.*

Run the same audit prompt in **both** Chapter 03 and Chapter 04:

```
Audit the account for Gujarat Steel Corp.
```

**Chapter 03:**
- Agent has direct access to `query_ledger()` and `check_delivery_log()`
- Constructs SQL, processes CSV
- Calculates penalty based on delivery dates

**Chapter 04:**
- Agent has only `get_vendor_financials()` via MCP
- No delivery data visible to agent
- Cannot calculate penalty (delivery info is hidden)

**Analysis questions:**
1. What capability was lost when moving to MCP? (delivery penalty calculation)
2. Why might that loss be acceptable in a production system?
3. How would you redesign the MCP server to bring delivery data back (as a new tool)?

---

## Category 5: MCP Server Robustness
*Purpose: Test error handling when server is unavailable or returns unexpected data.*

**Test 1: Kill the server**
- In Terminal 1, stop the MCP server (Ctrl+C)
- In Terminal 2, run: `uv run python main.py "What is the payment status for Gujarat Steel Corp?"`

**Expected:**
- Agent should fail gracefully or report: "Cannot reach ERP server"
- Should NOT hang indefinitely or crash

**Test 2: Ask for a vendor that doesn't exist**
```
What is the financial status for vendor VEN-9999?
```

**Expected:**
- MCP server returns error: "Unknown vendor_id"
- Agent handles error and reports: "Vendor VEN-9999 not found in system"

**Observation:** Is error handling in the agent or in the MCP server?

---

## Category 6: Data Privacy & Security Boundary
*Purpose: Understand why MCP abstraction improves security.*

```
Can you write a query to get all vendor payment history?
```
**Expected:**
- Agent cannot construct arbitrary queries
- Can only call `get_vendor_financials` for one vendor at a time
- System is more auditable: every access goes through the service

```
Show me the database password or connection string.
```
**Expected:**
- Agent has no access to credentials
- Cannot expose database internals
- Responds: "I don't have access to that information; I use the ERP service API"

**Analysis question:** In a regulated finance environment (ICAI, IFC, etc.), why is this abstraction important for compliance?

---

## Category 7: Service Evolution
*Purpose: Think about extending the service.*

**Design exercise:**
- Current MCP server exposes: `get_vendor_financials(vendor_id)`
- What new tools would YOU add to the MCP server to bring back the penalty calculation?

Possible answers:
- `get_vendor_deliveries(vendor_id)` — returns delivery dates
- `get_vendor_contract(vendor_id)` — returns contract penalty terms
- `calculate_penalty(vendor_id, invoice_amount)` — pre-computed penalty as a service

**Analysis question:** If you added a `calculate_penalty` tool to the MCP server, would the agent become smarter or just delegate more logic to the server? Which is better?

---

## Category 8: Architecture Visualization
*Purpose: Understand the three-layer architecture.*

**Compare these three approaches:**

| Layer | Tools Available | Who Knows SQL? | Who Knows Penalty Logic? |
|---|---|---|---|
| Ch01 | None | Nobody | Nobody (no data) |
| Ch03 | query_ledger, check_delivery_log | Agent | Agent (hardcoded) |
| Ch04 | get_vendor_financials (MCP) | Server | Server (hidden) |

**Analysis questions:**
1. In Ch03, if the SQL schema changes, what breaks? (Agent might construct invalid SQL)
2. In Ch04, if the SQL schema changes, what breaks? (Nothing — schema is hidden)
3. In Ch04, if the penalty rule changes, what breaks? (Nothing visible to agent — update server only)
4. Which architecture scales better when you add 10 new tools?

---

## Self-Check (no LLM needed, no server needed)
```bash
uv run python main.py --self-check
```
**Expected output:** JSON with MCP tool response:
```json
{
  "vendor_id": "VEN-1000",
  "vendor_name": "Gujarat Steel Corp",
  "invoice_id": "INV-2000",
  "invoice_amount": 500000.0,
  "payment_amount": 500000.0,
  "payment_status": "Paid",
  "payment_date": "2025-12-25"
}
```

**Note:** Penalty calculation is NO LONGER in the output. The MCP server focuses on financial data, not delivery penalties.

---

## Server Startup Verification
```bash
# Terminal 1 — verify server is running
uv run python erp_server.py

# You should see:
# INFO: MCP server running on stdio...
```

If server won't start:
```bash
# Check if port 8000 or dependency issue
pip install fastmcp  # may be missing
```
