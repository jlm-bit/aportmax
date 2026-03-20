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
        .option-card {
            background-color: #ffffff;
            padding: 25px;
            border-radius: 15px;
            border-left: 8px solid #3b82f6;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
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
        
        /* FORZADO DE COLOR AZUL PARA BOTONES PRIMARY */
        div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"] {
            background-color: #3b82f6 !important;
            color: white !important;
            border: none !important;
        }
        a[data-testid="stBaseLinkButton-primary"] {
            background-color: #3b82f6 !important;
            color: white !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES PDF (SÍMBOLO € SUSTITUIDO POR EUR PARA EVITAR ERROR) ---
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
    
    # Resumen
    pdf.set_font("helvetica", 'B', 10); pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 1. RESUMEN EJECUTIVO DE LA OPERACION", fill=True, ln=True); pdf.ln(2)
    pdf.set_font("helvetica", size=8.5)
    items_inv = [
        ("Aportacion Empresarial Anual (PPE)", f"{empresa_total:,.2f} EUR"),
        ("MAXIMA APORTACION PERSONAL PERMITIDA", f"{max_p:,.2f} EUR"),
        ("Inversion Total en Plan de Empleo", f"{inversion_t:,.2f} EUR"),
        ("AHORRO FISCAL ESTIMADO EN IRPF", f"{ahorro:,.2f} EUR"),
        ("Coste Real (Esfuerzo Neto Personal)", f"{esfuerzo:,.2f} EUR"),
        ("EFICIENCIA FISCAL (RETORNO IRPF)", f"{eficiencia:.2f}%")
    ]
    for i, (label, val) in enumerate(items_inv):
        pdf.set_font("helvetica", 'B' if "PERSONAL" in label or "EFICIENCIA" in label else '', 8.5)
        pdf.cell(140, 6, label, border='B' if i < 5 else 0)
        pdf.cell(0, 6, val, border='B' if i < 5 else 0, align='R', ln=True)
    
    # Tabla Fiscal
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 9); pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 2. TRAMOS IRPF APLICADOS (CATALUNYA 2026)", fill=True, ln=True); pdf.ln(2)
    pdf.set_font("helvetica", 'B', 7); pdf.set_fill_color(230, 230, 230)
    pdf.cell(60, 5, "Desde (EUR)", border=1, fill=True, align='C')
    pdf.cell(60, 5, "Hasta (EUR)", border=1, fill=True, align='C')
    pdf.cell(70, 5, "Tipo Aplicable (%)", border=1, fill=True, align='C', ln=True)
    pdf.set_font("helvetica", '', 7)
    tramos_lista = [
        (0, 12450, "19,0%"), (12450, 17707, "24,0%"), (17707, 20200, "26,0%"),
        (20200, 33007, "29,0%"), (33007, 35200, "33,5%"), (35200, 53407, "37,0%"),
        (53407, 60000, "40,0%"), (60000, 90000, "44,0%"), (90000, 120000, "46,0%"),
        (120000, 150000, "47,0%"), (150000, 175000, "48,0%"), (175000, "Inf.", "50,0%")
    ]
    for inf, sup, tipo in tramos_lista:
        pdf.cell(60, 4, f"{inf:,.0f}", border=1, align='C')
        pdf.cell(60, 4, f"{sup if isinstance(sup, str) else f'{sup:,.0f}'}", border=1, align='C')
        pdf.cell(70, 4, tipo, border=1, align='C', ln=True)

    # Desglose y Aviso Legal
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 9); pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 3. DESGLOSE TECNICO Y AVISO LEGAL", fill=True, ln=True); pdf.ln(2)
    pdf.set_font("helvetica", size=7.5)
    pdf.cell(140, 5, "Sueldo Bruto Anual:"); pdf.cell(0, 5, f"{sb:,.2f} EUR", align='R', ln=True)
    pdf.cell(140, 5, "Base Liquidable Final tras Reduccion (incluye Cuota Trabajador a la SS y Gastos Dificil Justificación):"); pdf.cell(0, 5, f"{(base_pre - max_p):,.2f} EUR", align='R', ln=True)
    
    pdf.ln(3); pdf.set_font("helvetica", 'B', 7); pdf.set_text_color(180, 0, 0)
    pdf.multi_cell(0, 4, "AVISO LEGAL: Los calculos mostrados son una estimacion basada en la normativa fiscal proyectada para 2026 en Cataluna. Esta informacion no constituye asesoramiento financiero oficial. Los resultados pueden variar segun las circunstancias personales del contribuyente.")
    
    pdf.set_y(-15); pdf.set_font("helvetica", 'I', 7); pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "Documento generado para fines de planificacion interna.", align='C', ln=True)
    return pdf.output()

