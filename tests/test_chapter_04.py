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


def test_build_augmented_prompt_maps_vendor_name_to_mcp_vendor_id():
    prompt = audit_agent.build_augmented_prompt("Audit the account for Gujarat Steel Corp.")

    assert "Gujarat Steel Corp" in prompt
    assert "VEN-1000" in prompt
    assert "get_vendor_financials(\"VEN-1000\")" in prompt
    assert "Do not pass the vendor name to get_vendor_financials" in prompt
    assert "raw SQL" in prompt
