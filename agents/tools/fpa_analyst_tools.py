"""
Herramientas del FP&A Analyst.
Ocupación, KPIs, presupuestos y análisis de desviaciones.
Normativa española y formato EUR (1.234,56€).
"""

from langchain_core.tools import tool
from .web_tools import buscar_mercado_residencias, buscar_indicadores_economicos
import pandas as pd
import os
from .utils import formato_euro, formato_numero, formato_porcentaje

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

@tool
def consultar_ocupacion() -> str:
    """
    Consulta la ocupación actual de las residencias.
    
    Returns:
        Ocupación por residencia con plazas totales, ocupadas y porcentaje
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "ocupacion.csv"))
        
        total_capacidad = df["capacidad"].sum()
        total_ocupacion = df["ocupacion_actual"].sum()
        media = (total_ocupacion / total_capacidad * 100) if total_capacidad > 0 else 0
        
        resultado = f"""## 🏠 OCUPACIÓN DE RESIDENCIAS
**Ocupación media:** {formato_porcentaje(media)}
**Plazas totales:** {total_capacidad} | **Ocupadas:** {total_ocupacion}

| Residencia | Capacidad | Ocupadas | Precio Medio | Ocupación |
|------------|-----------|----------|--------------|-----------|
"""
        for _, row in df.iterrows():
            pct = (row['ocupacion_actual'] / row['capacidad'] * 100) if row['capacidad'] > 0 else 0
            icono = "🟢" if pct >= 90 else "🟡" if pct >= 75 else "🔴"
            precio = row.get('precio_medio', 0)
            resultado += f"| {row['residencia']} | {row['capacidad']} | {row['ocupacion_actual']} | {formato_euro(precio)} | {icono} {formato_porcentaje(pct)} |\n"
        
        resultado += f"| **TOTAL** | **{total_capacidad}** | **{total_ocupacion}** | | **{formato_porcentaje(media)}** |"
        
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
**Ejercicio 2025**

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
    consultar_ocupacion,
    consultar_kpis,
    analisis_desviaciones,
    buscar_mercado_residencias, buscar_indicadores_economicos
]
