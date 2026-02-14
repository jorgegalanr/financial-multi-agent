"""
MCP Server 1: Servidor de Datos Financieros
Proporciona acceso a datos financieros de la empresa mediante el protocolo MCP.
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Crear servidor MCP
server = Server("financial-data-server")


def load_csv(filename: str) -> pd.DataFrame:
    """Carga un archivo CSV."""
    return pd.read_csv(os.path.join(DATA_PATH, filename))


# ============================================
# DEFINICIÓN DE TOOLS MCP
# ============================================

@server.list_tools()
async def list_tools() -> List[Tool]:
    """Lista las herramientas disponibles en el servidor MCP."""
    return [
        Tool(
            name="get_cash_position",
            description="Obtiene la posición de caja actual con saldos por banco",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_pending_payments",
            description="Lista los pagos pendientes de realizar",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Días hacia adelante para buscar (default: 30)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_bank_debt",
            description="Obtiene el detalle de la deuda bancaria",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_balance_sheet",
            description="Obtiene el balance de situación",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_income_statement",
            description="Obtiene la cuenta de resultados",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="calculate_liquidity_ratio",
            description="Calcula el ratio de liquidez y meses de cobertura",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Ejecuta una herramienta del servidor MCP."""
    
    try:
        if name == "get_cash_position":
            df = load_csv("posicion_caja.csv")
            total = df["saldo"].sum()
            result = {
                "fecha": datetime.now().isoformat(),
                "saldo_total": total,
                "cuentas": df.to_dict(orient="records")
            }
            
        elif name == "get_pending_payments":
            days = arguments.get("days", 30)
            df = load_csv("pagos_pendientes.csv")
            df["fecha_vencimiento"] = pd.to_datetime(df["fecha_vencimiento"])
            from datetime import timedelta
            limite = datetime.now() + timedelta(days=days)
            df = df[df["fecha_vencimiento"] <= limite]
            result = {
                "dias": days,
                "total": df["importe"].sum(),
                "num_pagos": len(df),
                "pagos": df.to_dict(orient="records")
            }
            
        elif name == "get_bank_debt":
            df = load_csv("deuda_bancaria.csv")
            result = {
                "deuda_total": df["capital_pendiente"].sum(),
                "cuota_mensual_total": df["cuota_mensual"].sum(),
                "prestamos": df.to_dict(orient="records")
            }
            
        elif name == "get_balance_sheet":
            df = load_csv("balance.csv")
            activo = df[df["tipo"] == "activo"]["importe"].sum()
            pasivo = df[df["tipo"] == "pasivo"]["importe"].sum()
            patrimonio = df[df["tipo"] == "patrimonio"]["importe"].sum()
            result = {
                "fecha": datetime.now().isoformat(),
                "activo_total": activo,
                "pasivo_total": pasivo,
                "patrimonio_neto": patrimonio,
                "detalle": df.to_dict(orient="records")
            }
            
        elif name == "get_income_statement":
            df = load_csv("cuenta_resultados.csv")
            ingresos = df[df["tipo"] == "ingreso"]["importe"].sum()
            gastos = df[df["tipo"] == "gasto"]["importe"].sum()
            result = {
                "ingresos_totales": ingresos,
                "gastos_totales": gastos,
                "resultado_neto": ingresos - gastos,
                "margen_porcentaje": ((ingresos - gastos) / ingresos * 100) if ingresos > 0 else 0,
                "detalle": df.to_dict(orient="records")
            }
            
        elif name == "calculate_liquidity_ratio":
            caja = load_csv("posicion_caja.csv")
            gastos = load_csv("gastos_fijos.csv")
            saldo = caja["saldo"].sum()
            gastos_mensuales = gastos["importe_mensual"].sum()
            meses = saldo / gastos_mensuales if gastos_mensuales > 0 else 0
            result = {
                "saldo_disponible": saldo,
                "gastos_mensuales": gastos_mensuales,
                "meses_cobertura": round(meses, 2),
                "estado": "OPTIMO" if meses >= 4 else "ACEPTABLE" if meses >= 2 else "CRITICO"
            }
            
        else:
            return [TextContent(type="text", text=f"Herramienta no encontrada: {name}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Ejecuta el servidor MCP."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
