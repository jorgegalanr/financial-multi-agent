"""
Grafo LangGraph FINAL - Optimizado para Qwen 2.5 (7b)
Incluye logs detallados, detección de rutas robusta y protección contra bucles.
"""

from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from graphs.routing import select_agent
import operator
import os
import sys
import json
import re

# ============================================
# 1. CONFIGURACIÓN
# ============================================

# Usamos el modelo 7b que es más rápido y estable en local
MODEL_NAME = "qwen2.5:7b" 

print("\n" + "="*50)
print(f"🚀 INICIANDO SISTEMA FINANCIERO ({MODEL_NAME})")
print("="*50)

# Asegurar que la raíz del proyecto está en el path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ============================================
# 2. CARGA DE MÓDULOS (Con Logs Visibles)
# ============================================

# --- AGENTES ---
try:
    from agents import AGENT_TOOLS, get_tools_for_agent
    print("✅ [OK] Agentes cargados")
except ImportError:
    print("⚠️ [WARN] No se encontró el paquete 'agents'. Usando modo fallback.")
    AGENT_TOOLS = {}
    def get_tools_for_agent(x): return []

# --- RAG ---
try:
    from rag.rag_system import RAG_TOOLS
    RAG_AVAILABLE = True
    print("✅ [OK] RAG disponible")
except ImportError:
    try:
        from rag_system import RAG_TOOLS
        RAG_AVAILABLE = True
        print("✅ [OK] RAG disponible (desde raíz)")
    except:
        RAG_TOOLS = []
        RAG_AVAILABLE = False
        print("⚠️ [WARN] RAG NO disponible")

# --- ADAPTADORES LOCALES EQUIVALENTES A LAS TOOLS MCP ---
MCP_AVAILABLE = False
ALL_MCP_TOOLS = []
MCP_FINANCIAL_TOOLS = []
MCP_COLLECTIONS_TOOLS = []
THIRD_PARTY_MCP_TOOLS = []

# Intento 1: Importar desde la raíz (lo más probable según tu ZIP)
try:
    from mcp_client import ALL_MCP_TOOLS, MCP_FINANCIAL_TOOLS, MCP_COLLECTIONS_TOOLS
    from third_party_mcp import THIRD_PARTY_MCP_TOOLS
    MCP_AVAILABLE = True
    print("✅ [OK] Adaptadores financieros locales disponibles")
except ImportError:
    # Intento 2: Importar desde carpeta mcp_servers
    try:
        from mcp_servers.mcp_client import ALL_MCP_TOOLS, MCP_FINANCIAL_TOOLS, MCP_COLLECTIONS_TOOLS
        from mcp_servers.third_party_mcp import THIRD_PARTY_MCP_TOOLS
        MCP_AVAILABLE = True
        print("✅ [OK] Adaptadores financieros locales disponibles")
    except ImportError:
        print("⚠️ [WARN] Adaptadores financieros locales no disponibles")

print("-" * 50)

# ============================================
# 3. DEFINICIÓN DE AGENTES
# ============================================

AGENT_CONFIG = {
    "director_financiero": {
        "nombre": "Director Financiero",
        "icono": "👔",
        "system_prompt": "Eres el CFO. Tu misión es estratégica. Usa tus herramientas para obtener datos y RESUME la información. Sé directo."
    },
    "ar_manager": {
        "nombre": "AR Manager",
        "icono": "💳",
        "system_prompt": "Eres el Responsable de Cobros. Gestiona morosos y facturas."
    },
    "tesorero": {
        "nombre": "Tesorero",
        "icono": "🏦",
        "system_prompt": "Eres el Tesorero. Controla la liquidez y deuda."
    },
    "controller": {
        "nombre": "Controller",
        "icono": "📊",
        "system_prompt": "Eres el Controller. Supervisa la contabilidad."
    },
    "fpa_analyst": {
        "nombre": "FP&A Analyst",
        "icono": "📈",
        "system_prompt": "Eres el Analista de Planificación."
    },
    "fiscalista": {
        "nombre": "Fiscalista",
        "icono": "⚖️",
        "system_prompt": "Eres el Asesor Fiscal."
    },
    "gestor_activos": {
        "nombre": "Gestor de Activos",
        "icono": "🏢",
        "system_prompt": "Eres el Gestor de Activos."
    }
}

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    current_agent: str
    next_agent: str | None
    forced_agent: str | None

def get_base_llm():
    """Devuelve un LLM limpio sin herramientas (para pensar rápido)."""
    return ChatOllama(model=MODEL_NAME, temperature=0)

