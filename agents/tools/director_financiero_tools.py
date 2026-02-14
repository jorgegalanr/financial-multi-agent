"""
Herramientas del Director Financiero (CFO).
Dashboard ejecutivo, resúmenes y análisis estratégico.
Normativa española y formato EUR (1.234,56€).
"""

from langchain_core.tools import tool
from .web_tools import buscar_tipos_interes, buscar_mercado_residencias, buscar_indicadores_economicos
import pandas as pd
import os
from datetime import datetime
from .utils import formato_euro, formato_numero, formato_porcentaje

# Configuración
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

@tool
def generar_dashboard_ejecutivo() -> str:
    """
    Genera un dashboard ejecutivo con los principales indicadores financieros.
    Visión consolidada para el Consejo de Administración.
    
    Returns:
        Resumen ejecutivo con KPIs, alertas y recomendaciones
    """
    try:
        # Cargar todos los datos necesarios
        caja = pd.read_csv(os.path.join(DATA_PATH, "posicion_caja.csv"))
        facturas = pd.read_csv(os.path.join(DATA_PATH, "facturas_emitidas.csv"))
        ocupacion = pd.read_csv(os.path.join(DATA_PATH, "ocupacion.csv"))
        deuda = pd.read_csv(os.path.join(DATA_PATH, "deuda_bancaria.csv"))
        kpis = pd.read_csv(os.path.join(DATA_PATH, "kpis.csv"))
        
        # Calcular métricas
        saldo_caja = caja["saldo"].sum()
        
        total_facturado = facturas["importe"].sum()
        cobrado = facturas[facturas["estado"] == "pagada"]["importe"].sum()
        pendiente = facturas[facturas["estado"] == "pendiente"]["importe"].sum()
        vencido = facturas[facturas["estado"] == "vencida"]["importe"].sum()
        
        total_plazas = ocupacion["capacidad"].sum()
        plazas_ocupadas = ocupacion["ocupacion_actual"].sum()
        pct_ocupacion = (plazas_ocupadas / total_plazas * 100) if total_plazas > 0 else 0
        
        deuda_total = deuda["capital_pendiente"].sum()
        cuota_mensual = deuda["cuota_mensual"].sum()
        
        tasa_morosidad = (vencido / total_facturado * 100) if total_facturado > 0 else 0
        
        resultado = f"""## 📊 DASHBOARD EJECUTIVO
**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Empresa:** Grupo Residencias Estudiantiles, S.L.

---

### 💰 POSICIÓN FINANCIERA
| Indicador | Valor | Estado |
|-----------|-------|--------|
| Saldo en caja | {formato_euro(saldo_caja)} | {"🟢" if saldo_caja > 500000 else "🟡" if saldo_caja > 200000 else "🔴"} |
| Deuda bancaria total | {formato_euro(deuda_total)} | ℹ️ |
| Cuota mensual deuda | {formato_euro(cuota_mensual)} | ℹ️ |

### 📈 FACTURACIÓN (Ejercicio 2025)
| Concepto | Importe | % |
|----------|---------|---|
| Total facturado | {formato_euro(total_facturado)} | 100% |
| ✅ Cobrado | {formato_euro(cobrado)} | {formato_porcentaje(cobrado/total_facturado*100 if total_facturado > 0 else 0)} |
| 🟡 Pendiente | {formato_euro(pendiente)} | {formato_porcentaje(pendiente/total_facturado*100 if total_facturado > 0 else 0)} |
| 🔴 Vencido | {formato_euro(vencido)} | {formato_porcentaje(vencido/total_facturado*100 if total_facturado > 0 else 0)} |

### 🏠 OCUPACIÓN
| Indicador | Valor |
|-----------|-------|
| Plazas totales | {total_plazas} |
| Plazas ocupadas | {plazas_ocupadas} |
| **Ocupación** | **{formato_porcentaje(pct_ocupacion)}** {"🟢" if pct_ocupacion >= 90 else "🟡" if pct_ocupacion >= 80 else "🔴"} |

### ⚠️ ALERTAS
| Indicador | Valor | Estado |
|-----------|-------|--------|
| Tasa de morosidad | {formato_porcentaje(tasa_morosidad)} | {"🟢" if tasa_morosidad < 3 else "🟡" if tasa_morosidad < 5 else "🔴"} |
| Ratio liquidez | {formato_numero(saldo_caja / cuota_mensual if cuota_mensual > 0 else 0, 1)} meses | {"🟢" if saldo_caja > cuota_mensual * 4 else "🟡" if saldo_caja > cuota_mensual * 2 else "🔴"} |

### 📋 KPIs CLAVE
"""
        for _, kpi in kpis.iterrows():
            unidad = kpi.get('unidad', '')
            valor = kpi['valor']
            if unidad == '€':
                valor_fmt = formato_euro(valor)
            elif unidad == '%':
                valor_fmt = formato_porcentaje(valor)
            else:
                valor_fmt = f"{formato_numero(valor, 1)} {unidad}"
            resultado += f"- **{kpi['nombre']}:** {valor_fmt}\n"
        
        return resultado
    except Exception as e:
        return f"Error generando dashboard: {str(e)}"


