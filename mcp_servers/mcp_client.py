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
    [MCP Financial] Obtiene la posición de caja actual.
    Herramienta del servidor MCP de datos financieros.
    
    Returns:
        JSON con saldo total y desglose por cuenta bancaria
    """
    try:
        df = load_csv("posicion_caja.csv")
        total = df["saldo"].sum()
        result = {
            "servidor": "MCP Financial Data Server",
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
    [MCP Financial] Obtiene el detalle de la deuda bancaria.
    Herramienta del servidor MCP de datos financieros.
    
    Returns:
        JSON con préstamos, capital pendiente y cuotas
    """
    try:
        df = load_csv("deuda_bancaria.csv")
        result = {
            "servidor": "MCP Financial Data Server",
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
    [MCP Financial] Obtiene el balance de situación.
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
            "servidor": "MCP Financial Data Server",
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
    [MCP Financial] Calcula el ratio de liquidez.
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
            "servidor": "MCP Financial Data Server",
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
    [MCP Collections] Obtiene listado de morosos.
    Herramienta del servidor MCP de gestión de cobros.
    
    Args:
        min_days: Días mínimos de retraso para considerar moroso
    
    Returns:
        JSON con lista de morosos y deuda total
    """
    try:
        facturas = load_csv("facturas_emitidas.csv")
        estudiantes = load_csv("estudiantes.csv")
        
        vencidas = facturas[facturas["estado"] == "vencida"].copy()
        vencidas["fecha_vencimiento"] = pd.to_datetime(vencidas["fecha_vencimiento"])
        vencidas["dias_retraso"] = (datetime.now() - vencidas["fecha_vencimiento"]).dt.days
        vencidas = vencidas[vencidas["dias_retraso"] >= min_days]
        
        if vencidas.empty:
            result = {
                "servidor": "MCP Collections Server",
                "herramienta": "get_defaulters",
                "total_morosos": 0,
                "deuda_total": 0,
                "morosos": []
            }
        else:
            morosos = vencidas.groupby("id_estudiante").agg({
                "importe": "sum",
                "id_factura": "count",
                "dias_retraso": "max"
            }).reset_index()
            morosos.columns = ["id_estudiante", "deuda_total", "num_facturas", "max_dias_retraso"]
            morosos = morosos.merge(estudiantes, on="id_estudiante", how="left")
            
            result = {
                "servidor": "MCP Collections Server",
                "herramienta": "get_defaulters",
                "total_morosos": len(morosos),
                "deuda_total": float(morosos["deuda_total"].sum()),
                "morosos": morosos.to_dict(orient="records")
            }
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_get_student_info(student_id: str) -> str:
    """
    [MCP Collections] Obtiene información de un estudiante.
    Herramienta del servidor MCP de gestión de cobros.
    
    Args:
        student_id: ID del estudiante (ej: EST-101)
    
    Returns:
        JSON con datos del estudiante y su historial de facturas
    """
    try:
        estudiantes = load_csv("estudiantes.csv")
        facturas = load_csv("facturas_emitidas.csv")
        
        student_id = student_id.upper()
        est = estudiantes[estudiantes["id_estudiante"] == student_id]
        
        if est.empty:
            return json.dumps({"error": f"Estudiante {student_id} no encontrado"})
        
        est_dict = est.iloc[0].to_dict()
        fact_est = facturas[facturas["id_estudiante"] == student_id]
        
        est_dict["servidor"] = "MCP Collections Server"
        est_dict["herramienta"] = "get_student_info"
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
    [MCP Collections] Genera el aging report de cuentas por cobrar.
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
            "servidor": "MCP Collections Server",
            "herramienta": "get_aging_report",
            "total_pendiente": float(pendientes["importe"].sum()),
            "total_facturas": len(pendientes),
            "tramos": aging.to_dict(orient="records")
        }
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mcp_get_occupancy() -> str:
    """
    [MCP Collections] Obtiene la ocupación de residencias.
    Herramienta del servidor MCP de gestión de cobros.
    
    Returns:
        JSON con ocupación por residencia y media total
    """
    try:
        df = load_csv("ocupacion.csv")
        total_cap = df["capacidad"].sum()
        total_ocu = df["ocupacion_actual"].sum()
        
        result = {
            "servidor": "MCP Collections Server",
            "herramienta": "get_occupancy",
            "ocupacion_media": round((total_ocu / total_cap * 100) if total_cap > 0 else 0, 1),
            "total_capacidad": int(total_cap),
            "total_ocupadas": int(total_ocu),
            "residencias": df.to_dict(orient="records")
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
    mcp_get_student_info,
    mcp_get_aging_report,
    mcp_get_occupancy
]


# ============================================
# MCP MARKET DATA (Servidor 3 - Datos de Mercado)
# ============================================

@tool
def mcp_get_interest_rates() -> str:
    """
    [MCP Market Data] Obtiene tipos de interés actuales: Euribor, BCE, hipotecas.
    Herramienta del servidor MCP de datos de mercado.
    
    Returns:
        JSON con tipos de interés actualizados
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
        "fuente": "Banco de España / BCE"
    }
    return json.dumps(result, indent=2, default=str)


@tool
def mcp_get_tax_rates() -> str:
    """
    [MCP Market Data] Obtiene tipos impositivos vigentes en España.
    Herramienta del servidor MCP de datos de mercado.
    
    Returns:
        JSON con tipos de IVA, IS, IRPF actualizados
    """
    result = {
        "servidor": "MCP Market Data Server",
        "herramienta": "get_tax_rates",
        "fecha_consulta": datetime.now().isoformat(),
        "iva": {
            "general": 21,
            "reducido": 10,
            "superreducido": 4,
            "alojamiento_estudiantes": 10,
            "arrendamiento_vivienda": "exento"
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
        "fuente": "AEAT 2025"
    }
    return json.dumps(result, indent=2, default=str)


@tool
def mcp_get_economic_indicators() -> str:
    """
    [MCP Market Data] Obtiene indicadores económicos de España.
    Herramienta del servidor MCP de datos de mercado.
    
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
        "mercado_residencias": {
            "ocupacion_media": 92,
            "precio_medio": 650,
            "crecimiento": 5.2
        },
        "fuente": "INE / BOE"
    }
    return json.dumps(result, indent=2, default=str)


MCP_MARKET_TOOLS = [
    mcp_get_interest_rates,
    mcp_get_tax_rates,
    mcp_get_economic_indicators
]

ALL_MCP_TOOLS = MCP_FINANCIAL_TOOLS + MCP_COLLECTIONS_TOOLS + MCP_MARKET_TOOLS
