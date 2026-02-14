"""
MCP Server 2: Servidor de Gestión de Cobros
Proporciona acceso a datos de facturación, morosos y estudiantes mediante MCP.
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
server = Server("collections-management-server")


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
            name="get_invoices",
            description="Obtiene las facturas emitidas con filtros opcionales",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filtrar por estado: todas, pendiente, pagada, vencida",
                        "enum": ["todas", "pendiente", "pagada", "vencida"]
                    },
                    "residence": {
                        "type": "string",
                        "description": "Filtrar por residencia: Sol, Luna, Estrella"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_defaulters",
            description="Obtiene listado de estudiantes morosos",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_days": {
                        "type": "integer",
                        "description": "Días mínimos de retraso (default: 1)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_student_info",
            description="Obtiene información completa de un estudiante",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "ID del estudiante (ej: EST-101)"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="get_aging_report",
            description="Genera el aging report de cuentas por cobrar",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_collection_forecast",
            description="Genera previsión de cobros",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Días hacia adelante (default: 30)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_occupancy",
            description="Obtiene la ocupación de las residencias",
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
        if name == "get_invoices":
            df = load_csv("facturas_emitidas.csv")
            status = arguments.get("status", "todas")
            residence = arguments.get("residence")
            
            if status != "todas":
                df = df[df["estado"] == status]
            if residence:
                df = df[df["residencia"].str.contains(residence, case=False, na=False)]
            
            result = {
                "total_facturas": len(df),
                "importe_total": df["importe"].sum(),
                "facturas": df.to_dict(orient="records")
            }
            
        elif name == "get_defaulters":
            min_days = arguments.get("min_days", 1)
            facturas = load_csv("facturas_emitidas.csv")
            estudiantes = load_csv("estudiantes.csv")
            
            vencidas = facturas[facturas["estado"] == "vencida"].copy()
            vencidas["fecha_vencimiento"] = pd.to_datetime(vencidas["fecha_vencimiento"])
            vencidas["dias_retraso"] = (datetime.now() - vencidas["fecha_vencimiento"]).dt.days
            vencidas = vencidas[vencidas["dias_retraso"] >= min_days]
            
            if vencidas.empty:
                result = {"total_morosos": 0, "deuda_total": 0, "morosos": []}
            else:
                morosos = vencidas.groupby("id_estudiante").agg({
                    "importe": "sum",
                    "id_factura": "count",
                    "dias_retraso": "max"
                }).reset_index()
                morosos.columns = ["id_estudiante", "deuda_total", "num_facturas", "max_dias_retraso"]
                morosos = morosos.merge(estudiantes, on="id_estudiante", how="left")
                
                result = {
                    "total_morosos": len(morosos),
                    "deuda_total": morosos["deuda_total"].sum(),
                    "morosos": morosos.to_dict(orient="records")
                }
            
        elif name == "get_student_info":
            student_id = arguments.get("student_id", "").upper()
            estudiantes = load_csv("estudiantes.csv")
            facturas = load_csv("facturas_emitidas.csv")
            
            est = estudiantes[estudiantes["id_estudiante"] == student_id]
            if est.empty:
                result = {"error": f"Estudiante {student_id} no encontrado"}
            else:
                est = est.iloc[0].to_dict()
                fact_est = facturas[facturas["id_estudiante"] == student_id]
                est["facturas"] = fact_est.to_dict(orient="records")
                est["total_pagado"] = fact_est[fact_est["estado"] == "pagada"]["importe"].sum()
                est["total_pendiente"] = fact_est[fact_est["estado"] == "pendiente"]["importe"].sum()
                est["total_vencido"] = fact_est[fact_est["estado"] == "vencida"]["importe"].sum()
                result = est
            
        elif name == "get_aging_report":
            facturas = load_csv("facturas_emitidas.csv")
            pendientes = facturas[facturas["estado"].isin(["pendiente", "vencida"])].copy()
            pendientes["fecha_vencimiento"] = pd.to_datetime(pendientes["fecha_vencimiento"])
            pendientes["dias"] = (datetime.now() - pendientes["fecha_vencimiento"]).dt.days
            
            def clasificar(dias):
                if dias <= 0: return "no_vencido"
                elif dias <= 30: return "1-30_dias"
                elif dias <= 60: return "31-60_dias"
                elif dias <= 90: return "61-90_dias"
                return "mas_90_dias"
            
            pendientes["tramo"] = pendientes["dias"].apply(clasificar)
            aging = pendientes.groupby("tramo").agg({
                "importe": "sum",
                "id_factura": "count"
            }).reset_index()
            aging.columns = ["tramo", "importe", "num_facturas"]
            
            result = {
                "total_pendiente": pendientes["importe"].sum(),
                "total_facturas": len(pendientes),
                "tramos": aging.to_dict(orient="records")
            }
            
        elif name == "get_collection_forecast":
            days = arguments.get("days", 30)
            facturas = load_csv("facturas_emitidas.csv")
            pendientes = facturas[facturas["estado"] == "pendiente"].copy()
            pendientes["fecha_vencimiento"] = pd.to_datetime(pendientes["fecha_vencimiento"])
            
            from datetime import timedelta
            limite = datetime.now() + timedelta(days=days)
            proximos = pendientes[pendientes["fecha_vencimiento"] <= limite]
            
            result = {
                "dias": days,
                "total_previsto": proximos["importe"].sum(),
                "num_facturas": len(proximos),
                "cobros": proximos.to_dict(orient="records")
            }
            
        elif name == "get_occupancy":
            df = load_csv("ocupacion.csv")
            total_cap = df["capacidad"].sum()
            total_ocu = df["ocupacion_actual"].sum()
            
            result = {
                "ocupacion_media": round((total_ocu / total_cap * 100) if total_cap > 0 else 0, 1),
                "total_capacidad": total_cap,
                "total_ocupadas": total_ocu,
                "residencias": df.to_dict(orient="records")
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
