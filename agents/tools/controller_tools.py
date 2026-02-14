"""
Herramientas del Controller.
Contabilidad, balance, cuenta de resultados y ratios.
Según Plan General Contable español (RD 1514/2007).
Formato EUR (1.234,56€).
"""

from langchain_core.tools import tool
from .web_tools import buscar_normativa_fiscal, buscar_indicadores_economicos
import pandas as pd
import os
from datetime import datetime
from .utils import formato_euro, formato_numero, formato_porcentaje

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def normalizar_tipo(tipo_val):
    """Normaliza los valores de tipo (activo/pasivo/patrimonio)."""
    tipo_lower = str(tipo_val).lower().strip()
    if tipo_lower in ['act', 'activo', 'a']:
        return 'activo'
    elif tipo_lower in ['pas', 'pasivo', 'p']:
        return 'pasivo'
    elif tipo_lower in ['pat', 'patrimonio', 'pn', 'neto']:
        return 'patrimonio'
    elif tipo_lower in ['ing', 'ingreso', 'ingresos', 'i']:
        return 'ingreso'
    elif tipo_lower in ['gas', 'gasto', 'gastos', 'g']:
        return 'gasto'
    return tipo_lower


@tool
def consultar_balance() -> str:
    """
    Obtiene el balance de situación actual según PGC español.
    Estructura: Activo, Pasivo, Patrimonio Neto.
    
    Returns:
        Balance de situación con totales por masa patrimonial
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "balance.csv"))
        df['tipo_norm'] = df['tipo'].apply(normalizar_tipo)
        
        activo = df[df["tipo_norm"] == "activo"]["importe"].sum()
        pasivo = df[df["tipo_norm"] == "pasivo"]["importe"].sum()
        patrimonio = df[df["tipo_norm"] == "patrimonio"]["importe"].sum()
        
        # Si no hay patrimonio explícito, calcularlo
        if patrimonio == 0 and activo > 0 and pasivo > 0:
            patrimonio = activo - pasivo
        
        resultado = f"""## 📊 BALANCE DE SITUACIÓN
**Fecha:** {datetime.now().strftime('%d/%m/%Y')}
**Según Plan General Contable (RD 1514/2007)**

| Masa Patrimonial | Importe |
|------------------|---------|
| **ACTIVO** | **{formato_euro(activo)}** |
| **PASIVO** | **{formato_euro(pasivo)}** |
| **PATRIMONIO NETO** | **{formato_euro(patrimonio)}** |

