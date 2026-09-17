"""Herramientas con datos macroeconómicos estáticos de demostración.

Este módulo no consulta Internet. Sus valores solo permiten probar el flujo de
herramientas del prototipo y no deben interpretarse como información vigente.
"""

from langchain_core.tools import tool
import json
from datetime import datetime

# Escenario fijo para demostrar las respuestas de los agentes sin conexión.
DEMO_NOTICE = "> ⚠️ Escenario sintético: valores no actualizados ni aptos para tomar decisiones.\n\n"
DATOS_MERCADO = {
    "euribor": {
        "1_mes": 3.042,
        "3_meses": 3.108,
        "6_meses": 3.187,
        "12_meses": 2.937,
        "fecha": "enero 2025",
        "tendencia": "bajista",
        "fuente": "dataset sintético"
    },
    "tipos_bce": {
        "tipo_principal": 4.50,
        "facilidad_deposito": 4.00,
        "facilidad_credito": 4.75,
        "fecha": "enero 2025",
        "proxima_reunion": "30 enero 2025",
        "fuente": "dataset sintético"
    },
    "hipotecas": {
        "tipo_fijo_medio": 3.25,
        "tipo_variable_medio": "Euribor + 0.99",
        "plazo_medio": 25,
        "fuente": "dataset sintético"
    },
    "iva_espana": {
        "general": 21,
        "reducido": 10,
        "superreducido": 4,
        "servicios_b2b": 10,
        "operaciones_exentas": "exento",
        "fuente": "dataset sintético"
    },
    "impuesto_sociedades": {
        "tipo_general": 25,
        "tipo_pymes": 23,
        "tipo_reducido": 15,
        "fuente": "dataset sintético"
    },
    "irpf_retenciones": {
        "rendimientos_trabajo": "según tablas",
        "rendimientos_capital": 19,
        "arrendamientos": 19,
        "profesionales": 15,
        "fuente": "dataset sintético"
    },
    "salario_minimo": {
        "smi_mensual": 1134,
        "smi_anual_14_pagas": 15876,
        "fecha": "2024",
        "fuente": "dataset sintético"
    },
    "ipc": {
        "interanual": 2.8,
        "mensual": 0.2,
        "subyacente": 3.6,
        "fecha": "diciembre 2024",
        "fuente": "dataset sintético"
    },
    "mercado_servicios": {
        "utilizacion_media_espana": 92,
        "precio_medio_mensual": 650,
        "crecimiento_anual": 5.2,
        "ciudades_top": ["Madrid", "Barcelona", "Valencia", "Sevilla"],
        "fuente": "dataset sintético"
    }
}


@tool
def buscar_tipos_interes() -> str:
    """
    Devuelve un escenario estático de tipos de interés para demostrar el prototipo.
    Útil para análisis de coste de financiación y previsiones.
    
    Returns:
        Información ficticia de tipos de interés
    """
    euribor = DATOS_MERCADO["euribor"]
    bce = DATOS_MERCADO["tipos_bce"]
    hipotecas = DATOS_MERCADO["hipotecas"]
    
    resultado = f"""## 📊 ESCENARIO DE TIPOS DE INTERÉS

### Euribor ({euribor['fecha']})
| Plazo | Tipo | Tendencia |
|-------|------|-----------|
| 1 mes | {euribor['1_mes']:.3f}% | {euribor['tendencia']} |
| 3 meses | {euribor['3_meses']:.3f}% | {euribor['tendencia']} |
| 6 meses | {euribor['6_meses']:.3f}% | {euribor['tendencia']} |
| **12 meses** | **{euribor['12_meses']:.3f}%** | {euribor['tendencia']} |

*Fuente: {euribor['fuente']}*

### Tipos BCE ({bce['fecha']})
| Tipo | Valor |
|------|-------|
| Tipo principal de refinanciación | {bce['tipo_principal']:.2f}% |
| Facilidad de depósito | {bce['facilidad_deposito']:.2f}% |
| Facilidad marginal de crédito | {bce['facilidad_credito']:.2f}% |

*Fecha ficticia del escenario: {bce['proxima_reunion']}*

### Hipotecas en España
| Tipo | Valor |
|------|-------|
| Tipo fijo medio | {hipotecas['tipo_fijo_medio']:.2f}% |
| Tipo variable medio | {hipotecas['tipo_variable_medio']} |
| Plazo medio | {hipotecas['plazo_medio']} años |

*Fuente: {hipotecas['fuente']}*

### Análisis
- El Euribor 12 meses se sitúa en {euribor['12_meses']:.3f}%, con tendencia {euribor['tendencia']}
- Para préstamos a tipo variable, el coste actual sería aproximadamente {euribor['12_meses'] + 1:.2f}% (Euribor + 1%)
- El escenario supone una tendencia bajista únicamente para probar el razonamiento.
"""
    return DEMO_NOTICE + resultado


