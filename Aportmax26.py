import streamlit as st
from fpdf import FPDF
import datetime
import plotly.graph_objects as go

# --- 1. MOTOR FISCAL CATALUÑA 2026 ---
def calcular_irpf_cat(base):
    tramos = [
        (0, 12450, 0.190), (12450, 17707, 0.240), (17707, 20200, 0.260),
        (20200, 33007, 0.29), (33007, 35200, 0.335), (35200, 53407, 0.37),
        (53407, 60000, 0.40), (60000, 90000, 0.440), (90000, 120000, 0.460),
        (120000, 150000, 0.470), (150000, 175000, 0.480), (175000, float('inf'), 0.500)
    ]
    def cuota_base(b):
        if b <= 0: return 0
        c = 0
        for inf, sup, tipo in tramos:
            if b > inf:
                c += (min(b, sup) - inf) * tipo
            else: break
        return c
    return cuota_base(base) - cuota_base(5550)

def calcular_max_personal_adicional(e, salario):
    if salario > 60000: return e
    if e <= 500: return e * 2.5
    elif e <= 1500: return 1250 + (0.25 * (e - 500))
    else: return e

# --- 2. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="AportaMax 2026", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
            padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;
        }
        .card {
            padding: 20px; border-radius: 15px; text-align: center;
            border: 1px solid #e2e8f0; margin-bottom: 10px; width: 100%;
        }
        .kpi-container {
            display: flex; gap: 10px; margin-bottom: 20px;
        }
        .kpi-card {
            flex: 1; background: #f8fafc; border: 1px solid #e2e8f0;
            padding: 15px; border-radius: 12px; text-align: center;
        }
        .kpi-card b { font-size: 1.2rem; color: #1e3a8a; }
        .step-pill {
            background: #eff6ff; color: #1e40af; padding: 4px 12px;
            border-radius: 20px; font-weight: bold; font-size: 0.8rem;
            margin-bottom: 10px; display: inline-block; border: 1px solid #dbeafe;
        }
        .plan-box {
            background: white; border-radius: 15px; padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES PDF (SOPORTE BYTES DIRECTO) ---
@st.cache_data
def generar_pdf_tecnico(empresa_total, max_p, inversion_t, ahorro, esfuerzo, sb, ss, gastos, base_pre, eficiencia):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", 'B', 16); pdf.set_xy(10, 8)
    pdf.cell(0, 10, "PLANIFICACION FISCAL APORTACION AL PPE", align='L')
    pdf.set_font("helvetica", '', 9); pdf.set_xy(10, 16)
    pdf.cell(0, 10, f"Ejercicio Fiscal 2026 | Catalunya", align='L')
    
    pdf.set_text_color(40, 40, 40); pdf.ln(20)
    pdf.set_font("helvetica", 'B', 10); pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 1. RESUMEN EJECUTIVO", fill=True, ln=True); pdf.ln(2)
    
    pdf.set_font("helvetica", size=9)
    pdf.cell(140, 6, "Aportacion Empresarial Anual (PPE):"); pdf.cell(0, 6, f"{empresa_total:,.2f} EUR", ln=True, align='R')
    pdf.cell(140, 6, "MAXIMA APORTACION PERSONAL:"); pdf.cell(0, 6, f"{max_p:,.2f} EUR", ln=True, align='R')
    pdf.cell(140, 6, "AHORRO FISCAL ESTIMADO:"); pdf.cell(0, 6, f"{ahorro:,.2f} EUR", ln=True, align='R')
    pdf.cell(140, 6, "Eficiencia Fiscal:"); pdf.cell(0, 6, f"{eficiencia:.2f}%", ln=True, align='R')
    
    # El método output() sin argumentos devuelve bytes en fpdf2
    return pdf.output()

@st.cache_data
def generar_pdf_visual_v2(max_p, ahorro, inversion, extra, cuota_r, meses, ya_aportado):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 15, 297, 'F')
    pdf.set_xy(25, 20)
    pdf.set_font("helvetica", 'B', 24); pdf.set_text_color(30, 58, 138); pdf.cell(0, 10, "TU HOJA DE RUTA 2026", ln=True)
    
    pdf.set_xy(25, 50); pdf.set_font("helvetica", 'B', 14); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"OBJETIVO DE APORTACION PERSONAL: {max_p:,.2f} EUR", ln=True)
    pdf.set_text_color(34, 197, 94)
    pdf.cell(0, 10, f"AHORRO FISCAL ESTIMADO: {ahorro:,.2f} EUR", ln=True)
    
    pdf.set_xy(25, 80); pdf.set_font("helvetica", '', 11); pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 7, f"Para alcanzar este objetivo en los {meses} meses restantes del año, se recomienda:")
    pdf.ln(5)
    pdf.set_x(25); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, f"- Nueva cuota mensual: {cuota_r:,.2f} EUR", ln=True)
    pdf.set_x(25); pdf.cell(0, 10, f"- O un ingreso extraordinario de: {extra:,.2f} EUR", ln=True)
    
    return pdf.output()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ CONFIGURACIÓN")
    sb = st.number_input("Sueldo Bruto Anual (€)", value=60000.0, step=1000.0)
    e_ahorro = st.number_input("Aportación Mensual Empresa (€)", value=100.0, step=10.0)
    e_riesgo = st.number_input("Prima Anual Riesgo PPE (€)", value=150.0, step=10.0)
    emp_t = min(e_ahorro * 12 + e_riesgo, 10000.0)

    # Cálculo dinámico de límites para el input
    CUOTA_SS_PRE = min(sb, 5101.0 * 12) * 0.0635 
    BASE_PRE_LIMIT = max(0.0, sb - CUOTA_SS_PRE - 2000.0)
    MAX_P_LIMIT = max(0.0, min(calcular_max_personal_adicional(emp_t, sb) + 1500, 10000.0 - emp_t))
    if (emp_t + MAX_P_LIMIT) > (BASE_PRE_LIMIT * 0.30): MAX_P_LIMIT = max(0.0, (BASE_PRE_LIMIT * 0.30) - emp_t)

    st.markdown("---")
    c_m = st.number_input("Tu aportación mensual actual (€)", value=0.0, step=50.0)
    e_y = st.number_input("Aportaciones extras ya realizadas (€)", value=0.0, step=100.0)

