"""
Herramientas del Tesorero.
Liquidez, pagos, caja y deuda bancaria.
Normativa española y formato EUR (1.234,56€).
"""

from langchain_core.tools import tool
import pandas as pd
import os
from datetime import datetime, timedelta
from .utils import formato_euro, formato_numero, formato_porcentaje
from .web_tools import buscar_tipos_interes, buscar_indicadores_economicos

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

@tool
def consultar_posicion_caja() -> str:
    """
    Obtiene la posición de caja actual con saldos por banco.
    
    Returns:
        Saldo total disponible y desglose por cuenta bancaria
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "posicion_caja.csv"))
        total = df["saldo"].sum()
        
        resultado = f"""## 🏦 POSICIÓN DE CAJA
**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Saldo Total Disponible: {formato_euro(total)}**

| Banco | Cuenta | Tipo | Saldo |
|-------|--------|------|-------|
"""
        for _, row in df.iterrows():
            resultado += f"| {row['banco']} | {row['cuenta']} | {row['tipo']} | {formato_euro(row['saldo'])} |\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def consultar_pagos_pendientes(dias: int = 30) -> str:
    """
    Lista los pagos pendientes de realizar en los próximos días.
    
    Args:
        dias: Días hacia adelante para buscar vencimientos (default: 30)
    
    Returns:
        Lista de pagos con proveedor, concepto, importe y fecha de vencimiento
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "pagos_pendientes.csv"))
        df["fecha_vencimiento"] = pd.to_datetime(df["fecha_vencimiento"])
        
        limite = datetime.now() + timedelta(days=dias)
        proximos = df[df["fecha_vencimiento"] <= limite].sort_values("fecha_vencimiento")
        
        if proximos.empty:
            return f"✅ No hay pagos pendientes en los próximos {dias} días."
        
        total = proximos["importe"].sum()
        
        resultado = f"""## 📋 PAGOS PENDIENTES (próximos {dias} días)
**Total a pagar:** {formato_euro(total)} | **Nº pagos:** {len(proximos)}

| Vencimiento | Proveedor | Concepto | Importe | Prioridad |
|-------------|-----------|----------|---------|-----------|
"""
        for _, row in proximos.iterrows():
            prioridad = str(row['prioridad']).lower()
            icono = "🔴" if prioridad == "alta" else "🟡" if prioridad == "media" else "🟢"
            resultado += f"| {row['fecha_vencimiento'].strftime('%d/%m/%Y')} | {row['proveedor']} | {row['concepto'][:20]} | {formato_euro(row['importe'])} | {icono} {row['prioridad']} |\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def consultar_deuda_bancaria() -> str:
    """
    Obtiene el detalle de la deuda bancaria (préstamos e hipotecas).
    
    Returns:
        Lista de préstamos con capital pendiente, cuota mensual, tipo de interés y vencimiento
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "deuda_bancaria.csv"))
        
        total_deuda = df["capital_pendiente"].sum()
        cuota_total = df["cuota_mensual"].sum()
        
        resultado = f"""## 🏛️ DEUDA BANCARIA
**Deuda total:** {formato_euro(total_deuda)} | **Cuota mensual total:** {formato_euro(cuota_total)}

| Entidad | Tipo | Capital Pendiente | Cuota Mensual | Interés | Vencimiento |
|---------|------|-------------------|---------------|---------|-------------|
"""
        for _, row in df.iterrows():
            resultado += f"| {row['entidad']} | {row['tipo'][:25]} | {formato_euro(row['capital_pendiente'])} | {formato_euro(row['cuota_mensual'])} | {formato_porcentaje(row['tipo_interes'])} | {row['fecha_vencimiento']} |\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def consultar_gastos_fijos() -> str:
    """
    Lista los gastos fijos mensuales recurrentes.
    
    Returns:
        Desglose de gastos fijos por categoría con importes mensuales
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "gastos_fijos.csv"))
        total = df["importe_mensual"].sum()
        
        por_categoria = df.groupby("categoria")["importe_mensual"].sum().sort_values(ascending=False)
        
        resultado = f"""## 💸 GASTOS FIJOS MENSUALES
**Total mensual:** {formato_euro(total)}

### Por Categoría
| Categoría | Importe | % Total |
|-----------|---------|---------|
"""
        for cat, imp in por_categoria.items():
            pct = (imp / total) * 100
            resultado += f"| {cat} | {formato_euro(imp)} | {formato_porcentaje(pct)} |\n"
        
        resultado += f"""
### Detalle
| Concepto | Categoría | Importe |
|----------|-----------|---------|
"""
        for _, row in df.iterrows():
            resultado += f"| {row['concepto']} | {row['categoria']} | {formato_euro(row['importe_mensual'])} |\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def analisis_liquidez() -> str:
    """
    Realiza análisis de liquidez: meses de cobertura de gastos con caja actual.
    
    Returns:
        Análisis de liquidez con ratio de cobertura, alertas y recomendaciones
    """
    try:
        caja = pd.read_csv(os.path.join(DATA_PATH, "posicion_caja.csv"))
        gastos = pd.read_csv(os.path.join(DATA_PATH, "gastos_fijos.csv"))
        
        saldo_total = caja["saldo"].sum()
        gastos_mensuales = gastos["importe_mensual"].sum()
        
        meses_cobertura = saldo_total / gastos_mensuales if gastos_mensuales > 0 else 0
        
        if meses_cobertura >= 4:
            semaforo = "🟢 ÓPTIMO"
            recomendacion = "Posición de liquidez saludable."
        elif meses_cobertura >= 2:
            semaforo = "🟡 ACEPTABLE"
            recomendacion = "Monitorizar cobros pendientes."
        else:
            semaforo = "🔴 CRÍTICO"
            recomendacion = "URGENTE: Intensificar cobros y revisar pagos."
        
        resultado = f"""## 💧 ANÁLISIS DE LIQUIDEZ

### Estado: {semaforo}

| Métrica | Valor |
|---------|-------|
| Saldo disponible | {formato_euro(saldo_total)} |
| Gastos fijos mensuales | {formato_euro(gastos_mensuales)} |
| **Meses de cobertura** | **{formato_numero(meses_cobertura, 1)} meses** |

### Interpretación
- ≥ 4 meses: 🟢 Óptimo
- 2-4 meses: 🟡 Aceptable  
- < 2 meses: 🔴 Crítico

### Recomendación
{recomendacion}
"""
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas para exportar
TESORERO_TOOLS = [
    consultar_posicion_caja,
    consultar_pagos_pendientes,
    consultar_deuda_bancaria,
    consultar_gastos_fijos,
    analisis_liquidez,
    buscar_tipos_interes,
    buscar_indicadores_economicos
]
