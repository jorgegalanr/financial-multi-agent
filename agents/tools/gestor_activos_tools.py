"""
Herramientas del Gestor de Activos.
Activos fijos, amortizaciones, mantenimientos y seguros.
Según PGC español (amortización lineal, tablas IS).
Formato EUR (1.234,56€).
"""

from langchain_core.tools import tool
from .web_tools import buscar_normativa_fiscal
import pandas as pd
import os
from datetime import datetime, timedelta
from .utils import formato_euro, formato_numero, formato_porcentaje

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

@tool
def consultar_activos_fijos(categoria: str = "todos") -> str:
    """
    Consulta el inventario de activos fijos según PGC español.
    
    Args:
        categoria: Filtrar por tipo - todos, inmuebles, mobiliario, equipos, vehiculos
    
    Returns:
        Lista de activos con valor de adquisición, amortización y valor neto
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "activos_fijos.csv"))
        
        if categoria != "todos":
            df = df[df["categoria"].str.lower().str.contains(categoria.lower())]
        
        total_adquisicion = df["valor_adquisicion"].sum()
        total_amortizado = df["amortizacion_acumulada"].sum()
        total_neto = df["valor_neto"].sum()
        
        resultado = f"""## 🏢 INVENTARIO DE ACTIVOS FIJOS
**Filtro:** {categoria}
**Valoración según PGC español**

### Resumen
| Métrica | Importe |
|---------|---------|
| Valor Adquisición | {formato_euro(total_adquisicion)} |
| Amortización Acumulada | {formato_euro(total_amortizado)} |
| **Valor Neto Contable** | **{formato_euro(total_neto)}** |

### Detalle
| ID | Descripción | Categoría | V. Adquisición | Amort. Acum. | V. Neto |
|----|-------------|-----------|----------------|--------------|---------|
"""
        for _, row in df.iterrows():
            resultado += f"| {row['id_activo']} | {row['descripcion'][:25]} | {row['categoria']} | {formato_euro(row['valor_adquisicion'])} | {formato_euro(row['amortizacion_acumulada'])} | {formato_euro(row['valor_neto'])} |\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def calcular_amortizacion_mensual() -> str:
    """
    Calcula la amortización mensual de todos los activos.
    Método lineal según tablas de amortización del Impuesto de Sociedades.
    
    Returns:
        Cuadro de amortización mensual para enviar al Controller
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "activos_fijos.csv"))
        df = df[df["vida_util_anos"] > 0].copy()
        
        df["amort_anual"] = df["valor_adquisicion"] / df["vida_util_anos"]
        df["amort_mensual"] = df["amort_anual"] / 12
        
        total_mensual = df["amort_mensual"].sum()
        total_anual = df["amort_anual"].sum()
        
        resultado = f"""## 📉 CUADRO DE AMORTIZACIÓN
**Para:** Controller | **Fecha:** {datetime.now().strftime('%d/%m/%Y')}
**Método:** Lineal según tablas IS (Ley 27/2014)

### Resumen
| Período | Importe |
|---------|---------|
| Amortización Mensual | {formato_euro(total_mensual)} |
| Amortización Anual | {formato_euro(total_anual)} |

### Detalle por Activo
| Activo | Categoría | V. Adquisición | Vida Útil | Amort. Mensual |
|--------|-----------|----------------|-----------|----------------|
"""
        for _, row in df.iterrows():
            resultado += f"| {row['descripcion'][:25]} | {row['categoria']} | {formato_euro(row['valor_adquisicion'])} | {int(row['vida_util_anos'])} años | {formato_euro(row['amort_mensual'])} |\n"
        
        resultado += f"| **TOTAL** | | | | **{formato_euro(total_mensual)}** |"
        
        resultado += """

### Vidas útiles según tablas IS
- Edificios: 50 años (2% anual)
- Instalaciones: 10-20 años
- Mobiliario: 10 años (10% anual)
- Equipos informáticos: 4-6 años
- Vehículos: 6-10 años
"""
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def consultar_mantenimientos(dias: int = 60) -> str:
    """
    Lista los mantenimientos programados en los próximos días.
    
    Args:
        dias: Días hacia adelante para buscar mantenimientos (default: 60)
    
    Returns:
        Mantenimientos programados con fechas, tipo y coste estimado
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "mantenimientos.csv"))
        df["proximo_mantenimiento"] = pd.to_datetime(df["proximo_mantenimiento"])
        
        limite = datetime.now() + timedelta(days=dias)
        proximos = df[df["proximo_mantenimiento"] <= limite].sort_values("proximo_mantenimiento")
        
        if proximos.empty:
            return f"✅ No hay mantenimientos programados en los próximos {dias} días."
        
        total_coste = proximos["coste_estimado"].sum()
        
        resultado = f"""## 🔧 MANTENIMIENTOS PRÓXIMOS ({dias} días)
**Total coste estimado:** {formato_euro(total_coste)}

| Fecha | Activo | Tipo | Descripción | Proveedor | Coste Est. |
|-------|--------|------|-------------|-----------|------------|
"""
        for _, row in proximos.iterrows():
            tipo = str(row['tipo']).lower()
            icono = "🔴" if tipo in ["correctivo", "corr"] else "🟢"
            resultado += f"| {row['proximo_mantenimiento'].strftime('%d/%m/%Y')} | {row['activo']} | {icono} {row['tipo']} | {row['descripcion'][:20]} | {row['proveedor']} | {formato_euro(row['coste_estimado'])} |\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas para exportar
GESTOR_ACTIVOS_TOOLS = [
    consultar_activos_fijos,
    calcular_amortizacion_mensual,
    consultar_mantenimientos,
    buscar_normativa_fiscal
]
