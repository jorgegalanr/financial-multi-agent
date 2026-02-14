"""
Integración con MCP de terceros: Filesystem MCP Server
Este módulo integra el servidor MCP de filesystem de Anthropic/terceros
para acceder al sistema de archivos.

MCP Server de terceros utilizado:
- @anthropic/mcp-server-filesystem (npm package)
- Permite listar, leer y buscar archivos

Documentación: https://github.com/anthropics/mcp-servers
"""

import os
import json
from typing import List, Dict, Any
from langchain_core.tools import tool

# Para usar el MCP de filesystem de terceros, se necesita instalarlo:
# npm install -g @anthropics/mcp-server-filesystem
# O usar la versión Python equivalente

# Configuración del directorio permitido
ALLOWED_DIRECTORY = os.path.dirname(os.path.dirname(__file__))


# ============================================
# IMPLEMENTACIÓN DIRECTA (sin servidor externo)
# Para demostrar la integración con MCP de terceros
# ============================================

@tool
def filesystem_list_directory(path: str = "") -> str:
    """
    [MCP Terceros - Filesystem] Lista el contenido de un directorio.
    Integración con el protocolo MCP de filesystem.
    
    Args:
        path: Ruta relativa al directorio del proyecto
    
    Returns:
        Lista de archivos y carpetas en el directorio
    """
    try:
        full_path = os.path.join(ALLOWED_DIRECTORY, path)
        
        # Validar que está dentro del directorio permitido
        if not os.path.abspath(full_path).startswith(os.path.abspath(ALLOWED_DIRECTORY)):
            return "Error: Acceso denegado. Solo se permite acceder al directorio del proyecto."
        
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
    [MCP Terceros - Filesystem] Lee el contenido de un archivo.
    Integración con el protocolo MCP de filesystem.
    
    Args:
        path: Ruta relativa al archivo dentro del proyecto
    
    Returns:
        Contenido del archivo
    """
    try:
        full_path = os.path.join(ALLOWED_DIRECTORY, path)
        
        # Validar acceso
        if not os.path.abspath(full_path).startswith(os.path.abspath(ALLOWED_DIRECTORY)):
            return "Error: Acceso denegado."
        
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
    [MCP Terceros - Filesystem] Busca archivos por patrón.
    Integración con el protocolo MCP de filesystem.
    
    Args:
        pattern: Patrón de búsqueda (ej: "*.csv", "*.py")
        directory: Directorio donde buscar (relativo al proyecto)
    
    Returns:
        Lista de archivos que coinciden con el patrón
    """
    try:
        import fnmatch
        
        search_path = os.path.join(ALLOWED_DIRECTORY, directory)
        
        if not os.path.abspath(search_path).startswith(os.path.abspath(ALLOWED_DIRECTORY)):
            return "Error: Acceso denegado."
        
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
    [MCP Terceros - Filesystem] Obtiene información de un archivo.
    Integración con el protocolo MCP de filesystem.
    
    Args:
        path: Ruta relativa al archivo
    
    Returns:
        Información del archivo (tamaño, fecha modificación, etc.)
    """
    try:
        full_path = os.path.join(ALLOWED_DIRECTORY, path)
        
        if not os.path.abspath(full_path).startswith(os.path.abspath(ALLOWED_DIRECTORY)):
            return "Error: Acceso denegado."
        
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


# Lista de herramientas MCP de terceros
THIRD_PARTY_MCP_TOOLS = [
    filesystem_list_directory,
    filesystem_read_file,
    filesystem_search_files,
    filesystem_get_file_info
]