def create_agent_node(agent_key: str):
    def agent_node(state: AgentState) -> dict:
        print(f"\n🔵 Agente activo: {agent_key}")
        
        config = AGENT_CONFIG[agent_key]
        base_llm = get_base_llm()
        
        # 1. Preparar herramientas
        tools = get_tools_for_agent(agent_key)
        
        # Inyección de capacidades extra según rol
        if RAG_AVAILABLE and agent_key in ["fiscalista", "director_financiero", "controller"]:
            tools += RAG_TOOLS
        if MCP_AVAILABLE:
            if agent_key == "tesorero": tools += MCP_FINANCIAL_TOOLS
            if agent_key == "ar_manager": tools += MCP_COLLECTIONS_TOOLS
            if agent_key == "director_financiero": 
                tools += MCP_FINANCIAL_TOOLS + MCP_COLLECTIONS_TOOLS + THIRD_PARTY_MCP_TOOLS
        
        # Vincular herramientas al LLM
        llm_with_tools = base_llm.bind_tools(tools)
        
        messages = [SystemMessage(content=config["system_prompt"])] + state["messages"]
        
        # 2. INVOCACIÓN AL MODELO (PENSAMIENTO)
        print(f"   🧠 Pensando... (Modelo: {MODEL_NAME})")
        try:
            response = llm_with_tools.invoke(messages)
            print("   ⚡ Respuesta recibida del LLM")
        except Exception as e:
            print(f"   ❌ Error en LLM: {e}")
            return {"messages": [AIMessage(content=f"Error técnico: {e}")], "current_agent": agent_key}

        # 3. PROCESAMIENTO DE HERRAMIENTAS
        content = response.content if hasattr(response, 'content') else str(response)
        tool_calls = getattr(response, 'tool_calls', [])

        # Parche para "sourceMapping" (error común de Qwen)
        if not tool_calls and "sourceMapping" in str(content):
            print("   🔧 Corrigiendo formato 'sourceMapping'...")
            matches = re.findall(r'\{.*?"name":\s*".*?".*?\}', str(content).replace('\n', ' '))
            for match in matches:
                try:
                    data = json.loads(match)
                    if 'name' in data:
                        tool_calls.append({'name': data['name'], 'args': data.get('arguments', {})})
                except: pass

        # 4. EJECUCIÓN (ACCION)
        tool_results_txt = ""
        if tool_calls:
            print(f"   🛠️ Ejecutando {len(tool_calls)} herramientas...")
            for call in tool_calls:
                t_name = call.get('name')
                t_args = call.get('args', {})
                
                # Buscar la función real
                selected = next((t for t in tools if t.name == t_name), None)
                if selected:
                    try:
                        print(f"      > Ejecutando: {t_name}")
                        output = selected.invoke(t_args)
                        
                        # Limitar tamaño para no saturar al 7b
                        str_out = str(output)
                        if len(str_out) > 3000: 
                            str_out = str_out[:3000] + "...[truncado por longitud]"
                        
                        tool_results_txt += f"\n--- Resultado de {t_name} ---\n{str_out}\n"
                    except Exception as e:
                        print(f"      ❌ Error en herramienta: {e}")
                        tool_results_txt += f"\nError en {t_name}: {e}\n"
        
        # 5. SÍNTESIS FINAL (RESUMEN)
        if tool_results_txt:
            print("   📝 Generando resumen final...")
            
            # Usamos el LLM base (SIN TOOLS) para que solo redacte y no entre en bucle
            synthesis_prompt = [
                SystemMessage(content="Eres un asistente financiero. Resume los datos proporcionados de forma clara y profesional en Español."),
                HumanMessage(content=f"""
                PREGUNTA USUARIO: {state['messages'][-1].content}
                
                DATOS TÉCNICOS OBTENIDOS:
                {tool_results_txt}
                
                INSTRUCCIONES:
                Responde a la pregunta del usuario basándote en los datos.
                Usa formato Markdown (negritas, listas).
                NO inventes datos.
                """)
            ]
            final_response = base_llm.invoke(synthesis_prompt)
            print("   ✅ Resumen completado")
            return {"messages": [final_response], "current_agent": agent_key}
        
        # Si no hubo herramientas, devolver respuesta directa
        print("   ✅ Respuesta directa enviada")
        return {"messages": [response], "current_agent": agent_key}
    
    return agent_node

def supervisor_node(state: AgentState) -> dict:
    llm = get_base_llm()
    # Convertimos a minúsculas para facilitar la búsqueda
    last_msg = state["messages"][-1].content.lower()
    print(f"\n🔍 Supervisor analizando: '{last_msg[:30]}...'")

    # --- 1. SELECCIÓN MANUAL O REGLAS FIJAS ---
    deterministic_agent = select_agent(last_msg, state.get("forced_agent"))
    if deterministic_agent:
        print(f"   👉 [Deterministic Route] Derivando a: {deterministic_agent}")
        return {"next_agent": deterministic_agent}
    
    # --- 2. ENRUTAMIENTO INTELIGENTE (LLM) ---
    # Solo si no coincide ninguna palabra clave, preguntamos al modelo
    
    prompt = (
        f"Clasifica la consulta en uno de estos roles: {', '.join(AGENT_CONFIG.keys())}. "
        f"Consulta: {last_msg!r}. Responde SOLO con el ID del rol exacto."
    )
    
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        decision = resp.content.strip().lower().replace('"', '').replace(" ", "_")
        
        found_agent = "director_financiero" # Default
        for key in AGENT_CONFIG:
            if key in decision:
                found_agent = key
                break
        
        print(f"   👉 [LLM Decision] Derivando a: {found_agent}")
        return {"next_agent": found_agent}
        
    except Exception as e:
        print(f"   ❌ Error en supervisor: {e}")
        return {"next_agent": "director_financiero"}

def build_graph():
    wf = StateGraph(AgentState)
    wf.add_node("supervisor", supervisor_node)
    
    for key in AGENT_CONFIG:
        wf.add_node(key, create_agent_node(key))
        wf.add_edge(key, END)
    
    wf.set_entry_point("supervisor")
    wf.add_conditional_edges("supervisor", lambda x: x["next_agent"], {k: k for k in AGENT_CONFIG})
    
    return wf.compile()

def run_agent_query(query: str, forced_agent: str = None):
    try:
        app = build_graph()
        inputs = {
            "messages": [HumanMessage(content=query)], 
            "current_agent": "", 
            "next_agent": None,
            "forced_agent": forced_agent,
        }

        result = app.invoke(inputs)
        
        last_msg = result["messages"][-1].content
        agent_key = result.get("current_agent", "director_financiero")
        agent_info = AGENT_CONFIG.get(agent_key, AGENT_CONFIG["director_financiero"])
        
        return last_msg, agent_info["nombre"], agent_info["icono"]
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN GRAFO: {e}")
        return f"Ocurrió un error en el sistema: {str(e)}", "Error de Sistema", "❌"
