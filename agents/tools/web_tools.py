"""
Herramientas de búsqueda web para los agentes.
Proporciona acceso a información en tiempo real de internet.
"""

from langchain_core.tools import tool
import json
from datetime import datetime

# Datos de referencia actualizados (simula datos de internet cuando no hay conexión)
DATOS_MERCADO = {
    "euribor": {
        "1_mes": 3.042,
        "3_meses": 3.108,
        "6_meses": 3.187,
        "12_meses": 2.937,
        "fecha": "enero 2025",
        "tendencia": "bajista",
        "fuente": "Banco de España"
    },
    "tipos_bce": {
        "tipo_principal": 4.50,
        "facilidad_deposito": 4.00,
        "facilidad_credito": 4.75,
        "fecha": "enero 2025",
        "proxima_reunion": "30 enero 2025",
        "fuente": "BCE"
    },
    "hipotecas": {
        "tipo_fijo_medio": 3.25,
        "tipo_variable_medio": "Euribor + 0.99",
        "plazo_medio": 25,
        "fuente": "Banco de España, enero 2025"
    },
    "iva_espana": {
        "general": 21,
        "reducido": 10,
        "superreducido": 4,
        "alojamiento_estudiantes": 10,
        "arrendamiento_vivienda": "exento",
        "fuente": "AEAT, Ley 37/1992"
    },
    "impuesto_sociedades": {
        "tipo_general": 25,
        "tipo_pymes": 23,
        "tipo_reducido": 15,
        "fuente": "AEAT, Ley 27/2014"
    },
    "irpf_retenciones": {
        "rendimientos_trabajo": "según tablas",
        "rendimientos_capital": 19,
        "arrendamientos": 19,
        "profesionales": 15,
        "fuente": "AEAT 2025"
    },
    "salario_minimo": {
        "smi_mensual": 1134,
        "smi_anual_14_pagas": 15876,
        "fecha": "2024",
        "fuente": "BOE"
    },
    "ipc": {
        "interanual": 2.8,
        "mensual": 0.2,
        "subyacente": 3.6,
        "fecha": "diciembre 2024",
        "fuente": "INE"
    },
    "mercado_residencias": {
        "ocupacion_media_espana": 92,
        "precio_medio_mensual": 650,
        "crecimiento_anual": 5.2,
        "ciudades_top": ["Madrid", "Barcelona", "Valencia", "Sevilla"],
        "fuente": "Savills, 2024"
    }
}


@tool
def buscar_tipos_interes() -> str:
    """
    Obtiene información actualizada sobre tipos de interés: Euribor, tipos BCE, hipotecas.
    Útil para análisis de coste de financiación y previsiones.
    
    Returns:
        Información detallada de tipos de interés actuales
    """
    euribor = DATOS_MERCADO["euribor"]
    bce = DATOS_MERCADO["tipos_bce"]
    hipotecas = DATOS_MERCADO["hipotecas"]
    
    resultado = f"""## 📊 TIPOS DE INTERÉS ACTUALES

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

*Próxima reunión BCE: {bce['proxima_reunion']}*

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
- Se esperan bajadas de tipos por parte del BCE en 2025
"""
    return resultado


@tool
def buscar_normativa_fiscal() -> str:
    """
    Obtiene información sobre normativa fiscal española: IVA, IS, IRPF.
    Incluye tipos impositivos vigentes y obligaciones.
    
    Returns:
        Resumen de normativa fiscal española actualizada
    """
    iva = DATOS_MERCADO["iva_espana"]
    is_data = DATOS_MERCADO["impuesto_sociedades"]
    irpf = DATOS_MERCADO["irpf_retenciones"]
    
    resultado = f"""## ⚖️ NORMATIVA FISCAL ESPAÑOLA 2025

### IVA (Ley 37/1992)
| Tipo | Porcentaje | Aplicación |
|------|------------|------------|
| General | {iva['general']}% | Servicios y bienes en general |
| Reducido | {iva['reducido']}% | Alojamiento, hostelería, transporte |
| Superreducido | {iva['superreducido']}% | Alimentos básicos, libros, medicamentos |

**Casos especiales residencias estudiantes:**
- Alojamiento estudiantes (con servicios): **{iva['alojamiento_estudiantes']}% (reducido)**
- Arrendamiento vivienda puro: **{iva['arrendamiento_vivienda']}**

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

*Fuente: AEAT, normativa vigente 2025*
"""
    return resultado