### Detalle
| Cuenta | Tipo | Importe |
|--------|------|---------|
"""
        for _, row in df.iterrows():
            resultado += f"| {row['cuenta']} | {row['tipo']} | {formato_euro(row['importe'])} |\n"
        
        resultado += f"\n**Verificación:** Activo ({formato_euro(activo)}) = Pasivo + PN ({formato_euro(pasivo + patrimonio)})"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def consultar_cuenta_resultados() -> str:
    """
    Obtiene la cuenta de pérdidas y ganancias (PyG) según PGC español.
    
    Returns:
        Cuenta de resultados con ingresos, gastos y resultado neto
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "cuenta_resultados.csv"))
        df['tipo_norm'] = df['tipo'].apply(normalizar_tipo)
        
        ingresos = df[df["tipo_norm"] == "ingreso"]["importe"].sum()
        gastos = df[df["tipo_norm"] == "gasto"]["importe"].sum()
        
        # Si no hay gastos en el CSV, cargar de gastos_fijos
        if gastos == 0:
            try:
                gastos_df = pd.read_csv(os.path.join(DATA_PATH, "gastos_fijos.csv"))
                gastos = gastos_df["importe_mensual"].sum() * 12  # Anualizar
            except:
                pass
        
        resultado_neto = ingresos - gastos
        margen = (resultado_neto / ingresos * 100) if ingresos > 0 else 0
        
        resultado = f"""## 📈 CUENTA DE PÉRDIDAS Y GANANCIAS
**Ejercicio:** 01/01/2025 - 31/12/2025
**Según PGC español**

| Concepto | Tipo | Importe |
|----------|------|---------|
"""
        for _, row in df.iterrows():
            signo = "+" if normalizar_tipo(row["tipo"]) == "ingreso" else "-"
            resultado += f"| {row['concepto']} | {row['tipo']} | {signo}{formato_euro(row['importe'])} |\n"
        
        resultado += f"""
### RESUMEN
| Métrica | Importe |
|---------|---------|
| Total Ingresos | +{formato_euro(ingresos)} |
| Total Gastos | -{formato_euro(gastos)} |
| **Resultado Neto** | **{formato_euro(resultado_neto)}** |
| Margen | {formato_porcentaje(margen)} |
"""
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def calcular_ratios_financieros() -> str:
    """
    Calcula los principales ratios financieros según estándares españoles.
    Liquidez, solvencia, rentabilidad.
    
    Returns:
        Ratios financieros con valores, interpretación y semáforo
    """
    try:
        balance = pd.read_csv(os.path.join(DATA_PATH, "balance.csv"))
        balance['tipo_norm'] = balance['tipo'].apply(normalizar_tipo)
        
        pyg = pd.read_csv(os.path.join(DATA_PATH, "cuenta_resultados.csv"))
        pyg['tipo_norm'] = pyg['tipo'].apply(normalizar_tipo)
        
        activo = balance[balance["tipo_norm"] == "activo"]["importe"].sum()
        pasivo = balance[balance["tipo_norm"] == "pasivo"]["importe"].sum()
        patrimonio = balance[balance["tipo_norm"] == "patrimonio"]["importe"].sum()
        
        # Si no hay patrimonio, calcularlo
        if patrimonio == 0:
            patrimonio = activo - pasivo
        
        ingresos = pyg[pyg["tipo_norm"] == "ingreso"]["importe"].sum()
        gastos = pyg[pyg["tipo_norm"] == "gasto"]["importe"].sum()
        resultado = ingresos - gastos
        
        liquidez = activo / pasivo if pasivo > 0 else 0
        endeudamiento = (pasivo / activo * 100) if activo > 0 else 0
        roe = (resultado / patrimonio * 100) if patrimonio > 0 else 0
        margen = (resultado / ingresos * 100) if ingresos > 0 else 0
        
        resultado_txt = f"""## 📉 RATIOS FINANCIEROS
**Análisis según estándares de la banca española**

| Ratio | Valor | Referencia | Estado |
|-------|-------|------------|--------|
| Liquidez General | {formato_numero(liquidez, 2)} | >1,5 óptimo | {"🟢" if liquidez > 1.5 else "🟡" if liquidez > 1 else "🔴"} |
| Endeudamiento | {formato_porcentaje(endeudamiento)} | <60% óptimo | {"🟢" if endeudamiento < 60 else "🟡" if endeudamiento < 80 else "🔴"} |
| ROE | {formato_porcentaje(roe)} | >8% óptimo | {"🟢" if roe > 8 else "🟡" if roe > 5 else "🔴"} |
| Margen Neto | {formato_porcentaje(margen)} | >10% óptimo | {"🟢" if margen > 10 else "🟡" if margen > 5 else "🔴"} |

### Datos base
| Concepto | Valor |
|----------|-------|
| Activo Total | {formato_euro(activo)} |
| Pasivo Total | {formato_euro(pasivo)} |
| Patrimonio Neto | {formato_euro(patrimonio)} |
| Ingresos | {formato_euro(ingresos)} |
| Resultado | {formato_euro(resultado)} |

### Interpretación
- **Liquidez:** Capacidad de cubrir deudas a corto plazo
- **Endeudamiento:** Proporción de deuda sobre activos
- **ROE:** Rentabilidad sobre fondos propios
- **Margen:** Beneficio por cada euro de ingreso
"""
        return resultado_txt
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas para exportar
CONTROLLER_TOOLS = [
    consultar_balance,
    consultar_cuenta_resultados,
    calcular_ratios_financieros,
    buscar_normativa_fiscal, buscar_indicadores_economicos
]
