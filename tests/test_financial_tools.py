from agents.tools.ar_manager_tools import generar_aging_report
from agents.tools.controller_tools import consultar_balance
from agents.tools.tesorero_tools import consultar_posicion_caja
from rag.rag_system import RAGSystem


def test_core_financial_tools_return_expected_sections():
    assert "AGING" in generar_aging_report.invoke({})
    assert "BALANCE" in consultar_balance.invoke({})
    assert "POSICIÓN DE CAJA" in consultar_posicion_caja.invoke({})


def test_rag_returns_source_metadata():
    rag = RAGSystem()
    results = rag.search("clientes vencidos aging deterioro", k=3)

    assert results
    assert all(result["fuente"].endswith(".md") for result in results)
    assert all(result["contenido"] for result in results)
