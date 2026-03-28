import numpy as np
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

# --- 3. FUNCIONES PDF ---
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

    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 9); pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 3. DESGLOSE TECNICO Y AVISO LEGAL", fill=True, ln=True); pdf.ln(2)
    pdf.set_font("helvetica", size=7.5)
    pdf.cell(140, 5, "Sueldo Bruto Anual:"); pdf.cell(0, 5, f"{sb:,.2f} EUR", align='R', ln=True)
    pdf.cell(140, 5, "Base Liquidable Final tras Reduccion:"); pdf.cell(0, 5, f"{(base_pre - max_p):,.2f} EUR", align='R', ln=True)
    
    pdf.ln(3); pdf.set_font("helvetica", 'B', 7); pdf.set_text_color(180, 0, 0)
    pdf.multi_cell(0, 4, "AVISO LEGAL: Calculos estimados segun normativa 2026.")
    
    pdf.set_y(-15); pdf.set_font("helvetica", 'I', 7); pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "Documento generado para fines de planificacion interna.", align='C', ln=True)
    return pdf.output(dest='S').encode('latin-1', errors='replace')

@st.cache_data
def generar_pdf_visual_v2(max_p, ahorro, inversion, extra, cuota_r, meses, ya_aportado):
    pdf = FPDF()
    pdf.add_page()
    
    # --- Encabezado ---
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_xy(10, 12)
    pdf.set_font("helvetica", 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "TU ESTRATEGIA DE AHORRO 2026", align='C', ln=True)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 8, "Plan Personalizado para la Maximizacion del Beneficio Fiscal", align='C', ln=True)

    # --- Bloque 1: El Objetivo ---
    pdf.ln(15)
    pdf.set_fill_color(240, 248, 255); pdf.rect(10, 45, 190, 45, 'F')
    pdf.set_xy(15, 50); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, "OBJETIVO DE APORTACION PERSONAL TOTAL:", ln=True)
    pdf.set_x(15); pdf.set_font("helvetica", 'B', 28); pdf.cell(0, 15, f"{max_p:,.2f} EUR", ln=True)
    pdf.set_x(15); pdf.set_font("helvetica", 'B', 14); pdf.set_text_color(34, 197, 94)
    pdf.cell(0, 10, f"AHORRO FISCAL ESTIMADO (IRPF): {ahorro:,.2f} EUR", ln=True)

    # --- Bloque 2: Plan de Ejecucion ---
    pdf.set_xy(10, 100); pdf.set_font("helvetica", 'B', 14); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "COMO ALCANZAR TU MAXIMO AHORRO:", ln=True)
    pdf.ln(2)
    
    # Opcion A
    pdf.set_x(15); pdf.set_font("helvetica", 'B', 11); pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 8, f"OPCION A: Nueva Cuota Mensual de {cuota_r:,.2f} EUR", ln=True)
    pdf.set_x(20); pdf.set_font("helvetica", '', 10); pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, f"Ajusta tu aportacion periodica para los {meses} meses restantes del año. Es la forma mas comoda de diluir el esfuerzo de ahorro.")
    pdf.ln(3)

    # Opcion B
    pdf.set_x(15); pdf.set_font("helvetica", 'B', 11); pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 8, f"OPCION B: Aportacion Extraordinaria de {extra:,.2f} EUR", ln=True)
    pdf.set_x(20); pdf.set_font("helvetica", '', 10); pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, "Realiza un ingreso unico antes del 31 de diciembre. Ideal si dispones de liquidez puntual o bonus.")
    
    # --- Bloque 3: Guia de Pasos ---
    pdf.ln(10)
    pdf.set_fill_color(248, 250, 252); pdf.rect(10, 165, 190, 85, 'F')
    pdf.set_xy(15, 170); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "PASOS PARA REALIZAR LA APORTACION:", ln=True)
    
    pdf.set_font("helvetica", 'B', 10); pdf.set_x(15); pdf.cell(0, 8, "En CaixaBankNow / Aporta+:", ln=True)
    pdf.set_font("helvetica", '', 10); pdf.set_text_color(80, 80, 80)
    pasos = [
        "1. Accede a tu banca online o al portal Aporta+ de VidaCaixa.",
        "2. Dirigete a la seccion de 'Pensiones' o 'Mis Planes de Empleo'.",
        "3. Selecciona tu Plan de Empleo (PPE) actual y pulsa en 'Gestionar' u 'Operar'.",
        "4. Elige 'Aportacion Unica' o 'Modificar Cuota Mensual' segun tu preferencia.",
        "5. Introduce el importe recomendado en este informe y firma la operacion.",
        "6. ¡Listo! Tu ahorro fiscal se reflejara en la proxima Declaracion de la Renta."
    ]
    for paso in pasos:
        pdf.set_x(20); pdf.multi_cell(0, 6, paso)

    # --- Pie de pagina ---
    pdf.set_y(-25); pdf.set_font("helvetica", 'I', 8); pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Nota: Este documento es una simulacion basada en la normativa fiscal de Catalunya 2026.", align='C', ln=True)
    pdf.cell(0, 5, "Asegurate de realizar tus aportaciones antes del cierre del ejercicio (31/12).", align='C')
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- 4. SIDEBAR (CON MIN_VALUE=0.0) ---