# --- 5. LÓGICA DE CÁLCULO ---
hoy = datetime.date.today()
meses_restantes = 12 - hoy.month + 1
meses_pasados = 12 - meses_restantes
CUOTA_SS = min(sb, 5101.0 * 12) * 0.0635 
base_pre = max(0.0, sb - CUOTA_SS - 2000.0)
max_p = MAX_P_LIMIT

ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
eficiencia = (ahorro / max_p * 100) if max_p > 0 else 0
esfuerzo_neto = max_p - ahorro
ya_aportado = (c_m * meses_pasados) + e_y
pendiente_para_limite = max(0.0, max_p - ya_aportado)
nueva_cuota_total = pendiente_para_limite / meses_restantes if meses_restantes > 0 else 0
diferencia_mensual = nueva_cuota_total - c_m
aportacion_extraordinaria_neta = max(0.0, pendiente_para_limite - (c_m * meses_restantes))

# --- 6. RENDERIZADO PRINCIPAL ---
st.markdown('<div class="main-header"><h1>📈 APORTAMAX 2026</h1></div>', unsafe_allow_html=True)

t1, t2 = st.tabs(["📊 Análisis Fiscal", "🎯 Plan de Acción"])

with t1:
    col_a, col_b = st.columns([1, 1.2])
    with col_a:
        st.markdown(f"""
            <div class="card" style="background-color: #1E3A8A; color: white;">
                <p style="margin:0; opacity: 0.8;">LÍMITE PERSONAL MÁXIMO</p>
                <h2 style="font-size: 32px; margin: 5px 0;">{max_p:,.2f} €</h2>
            </div>
            <div class="card" style="background-color: #F0FDF4; color: #166534;">
                <p style="margin:0; opacity: 0.8;">TU AHORRO EN IMPUESTOS</p>
                <h2 style="font-size: 32px; margin: 5px 0;">{ahorro:,.2f} €</h2>
                <p style="margin:0; font-weight: bold;">Eficiencia: {eficiencia:.1f}%</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_b:
        fig = go.Figure(data=[go.Pie(labels=['Tu Esfuerzo', 'Ahorro Fiscal', 'Empresa'], 
                                     values=[esfuerzo_neto, ahorro, emp_t], hole=.6)])
        fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    # Botón Informe Técnico
    pdf_t = generar_pdf_tecnico(emp_t, max_p, (emp_t+max_p), ahorro, esfuerzo_neto, sb, CUOTA_SS, 2000.0, base_pre, eficiencia)
    st.download_button("📄 Descargar Informe Fiscal Detallado", data=pdf_t, file_name="Informe_Fiscal_2026.pdf", mime="application/pdf", use_container_width=True)

with t2:
    st.markdown("### Estrategia para completar tu límite")
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-card">Ya Aportado<br><b>{ya_aportado:,.2f} €</b></div>
        <div class="kpi-card">Pendiente<br><b>{pendiente_para_limite:,.2f} €</b></div>
        <div class="kpi-card">Meses Restantes<br><b>{meses_restantes}</b></div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="plan-box">
            <div class="step-pill">RECOMENDACIÓN</div>
            <p style="color: #64748b; margin-bottom: 5px;">Incrementa tu cuota mensual en:</p>
            <h2 style="color: #1e40af; margin-top: 0;">+{diferencia_mensual:,.2f} € / mes</h2>
            <p>Nueva aportación total: <b>{nueva_cuota_total:,.2f} €/mes</b></p>
        </div>
    """, unsafe_allow_html=True)

    # Botón Hoja de Ruta
    pdf_v = generar_pdf_visual_v2(max_p, ahorro, (emp_t+max_p), aportacion_extraordinaria_neta, nueva_cuota_total, meses_restantes, ya_aportado)
    st.download_button("🚀 DESCARGAR MI HOJA DE RUTA", data=pdf_v, file_name="Plan_Accion_PPE.pdf", mime="application/pdf", key="v2_btn", use_container_width=True)

st.caption("Nota: Cálculos basados en la normativa de IRPF de Cataluña proyectada para 2026.")
