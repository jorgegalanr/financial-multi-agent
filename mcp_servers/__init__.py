"""
Módulo MCP Servers para el sistema financiero.
Incluye 3 servidores MCP:
- financial_data_server: Datos financieros (caja, deuda, balance)
- collections_server: Gestión de cobros (facturas, morosos, estudiantes)
- market_data_server: Datos de mercado (tipos interés, impuestos, indicadores)
"""

from .mcp_client import (
    MCP_FINANCIAL_TOOLS,
    MCP_COLLECTIONS_TOOLS,
    MCP_MARKET_TOOLS,
    ALL_MCP_TOOLS,
    mcp_get_cash_position,
    mcp_get_bank_debt,
    mcp_get_balance_sheet,
    mcp_calculate_liquidity,
    mcp_get_defaulters,
    mcp_get_student_info,
    mcp_get_aging_report,
    mcp_get_occupancy,
    mcp_get_interest_rates,
    mcp_get_tax_rates,
    mcp_get_economic_indicators
)

__all__ = [
    "MCP_FINANCIAL_TOOLS",
    "MCP_COLLECTIONS_TOOLS",
    "MCP_MARKET_TOOLS",
    "ALL_MCP_TOOLS",
    "mcp_get_cash_position",
    "mcp_get_bank_debt",
    "mcp_get_balance_sheet",
    "mcp_calculate_liquidity",
    "mcp_get_defaulters",
    "mcp_get_student_info",
    "mcp_get_aging_report",
    "mcp_get_occupancy",
    "mcp_get_interest_rates",
    "mcp_get_tax_rates",
    "mcp_get_economic_indicators"
]
