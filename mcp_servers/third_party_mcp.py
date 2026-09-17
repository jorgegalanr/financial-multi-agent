"""Adaptador local de filesystem para las herramientas LangChain.

Estas funciones no abren una sesión MCP: replican de forma local las
operaciones necesarias para que Streamlit funcione sin procesos auxiliares.
El servidor MCP real se configura por separado en ``mcp_config.json``.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import tool

# Configuración del directorio permitido
ALLOWED_DIRECTORY = os.path.dirname(os.path.dirname(__file__))


def resolve_allowed_path(path: str) -> Path:
    """Resuelve una ruta y rechaza escapes fuera del directorio permitido."""

    base = Path(ALLOWED_DIRECTORY).resolve()
    candidate = (base / path).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError("Acceso denegado. La ruta está fuera del proyecto.")
    return candidate


# ============================================
# IMPLEMENTACIÓN DIRECTA (sin servidor externo)
# ============================================

@tool
def filesystem_list_directory(path: str = "") -> str:
    """
    Lista el contenido de un directorio permitido.
    
    Args:
        path: Ruta relativa al directorio del proyecto
    
    Returns:
        Lista de archivos y carpetas en el directorio
    """
    try:
        full_path = resolve_allowed_path(path)
        
        if not os.path.exists(full_path):
            return f"Error: El directorio '{path}' no existe."
        
        entries = []
        for entry in os.listdir(full_path):
            entry_path = os.path.join(full_path, entry)
            entry_type = "directory" if os.path.isdir(entry_path) else "file"
            size = os.path.getsize(entry_path) if os.path.isfile(entry_path) else 0
            entries.append({
                "name": entry,
                "type": entry_type,
                "size": size
            })
        
        result = {
            "path": path or "/",
            "entries": sorted(entries, key=lambda x: (x["type"] == "file", x["name"]))
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def filesystem_read_file(path: str) -> str:
    """
    Lee el contenido de un archivo permitido.
    
    Args:
        path: Ruta relativa al archivo dentro del proyecto
    
    Returns:
        Contenido del archivo
    """
    try:
        full_path = resolve_allowed_path(path)
        
        if not os.path.exists(full_path):
            return f"Error: El archivo '{path}' no existe."
        
        if not os.path.isfile(full_path):
            return f"Error: '{path}' no es un archivo."
        
        # Limitar tamaño de lectura
        if os.path.getsize(full_path) > 100000:  # 100KB max
            return "Error: Archivo demasiado grande (máximo 100KB)."
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def filesystem_search_files(pattern: str, directory: str = "") -> str:
    """
    Busca archivos por patrón dentro del proyecto.
    
    Args:
        pattern: Patrón de búsqueda (ej: "*.csv", "*.py")
        directory: Directorio donde buscar (relativo al proyecto)
    
    Returns:
        Lista de archivos que coinciden con el patrón
    """
    try:
        import fnmatch
        
        search_path = resolve_allowed_path(directory)
        
        matches = []
        for root, dirs, files in os.walk(search_path):
            # Excluir directorios ocultos y __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for filename in fnmatch.filter(files, pattern):
                rel_path = os.path.relpath(os.path.join(root, filename), ALLOWED_DIRECTORY)
                matches.append(rel_path)
        
        result = {
            "pattern": pattern,
            "directory": directory or "/",
            "matches": matches[:50]  # Limitar a 50 resultados
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def filesystem_get_file_info(path: str) -> str:
    """
    Obtiene información de un archivo permitido.
    
    Args:
        path: Ruta relativa al archivo
    
    Returns:
        Información del archivo (tamaño, fecha modificación, etc.)
    """
    try:
        full_path = resolve_allowed_path(path)
        
        if not os.path.exists(full_path):
            return f"Error: '{path}' no existe."
        
        stat = os.stat(full_path)
        from datetime import datetime
        
        result = {
            "path": path,
            "type": "directory" if os.path.isdir(full_path) else "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


# Alias mantenido para no romper el grafo existente.
THIRD_PARTY_MCP_TOOLS = [
    filesystem_list_directory,
    filesystem_read_file,
    filesystem_search_files,
    filesystem_get_file_info
]
