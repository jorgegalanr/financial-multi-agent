"""
Sistema RAG (Retrieval-Augmented Generation) simplificado.
Utiliza BM25 para búsqueda léxica - NO requiere ChromaDB.
Compatible con Windows sin Visual C++ Build Tools.
"""

import os
from typing import List, Dict, Any
from langchain_core.tools import tool

# Configuración de rutas
RAG_PATH = os.path.dirname(__file__)
DOCS_PATH = os.path.join(RAG_PATH, "documentos")


class RAGSystem:
    """Sistema RAG simplificado con BM25 (sin dependencias compiladas)."""
    
    def __init__(self):
        self.documents = []
        self.doc_contents = []
        self.bm25 = None
        self._initialized = False
        self._init_error = None
    
    def initialize(self):
        """Inicializa el sistema RAG cargando documentos."""
        if self._initialized:
            return True
        
        if self._init_error:
            return False
        
        try:
            print("🔄 Inicializando sistema RAG...")
            
            # Imports
            from rank_bm25 import BM25Okapi
            
            # 1. Cargar documentos manualmente
            print(f"📂 Cargando documentos desde {DOCS_PATH}")
            self.documents = []
            self.doc_contents = []
            
            for filename in os.listdir(DOCS_PATH):
                if filename.endswith('.md'):
                    filepath = os.path.join(DOCS_PATH, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Dividir en chunks por secciones
                            chunks = self._split_document(content, filename)
                            self.documents.extend(chunks)
                    except Exception as e:
                        print(f"Error leyendo {filename}: {e}")
            
            print(f"📄 {len(self.documents)} chunks creados")
            
            # 2. Crear índice BM25
            print("📊 Creando índice BM25...")
            self.doc_contents = [doc['contenido'] for doc in self.documents]
            tokenized_docs = [doc.lower().split() for doc in self.doc_contents]
            self.bm25 = BM25Okapi(tokenized_docs)
            
            self._initialized = True
            print("✅ Sistema RAG inicializado correctamente")
            return True
            
        except Exception as e:
            self._init_error = str(e)
            print(f"❌ Error inicializando RAG: {e}")
            return False
    
    def _split_document(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Divide un documento en chunks."""
        chunks = []
        
        # Dividir por secciones (##)
        sections = content.split('\n## ')
        
        for i, section in enumerate(sections):
            if section.strip():
                # Limpiar y limitar tamaño
                text = section.strip()
                if i > 0:
                    text = '## ' + text
                
                # Dividir secciones largas
                if len(text) > 600:
                    parts = text.split('\n\n')
                    current_chunk = ""
                    for part in parts:
                        if len(current_chunk) + len(part) < 600:
                            current_chunk += part + "\n\n"
                        else:
                            if current_chunk:
                                chunks.append({
                                    'contenido': current_chunk.strip(),
                                    'fuente': filename
                                })
                            current_chunk = part + "\n\n"
                    if current_chunk:
                        chunks.append({
                            'contenido': current_chunk.strip(),
                            'fuente': filename
                        })
                else:
                    chunks.append({
                        'contenido': text,
                        'fuente': filename
                    })
        
        return chunks
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Realiza búsqueda con BM25."""
        if not self.initialize():
            return []
        
        try:
            tokenized_query = query.lower().split()
            scores = self.bm25.get_scores(tokenized_query)
            
            # Obtener top-k resultados
            top_indices = sorted(
                range(len(scores)), 
                key=lambda i: scores[i], 
                reverse=True
            )[:k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Solo resultados con puntuación positiva
                    results.append({
                        'contenido': self.documents[idx]['contenido'],
                        'fuente': self.documents[idx]['fuente'],
                        'score': scores[idx]
                    })
            
            return results
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
    
    def search_semantic(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Alias para search (sin búsqueda semántica real)."""
        return self.search(query, k)


# Instancia global del sistema RAG
rag_system = RAGSystem()


# ============================================
# TOOLS PARA LOS AGENTES
# ============================================

@tool
def buscar_normativa(consulta: str) -> str:
    """
    Busca información en la base de conocimiento de normativa fiscal y contable.
    
    Args:
        consulta: Pregunta o tema a buscar (ej: "tipos de IVA residencias", "plazos modelo 303")
    
    Returns:
        Información relevante encontrada en la normativa
    """
    try:
        results = rag_system.search(consulta, k=4)
        
        if not results:
            return "No se encontró información relevante sobre ese tema en la base de conocimiento."
        
        response = f"📚 **RESULTADOS DE BÚSQUEDA EN NORMATIVA**\n"
        response += f"Consulta: *{consulta}*\n\n"
        
        for i, result in enumerate(results, 1):
            fuente = result.get("fuente", "documento")
            contenido = result.get("contenido", "")[:400]
            response += f"### Resultado {i} ({fuente})\n{contenido}\n\n"
        
        return response
    except Exception as e:
        return f"Error al buscar en la base de conocimiento: {str(e)}"


@tool
def buscar_procedimiento_cobros(tipo_consulta: str) -> str:
    """
    Busca procedimientos específicos de gestión de cobros y morosidad.
    
    Args:
        tipo_consulta: Tipo de procedimiento (ej: "reclamación", "fraccionamiento", "impago")
    
    Returns:
        Procedimiento detallado según la normativa interna
    """
    try:
        query = f"procedimiento cobros {tipo_consulta}"
        results = rag_system.search(query, k=3)
        
        if not results:
            return "No se encontró el procedimiento solicitado."
        
        response = f"📋 **PROCEDIMIENTO: {tipo_consulta.upper()}**\n\n"
        for result in results:
            response += f"{result.get('contenido', '')}\n\n"
        
        return response
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def consultar_normativa_iva(aspecto: str) -> str:
    """
    Consulta específica sobre normativa de IVA para residencias de estudiantes.
    
    Args:
        aspecto: Aspecto del IVA a consultar (ej: "tipos aplicables", "deducciones", "exenciones")
    
    Returns:
        Información detallada sobre el aspecto de IVA consultado
    """
    try:
        query = f"IVA {aspecto} residencias estudiantes"
        results = rag_system.search(query, k=3)
        
        if not results:
            return "No se encontró información sobre ese aspecto del IVA."
        
        response = f"⚖️ **NORMATIVA IVA: {aspecto.upper()}**\n\n"
        for result in results:
            response += f"{result.get('contenido', '')}\n\n---\n\n"
        
        return response
    except Exception as e:
        return f"Error: {str(e)}"


# Lista de herramientas RAG para exportar
RAG_TOOLS = [
    buscar_normativa,
    buscar_procedimiento_cobros,
    consultar_normativa_iva
]