@st.cache_data
def generar_pdf_visual_v2(max_p, ahorro, inversion, extra, cuota_r, meses, ya_aportado):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 15, 297, 'F')
    pdf.set_xy(25, 20)
    pdf.set_font("helvetica", 'B', 24); pdf.set_text_color(30, 58, 138); pdf.cell(0, 10, "TU HOJA DE RUTA 2026", ln=True)
    
    # Caja de Objetivo
    pdf.set_fill_color(240, 248, 255); pdf.rect(25, 45, 165, 55, 'F')
    pdf.set_xy(30, 52); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(0, 0, 0); pdf.cell(0, 10, "OBJETIVO DE APORTACION PERSONAL TOTAL:", ln=True)
    pdf.set_xy(30, 65); pdf.set_font("helvetica", 'B', 28); pdf.set_text_color(30, 58, 138); pdf.cell(0, 15, f"{max_p:,.2f} EUR", ln=True)
    pdf.set_xy(30, 82); pdf.set_font("helvetica", 'B', 14); pdf.set_text_color(34, 197, 94); 
    pdf.cell(0, 10, f"AHORRO FISCAL ESTIMADO: {ahorro:,.2f} EUR", ln=True)
    
    pdf.set_xy(25, 115); pdf.set_font("helvetica", 'B', 16); pdf.set_text_color(0, 0, 0); pdf.cell(0, 10, "ACCIONES RECOMENDADAS:", ln=True)
    pasos = [
        (f"OPCION 1: Nueva Cuota Mensual: {cuota_r:,.2f} EUR", f"Actualiza tu aportacion periodica para los {meses} meses restantes."),
        (f"OPCION 2: Ingreso Extraordinario: {extra:,.2f} EUR", f"Realiza una aportacion unica manteniendo tu cuota actual."),
        (f"Estado Actual: Ya has aportado {ya_aportado:,.2f} EUR", "Cifra acumulada hasta la fecha segun tus datos.")
    ]
    for t, s in pasos:
        pdf.set_x(30); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(30, 58, 138); pdf.cell(0, 8, t, ln=True)
        pdf.set_x(35); pdf.set_font("helvetica", '', 11); pdf.set_text_color(60, 60, 60); pdf.multi_cell(0, 6, s); pdf.ln(5)
    return pdf.output()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ DATOS NECESARIOS")
    with st.expander("👤 DATOS EMPRESA", expanded=True):
        sb = st.number_input("Sueldo Bruto Anual (€)", value=60000.0, step=1000.0)
        e_ahorro = st.number_input("Aportación Mensual Empresa (€)", value=0.0, step=25.0)
        e_riesgo = st.number_input("Prima Anual Riesgo PPE (€)", value=0.0, step=25.0)
        emp_t = min(e_ahorro * 12 + e_riesgo, 10000.0)

    CUOTA_SS_PRE = min(sb, 5101.0 * 12) * 0.0635 
    BASE_PRE_LIMIT = max(0.0, sb - CUOTA_SS_PRE - 2000.0)
    MAX_P_LIMIT = max(0.0, min(calcular_max_personal_adicional(emp_t, sb) + 1500, 10000.0 - emp_t))
    if (emp_t + MAX_P_LIMIT) > (BASE_PRE_LIMIT * 0.30): MAX_P_LIMIT = max(0.0, (BASE_PRE_LIMIT * 0.30) - emp_t)

    with st.expander("📅 APORTACIONES PERSONALES", expanded=True):
        c_m = st.number_input("Aport. periódica mensual (€)", value=0.0, step=50.0)
        e_y = st.number_input("Aport. Extras ya realizadas (€)", value=0.0, max_value=MAX_P_LIMIT, step=100.0)

