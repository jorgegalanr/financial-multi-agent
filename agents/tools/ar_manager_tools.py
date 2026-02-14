"""
Herramientas del AR Manager (Cuentas por Cobrar).
Facturación, cobros, morosos y gestión de estudiantes.
Normativa española y formato de moneda EUR (1.234,56€).
"""

from langchain_core.tools import tool
from .web_tools import buscar_normativa_fiscal
import pandas as pd
import os
from datetime import datetime
from .utils import formato_euro, formato_numero, formato_porcentaje

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


@tool
def consultar_facturas(estado: str = "todas", residencia: str = "todas") -> str:
    """
    Consulta las facturas emitidas a estudiantes según normativa española de facturación.
    
    Args:
        estado: Filtrar por estado - todas, pendiente, pagada, vencida
        residencia: Filtrar por residencia - todas o nombre de residencia
    
    Returns:
        Listado de facturas con id, estudiante, importe, estado, vencimiento
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "facturas_emitidas.csv"))
        
        if estado != "todas":
            df = df[df["estado"] == estado]
        if residencia != "todas":
            df = df[df["residencia"].str.contains(residencia, case=False, na=False)]
        
        if df.empty:
            return "No se encontraron facturas con los filtros especificados."
        
        total = df["importe"].sum()
        resultado = f"📋 **{len(df)} facturas encontradas** | Total: {formato_euro(total)}\n\n"
        resultado += "| Factura | Estudiante | Concepto | Importe | Estado | Vencimiento |\n"
        resultado += "|---------|------------|----------|---------|--------|-------------|\n"
        
        for _, row in df.head(20).iterrows():
            resultado += f"| {row['id_factura']} | {row['id_estudiante']} | {row['concepto'][:15]}... | {formato_euro(row['importe'])} | {row['estado']} | {row['fecha_vencimiento']} |\n"
        
        if len(df) > 20:
            resultado += f"\n*Mostrando 20 de {len(df)} facturas*"
        
        return resultado
    except Exception as e:
        return f"Error al consultar facturas: {str(e)}"


@tool
def consultar_morosos(dias_minimo: int = 1) -> str:
    """
    Obtiene listado de estudiantes con facturas vencidas (morosos).
    Según Ley 3/2004 de morosidad en operaciones comerciales.
    
    Args:
        dias_minimo: Días mínimos de retraso para considerar moroso (default: 1)
    
    Returns:
        Lista de morosos con nombre, deuda total, días de retraso, contacto
    """
    try:
        facturas = pd.read_csv(os.path.join(DATA_PATH, "facturas_emitidas.csv"))
        estudiantes = pd.read_csv(os.path.join(DATA_PATH, "estudiantes.csv"))
        
        vencidas = facturas[facturas["estado"] == "vencida"].copy()
        
        if vencidas.empty:
            return "✅ ¡Excelente! No hay estudiantes morosos. Todas las facturas están al día."
        
        vencidas["fecha_vencimiento"] = pd.to_datetime(vencidas["fecha_vencimiento"])
        vencidas["dias_retraso"] = (datetime.now() - vencidas["fecha_vencimiento"]).dt.days
        vencidas = vencidas[vencidas["dias_retraso"] >= dias_minimo]
        
        if vencidas.empty:
            return f"✅ No hay morosos con más de {dias_minimo} días de retraso."
        
        morosos = vencidas.groupby("id_estudiante").agg({
            "importe": "sum",
            "id_factura": "count",
            "dias_retraso": "max"
        }).reset_index()
        morosos.columns = ["id_estudiante", "deuda_total", "num_facturas", "max_dias_retraso"]
        morosos = morosos.merge(estudiantes, on="id_estudiante", how="left")
        morosos = morosos.sort_values("deuda_total", ascending=False)
        
        total_deuda = morosos['deuda_total'].sum()
        resultado = f"🔴 **LISTADO DE MOROSOS**\n"
        resultado += f"Total morosos: {len(morosos)} | Deuda total: {formato_euro(total_deuda)}\n\n"
        
        for _, m in morosos.head(15).iterrows():
            resultado += f"""**{m['nombre']}** ({m['id_estudiante']})
- Deuda: {formato_euro(m['deuda_total'])} ({int(m['num_facturas'])} facturas)
- Días máximo retraso: {int(m['max_dias_retraso'])}
- Residencia: {m['residencia']} - Hab. {m['habitacion']}
- Email: {m['email']}
- Teléfono: {m['telefono']}

"""
        if len(morosos) > 15:
            resultado += f"\n*Mostrando 15 de {len(morosos)} morosos*"
        
        return resultado
    except Exception as e:
        return f"Error al consultar morosos: {str(e)}"


@tool
def consultar_estudiante(id_estudiante: str) -> str:
    """
    Obtiene ficha completa de un estudiante con historial de facturación.
    
    Args:
        id_estudiante: ID del estudiante (ej: EST-0001, EST-0002)
    
    Returns:
        Ficha completa con datos personales, alojamiento y facturas
    """
    try:
        estudiantes = pd.read_csv(os.path.join(DATA_PATH, "estudiantes.csv"))
        facturas = pd.read_csv(os.path.join(DATA_PATH, "facturas_emitidas.csv"))
        
        est = estudiantes[estudiantes["id_estudiante"] == id_estudiante.upper()]
        
        if est.empty:
            return f"❌ Estudiante {id_estudiante} no encontrado. Verifica el ID."
        
        est = est.iloc[0]
        fact_est = facturas[facturas["id_estudiante"] == id_estudiante.upper()]
        
        pagadas = fact_est[fact_est["estado"] == "pagada"]["importe"].sum()
        pendientes = fact_est[fact_est["estado"] == "pendiente"]["importe"].sum()
        vencidas = fact_est[fact_est["estado"] == "vencida"]["importe"].sum()
        
        resultado = f"""## 👤 Ficha: {est['nombre']}

