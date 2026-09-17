import pytest

from graphs.routing import select_agent


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Muéstrame la posición de caja y la liquidez", "tesorero"),
        ("Necesito el aging de clientes morosos", "ar_manager"),
        ("Analiza el balance y el margen", "controller"),
        ("Compara presupuesto y forecast", "fpa_analyst"),
        ("Calcula la amortización de los activos", "gestor_activos"),
        ("¿Cuándo se presenta el IVA?", "fiscalista"),
        ("Prepara un resumen ejecutivo", "director_financiero"),
    ],
)
def test_routes_known_financial_queries(query, expected):
    assert select_agent(query) == expected


def test_manual_agent_selection_has_priority():
    assert select_agent("Muéstrame la caja", "controller") == "controller"


def test_unknown_query_delegates_to_llm():
    assert select_agent("Ayúdame con este asunto") is None


def test_invalid_manual_agent_is_rejected():
    with pytest.raises(ValueError, match="Agente no válido"):
        select_agent("consulta", "agente_inexistente")