@tool
def resumen_para_consejo() -> str:
    """
    Genera un resumen ejecutivo para presentar al Consejo de Administración.
    
    Returns:
        Informe resumido con puntos clave y recomendaciones
    """
    try:
        # Cargar datos
        balance = pd.read_csv(os.path.join(DATA_PATH, "balance.csv"))
        pyg = pd.read_csv(os.path.join(DATA_PATH, "cuenta_resultados.csv"))
        ocupacion = pd.read_csv(os.path.join(DATA_PATH, "ocupacion.csv"))
        
        # Normalizar tipos
        def norm_tipo(t):
            t = str(t).lower()
            if t in ['act', 'activo']: return 'activo'
            if t in ['pas', 'pasivo']: return 'pasivo'
            if t in ['ing', 'ingreso']: return 'ingreso'
            return t
        
        balance['tipo_norm'] = balance['tipo'].apply(norm_tipo)
        pyg['tipo_norm'] = pyg['tipo'].apply(norm_tipo)
        
        activo = balance[balance['tipo_norm'] == 'activo']['importe'].sum()
        pasivo = balance[balance['tipo_norm'] == 'pasivo']['importe'].sum()
        patrimonio = activo - pasivo
        
        ingresos = pyg[pyg['tipo_norm'] == 'ingreso']['importe'].sum()
        
        total_plazas = ocupacion['capacidad'].sum()
        ocupadas = ocupacion['ocupacion_actual'].sum()
        
        resultado = f"""## 📋 INFORME PARA CONSEJO DE ADMINISTRACIÓN
**Fecha:** {datetime.now().strftime('%d/%m/%Y')}
**Ejercicio:** 2025

---

### SITUACIÓN PATRIMONIAL
La empresa presenta una situación financiera **sólida**:
- **Activo Total:** {formato_euro(activo)}
- **Pasivo Total:** {formato_euro(pasivo)}
- **Patrimonio Neto:** {formato_euro(patrimonio)}
- **Ratio de solvencia:** {formato_porcentaje(patrimonio/activo*100 if activo > 0 else 0)}

### RESULTADOS
- **Ingresos ejercicio:** {formato_euro(ingresos)}
- **Previsión anual:** En línea con presupuesto

### OPERACIONES
- **Residencias operativas:** {len(ocupacion)}
- **Capacidad total:** {total_plazas} plazas
- **Ocupación actual:** {ocupadas} plazas ({formato_porcentaje(ocupadas/total_plazas*100 if total_plazas > 0 else 0)})

### RECOMENDACIONES
1. Mantener política de cobro activa para reducir morosidad
2. Continuar con plan de mantenimiento preventivo
3. Evaluar expansión según evolución del mercado

---
*Informe generado automáticamente por el Sistema Financiero Multi-Agente*
"""
        return resultado
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas para exportar
DIRECTOR_FINANCIERO_TOOLS = [
    generar_dashboard_ejecutivo,
    resumen_para_consejo,
    buscar_tipos_interes, buscar_mercado_residencias, buscar_indicadores_economicos
]