with st.sidebar:
    st.header("⚙️ DATOS NECESARIOS")
    with st.expander("👤 DATOS EMPRESA", expanded=True):
       # edad = st.number_input("Edad Actual", value=40, min_value=18, max_value=66)
        sb = st.number_input("Sueldo Bruto Anual (€)", value=60000.0, step=1000.0, min_value=0.0)
        e_ahorro = st.number_input("Aportación Mensual Empresa (€)", value=0.0, step=25.0, min_value=0.0)
        e_riesgo = st.number_input("Prima Anual Riesgo PPE (€)", value=0.0, step=25.0, min_value=0.0)
        emp_t = min(e_ahorro * 12 + e_riesgo, 10000.0)

    CUOTA_SS_PRE = min(sb, 5101.0 * 12) * 0.0635 
    BASE_PRE_LIMIT = max(0.0, sb - CUOTA_SS_PRE - 2000.0)
    MAX_P_LIMIT = max(0.0, min(calcular_max_personal_adicional(emp_t, sb) + 1500, 10000.0 - emp_t))
    if (emp_t + MAX_P_LIMIT) > (BASE_PRE_LIMIT * 0.30): MAX_P_LIMIT = max(0.0, (BASE_PRE_LIMIT * 0.30) - emp_t)

    with st.expander("📅 APORTACIONES PERSONALES", expanded=True):
        c_m = st.number_input("Aport. periódica mensual (€)", value=0.0, step=50.0, min_value=0.0)
        e_y = st.number_input("Aport. Extras ya realizadas (€)", value=0.0, max_value=max(0.0, MAX_P_LIMIT), step=100.0, min_value=0.0)

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
total_mensual_previsto = c_m * meses_restantes
aportacion_extraordinaria_neta = max(0.0, pendiente_para_limite - total_mensual_previsto)

# --- CÁLCULOS GLOBALES (Poner esto ANTES de los st.tabs) ---
# Sumamos lo que pone la empresa y lo que pones tú (el máximo permitido)
total_inv = emp_t + max_p 

# Calculamos el ahorro y los meses (ya lo tienes en tu lógica anterior)
ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
# años_jub = 67 - edad  # 'edad' viene del sidebar

# --- 6. RENDERIZADO PRINCIPAL ---
st.markdown('<div class="main-header"><h1 style="margin:0;">📈 APORTAMAX 2026</h1></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["      💰    Cálculo Fiscal   ", "      🎯    Plan de Acción   ", "      🚀    Proyección Jubilación   "])

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
    
    # ... (Todo el código previo igual hasta la sección del gráfico en el tab1)

    with col_right:
        # 1. Calculamos el valor total para la etiqueta central
        total_inversion = esfuerzo_neto + ahorro + emp_t
        
        fig = go.Figure(data=[go.Pie(
            labels=['Esfuerzo Neto', 'Ahorro Fiscal', 'Empresa'], 
            values=[esfuerzo_neto, ahorro, emp_t], 
            hole=.6, 
            marker_colors=['#3B82F6', '#10B981', '#1E293B'],
            textinfo='none' # Quitamos los números de los quesitos para que quede limpio
        )])
        
        # 2. Añadimos la anotación central
        fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0), 
            height=300, 
            showlegend=True, 
            legend=dict(orientation="h", y=-0.1),
            annotations=[dict(
                text=f'TOTAL<br><b>{total_inversion:,.0f} €</b>', 
                x=0.5, y=0.5, 
                font_size=16, 
                showarrow=False,
                font_family="Arial"
            )]
        )
        st.plotly_chart(fig, use_container_width=True)

  
    
   
    
    pdf_t = generar_pdf_tecnico(emp_t, max_p, (emp_t+max_p), ahorro, esfuerzo_neto, sb, CUOTA_SS, 2000.0, base_pre, eficiencia)
    st.download_button("📄 Informe Fiscal Detallado", data=pdf_t, file_name="informe_fiscal_2026.pdf", mime="application/pdf")

