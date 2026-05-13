import audit_agent
import erp_server


def test_agent_uses_mcp_tool_instead_of_local_query_tool(monkeypatch):
    calls = {}

    def fake_create_deep_agent(**kwargs):
        calls.update(kwargs)
        return "agent"

    monkeypatch.setattr(audit_agent, "create_deep_agent", fake_create_deep_agent)
    audit_agent.build_agent("test-model")

    assert "query_ledger" not in audit_agent.SYSTEM_PROMPT
    assert "get_vendor_financials" in audit_agent.SYSTEM_PROMPT
    assert calls["tools"] == [audit_agent.get_vendor_financials]


def test_mcp_tool_returns_summarized_vendor_financials():
    data = erp_server.get_vendor_financials("VEN-1000")
    assert data["vendor_name"] == "Gujarat Steel Corp"
    assert data["invoice_amount"] == 500000.0
    assert data["payment_status"] == "Paid"