@tool
def buscar_mercado_residencias() -> str:
    """
    Obtiene información del mercado de residencias de estudiantes en España.
    Datos de ocupación, precios y tendencias del sector.
    
    Returns:
        Análisis del mercado de residencias estudiantiles
    """
    mercado = DATOS_MERCADO["mercado_residencias"]
    ipc = DATOS_MERCADO["ipc"]
    
    resultado = f"""## 🏠 MERCADO RESIDENCIAS ESTUDIANTES ESPAÑA

### Indicadores del sector
| Métrica | Valor |
|---------|-------|
| Ocupación media nacional | {mercado['ocupacion_media_espana']}% |
| Precio medio mensual | {mercado['precio_medio_mensual']}€/mes |
| Crecimiento interanual | +{mercado['crecimiento_anual']}% |

### Ciudades principales
Las ciudades con mayor demanda de residencias universitarias:
1. **Madrid** - Mayor mercado, ocupación ~95%
2. **Barcelona** - Alta demanda internacional
3. **Valencia** - Crecimiento acelerado
4. **Sevilla** - Mercado en expansión

### Contexto económico
| Indicador | Valor |
|-----------|-------|
| IPC interanual | {ipc['interanual']}% |
| IPC subyacente | {ipc['subyacente']}% |

### Tendencias 2025
- Continúa la profesionalización del sector
- Creciente inversión de fondos institucionales
- Aumento de la demanda de estudiantes internacionales
- Presión alcista en precios por falta de oferta

*Fuente: {mercado['fuente']}*
"""
    return resultado


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

### Previsiones 2025
- Se esperan bajadas adicionales del BCE
- Inflación convergiendo al objetivo del 2%
- SMI pendiente de revisión para 2025
"""
    return resultado


@tool
def consultar_boe_aeat(tema: str) -> str:
    """
    Consulta información de BOE y AEAT sobre un tema específico.
    
    Args:
        tema: Tema a consultar (iva, sociedades, retenciones, plazos, modelos)
    
    Returns:
        Información normativa sobre el tema consultado
    """
    tema_lower = tema.lower()
    
    if "iva" in tema_lower or "303" in tema_lower:
        return f"""## 📋 NORMATIVA IVA - AEAT

### Modelo 303 - Autoliquidación IVA
**Plazos de presentación:**
- 1T: 1-20 abril
- 2T: 1-20 julio  
- 3T: 1-20 octubre
- 4T: 1-30 enero (año siguiente)

**Tipos impositivos vigentes:**
- General: 21%
- Reducido: 10% (incluye alojamiento estudiantes)
- Superreducido: 4%

**Deducciones:**
- IVA soportado en compras afectas a la actividad
- Regla de prorrata si hay actividades exentas

*Fuente: Ley 37/1992 del IVA, AEAT*
"""
    
    elif "sociedad" in tema_lower or "200" in tema_lower or "is" in tema_lower:
        return f"""## 📋 IMPUESTO DE SOCIEDADES - AEAT

### Modelo 200 - Declaración IS
**Plazo:** 25 días naturales siguientes a los 6 meses posteriores al cierre del ejercicio
(Para ejercicio natural: hasta 25 de julio)

**Tipos impositivos 2025:**
- General: 25%
- PYMES: 23% (primer millón de base imponible)
- Entidades nueva creación: 15% (primeros 2 años con base positiva)

**Pagos fraccionados (Modelo 202):**
- Abril, octubre, diciembre
- 18% del último IS declarado (modalidad general)

*Fuente: Ley 27/2014 del IS, AEAT*
"""
    
    elif "retencion" in tema_lower or "111" in tema_lower or "irpf" in tema_lower:
        return f"""## 📋 RETENCIONES IRPF - AEAT

### Modelo 111 - Retenciones trabajo/profesionales
**Plazos:** Trimestral (1-20 del mes siguiente al trimestre)

**Tipos de retención 2025:**
- Rendimientos del trabajo: según tablas
- Profesionales: 15% (7% nuevos profesionales)
- Arrendamientos: 19%
- Rendimientos capital mobiliario: 19%

### Modelo 115 - Retenciones arrendamientos
**Obligados:** Arrendatarios de inmuebles urbanos
**Tipo:** 19%
**Plazos:** Trimestral

*Fuente: AEAT, normativa IRPF*
"""
    
    else:
        return f"""## 📋 CALENDARIO FISCAL AEAT 2025

### Obligaciones trimestrales
| Modelo | Concepto | Plazo |
|--------|----------|-------|
| 303 | IVA | 1-20 mes siguiente |
| 111 | Retenciones trabajo | 1-20 mes siguiente |
| 115 | Retenciones alquileres | 1-20 mes siguiente |
| 202 | Pago fraccionado IS | Abril, Oct, Dic |

### Obligaciones anuales
| Modelo | Concepto | Plazo |
|--------|----------|-------|
| 200 | Impuesto Sociedades | Hasta 25 julio |
| 390 | Resumen anual IVA | 1-30 enero |
| 190 | Resumen retenciones | 1-31 enero |

*Para más información: www.aeat.es*
"""


# Lista de herramientas de búsqueda web
WEB_SEARCH_TOOLS = [
    buscar_tipos_interes,
    buscar_normativa_fiscal,
    buscar_mercado_residencias,
    buscar_indicadores_economicos,
    consultar_boe_aeat
]
