# Sistema Multi-Agente Financiero

Sistema multi-agente que simula un **departamento financiero completo** de una empresa de alojamiento estudiantil.  
Integra **LangGraph** para la orquestación de agentes, **RAG local**, y **MCP (Model Context Protocol)** con servidores propios y de terceros, todo accesible desde una interfaz **Streamlit**.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Usuario (Streamlit)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 SUPERVISOR / ROUTER (LangGraph)                       │
│            Analiza consulta y selecciona agente              │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ 👔 CFO   │    │ 💳 AR    │    │ 🏦 Tes.  │ ...
    │          │    │ Manager  │    │          │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         ▼               ▼               ▼
    ┌─────────────────────────────────────────┐
    │         HERRAMIENTAS DISPONIBLES        │
    │  • Tools propias (CSV, cálculos, KPIs)  │
    │  • RAG local(BM25 sobre documentación)  │
    │  • MCP Propios (2 servidores)           │
    │  • MCP Terceros (filesystem)            │
    │  • Web tools (datos csv/referenciales)  │
    └─────────────────────────────────────────┘
```

## Agentes (7 total)

| Agente | Rol | Herramientas |
|--------|-----|--------------|
| 👔 Director Financiero | Estrategia y supervisión | Dashboard, RAG, MCP, Filesystem |
| 💳 AR Manager | Facturación y cobros | Facturas, morosos, aging, MCP cobros |
| 🏦 Tesorero | Liquidez y pagos | Caja, pagos, deuda, MCP financiero |
| 📊 Controller | Contabilidad | Balance, PyG, ratios, RAG normativa |
| 📈 FP&A Analyst | Análisis y presupuesto | Ocupación, KPIs, desviaciones |
| ⚖️ Fiscalista | Impuestos | IVA, obligaciones fiscales, RAG normativa |
| 🏢 Gestor de Activos | Activos fijos | Inventario, amortización, mantenimientos |

> El modo **“auto”** actúa como un **router semántico/heurístico**, delegando la consulta al agente más adecuado según el dominio financiero detectado.

## RAG

El sistema incorpora un **RAG local, ligero y reproducible**, basado en:

- **BM25 (búsqueda léxica)** sobre documentos Markdown locales.
- Sin bases vectoriales externas (ChromaDB, FAISS, etc.) para garantizar estabilidad en Windows.
- Integrado como **tools** accesibles por los agentes.

### Documentos indexados:
- `normativa_iva.md` - Régimen IVA residencias estudiantes
- `normativa_contable.md` - Plan General Contable
- `normativa_arrendamientos.md` - Ley de Arrendamientos Urbanos
- `procedimientos_cobros.md` - Procedimientos internos

### Tools RAG:
- `buscar_normativa(consulta)` - Búsqueda híbrida general
- `buscar_procedimiento_cobros(tipo)` - Procedimientos de cobro
- `consultar_normativa_iva(aspecto)` - Normativa IVA específica

## 🔌 MCP - Model Context Protocol

### MCP Propios (2 servidores):

**1. Financial Data Server** (`mcp_servers/financial_data_server.py`)
- `get_cash_position` - Posición de caja
- `get_pending_payments` - Pagos pendientes
- `get_bank_debt` - Deuda bancaria
- `get_balance_sheet` - Balance de situación
- `get_income_statement` - Cuenta de resultados
- `calculate_liquidity_ratio` - Ratio de liquidez

**2. Collections Server** (`mcp_servers/collections_server.py`)
- `get_invoices` - Facturas emitidas
- `get_defaulters` - Listado de morosos
- `get_student_info` - Info de estudiante
- `get_aging_report` - Aging de cuentas por cobrar
- `get_collection_forecast` - Previsión de cobros
- `get_occupancy` - Ocupación de residencias

### MCP Terceros (1 servidor):

**Filesystem MCP** (`mcp_servers/third_party_mcp.py`)
- `filesystem_list_directory` - Listar directorio
- `filesystem_read_file` - Leer archivo
- `filesystem_search_files` - Buscar archivos
- `filesystem_get_file_info` - Info de archivo

## Web Tools

Las herramientas web proporcionan **datos referenciales o simulados** (Euríbor, tipos BCE, etc.) cuando no existe conectividad externa, garantizando la **reproducibilidad del proyecto**.


## Instalación

## Requisitos
- Python 3.10+
- Ollama instalado (LLM local)

### 1. Instalar Ollama
```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

o también desde la web

# Windows
https://ollama.com/download/windows

# Descargar modelo
ollama pull qwen2.5:14b
```

### 2. Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### 3. Ejecutar
```bash
# Terminal 1: Ollama
ollama run qwen2.5:14b

# Terminal 2: Streamlit
streamlit run app.py
```

## Estructura del Proyecto

```
AgentesFinancieros/
├── app.py
├── requirements.txt
├── README.md
│
├── agents/
│   ├── __init__.py
│   └── tools/
│       ├── ar_manager_tools.py
│       ├── tesorero_tools.py
│       ├── controller_tools.py
│       ├── fpa_analyst_tools.py
│       ├── fiscalista_tools.py
│       ├── gestor_activos_tools.py
│       └── director_financiero_tools.py
│
├── graphs/
│   └── financial_graph.py
│
├── rag/
│   ├── rag_system.py
│   └── documentos/
│
├── mcp_servers/
│   ├── financial_data_server.py
│   ├── collections_server.py
│   ├── mcp_client.py
│   └── third_party_mcp.py
│
└── data/
    ├── facturas_emitidas.csv
    ├── estudiantes.csv
    ├── posicion_caja.csv
    └── ...

```

## 💡 Ejemplos de uso

```
"¿Cuál es la normativa de IVA para residencias?"  → RAG + Fiscalista
"Dame el balance desde el servidor MCP"           → MCP + Controller
"Lista los archivos del proyecto"                 → MCP terceros + CFO
"¿Quiénes son los morosos?"                       → AR Manager
"Genera un dashboard ejecutivo"                   → Director Financiero
```

## 🔧 Tecnologías

- **LangChain**: Framework para agentes LLM
- **LangGraph**: Orquestación de flujos de agentes
- **Ollama**: LLM local (qwen2.5:14b)
- **MCP**: Model Context Protocol para herramientas
- **Streamlit**: Interfaz web
- **RAG local (BM25)**: Búsqueda interna
