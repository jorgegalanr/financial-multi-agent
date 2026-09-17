"""
Módulo de herramientas para los agentes financieros.
Cada agente tiene su archivo de herramientas separado.
"""

from .ar_manager_tools import (
    AR_MANAGER_TOOLS,
    consultar_facturas,
    consultar_morosos,
    consultar_cliente,
    generar_aging_report,
    prevision_cobros_semanal
)

from .tesorero_tools import (
    TESORERO_TOOLS,
    consultar_posicion_caja,
    consultar_pagos_pendientes,
    consultar_deuda_bancaria,
    consultar_gastos_fijos,
    analisis_liquidez
)

from .controller_tools import (
    CONTROLLER_TOOLS,
    consultar_balance,
    consultar_cuenta_resultados,
    calcular_ratios_financieros
)

from .fpa_analyst_tools import (
    FPA_ANALYST_TOOLS,
    consultar_utilizacion,
    consultar_kpis,
    analisis_desviaciones
)

from .fiscalista_tools import (
    FISCALISTA_TOOLS,
    consultar_obligaciones_fiscales,
    calcular_liquidacion_iva
)

from .gestor_activos_tools import (
    GESTOR_ACTIVOS_TOOLS,
    consultar_activos_fijos,
    calcular_amortizacion_mensual,
    consultar_mantenimientos
)

from .director_financiero_tools import (
    DIRECTOR_FINANCIERO_TOOLS,
    generar_dashboard_ejecutivo,
    resumen_para_consejo
)

from .web_tools import (
    WEB_SEARCH_TOOLS,
    buscar_tipos_interes,
    buscar_normativa_fiscal,
    buscar_mercado_servicios,
    buscar_indicadores_economicos,
    consultar_referencia_fiscal
)

# Alias por compatibilidad (agents/__init__.py esperaba "web_search")
web_search = WEB_SEARCH_TOOLS

# Mapeo de herramientas por agente
AGENT_TOOLS = {
    "director_financiero": DIRECTOR_FINANCIERO_TOOLS,
    "ar_manager": AR_MANAGER_TOOLS,
    "tesorero": TESORERO_TOOLS,
    "controller": CONTROLLER_TOOLS,
    "fpa_analyst": FPA_ANALYST_TOOLS,
    "fiscalista": FISCALISTA_TOOLS,
    "gestor_activos": GESTOR_ACTIVOS_TOOLS
}


def get_tools_for_agent(agent_key: str) -> list:
    """
    Obtiene las herramientas disponibles para un agente específico.
    
    Args:
        agent_key: Identificador del agente
    
    Returns:
        Lista de herramientas del agente
    """
    # Devolver una copia evita que el grafo añada RAG/MCP sobre la lista global
    # y duplique herramientas en consultas posteriores.
    return list(AGENT_TOOLS.get(agent_key, WEB_SEARCH_TOOLS))