### Datos Personales
- **ID:** {est['id_estudiante']}
- **Email:** {est['email']}
- **Teléfono:** {est['telefono']}

### Alojamiento
- **Residencia:** {est['residencia']}
- **Habitación:** {est['habitacion']}
- **Fecha entrada:** {est['fecha_entrada']}
- **Cuota mensual:** {formato_euro(est['cuota_mensual'])}

### Resumen Financiero
| Estado | Importe |
|--------|---------|
| ✅ Pagado | {formato_euro(pagadas)} |
| 🟡 Pendiente | {formato_euro(pendientes)} |
| 🔴 Vencido | {formato_euro(vencidas)} |

### Últimas Facturas ({len(fact_est)} total)
"""
        for _, f in fact_est.tail(10).iterrows():
            icono = "✅" if f['estado'] == "pagada" else "🟡" if f['estado'] == "pendiente" else "🔴"
            resultado += f"- {icono} {f['id_factura']}: {f['concepto'][:25]} - {formato_euro(f['importe'])}\n"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def generar_aging_report() -> str:
    """
    Genera análisis de antigüedad de cuentas por cobrar (Aging Report).
    Clasifica facturas pendientes por tramos según normativa española.
    
    Returns:
        Reporte aging con importes y porcentajes por tramo
    """
    try:
        facturas = pd.read_csv(os.path.join(DATA_PATH, "facturas_emitidas.csv"))
        pendientes = facturas[facturas["estado"].isin(["pendiente", "vencida"])].copy()
        
        if pendientes.empty:
            return "✅ No hay facturas pendientes de cobro."
        
        pendientes["fecha_vencimiento"] = pd.to_datetime(pendientes["fecha_vencimiento"])
        pendientes["dias"] = (datetime.now() - pendientes["fecha_vencimiento"]).dt.days
        
        def clasificar(dias):
            if dias <= 0: return "No vencido"
            elif dias <= 30: return "1-30 días"
            elif dias <= 60: return "31-60 días"
            elif dias <= 90: return "61-90 días"
            return ">90 días"
        
        pendientes["tramo"] = pendientes["dias"].apply(clasificar)
        aging = pendientes.groupby("tramo").agg({"importe": ["sum", "count"]}).reset_index()
        aging.columns = ["tramo", "importe", "num_facturas"]
        
        total = aging["importe"].sum()
        
        resultado = f"""## 📊 AGING DE CUENTAS POR COBRAR
**Total pendiente:** {formato_euro(total)}

| Tramo | Importe | Facturas | % Total |
|-------|---------|----------|---------|
"""
        orden = ["No vencido", "1-30 días", "31-60 días", "61-90 días", ">90 días"]
        for tramo in orden:
            row = aging[aging["tramo"] == tramo]
            if not row.empty:
                imp = row["importe"].values[0]
                num = int(row["num_facturas"].values[0])
                pct = (imp / total) * 100
                icono = "🟢" if tramo == "No vencido" else "🟡" if "30" in tramo else "🟠" if "60" in tramo else "🔴"
                resultado += f"| {icono} {tramo} | {formato_euro(imp)} | {num} | {formato_porcentaje(pct)} |\n"
        
        resultado += f"| **TOTAL** | **{formato_euro(total)}** | **{len(pendientes)}** | **100%** |"
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def prevision_cobros_semanal() -> str:
    """
    Genera previsión de cobros para enviar al Tesorero.
    Lista facturas pendientes ordenadas por fecha de vencimiento.
    
    Returns:
        Previsión de cobros con fechas e importes para planificación de tesorería
    """
    try:
        facturas = pd.read_csv(os.path.join(DATA_PATH, "facturas_emitidas.csv"))
        pendientes = facturas[facturas["estado"] == "pendiente"].copy()
        pendientes["fecha_vencimiento"] = pd.to_datetime(pendientes["fecha_vencimiento"])
        pendientes = pendientes.sort_values("fecha_vencimiento")
        
        total = pendientes["importe"].sum()
        
        resultado = f"""## 📅 PREVISIÓN DE COBROS
**Para:** Tesorero | **Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Total previsto:** {formato_euro(total)}

| Fecha Venc. | Estudiante | Residencia | Importe |
|-------------|------------|------------|---------|
"""
        for _, row in pendientes.head(30).iterrows():
            resultado += f"| {row['fecha_vencimiento'].strftime('%d/%m/%Y')} | {row['id_estudiante']} | {row['residencia'][:15]} | {formato_euro(row['importe'])} |\n"
        
        if len(pendientes) > 30:
            resultado += f"\n*Mostrando 30 de {len(pendientes)} cobros previstos*"
        
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas para exportar
AR_MANAGER_TOOLS = [
    consultar_facturas,
    consultar_morosos,
    consultar_estudiante,
    generar_aging_report,
    prevision_cobros_semanal,
    buscar_normativa_fiscal
]
