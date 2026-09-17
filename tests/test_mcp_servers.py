import asyncio

from mcp_servers.collections_server import call_tool as collections_call
from mcp_servers.financial_data_server import call_tool as financial_call


def test_financial_mcp_server_returns_cash_position():
    result = asyncio.run(financial_call("get_cash_position", {}))
    assert result
    assert "saldo_total" in result[0].text


def test_collections_mcp_server_returns_customer():
    result = asyncio.run(
        collections_call("get_customer_info", {"customer_id": "CLI-0001"})
    )
    assert result
    assert "CLI-0001" in result[0].text
