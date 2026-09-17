"""
Cliente MCP simplificado para integrar con LangChain.
Implementa las herramientas MCP como funciones directas sin servidor externo.
Esto evita problemas de asyncio en Windows/Streamlit.
Incluye datos de mercado (tipos de interés, indicadores).
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
from langchain_core.tools import tool

# Ruta a los datos
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_csv(filename: str) -> pd.DataFrame:
    """Carga un archivo CSV."""
    return pd.read_csv(os.path.join(DATA_PATH, filename))


def formato_euro(valor):
    """Formatea número como euros en formato español."""
    try:
        if valor >= 0:
            return f"{valor:,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"-{abs(valor):,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"{valor}€"


# ============================================
# MCP FINANCIAL TOOLS (Servidor 1)
# ============================================

@tool
def mcp_get_cash_position() -> str:
    """
    [Adaptador local] Obtiene la posición de caja actual.
    Herramienta del servidor MCP de datos financieros.
    
    Returns:
        JSON con saldo total y desglose por cuenta bancaria
    """
    try:
        df = load_csv("posicion_caja.csv")
        total = df["saldo"].sum()
        result = {
            "adaptador": "financial_local",
            "herramienta": "get_cash_position",
            "fecha": datetime.now().isoformat(),
            "saldo_total": float(total),
            "cuentas": df.to_dict(orient="records")
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_get_bank_debt() -> str:
    """
    [Adaptador local] Obtiene el detalle de la deuda bancaria.
    Herramienta del servidor MCP de datos financieros.
    
    Returns:
        JSON con préstamos, capital pendiente y cuotas
    """
    try:
        df = load_csv("deuda_bancaria.csv")
        result = {
            "adaptador": "financial_local",
            "herramienta": "get_bank_debt",
            "deuda_total": float(df["capital_pendiente"].sum()),
            "cuota_mensual_total": float(df["cuota_mensual"].sum()),
            "prestamos": df.to_dict(orient="records")
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_get_balance_sheet() -> str:
    """
    [Adaptador local] Obtiene el balance de situación.
    Herramienta del servidor MCP de datos financieros.
    
    Returns:
        JSON con activo, pasivo y patrimonio neto
    """
    try:
        df = load_csv("balance.csv")
        activo = df[df["tipo"] == "activo"]["importe"].sum()
        pasivo = df[df["tipo"] == "pasivo"]["importe"].sum()
        patrimonio = df[df["tipo"] == "patrimonio"]["importe"].sum()
        result = {
            "adaptador": "financial_local",
            "herramienta": "get_balance_sheet",
            "fecha": datetime.now().isoformat(),
            "activo_total": float(activo),
            "pasivo_total": float(pasivo),
            "patrimonio_neto": float(patrimonio),
            "detalle": df.to_dict(orient="records")
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_calculate_liquidity() -> str:
    """
    [Adaptador local] Calcula el ratio de liquidez.
    Herramienta del servidor MCP de datos financieros.
    
    Returns:
        JSON con ratio de liquidez y meses de cobertura
    """
    try:
        caja = load_csv("posicion_caja.csv")
        gastos = load_csv("gastos_fijos.csv")
        saldo = caja["saldo"].sum()
        gastos_mensuales = gastos["importe_mensual"].sum()
        meses = saldo / gastos_mensuales if gastos_mensuales > 0 else 0
        result = {
            "adaptador": "financial_local",
            "herramienta": "calculate_liquidity_ratio",
            "saldo_disponible": float(saldo),
            "gastos_mensuales": float(gastos_mensuales),
            "meses_cobertura": round(meses, 2),
            "estado": "OPTIMO" if meses >= 4 else "ACEPTABLE" if meses >= 2 else "CRITICO"
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================
# MCP COLLECTIONS TOOLS (Servidor 2)
# ============================================

@tool
def mcp_get_defaulters(min_days: int = 1) -> str:
    """
    [Adaptador local] Obtiene listado de morosos.
    Herramienta del servidor MCP de gestión de cobros.
    
    Args:
        min_days: Días mínimos de retraso para considerar moroso
    
    Returns:
        JSON con lista de morosos y deuda total
    """
    try:
        facturas = load_csv("facturas_emitidas.csv")
        clientes = load_csv("clientes.csv")
        
        vencidas = facturas[facturas["estado"] == "vencida"].copy()
        vencidas["fecha_vencimiento"] = pd.to_datetime(vencidas["fecha_vencimiento"])
        vencidas["dias_retraso"] = (datetime.now() - vencidas["fecha_vencimiento"]).dt.days
        vencidas = vencidas[vencidas["dias_retraso"] >= min_days]
        
        if vencidas.empty:
            result = {
                "adaptador": "collections_local",
                "herramienta": "get_defaulters",
                "total_morosos": 0,
                "deuda_total": 0,
                "morosos": []
            }
        else:
            morosos = vencidas.groupby("id_cliente").agg({
                "importe": "sum",
                "id_factura": "count",
                "dias_retraso": "max"
            }).reset_index()
            morosos.columns = ["id_cliente", "deuda_total", "num_facturas", "max_dias_retraso"]
            morosos = morosos.merge(clientes, on="id_cliente", how="left")
            
            result = {
                "adaptador": "collections_local",
                "herramienta": "get_defaulters",
                "total_morosos": len(morosos),
                "deuda_total": float(morosos["deuda_total"].sum()),
                "morosos": morosos.to_dict(orient="records")
            }
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_get_customer_info(customer_id: str) -> str:
    """
    [Adaptador local] Obtiene información de un cliente.
    Herramienta del servidor MCP de gestión de cobros.
    
    Args:
        customer_id: ID del cliente (ej: CLI-101)
    
    Returns:
        JSON con datos del cliente y su historial de facturas
    """
    try:
        clientes = load_csv("clientes.csv")
        facturas = load_csv("facturas_emitidas.csv")
        
        customer_id = customer_id.upper()
        est = clientes[clientes["id_cliente"] == customer_id]
        
        if est.empty:
            return json.dumps({"error": f"Cliente {customer_id} no encontrado"})
        
        est_dict = est.iloc[0].to_dict()
        fact_est = facturas[facturas["id_cliente"] == customer_id]
        
        est_dict["adaptador"] = "collections_local"
        est_dict["herramienta"] = "get_customer_info"
        est_dict["facturas"] = fact_est.to_dict(orient="records")
        est_dict["total_pagado"] = float(fact_est[fact_est["estado"] == "pagada"]["importe"].sum())
        est_dict["total_pendiente"] = float(fact_est[fact_est["estado"] == "pendiente"]["importe"].sum())
        est_dict["total_vencido"] = float(fact_est[fact_est["estado"] == "vencida"]["importe"].sum())
        
        return json.dumps(est_dict, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_get_aging_report() -> str:
    """
    [Adaptador local] Genera el aging report de cuentas por cobrar.
    Herramienta del servidor MCP de gestión de cobros.
    
    Returns:
        JSON con análisis de antigüedad de cuentas por cobrar
    """
    try:
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
            "adaptador": "collections_local",
            "herramienta": "get_aging_report",
            "total_pendiente": float(pendientes["importe"].sum()),
            "total_facturas": len(pendientes),
            "tramos": aging.to_dict(orient="records")
        }
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_get_utilization() -> str:
    """
    [Adaptador local] Obtiene la utilización de unidades.
    Herramienta del servidor MCP de gestión de cobros.
    
    Returns:
        JSON con utilización por unidad y media total
    """
    try:
        df = load_csv("utilizacion.csv")
        total_cap = df["capacidad"].sum()
        total_ocu = df["utilizacion_actual"].sum()
        
        result = {
            "adaptador": "collections_local",
            "herramienta": "get_utilization",
            "utilizacion_media": round((total_ocu / total_cap * 100) if total_cap > 0 else 0, 1),
            "total_capacidad": int(total_cap),
            "total_utilizadas": int(total_ocu),
            "unidades": df.to_dict(orient="records")
        }
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# Lista de herramientas MCP para exportar
MCP_FINANCIAL_TOOLS = [
    mcp_get_cash_position,
    mcp_get_bank_debt,
    mcp_get_balance_sheet,
    mcp_calculate_liquidity
]

MCP_COLLECTIONS_TOOLS = [
    mcp_get_defaulters,
    mcp_get_customer_info,
    mcp_get_aging_report,
    mcp_get_utilization
]


# ============================================
# MCP MARKET DATA (Servidor 3 - Datos de Mercado)
# ============================================

@tool
def mcp_get_interest_rates() -> str:
    """
    Devuelve un escenario sintético de tipos de interés.
    
    Returns:
        JSON de demostración; no contiene datos actuales
    """
    result = {
        "servidor": "MCP Market Data Server",
        "herramienta": "get_interest_rates",
        "fecha_consulta": datetime.now().isoformat(),
        "euribor": {
            "1_mes": 3.042,
            "3_meses": 3.108,
            "6_meses": 3.187,
            "12_meses": 2.937,
            "fecha": "enero 2025",
            "tendencia": "bajista"
        },
        "bce": {
            "tipo_principal": 4.50,
            "facilidad_deposito": 4.00,
            "facilidad_credito": 4.75
        },
        "hipotecas_espana": {
            "tipo_fijo_medio": 3.25,
            "tipo_variable_medio": "Euribor + 0.99"
        },
        "es_dato_sintetico": True,
        "fuente": "dataset sintético"
    }
    return json.dumps(result, indent=2, default=str)


@tool
def mcp_get_tax_rates() -> str:
    """
    Devuelve un escenario fiscal sintético.
    
    Returns:
        JSON de demostración; requiere verificación oficial
    """
    result = {
        "servidor": "MCP Market Data Server",
        "herramienta": "get_tax_rates",
        "fecha_consulta": datetime.now().isoformat(),
        "iva": {
            "general": 21,
            "reducido": 10,
            "superreducido": 4,
            "servicios_b2b": 10,
            "operaciones_exentas": "exento"
        },
        "impuesto_sociedades": {
            "general": 25,
            "pymes": 23,
            "nuevas_empresas": 15
        },
        "irpf_retenciones": {
            "capital_mobiliario": 19,
            "arrendamientos": 19,
            "profesionales": 15
        },
        "es_dato_sintetico": True,
        "fuente": "dataset sintético"
    }
    return json.dumps(result, indent=2, default=str)


@tool
def mcp_get_economic_indicators() -> str:
    """
    Devuelve indicadores económicos sintéticos.
    
    Returns:
        JSON con IPC, SMI, indicadores económicos
    """
    result = {
        "servidor": "MCP Market Data Server",
        "herramienta": "get_economic_indicators",
        "fecha_consulta": datetime.now().isoformat(),
        "ipc": {
            "interanual": 2.8,
            "mensual": 0.2,
            "subyacente": 3.6,
            "fecha": "diciembre 2024"
        },
        "smi": {
            "mensual_14_pagas": 1134,
            "anual": 15876,
            "fecha": "2024"
        },
        "mercado_servicios": {
            "utilizacion_media": 92,
            "precio_medio": 650,
            "crecimiento": 5.2
        },
        "es_dato_sintetico": True,
        "fuente": "dataset sintético"
    }
    return json.dumps(result, indent=2, default=str)


MCP_MARKET_TOOLS = [
    mcp_get_interest_rates,
    mcp_get_tax_rates,
    mcp_get_economic_indicators
]

ALL_MCP_TOOLS = MCP_FINANCIAL_TOOLS + MCP_COLLECTIONS_TOOLS
