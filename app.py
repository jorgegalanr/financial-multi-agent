"""
Sistema Multi-Agente Financiero - Dashboard Profesional
Streamlit + LangGraph + Ollama + Plotly
Formato español: 1.234.567,89€
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import io
import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# IMPORTANTE: Añadir el directorio actual al path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

DATA_PATH = os.path.join(CURRENT_DIR, "data")

from graphs.financial_graph import run_agent_query, AGENT_CONFIG, MODEL_NAME

# ============================================
# FUNCIONES DE FORMATO ESPAÑOL
# ============================================

def formato_euro(valor):
    """Formatea número como euros: 1.234.567,89€"""
    try:
        if pd.isna(valor):
            return "0,00€"
        if valor >= 0:
            return f"{valor:,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"-{abs(valor):,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"{valor}€"

def formato_numero(valor, decimales=2):
    """Formatea número: 1.234.567,89"""
    try:
        if pd.isna(valor):
            return "0"
        formato = f"{valor:,.{decimales}f}"
        return formato.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def formato_porcentaje(valor):
    """Formatea porcentaje: 85,5%"""
    try:
        if pd.isna(valor):
            return "0,0%"
        return f"{valor:.1f}%".replace(".", ",")
    except:
        return f"{valor}%"

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(
    page_title="Dashboard Financiero | Residencias Estudiantiles",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Control manual de tema para títulos
if "titulos_blancos" not in st.session_state:
    st.session_state.titulos_blancos = False

if "titulos_blancos" not in st.session_state:
    st.session_state.titulos_blancos = True

# Toggle grande y visible en sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Apariencia")

titulos_blancos = st.sidebar.toggle(
    "🌙 Modo Oscuro (activar)",
    value=st.session_state.titulos_blancos,
    key="toggle_titulos"
)
st.sidebar.markdown("---")

is_dark = titulos_blancos
section_title_color = "#ffffff" if is_dark else "#000000"
kpi_value_color = "#000000"  # Siempre negro
kpi_label_color = "#495057"  # Siempre gris oscuro
section_border_color = "#495057" if is_dark else "#e9ecef"

# CSS
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .main-header {{
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 50%, #415a77 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    .main-header h1 {{ color: white !important; margin: 0; font-size: 2rem; font-weight: 600; }}
    .main-header p {{ color: white !important; margin: 10px 0 0 0; font-size: 1rem; }}
    
    .metric-card {{
        background: linear-gradient(135deg, #f1f3f5 0%, #e9ecef 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #00b4d8;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }}
    .metric-card.green {{ border-left-color: #2ecc71; }}
    .metric-card.yellow {{ border-left-color: #f1c40f; }}
    .metric-card.red {{ border-left-color: #e74c3c; }}
    .metric-card.blue {{ border-left-color: #3498db; }}
    
    .metric-card * {{ color: #000000 !important; }}
    
    .kpi-value {{ font-size: 2rem; font-weight: 700; color: #000000 !important; }}
    .kpi-label {{ font-size: 0.9rem; color: #495057 !important; margin-top: 5px; }}
    .kpi-delta {{ font-size: 0.85rem; margin-top: 8px; }}
    .kpi-delta.positive {{color: #2ecc71 !important; }}
    .kpi-delta.negative {{ color: #e74c3c !important; }}
    
    .section-title {{
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: {section_title_color} !important;
        margin: 25px 0 15px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid {section_border_color} !important;
    }}
            
    div[data-testid="stMetricValue"] {{
        font-size: 1.8rem;
    }}
</style>
""", unsafe_allow_html=True)




# ============================================
# FUNCIONES DE CARGA DE DATOS
# ============================================

@st.cache_data(ttl=60)
def cargar_datos():
    """Carga todos los CSVs necesarios."""
    datos = {}
    archivos = [
        "estudiantes", "facturas_emitidas", "ocupacion", "posicion_caja",
        "deuda_bancaria", "gastos_fijos", "balance", "cuenta_resultados",
        "kpis", "obligaciones_fiscales", "activos_fijos", "iva_repercutido",
        "iva_soportado", "desviaciones", "pagos_pendientes", "mantenimientos"
    ]
    for archivo in archivos:
        try:
            datos[archivo] = pd.read_csv(os.path.join(DATA_PATH, f"{archivo}.csv"))
        except:
            datos[archivo] = pd.DataFrame()
    return datos