with tab2:
    st.markdown("### 🎯 Plan Estratégico Personalizado")
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-card">Ya Aportado a día de hoy<br><b>{ya_aportado:,.2f} €</b></div>
        <div class="kpi-card">Pendiente para alcanzar tu Objetivo<br><b>{max_p - ya_aportado:,.2f} €</b></div>
        <div class="kpi-card">Meses restantes<br><b>{meses_restantes}</b></div>
    </div>""", unsafe_allow_html=True)

    if ya_aportado > max_p:
        st.error(f"⚠️ **HAS SUPERADO EL LÍMITE:** Aportación de {ya_aportado:,.2f} € excede el límite de {max_p:,.2f} €.")
    elif ya_aportado + (c_m * meses_restantes) >= max_p:
        st.success("✅ **PLANIFICACIÓN PERFECTA**")
    else:
        st.markdown(f"""
            <div class="plan-box" style="border-left: 10px solid #1e40af;">
                <div class="step-pill" style="background: #1e40af; color: white;">OPCIÓN 1 (RECOMENDADA)</div>
                <h1 style="color: #1e40af; margin:0; font-size: 1.9rem;">+{diferencia_mensual:,.2f} €<span style="font-size: 1.4rem; color: #64748b;"> / mes</span></h1>
                <p>Nueva cuota total: <b>{nueva_cuota_total:,.2f} €/mes</b></p>
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px dashed #cbd5e1; margin-top: 25px;">
                    <div class="step-pill" style="background: #64748b; color: white;">OPCIÓN 2: APORTACIÓN EXTRAORDINARIA</div>
                    <h2 style="color: #334155; margin: 5px 0 0 0; font-size: 1.7rem">{aportacion_extraordinaria_neta:,.2f} €</h2>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🚀 ¿Cómo realizar tu aportación?")
    col_web, col_steps = st.columns([1, 1.5])
    with col_web:
        st.markdown("**Vías de Acceso Online**")
        st.link_button("✨ Acceder a Aporta+ (VidaCaixa)", "https://aportamas.vidacaixa.es/pasos-para-el-alta-de-usuario", use_container_width=True, type="primary")
        st.link_button("🏦 Ir a CaixaBankNow", "https://www.caixabank.es/particular/home/particulares_es.html", use_container_width=True, type="secondary")
        st.info("💡 **Dato:** Aporta+ es la plataforma de VidaCaixa para gestionar tus planes de empleo.")
    with col_steps:
        st.markdown("**Pasos a seguir:**")
        st.markdown("""
        1. **Identifícate** en tu plataforma (Aporta+ o CaixaBankNow).
        2. Localiza la sección de **'Pensiones'** o **'Mis Planes'**.
        3. Selecciona tu **Plan de Empleo (PPE)** y pulsa **'Gestionar'**.
        4. Elige **'Aportación Única'** o **'Modificar periódica'**.
        5. Introduce el importe y **firma la operación**.
        """)

    pdf_v = generar_pdf_visual_v2(max_p, ahorro, (emp_t+max_p), aportacion_extraordinaria_neta, nueva_cuota_total, meses_restantes, ya_aportado)
    st.download_button("🚀 DESCARGAR HOJA DE RUTA (PDF)", data=pdf_v, file_name="hoja_ruta_2026.pdf", mime="application/pdf")

