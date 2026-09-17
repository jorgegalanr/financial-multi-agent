"""Reglas deterministas para enrutar consultas financieras."""

from __future__ import annotations


AGENT_KEYS = {
    "director_financiero",
    "ar_manager",
    "tesorero",
    "controller",
    "fpa_analyst",
    "fiscalista",
    "gestor_activos",
}


ROUTING_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "director_financiero",
        (
            "consejo",
            "resumen",
            "ejecutivo",
            "dashboard",
            "estado general",
            "situación financiera",
            "estrategia",
            "global",
        ),
    ),
    (
        "controller",
        (
            "balance",
            "cuenta de resultados",
            "pérdidas",
            "ganancias",
            "ratios",
            "contable",
            "margen",
        ),
    ),
    (
        "ar_manager",
        (
            "cobros",
            "morosos",
            "facturas",
            "clientes",
            "deuda cliente",
            "aging",
            "impagados",
        ),
    ),
    (
        "tesorero",
        (
            "caja",
            "bancos",
            "liquidez",
            "pagos",
            "deuda bancaria",
            "préstamos",
            "dinero",
        ),
    ),
    (
        "fiscalista",
        ("impuestos", "iva", "hacienda", "aeat", "modelo", "fiscal", "tributar"),
    ),
    (
        "fpa_analyst",
        ("presupuesto", "forecast", "previsión", "desviación", "escenario"),
    ),
    (
        "gestor_activos",
        ("activo fijo", "activos", "amortización", "mantenimiento", "inventario"),
    ),
)


def select_agent(query: str, forced_agent: str | None = None) -> str | None:
    """Devuelve un agente forzado o la primera coincidencia determinista.

    Si ninguna regla coincide, devuelve ``None`` para que el supervisor pueda
    solicitar una clasificación al modelo de lenguaje.
    """

    if forced_agent and forced_agent != "auto":
        if forced_agent not in AGENT_KEYS:
            raise ValueError(f"Agente no válido: {forced_agent}")
        return forced_agent

    normalized_query = query.casefold()
    for agent, keywords in ROUTING_RULES:
        if any(keyword in normalized_query for keyword in keywords):
            return agent
    return None
