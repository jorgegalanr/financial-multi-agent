"""
Herramientas del Fiscalista.
Obligaciones fiscales, IVA, IRPF e Impuesto de Sociedades.
Normativa tributaria española (Ley 37/1992 IVA, Ley 27/2014 IS).
Formato EUR (1.234,56€).
"""

from langchain_core.tools import tool
import pandas as pd
import os
from .utils import formato_euro, formato_numero, formato_porcentaje
from .web_tools import buscar_normativa_fiscal, consultar_boe_aeat

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

@tool
def consultar_obligaciones_fiscales() -> str:
    """
    Consulta las obligaciones fiscales pendientes según calendario de la AEAT.
    Modelos: 303 (IVA), 111 (retenciones), 200 (IS), etc.
    
    Returns:
        Calendario de obligaciones fiscales con modelos, fechas y estados
    """
    try:
        df = pd.read_csv(os.path.join(DATA_PATH, "obligaciones_fiscales.csv"))
        
        resultado = """## ⚖️ OBLIGACIONES FISCALES (AEAT)

| Modelo | Concepto | Período | Fecha Límite | Estado | Importe Est. |
|--------|----------|---------|--------------|--------|--------------|
"""
        for _, row in df.iterrows():
            estado = str(row['estado']).lower()
            icono = "✅" if estado == "presentado" else "🟡" if estado in ["pendiente", "pdte"] else "🔴"
            resultado += f"| {row['modelo']} | {row['concepto']} | {row['periodo']} | {row['fecha_limite']} | {icono} {row['estado']} | {formato_euro(row['importe_estimado'])} |\n"
        
        resultado += """
### Calendario AEAT 2025
- **Mod. 303 (IVA):** Trimestral, del 1-20 del mes siguiente
- **Mod. 111 (Retenciones):** Trimestral, del 1-20 del mes siguiente
- **Mod. 200 (IS):** Anual, hasta 25 de julio
- **Mod. 390 (Resumen IVA):** Anual, del 1-30 de enero
"""
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def calcular_liquidacion_iva() -> str:
    """
    Calcula la liquidación de IVA trimestral (Modelo 303).
    Según Ley 37/1992 del IVA.
    Tipos: General 21%, Reducido 10%, Superreducido 4%.
    
    Returns:
        Cálculo de IVA: repercutido - soportado = resultado a ingresar/compensar
    """
    try:
        soportado = pd.read_csv(os.path.join(DATA_PATH, "iva_soportado.csv"))
        repercutido = pd.read_csv(os.path.join(DATA_PATH, "iva_repercutido.csv"))
        
        # Detectar nombres de columnas (flexibilidad)
        def get_col(df, options):
            for opt in options:
                if opt in df.columns:
                    return opt
            return options[0]
        
        col_cuota = get_col(soportado, ['cuota_iva', 'cuota', 'iva', 'cuota_IVA'])
        col_base = get_col(soportado, ['base_imponible', 'base', 'base_imp'])
        col_tipo = get_col(soportado, ['tipo_iva', 'tipo', 'tipo_IVA', 'porcentaje'])
        
        total_soportado = soportado[col_cuota].sum()
        total_repercutido = repercutido[col_cuota].sum()
        resultado_iva = total_repercutido - total_soportado
        
        resultado = f"""## 📋 LIQUIDACIÓN IVA (Modelo 303)
**Según Ley 37/1992 del IVA**
**Período:** 4º Trimestre 2025

### IVA Repercutido (ventas)
| Concepto | Base Imponible | Tipo | Cuota IVA |
|----------|----------------|------|-----------|
"""
        for _, row in repercutido.iterrows():
            base = row.get(col_base, 0)
            tipo = row.get(col_tipo, 0)
            cuota = row.get(col_cuota, 0)
            resultado += f"| {row['concepto']} | {formato_euro(base)} | {formato_porcentaje(tipo)} | {formato_euro(cuota)} |\n"
        resultado += f"| **TOTAL** | | | **{formato_euro(total_repercutido)}** |\n"

        resultado += f"""
### IVA Soportado Deducible (compras)
| Concepto | Base Imponible | Tipo | Cuota IVA |
|----------|----------------|------|-----------|
"""
        for _, row in soportado.iterrows():
            base = row.get(col_base, 0)
            tipo = row.get(col_tipo, 0)
            cuota = row.get(col_cuota, 0)
            resultado += f"| {row['concepto']} | {formato_euro(base)} | {formato_porcentaje(tipo)} | {formato_euro(cuota)} |\n"
        resultado += f"| **TOTAL** | | | **{formato_euro(total_soportado)}** |\n"

        tipo_resultado = "A INGRESAR" if resultado_iva > 0 else "A COMPENSAR"
        icono = "💰" if resultado_iva > 0 else "📥"
        
        resultado += f"""
### RESULTADO LIQUIDACIÓN
| Concepto | Importe |
|----------|---------|
| IVA Repercutido | +{formato_euro(total_repercutido)} |
| IVA Soportado | -{formato_euro(total_soportado)} |
| **{icono} {tipo_resultado}** | **{formato_euro(abs(resultado_iva))}** |

### Tipos de IVA vigentes en España
- **General:** 21% (servicios, bienes en general)
- **Reducido:** 10% (alojamiento, hostelería, transporte)
- **Superreducido:** 4% (alimentos básicos, libros, medicamentos)
"""
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas para exportar
FISCALISTA_TOOLS = [
    consultar_obligaciones_fiscales,
    calcular_liquidacion_iva,
    buscar_normativa_fiscal,
    consultar_boe_aeat
]