with tab3:
    st.markdown("### 🔮 Comparativa de Renta Mensual: Plan Full vs. Solo Empresa")
    
    # 1. Entradas de Datos
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        edad_act = st.number_input("Tu Edad Actual", value=40, min_value=18, max_value=62, key="edad_tab3")
        saldo_existente = st.number_input("Saldo acumulado actual en el Plan (€)", value=0.0, step=1000.0, min_value=0.0, key="saldo_tab3")
    
    with col_in2:
        edad_jub = st.radio("Edad prevista de jubilación", [63, 64, 65, 66, 67], index=4, horizontal=True, key="jub_tab3")
        rent_pct = st.slider("Rentabilidad anual estimada (%)", 0.0, 10.0, 4.0, key="rent_tab3")
    
    # --- Lógica de Simulación (Aportaciones fijas) ---
    rent_dec = rent_pct / 100
    edades = np.arange(edad_act, edad_jub + 1)
    
    cap_total_evol = []
    solo_capital_evol = []
    interes_evol = []
    cap_solo_empresa_evol = []
    
    saldo_a = saldo_existente
    saldo_b = saldo_existente
    aport_acum_a = saldo_existente
    
    # Cuotas FIJAS basadas en el cálculo de 2026
    cuota_empresa_fija = emp_t 
    cuota_empleado_fija = max_p - e_riesgo 
    
    for i in range(len(edades)):
        # ESCENARIO A: Plan Full
        int_a = saldo_a * rent_dec
        cap_total_evol.append(saldo_a)
        solo_capital_evol.append(aport_acum_a)
        interes_evol.append(saldo_a - aport_acum_a)
        
        # ESCENARIO B: Solo Empresa
        int_b = saldo_b * rent_dec
        cap_solo_empresa_evol.append(saldo_b)
        
        # Actualización de saldos
        saldo_a += (cuota_empresa_fija + cuota_empleado_fija) + int_a
        saldo_b += cuota_empresa_fija + int_b
        aport_acum_a += (cuota_empresa_fija + cuota_empleado_fija)

    # 2. Gráfico Comparativo
    fig_j = go.Figure()
    fig_j.add_trace(go.Scatter(
        x=edades, y=solo_capital_evol,
        mode='lines', name='Capital Aportado (Tú + Emp)',
        stackgroup='one', fillcolor='rgba(30, 58, 138, 0.7)', line=dict(width=0)
    ))
    fig_j.add_trace(go.Scatter(
        x=edades, y=interes_evol,
        mode='lines', name='Intereses Acumulados',
        stackgroup='one', fillcolor='rgba(16, 185, 129, 0.6)', line=dict(width=0)
    ))
    fig_j.add_trace(go.Scatter(
        x=edades, y=cap_solo_empresa_evol,
        mode='lines', name='Si dejas de aportar tú',
        line=dict(color='#EF4444', width=3, dash='dot')
    ))

    fig_j.update_layout(
        title=f"Proyección de Capital hasta los {edad_jub} años",
        xaxis_title="Edad", yaxis_title="Euros (€)",
        hovermode='x unified', height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_j, use_container_width=True)

    # 3. Cálculo de las 2 Rentas Mensuales
    años_renta = 20
    meses = años_renta * 12
    
    cap_final_full = cap_total_evol[-1]
    cap_final_solo_emp = cap_solo_empresa_evol[-1]
    
    renta_full = cap_final_full / meses
    renta_solo_emp = cap_final_solo_emp / meses
    dif_renta = renta_full - renta_solo_emp

    # 4. Panel de Resultados Comparativo
    st.markdown("---")
    st.markdown("#### 💰 Comparativa de Renta Mensual (Consumo en 20 años)")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Renta PLAN FULL", f"{renta_full:,.2f} €/mes", help="Aportando tú y la empresa.")
    c2.metric("Renta SOLO EMPRESA", f"{renta_solo_emp:,.2f} €/mes", delta=f"-{dif_renta:,.2f} €", delta_color="inverse")
    c3.metric("Capital Final Full", f"{cap_final_full:,.0f} €")

    # Mensaje de cierre potente
    st.warning(f"💡 **Decisión clave:** Mantener tu aportación hoy supone cobrar **{dif_renta:,.2f} € más cada mes** durante toda tu jubilación. "
               f"Sin tu parte, el fondo final se quedaría en **{cap_final_solo_emp:,.0f} €**.")