# --- 5. LÓGICA DE CÁLCULO ---
hoy = datetime.date.today()
meses_restantes = 12 - hoy.month + 1 # Cálculo automático de meses restantes incluyendo el actual
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
total_mensual_previsto = c_m * meses_restantes
aportacion_extraordinaria_neta = max(0.0, pendiente_para_limite - total_mensual_previsto)

# --- 6. RENDERIZADO PRINCIPAL ---
st.markdown('<div class="main-header"><h1 style="margin:0;">📈 APORTAMAX 2026</h1></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["1. Cálculo del Límite", "2. Plan de Acción"])

with tab1:
    col_left, col_right = st.columns([1, 1.2])
    with col_left:
        st.markdown(f"""
            <div class="card" style="background-color: #1E3A8A; color: white;">
                <p style="margin:0; opacity: 0.8;">MÁXIMA APORTACIÓN PERSONAL</p>
                <h2 style="font-size: 32px; margin: 5px 0;">{max_p:,.2f} €</h2>
            </div>
            <div class="card" style="background-color: #F0FDF4; color: #166534;">
                <p style="margin:0; opacity: 0.8;">AHORRO FISCAL (IRPF)</p>
                <h2 style="font-size: 32px; margin: 5px 0;">{ahorro:,.2f} €</h2>
                <p style="margin:0; font-weight: bold;">Tax Return: {eficiencia:.1f}%</p>
            </div>
        """, unsafe_allow_html=True)
    with col_right:
        fig = go.Figure(data=[go.Pie(labels=['Esfuerzo Neto', 'Ahorro Fiscal', 'Empresa'], values=[esfuerzo_neto, ahorro, emp_t], hole=.6, marker_colors=['#3B82F6', '#10B981', '#1E293B'])])
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=300, showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)
    
    pdf_t = generar_pdf_tecnico(emp_t, max_p, (emp_t+max_p), ahorro, esfuerzo_neto, sb, CUOTA_SS, 2000.0, base_pre, eficiencia)
    st.download_button("📄 Informe Fiscal Detallado", data=pdf_t.encode('latin-1'), file_name="Informe_Fiscal.pdf", use_container_width=True)