# ============================================
# COMPONENTES DE DASHBOARD
# ============================================

def crear_kpi_card(titulo, valor, delta=None, delta_color="normal", icono="📊"):
    """Crea una tarjeta KPI estilizada."""
    delta_html = ""
    if delta:
        color_class = "positive" if delta_color == "positive" else "negative" if delta_color == "negative" else ""
        delta_html = f'<div class="kpi-delta {color_class}">{delta}</div>'
    
    color_class = "green" if delta_color == "positive" else "red" if delta_color == "negative" else "blue"
    
    return f"""
    <div class="metric-card {color_class}">
        <div class="kpi-label">{icono} {titulo}</div>
        <div class="kpi-value">{valor}</div>
        {delta_html}
    </div>
    """
def aplicar_tema_plotly(fig):
    if is_dark:
        fig.update_layout(
            font=dict(color="white"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        fig.update_xaxes(color="white", gridcolor="rgba(255,255,255,0.15)")
        fig.update_yaxes(color="white", gridcolor="rgba(255,255,255,0.15)")
    return fig


def dashboard_resumen(datos):
    """Dashboard principal con KPIs y gráficas."""
    
    st.markdown('<div class="section-title">📊 Indicadores Clave de Rendimiento</div>', unsafe_allow_html=True)
    
    # Calcular métricas
    facturas = datos.get("facturas_emitidas", pd.DataFrame())
    ocupacion = datos.get("ocupacion", pd.DataFrame())
    caja = datos.get("posicion_caja", pd.DataFrame())
    deuda = datos.get("deuda_bancaria", pd.DataFrame())
    
    total_facturado = facturas["importe"].sum() if not facturas.empty else 0
    cobrado = facturas[facturas["estado"] == "pagada"]["importe"].sum() if not facturas.empty else 0
    vencido = facturas[facturas["estado"] == "vencida"]["importe"].sum() if not facturas.empty else 0
    
    total_plazas = ocupacion["capacidad"].sum() if not ocupacion.empty else 0
    ocupadas = ocupacion["ocupacion_actual"].sum() if not ocupacion.empty else 0
    pct_ocupacion = (ocupadas / total_plazas * 100) if total_plazas > 0 else 0
    
    saldo_caja = caja["saldo"].sum() if not caja.empty else 0
    deuda_total = deuda["capital_pendiente"].sum() if not deuda.empty else 0
    
    tasa_morosidad = (vencido / total_facturado * 100) if total_facturado > 0 else 0
    
    # Fila de KPIs principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(crear_kpi_card(
            "Facturación Total",
            formato_euro(total_facturado),
            "Ejercicio 2025",
            "normal",
            "💰"
        ), unsafe_allow_html=True)
    
    with col2:
        color = "positive" if pct_ocupacion >= 90 else "negative" if pct_ocupacion < 80 else "normal"
        st.markdown(crear_kpi_card(
            "Ocupación",
            formato_porcentaje(pct_ocupacion),
            f"{int(ocupadas)}/{int(total_plazas)} plazas",
            color,
            "🏠"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(crear_kpi_card(
            "Saldo en Caja",
            formato_euro(saldo_caja),
            "Disponible",
            "positive" if saldo_caja > 500000 else "negative",
            "🏦"
        ), unsafe_allow_html=True)
    
    with col4:
        color = "positive" if tasa_morosidad < 3 else "negative" if tasa_morosidad > 5 else "normal"
        st.markdown(crear_kpi_card(
            "Morosidad",
            formato_porcentaje(tasa_morosidad),
            formato_euro(vencido) + " vencido",
            "negative" if tasa_morosidad > 3 else "positive",
            "⚠️"
        ), unsafe_allow_html=True)
    
    with col5:
        st.markdown(crear_kpi_card(
            "Deuda Bancaria",
            formato_euro(deuda_total),
            f"{len(deuda)} préstamos",
            "normal",
            "🏛️"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos principales
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown('<div class="section-title">📈 Ocupación por Residencia</div>', unsafe_allow_html=True)
        if not ocupacion.empty:
            fig_ocupacion = go.Figure()
            
            fig_ocupacion.add_trace(go.Bar(
                name='Libres',
                x=ocupacion['residencia'],
                y=ocupacion['capacidad'] - ocupacion['ocupacion_actual'],
                marker_color='#2ecc71',
                text=ocupacion['capacidad'] - ocupacion['ocupacion_actual'],
                textposition='auto'
            ))
            
            fig_ocupacion.add_trace(go.Bar(
                name='Ocupadas',
                x=ocupacion['residencia'],
                y=ocupacion['ocupacion_actual'],
                marker_color='#e74c3c',
                text=ocupacion['ocupacion_actual'],
                textposition='auto'
            ))
            
            fig_ocupacion.update_layout(
                barmode='stack',
                height=400,
                xaxis_tickangle=-45,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(l=20, r=20, t=40, b=100),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_ocupacion = aplicar_tema_plotly(fig_ocupacion)
            st.plotly_chart(fig_ocupacion, use_container_width=True)

    
    with col_right:
        st.markdown('<div class="section-title">💳 Estado de Facturación</div>', unsafe_allow_html=True)
        if not facturas.empty:
            estados = facturas.groupby("estado")["importe"].sum().reset_index()
            colores = {'pagada': '#2ecc71', 'pendiente': '#f1c40f', 'vencida': '#e74c3c'}
            
            fig_facturas = px.pie(
                estados,
                values='importe',
                names='estado',
                color='estado',
                color_discrete_map=colores,
                hole=0.5
            )
            
            fig_facturas.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>%{value:,.2f}€<br>%{percent}'
            )
            
            fig_facturas.update_layout(
                height=400,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                margin=dict(l=20, r=20, t=20, b=60),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig_facturas = aplicar_tema_plotly(fig_facturas)
            st.plotly_chart(fig_facturas, use_container_width=True)



def dashboard_cobros(datos):
    """Dashboard de gestión de cobros y morosidad."""
    
    facturas = datos.get("facturas_emitidas", pd.DataFrame())
    estudiantes = datos.get("estudiantes", pd.DataFrame())
    
    if facturas.empty:
        st.warning("No hay datos de facturas disponibles.")
        return
    
    st.markdown('<div class="section-title">📋 Análisis de Cuentas por Cobrar</div>', unsafe_allow_html=True)
    
    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    pendiente = facturas[facturas["estado"] == "pendiente"]["importe"].sum()
    vencido = facturas[facturas["estado"] == "vencida"]["importe"].sum()
    total_facturas = len(facturas)
    facturas_vencidas = len(facturas[facturas["estado"] == "vencida"])
    
    col1.metric("💵 Pendiente de Cobro", formato_euro(pendiente))
    col2.metric("🔴 Importe Vencido", formato_euro(vencido))
    col3.metric("📄 Total Facturas", formato_numero(total_facturas, 0))
    col4.metric("⚠️ Facturas Vencidas", formato_numero(facturas_vencidas, 0))
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 📊 Aging Report")
        
        # Calcular aging
        facturas_pend = facturas[facturas["estado"].isin(["pendiente", "vencida"])].copy()
        if not facturas_pend.empty:
            facturas_pend["fecha_vencimiento"] = pd.to_datetime(facturas_pend["fecha_vencimiento"])
            facturas_pend["dias"] = (datetime.now() - facturas_pend["fecha_vencimiento"]).dt.days
            
            def clasificar(dias):
                if dias <= 0: return "No vencido"
                elif dias <= 30: return "1-30 días"
                elif dias <= 60: return "31-60 días"
                elif dias <= 90: return "61-90 días"
                return ">90 días"
            
            facturas_pend["tramo"] = facturas_pend["dias"].apply(clasificar)
            aging = facturas_pend.groupby("tramo")["importe"].sum().reset_index()
            
            orden = ["No vencido", "1-30 días", "31-60 días", "61-90 días", ">90 días"]
            aging["tramo"] = pd.Categorical(aging["tramo"], categories=orden, ordered=True)
            aging = aging.sort_values("tramo")
            
            colores = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#c0392b"]
            
            fig_aging = px.bar(
                aging,
                x="tramo",
                y="importe",
                color="tramo",
                color_discrete_sequence=colores,
                text=aging["importe"].apply(lambda x: formato_euro(x))
            )
            
            fig_aging.update_traces(textposition='outside')
            fig_aging.update_layout(
                height=350,
                showlegend=False,
                xaxis_title="",
                yaxis_title="Importe",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            fig_aging = aplicar_tema_plotly(fig_aging)
            st.plotly_chart(fig_aging, use_container_width=True)

    
    with col_right:
        st.markdown("#### 🔴 Top 10 Morosos")
        
        vencidas = facturas[facturas["estado"] == "vencida"].copy()
        if not vencidas.empty and not estudiantes.empty:
            vencidas["fecha_vencimiento"] = pd.to_datetime(vencidas["fecha_vencimiento"])
            vencidas["dias_retraso"] = (datetime.now() - vencidas["fecha_vencimiento"]).dt.days
            
            morosos = vencidas.groupby("id_estudiante").agg({
                "importe": "sum",
                "id_factura": "count",
                "dias_retraso": "max"
            }).reset_index()
            morosos.columns = ["ID", "Deuda", "Facturas", "Días"]
            morosos = morosos.merge(
                estudiantes[["id_estudiante", "nombre", "email"]],
                left_on="ID", right_on="id_estudiante", how="left"
            )
            morosos = morosos.sort_values("Deuda", ascending=False).head(10)
            
            # Formatear para mostrar
            morosos["Deuda_fmt"] = morosos["Deuda"].apply(formato_euro)
            
            st.dataframe(
                morosos[["nombre", "Deuda_fmt", "Facturas", "Días", "email"]].rename(columns={
                    "nombre": "Estudiante",
                    "Deuda_fmt": "Deuda Total",
                    "email": "Email"
                }),
                use_container_width=True,
                hide_index=True
            )


def dashboard_tesoreria(datos):
    """Dashboard de tesorería y liquidez."""
    
    caja = datos.get("posicion_caja", pd.DataFrame())
    deuda = datos.get("deuda_bancaria", pd.DataFrame())
    gastos = datos.get("gastos_fijos", pd.DataFrame())
    pagos = datos.get("pagos_pendientes", pd.DataFrame())
    
    st.markdown('<div class="section-title">🏦 Posición de Tesorería</div>', unsafe_allow_html=True)
    
    # Métricas principales
    saldo_total = caja["saldo"].sum() if not caja.empty else 0
    deuda_total = deuda["capital_pendiente"].sum() if not deuda.empty else 0
    cuota_mensual = deuda["cuota_mensual"].sum() if not deuda.empty else 0
    gastos_mensuales = gastos["importe_mensual"].sum() if not gastos.empty else 0
    
    meses_cobertura = saldo_total / gastos_mensuales if gastos_mensuales > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Saldo Disponible", formato_euro(saldo_total))
    col2.metric("🏛️ Deuda Total", formato_euro(deuda_total))
    col3.metric("📅 Cuota Mensual", formato_euro(cuota_mensual))
    col4.metric("⏱️ Meses Cobertura", formato_numero(meses_cobertura, 1))
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🏦 Saldos por Banco")
        if not caja.empty:
            fig_caja = px.bar(
                caja,
                x="banco",
                y="saldo",
                color="tipo",
                text=caja["saldo"].apply(lambda x: formato_euro(x)),
                color_discrete_sequence=["#3498db", "#2ecc71", "#9b59b6"]
            )
            fig_caja.update_traces(textposition='outside')
            fig_caja.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            fig_caja = aplicar_tema_plotly(fig_caja)
            st.plotly_chart(fig_caja, use_container_width=True)


    
    with col_right:
        st.markdown("#### 📊 Distribución Deuda Bancaria")
        if not deuda.empty:
            fig_deuda = px.pie(
                deuda,
                values="capital_pendiente",
                names="tipo",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_deuda.update_traces(textposition='inside', textinfo='percent+label')
            fig_deuda.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            fig_deuda = aplicar_tema_plotly(fig_deuda)
            st.plotly_chart(fig_deuda, use_container_width=True)


    
    # Tabla de deuda detallada
    st.markdown("#### 📋 Detalle de Préstamos")
    if not deuda.empty:
        deuda_display = deuda.copy()
        deuda_display["capital_pendiente"] = deuda_display["capital_pendiente"].apply(formato_euro)
        deuda_display["cuota_mensual"] = deuda_display["cuota_mensual"].apply(formato_euro)
        deuda_display["tipo_interes"] = deuda_display["tipo_interes"].apply(lambda x: formato_porcentaje(x))
        
        st.dataframe(
            deuda_display[["entidad", "tipo", "capital_pendiente", "cuota_mensual", "tipo_interes", "fecha_vencimiento"]].rename(columns={
                "entidad": "Entidad",
                "tipo": "Tipo",
                "capital_pendiente": "Capital Pendiente",
                "cuota_mensual": "Cuota Mensual",
                "tipo_interes": "Interés",
                "fecha_vencimiento": "Vencimiento"
            }),
            use_container_width=True,
            hide_index=True,
            height=300
        )


def dashboard_fiscal(datos):
    """Dashboard fiscal e IVA."""
    
    iva_rep = datos.get("iva_repercutido", pd.DataFrame())
    iva_sop = datos.get("iva_soportado", pd.DataFrame())
    obligaciones = datos.get("obligaciones_fiscales", pd.DataFrame())
    
    st.markdown('<div class="section-title">⚖️ Situación Fiscal</div>', unsafe_allow_html=True)
    
    # Calcular IVA
    col_cuota = "cuota" if "cuota" in iva_rep.columns else "cuota_iva"
    col_base = "base" if "base" in iva_rep.columns else "base_imponible"
    
    total_repercutido = iva_rep[col_cuota].sum() if not iva_rep.empty else 0
    total_soportado = iva_sop[col_cuota].sum() if not iva_sop.empty else 0
    resultado_iva = total_repercutido - total_soportado
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📤 IVA Repercutido", formato_euro(total_repercutido))
    col2.metric("📥 IVA Soportado", formato_euro(total_soportado))
    
    if resultado_iva > 0:
        col3.metric("💰 A Ingresar", formato_euro(resultado_iva), delta="A favor de Hacienda", delta_color="inverse")
    else:
        col3.metric("📥 A Compensar", formato_euro(abs(resultado_iva)), delta="A nuestro favor", delta_color="normal")
    
    col4.metric("📅 Próxima Liquidación", "30/01/2026", delta="Mod. 303")
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 📊 Liquidación IVA (Modelo 303)")
        
        data_iva = pd.DataFrame({
            "Concepto": ["IVA Repercutido", "IVA Soportado", "Resultado"],
            "Importe": [total_repercutido, total_soportado, resultado_iva]
        })
        
        colores = ["#2ecc71", "#e74c3c", "#3498db" if resultado_iva <= 0 else "#f1c40f"]
        
        fig_iva = go.Figure(go.Bar(
            x=data_iva["Concepto"],
            y=data_iva["Importe"],
            marker_color=colores,
            text=data_iva["Importe"].apply(lambda x: formato_euro(x)),
            textposition="outside"
        ))
        fig_iva.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        fig_iva = aplicar_tema_plotly(fig_iva)
        st.plotly_chart(fig_iva, use_container_width=True)

    
    with col_right:
        st.markdown("#### 📅 Obligaciones Fiscales")
        if not obligaciones.empty:
            oblig_display = obligaciones.copy()
            oblig_display["importe_estimado"] = oblig_display["importe_estimado"].apply(formato_euro)
            oblig_display["estado_icono"] = oblig_display["estado"].apply(
                lambda x: "✅" if x.lower() == "presentado" else "🟡" if x.lower() in ["pendiente", "pdte"] else "🔴"
            )
            
            st.dataframe(
                oblig_display[["modelo", "concepto", "periodo", "fecha_limite", "estado_icono", "importe_estimado"]].rename(columns={
                    "modelo": "Modelo",
                    "concepto": "Concepto",
                    "periodo": "Período",
                    "fecha_limite": "Fecha Límite",
                    "estado_icono": "Estado",
                    "importe_estimado": "Importe Est."
                }),
                use_container_width=True,
                hide_index=True
            )


# ============================================
# EXPORTACIÓN PDF
# ============================================

def generar_pdf_dashboard(datos):
    """Genera un PDF con el resumen del dashboard."""
    try:
        from fpdf import FPDF
        
        facturas = datos.get("facturas_emitidas", pd.DataFrame())
        ocupacion = datos.get("ocupacion", pd.DataFrame())
        caja = datos.get("posicion_caja", pd.DataFrame())
        
        total_facturado = facturas["importe"].sum() if not facturas.empty else 0
        cobrado = facturas[facturas["estado"] == "pagada"]["importe"].sum() if not facturas.empty else 0
        vencido = facturas[facturas["estado"] == "vencida"]["importe"].sum() if not facturas.empty else 0
        
        total_plazas = ocupacion["capacidad"].sum() if not ocupacion.empty else 0
        ocupadas = ocupacion["ocupacion_actual"].sum() if not ocupacion.empty else 0
        pct_ocupacion = (ocupadas / total_plazas * 100) if total_plazas > 0 else 0
        
        saldo_caja = caja["saldo"].sum() if not caja.empty else 0
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Registrar fuente Unicode (OBLIGATORIO)
        font_path = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"
        pdf.add_font("DejaVu", "", str(font_path))
        pdf.add_font("DejaVu", "B", str(font_path))
        pdf.add_font("DejaVu", "I", str(font_path))

        # Header
        pdf.set_fill_color(27, 38, 59)
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_font('DejaVu', 'B', 20)
        pdf.set_text_color(255, 255, 255)
        pdf.set_y(12)
        pdf.cell(0, 10, 'Dashboard Financiero', align='C')
        pdf.set_font('DejaVu', '', 12)
        pdf.set_y(24)
        pdf.cell(0, 10, 'Unilife S.L.', align='C')
        
        pdf.set_y(50)
        pdf.set_text_color(0, 0, 0)
        
        # Fecha
        pdf.set_font('DejaVu', 'I', 10)
        pdf.cell(0, 10, f'Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        pdf.ln(15)
        
        # KPIs
        pdf.set_font('DejaVu', 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, 'INDICADORES CLAVE', fill=True)
        pdf.ln(15)
        
        pdf.set_font('DejaVu', '', 11)
        kpis = [
            ("Facturacion Total", formato_euro(total_facturado)),
            ("Importe Cobrado", formato_euro(cobrado)),
            ("Importe Vencido", formato_euro(vencido)),
            ("Ocupacion", formato_porcentaje(pct_ocupacion)),
            ("Plazas Ocupadas", f"{int(ocupadas)} / {int(total_plazas)}"),
            ("Saldo en Caja", formato_euro(saldo_caja))
        ]
        
        for nombre, valor in kpis:
            pdf.cell(90, 8, nombre + ":")
            pdf.cell(90, 8, valor)
            pdf.ln(8)
        
        pdf.ln(10)
        
        # Ocupación por residencia
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(0, 10, 'OCUPACION POR RESIDENCIA', fill=True)
        pdf.ln(15)
        
        pdf.set_font('DejaVu', 'B', 10)
        pdf.cell(70, 8, 'Residencia', border=1)
        pdf.cell(30, 8, 'Capacidad', border=1, align='C')
        pdf.cell(30, 8, 'Ocupadas', border=1, align='C')
        pdf.cell(30, 8, 'Ocupacion', border=1, align='C')
        pdf.ln()
        
        pdf.set_font('DejaVu', '', 9)
        if not ocupacion.empty:
            for _, row in ocupacion.head(15).iterrows():
                pct = (row['ocupacion_actual'] / row['capacidad'] * 100) if row['capacidad'] > 0 else 0
                pdf.cell(70, 7, str(row['residencia'])[:30], border=1)
                pdf.cell(30, 7, str(int(row['capacidad'])), border=1, align='C')
                pdf.cell(30, 7, str(int(row['ocupacion_actual'])), border=1, align='C')
                pdf.cell(30, 7, formato_porcentaje(pct), border=1, align='C')
                pdf.ln()
        
        # Footer
        pdf.set_y(-20)
        pdf.set_font('DejaVu', 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 10, f'Sistema Financiero Multi-Agente | Pagina {pdf.page_no()}', align='C')
        
        try:
            out = pdf.output()
            return bytes(out)
        except Exception as e:
            return pdf.output(dest="S").encode("latin-1")

    except Exception as e:
        st.error(f"Error generando PDF: {e}")
        return None


# ============================================
# CHAT CON AGENTES
# ============================================

def chat_agentes():
    """Interfaz de chat con los agentes."""
    
    st.markdown('<div class="section-title">🤖 Consulta a los Agentes</div>', unsafe_allow_html=True)
    
    # Selector de agente
    col1, col2 = st.columns([1, 3])
    
    with col1:
        agente_seleccionado = st.selectbox(
            "Seleccionar Agente:",
            options=["auto"] + list(AGENT_CONFIG.keys()),
            format_func=lambda x: "🔄 Automático" if x == "auto" else f"{AGENT_CONFIG[x]['icono']} {AGENT_CONFIG[x]['nombre']}"
        )
    
    # Historial de mensajes
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "👤")):
            st.markdown(msg["content"])
    
    # Input
    if prompt := st.chat_input("Escribe tu consulta financiera..."):
        # Mostrar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Obtener respuesta
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Procesando..."):
                agente = agente_seleccionado if agente_seleccionado != "auto" else None

                prompt_to_send = prompt
                if agente is None:
                    prompt_to_send = prompt_to_send.replace("cliente", "estudiante").replace("clientes", "estudiantes")
                    prompt_to_send = prompt_to_send.replace("cuenta de clientes", "cuentas a cobrar")
                    prompt_to_send = prompt_to_send.replace("listado de clientes", "listado de estudiantes")

                response, agent_name, icon = run_agent_query(prompt_to_send, agente)

                st.markdown(f"**{icon} {agent_name}**")
                st.markdown(response)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**{icon} {agent_name}**\n\n{response}",
            "avatar": icon
        })
        
        st.session_state.active_page = "🤖 Chat Agentes"
        st.rerun()



# ============================================
# PÁGINA PRINCIPAL
# ============================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard Financiero</h1>
        <p>Unilife S.L. | Sistema Multi-Agente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    datos = cargar_datos()
    
    # Tabs principales
    pages = ["📊 Resumen Ejecutivo", "💳 Cobros y Morosidad", "🏦 Tesorería", "⚖️ Fiscal", "🤖 Chat Agentes"]
    if "active_page" not in st.session_state:
        st.session_state.active_page = "📊 Resumen Ejecutivo"

    page = st.radio(
        "Navegación",
        pages,
        index=pages.index(st.session_state.active_page),
        horizontal=True,
        label_visibility="collapsed"
    )

    st.session_state.active_page = page

    if page == "📊 Resumen Ejecutivo":
        dashboard_resumen(datos)
    elif page == "💳 Cobros y Morosidad":
        dashboard_cobros(datos)
    elif page == "🏦 Tesorería":
        dashboard_tesoreria(datos)
    elif page == "⚖️ Fiscal":
        dashboard_fiscal(datos)
    else:
        chat_agentes()

    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📥 Exportar")
        
        # Botón PDF
        pdf_data = generar_pdf_dashboard(datos)
        if pdf_data:
            st.download_button(
                label="📕 Descargar PDF",
                data=pdf_data,
                file_name=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        # Botón Excel
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if not datos["facturas_emitidas"].empty:
                    datos["facturas_emitidas"].to_excel(writer, sheet_name='Facturas', index=False)
                if not datos["estudiantes"].empty:
                    datos["estudiantes"].head(100).to_excel(writer, sheet_name='Estudiantes', index=False)
                if not datos["ocupacion"].empty:
                    datos["ocupacion"].to_excel(writer, sheet_name='Ocupacion', index=False)
            
            st.download_button(
                label="📊 Descargar Excel",
                data=output.getvalue(),
                file_name=f"datos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error Excel: {e}")
        
        st.markdown("---")
        
        st.markdown("### ℹ️ Sistema")
        st.caption(f"🤖 Modelo: {MODEL_NAME}")
        st.caption(f"📊 Agentes: {len(AGENT_CONFIG)}")
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        if st.button("🗑️ Limpiar Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()