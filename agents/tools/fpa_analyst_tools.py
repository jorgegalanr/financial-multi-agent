"""
Herramientas del FP&A Analyst.
Utilización, KPIs, presupuestos y análisis de desviaciones.
Normativa española y formato EUR (1.234,56€).
"""

from langchain_core.tools import tool
from .web_tools import buscar_mercado_servicios, buscar_indicadores_economicos
import pandas as pd
import os
from .utils import formato_euro, formato_numero, formato_porcentaje

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

@tool
def consultar_utilizacion() -> str:
    """
    Consulta la utilización actual de las unidades.
    
    Returns:
        Utilización por unidad con capacidad total, utilizadas y porcentaje
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "utilizacion.csv"))
        
        total_capacidad = df["capacidad"].sum()
        total_utilizacion = df["utilizacion_actual"].sum()
        media = (total_utilizacion / total_capacidad * 100) if total_capacidad > 0 else 0
        
        resultado = f"""## 🏠 UTILIZACIÓN DE UNIDADES
**Utilización media:** {formato_porcentaje(media)}
**Capacidad total:** {total_capacidad} | **Contratos activos:** {total_utilizacion}

| Unidad | Capacidad | Contratos activos | Precio Medio | Utilización |
|------------|-----------|----------|--------------|-----------|
"""
        for _, row in df.iterrows():
            pct = (row['utilizacion_actual'] / row['capacidad'] * 100) if row['capacidad'] > 0 else 0
            icono = "🟢" if pct >= 90 else "🟡" if pct >= 75 else "🔴"
            precio = row.get('precio_medio', 0)
            resultado += f"| {row['unidad']} | {row['capacidad']} | {row['utilizacion_actual']} | {formato_euro(precio)} | {icono} {formato_porcentaje(pct)} |\n"
        
        resultado += f"| **TOTAL** | **{total_capacidad}** | **{total_utilizacion}** | | **{formato_porcentaje(media)}** |"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def consultar_kpis() -> str:
    """
    Consulta los KPIs operativos y financieros principales.
    
    Returns:
        Dashboard de KPIs con valor actual, objetivo y estado
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "kpis.csv"))
        
        resultado = """## 📈 DASHBOARD DE KPIs

| KPI | Valor | Objetivo | Unidad | Estado |
|-----|-------|----------|--------|--------|
"""
        for _, row in df.iterrows():
            valor = row['valor']
            objetivo = row.get('objetivo', None)
            unidad = row.get('unidad', '')
            
            # Determinar si cumple objetivo
            if pd.notna(objetivo):
                if unidad == '%' and 'morosidad' in row['nombre'].lower():
                    cumple = valor <= objetivo  # Para morosidad, menor es mejor
                elif unidad == 'días':
                    cumple = valor <= objetivo  # Para DSO, menor es mejor
                else:
                    cumple = valor >= objetivo
            else:
                cumple = True
            
            icono = "🟢" if cumple else "🔴"
            
            # Formatear valor según unidad
            if unidad == '€':
                valor_fmt = formato_euro(valor)
                obj_fmt = formato_euro(objetivo) if pd.notna(objetivo) else "-"
            elif unidad == '%':
                valor_fmt = formato_porcentaje(valor)
                obj_fmt = formato_porcentaje(objetivo) if pd.notna(objetivo) else "-"
            else:
                valor_fmt = formato_numero(valor, 1)
                obj_fmt = formato_numero(objetivo, 1) if pd.notna(objetivo) else "-"
            
            resultado += f"| {row['nombre']} | {valor_fmt} | {obj_fmt} | {unidad} | {icono} |\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def analisis_desviaciones() -> str:
    """
    Compara presupuesto con datos reales y analiza desviaciones.
    
    Returns:
        Análisis de desviaciones presupuestarias con causas
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "desviaciones.csv"))
        
        resultado = """## 📊 ANÁLISIS DE DESVIACIONES PRESUPUESTARIAS
**Ejercicio 2026**

| Concepto | Presupuesto | Real | Desviación | % |
|----------|-------------|------|------------|---|
"""
        for _, row in df.iterrows():
            desv = row['real'] - row['presupuesto']
            pct = (desv / row['presupuesto'] * 100) if row['presupuesto'] != 0 else 0
            icono = "🟢" if abs(pct) < 5 else "🟡" if abs(pct) < 10 else "🔴"
            signo = "+" if desv >= 0 else ""
            resultado += f"| {row['concepto']} | {formato_euro(row['presupuesto'])} | {formato_euro(row['real'])} | {icono} {signo}{formato_euro(desv)} | {signo}{formato_porcentaje(pct)} |\n"
        
        resultado += """
### Interpretación
- 🟢 Desviación < 5%: Bajo control
- 🟡 Desviación 5-10%: Vigilar
- 🔴 Desviación > 10%: Requiere acción
"""
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas para exportar
FPA_ANALYST_TOOLS = [
    consultar_utilizacion,
    consultar_kpis,
    analisis_desviaciones,
    buscar_mercado_servicios, buscar_indicadores_economicos
]
