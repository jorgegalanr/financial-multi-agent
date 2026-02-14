"""
Módulo RAG para búsqueda de normativa fiscal y contable.
"""

from .rag_system import (
    RAGSystem,
    rag_system,
    RAG_TOOLS,
    buscar_normativa,
    buscar_procedimiento_cobros,
    consultar_normativa_iva
)

__all__ = [
    "RAGSystem",
    "rag_system",
    "RAG_TOOLS",
    "buscar_normativa",
    "buscar_procedimiento_cobros",
    "consultar_normativa_iva"
]