with tab2:
    st.markdown("### 🎯 Plan Estratégico Personalizado")
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-card">Ya Aportado a día de hoy<br><b>{ya_aportado:,.2f} €</b></div>
        <div class="kpi-card">Pendiente para alcanzar tu Objetivo<br><b>{max_p - ya_aportado:,.2f} €</b></div>
        <div class="kpi-card">Meses restantes<br><b>{meses_restantes}</b></div>
    </div>""", unsafe_allow_html=True)

    if ya_aportado > max_p:
        st.error(f"⚠️ **HAS SUPERADO EL LÍMITE MÁXIMO:** Aportación de {ya_aportado:,.2f} € excede el límite de {max_p:,.2f} €.")
        st.markdown(f"""<div class="option-card" style="border-left-color: #dc2626; background-color: #fef2f2;">
            <h3 style="color: #991b1b; margin-top:0;">ATENCIÓN: EXCESO</h3>
            <p style="color: #991b1b;">Has aportado <b>{ya_aportado - max_p:,.2f} €</b> de más. Pausa tu cuota de {c_m:,.2f} € ya.</p>
        </div>""", unsafe_allow_html=True)
    elif ya_aportado + (c_m * meses_restantes) >= max_p:
        ajuste_necesario = c_m - nueva_cuota_total
        if ajuste_necesario > 0.01:
            st.warning("🔔 **AJUSTE RECOMENDADO:** Reduce tu cuota para no excederte del límite.")
            st.markdown(f"""<div class="option-card" style="border-left-color: #f59e0b; background-color: #fffbeb;">
                <h3 style="color: #92400e; margin-top:0;">✅ AJUSTE DE CUOTA</h3>
                <p style="color: #92400e;">Cambia tu aportación a <b>{nueva_cuota_total:,.2f} €/mes</b> para no exceder el límite.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.success("✅ **PLANIFICACIÓN PERFECTA**")
            st.markdown(f"""<div class="option-card" style="border-left-color: #10B981; background-color: #f0fdf4;">
                <p style="color: #065f46; font-size: 1.1em; margin:0;">Con <b>{c_m:,.2f} €/mes</b> llegarás exacto al límite legal.</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="plan-box" style="border-left: 10px solid #1e40af;">
                <div class="step-pill" style="background: #1e40af; color: white;">OPCIÓN 1 (RECOMENDADA): INCREMENTO DE TU APORTACIÓN MENSUAL AL PLAN DE PENSIONES</div>
                <div style="margin: 15px 0;">
                    <p style="margin:0; color: #64748b; font-size: 0.9rem; font-weight: bold;">SUBE TU CUOTA EN:</p>
                    <h1 style="color: #1e40af; margin:0; font-size: 1.9rem;">+{diferencia_mensual:,.2f} €<span style="font-size: 1.4rem; color: #64748b;"> / mes</span></h1>
                    <p style="margin: 5px 0 0 0; color: #1e40af; font-size: 1.1rem;">
                        Tu nueva aportación total será de <b>{nueva_cuota_total:,.2f} €/mes</b>
                    </p>
                </div>
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px dashed #cbd5e1; margin-top: 25px;">
                    <div class="step-pill" style="background: #64748b; color: white;">OPCIÓN 2: APORTACIÓN EXTRAORDINARIA</div>
                    <p style="margin: 10px 0 0 0; color: #334155; font-size: 0.8rem;">
                        Si prefieres no tocar tu cuota mensual, realiza una <b>aportación extraordinaria</b> única de:
                    </p>
                    <h2 style="color: #334155; margin: 5px 0 0 0; font-size: 1.7rem">{aportacion_extraordinaria_neta:,.2f} €</h2>
                    <p style="margin: 5px 0 0 0; color: #64748b; font-size: 0.85rem;">
                        *Manteniendo tu aportación actual de {c_m:,.2f} €/mes hasta diciembre.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- SECCIÓN CAIXABANK / APORTA+ ---
    st.markdown("---")
    st.markdown("#### 🚀 ¿Cómo realizar tu aportación?")
    col_web, col_steps = st.columns([1, 1.5])
    
    with col_web:
        st.markdown("**Vías de Acceso Online**")
        st.link_button(
            "✨ Acceder a Aporta+ (VidaCaixa)", 
            "https://aportamas.vidacaixa.es/pasos-para-el-alta-de-usuario", 
            use_container_width=True, 
            type="primary"
        )
        st.link_button(
            "🏦 Ir a CaixaBankNow", 
            "https://www.caixabank.es/particular/home/particulares_es.html", 
            use_container_width=True, 
            type="secondary"
        )
        st.info("💡 **Dato:** Aporta+ es la plataforma específica de VidaCaixa para gestionar de forma ágil tus planes de pensiones de empleo.")

    with col_steps:
        st.markdown("**Pasos a seguir:**")
        st.markdown("""
        1. **Identifícate** en tu plataforma preferida (Aporta+ o CaixaBankNow).
        2. Localiza la sección de **'Pensiones'** o **'Mis Planes'**.
        3. Selecciona tu **Plan de Empleo (PPE)** y pulsa en el botón **'Gestionar'** o **'Aportar'**.
        4. Elige el tipo de movimiento:
            * **'Aportación Única'** para ingresos puntuales.
            * **'Modificar aportación periódica'** para cambiar tu cuota mensual.
        5. Introduce el importe recomendado en tu plan y **firma la operación**.
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    pdf_v = generar_pdf_visual_v2(max_p, ahorro, (emp_t+max_p), aportacion_extraordinaria_neta, nueva_cuota_total, meses_restantes, ya_aportado)
    st.download_button(
        st.download_button("🚀 DESCARGAR HOJA DE RUTA (PDF)", data=pdf_v.encode('latin-1'), file_name="Plan_Accion.pdf", key="plan_pdf_final", use_container_width=True, type="primary")
        data=bytes(pdf_v), 
        file_name="Plan_Accion.pdf", 
        key="plan_pdf_final", 
        use_container_width=True, 
        type="primary"
    )