@tool
def buscar_normativa_fiscal() -> str:
    """
    Devuelve un resumen fiscal estático para demostrar el prototipo.
    
    Returns:
        Resumen fiscal de demostración que requiere verificación oficial
    """
    iva = DATOS_MERCADO["iva_espana"]
    is_data = DATOS_MERCADO["impuesto_sociedades"]
    irpf = DATOS_MERCADO["irpf_retenciones"]
    
    resultado = f"""## ⚖️ ESCENARIO FISCAL DE DEMOSTRACIÓN

### IVA (Ley 37/1992)
| Tipo | Porcentaje | Aplicación |
|------|------------|------------|
| General | {iva['general']}% | Servicios y bienes en general |
| Reducido | {iva['reducido']}% | Servicios, hostelería, transporte |
| Superreducido | {iva['superreducido']}% | Alimentos básicos, libros, medicamentos |

**Valores utilizados por el escenario:**
- Servicio de ejemplo: **{iva['servicios_b2b']}%**
- Operación exenta de ejemplo: **{iva['operaciones_exentas']}**

### Impuesto de Sociedades (Ley 27/2014)
| Tipo | Porcentaje |
|------|------------|
| General | {is_data['tipo_general']}% |
| PYMES (cifra negocios < 1M€) | {is_data['tipo_pymes']}% |
| Empresas nueva creación (2 primeros años) | {is_data['tipo_reducido']}% |

### Retenciones IRPF
| Concepto | Retención |
|----------|-----------|
| Rendimientos del capital mobiliario | {irpf['rendimientos_capital']}% |
| Arrendamientos inmuebles | {irpf['arrendamientos']}% |
| Profesionales | {irpf['profesionales']}% |

*Fuente: dataset sintético; requiere verificación oficial.*
"""
    return DEMO_NOTICE + resultado


@tool
def buscar_mercado_servicios() -> str:
    """
    Devuelve un escenario estático de mercado para el caso B2B.
    
    Returns:
        Análisis del mercado de servicios B2B
    """
    mercado = DATOS_MERCADO["mercado_servicios"]
    ipc = DATOS_MERCADO["ipc"]
    
    resultado = f"""## 🏠 MERCADO UNIDADES CLIENTES ESPAÑA

### Indicadores del sector
| Métrica | Valor |
|---------|-------|
| Utilización media nacional | {mercado['utilizacion_media_espana']}% |
| Precio medio mensual | {mercado['precio_medio_mensual']}€/mes |
| Crecimiento interanual | +{mercado['crecimiento_anual']}% |

### Ciudades principales
Las ciudades con mayor demanda de servicios empresariales:
1. **Madrid** - Mayor mercado, utilización ~95%
2. **Barcelona** - Alta demanda internacional
3. **Valencia** - Crecimiento acelerado
4. **Sevilla** - Mercado en expansión

### Contexto económico
| Indicador | Valor |
|-----------|-------|
| IPC interanual | {ipc['interanual']}% |
| IPC subyacente | {ipc['subyacente']}% |

### Hipótesis del escenario
- Continúa la profesionalización del sector
- Creciente inversión de fondos institucionales
- Aumento de la demanda de clientes internacionales
- Presión alcista en precios por falta de oferta

*Fuente: {mercado['fuente']}*
"""
    return DEMO_NOTICE + resultado


@tool  
def buscar_indicadores_economicos() -> str:
    """
    Obtiene indicadores económicos de España: IPC, SMI, tipos de interés.
    
    Returns:
        Resumen de indicadores económicos actuales
    """
    ipc = DATOS_MERCADO["ipc"]
    smi = DATOS_MERCADO["salario_minimo"]
    euribor = DATOS_MERCADO["euribor"]
    
    resultado = f"""## 📈 INDICADORES ECONÓMICOS ESPAÑA

### Inflación (IPC) - {ipc['fecha']}
| Indicador | Valor |
|-----------|-------|
| IPC interanual | {ipc['interanual']}% |
| IPC mensual | {ipc['mensual']}% |
| IPC subyacente | {ipc['subyacente']}% |

*Fuente: {ipc['fuente']}*

### Salario Mínimo Interprofesional (SMI) - {smi['fecha']}
| Concepto | Importe |
|----------|---------|
| SMI mensual (14 pagas) | {smi['smi_mensual']:,}€ |
| SMI anual | {smi['smi_anual_14_pagas']:,}€ |

*Fuente: {smi['fuente']}*

### Tipos de interés de referencia
| Indicador | Valor |
|-----------|-------|
| Euribor 12 meses | {euribor['12_meses']:.3f}% |
| Tendencia | {euribor['tendencia']} |

### Uso del escenario
- Comparar sensibilidad del coste financiero.
- Probar consultas del agente sin depender de una API externa.
- Validar el formato de respuesta; no validar cifras de mercado.
"""
    return DEMO_NOTICE + resultado


@tool
def consultar_referencia_fiscal(tema: str) -> str:
    """Devuelve una referencia fiscal estática para probar el agente.

    No realiza una consulta al BOE ni a la AEAT. La salida recuerda al usuario
    que debe verificar normativa, tipos y plazos en las fuentes oficiales.
    """

    return (
        DEMO_NOTICE
        + "## Referencia fiscal de demostración\n\n"
        + f"Tema solicitado: **{tema}**.\n\n"
        + "El prototipo puede recuperar contexto de los documentos locales, "
        + "pero no comprueba cambios normativos en tiempo real. Verifica el "
        + "resultado en la AEAT y el BOE antes de utilizarlo."
    )


# Lista de herramientas de búsqueda web
WEB_SEARCH_TOOLS = [
    buscar_tipos_interes,
    buscar_normativa_fiscal,
    buscar_mercado_servicios,
    buscar_indicadores_economicos,
    consultar_referencia_fiscal
]
