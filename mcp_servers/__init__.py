"""Servidores MCP y adaptadores locales del sistema financiero.

Los servidores MCP reales están en ``financial_data_server.py`` y
``collections_server.py``. ``mcp_client.py`` conserva adaptadores LangChain
locales para la interfaz Streamlit.
"""

from .mcp_client import (
    MCP_FINANCIAL_TOOLS,
    MCP_COLLECTIONS_TOOLS,
    ALL_MCP_TOOLS,
    mcp_get_cash_position,
    mcp_get_bank_debt,
    mcp_get_balance_sheet,
    mcp_calculate_liquidity,
    mcp_get_defaulters,
    mcp_get_customer_info,
    mcp_get_aging_report,
    mcp_get_utilization,
)

__all__ = [
    "MCP_FINANCIAL_TOOLS",
    "MCP_COLLECTIONS_TOOLS",
    "ALL_MCP_TOOLS",
    "mcp_get_cash_position",
    "mcp_get_bank_debt",
    "mcp_get_balance_sheet",
    "mcp_calculate_liquidity",
    "mcp_get_defaulters",
    "mcp_get_customer_info",
    "mcp_get_aging_report",
    "mcp_get_utilization",
]
