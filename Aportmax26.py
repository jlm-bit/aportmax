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
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES PDF (CONTENIDO INTACTO) ---
@st.cache_data
def generar_pdf_tecnico(empresa_total, max_p, inversion_t, ahorro, esfuerzo, sb, ss, gastos, base_pre, eficiencia):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 16)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "PLANIFICACIÓN FISCAL APORTACION AL PPE", align='L')
    pdf.set_font("helvetica", '', 9)
    pdf.set_xy(10, 16)
    pdf.cell(0, 10, f"Ejercicio Fiscal 2026 | Catalunya", align='L')
    pdf.set_text_color(40, 40, 40)
    pdf.ln(20)
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 1. RESUMEN EJECUTIVO", fill=True, ln=True)
    pdf.ln(2)
    pdf.set_font("helvetica", size=8.5)
    items_inv = [
        ("Aportación Empresarial Anual", f"{empresa_total:,.2f} EUR"),
        ("APORTACION PERSONAL RECOMENDADA", f"{max_p:,.2f} EUR"),
        ("Aportación Total", f"{inversion_t:,.2f} EUR"),
        ("AHORRO FISCAL ESTIMADO (IRPF)", f"{ahorro:,.2f} EUR"),
        ("Coste (Esfuerzo Neto)", f"{(max_p - ahorro):,.2f} EUR"),
        ("EFICIENCIA FISCAL SOBRE APORTACIÓN", f"{eficiencia:.2f}%")
    ]
    for i, (label, val) in enumerate(items_inv):
        pdf.set_font("helvetica", 'B' if "PERSONAL" in label or "EFICIENCIA" in label else '', 8.5)
        pdf.cell(140, 6, label, border='B' if i < 5 else 0)
        pdf.cell(0, 6, val, border='B' if i < 5 else 0, align='R', ln=True)
    pdf.ln(3)
    pdf.set_font("helvetica", 'B', 8)
    pdf.cell(0, 5, "DESGLOSE VISUAL DE LA APORTACIÓN PERSONAL:", ln=True)
    ancho_max = 100 
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(10, pdf.get_y() + 2, ancho_max, 6, 'F')
    ancho_ahorro = (ahorro / max_p) * ancho_max if max_p > 0 else 0
    pdf.set_fill_color(34, 197, 94)
    pdf.rect(10, pdf.get_y() + 2, ancho_ahorro, 6, 'F')
    pdf.set_xy(10, pdf.get_y() + 9)
    pdf.set_font("helvetica", '', 7)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(40, 5, f"Ahorro Fiscal ({eficiencia:.1f}%)", align='L')
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 5, f"Esfuerzo Neto ({100-eficiencia:.1f}%)", align='R', ln=True)
    pdf.set_text_color(40, 40, 40); pdf.ln(5)
    pdf.set_font("helvetica", 'B', 9); pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 2. CÁLCULO TÉCNICO DE LA BASE LIQUIDABLE", fill=True, ln=True); pdf.ln(2)
    pdf.set_font("helvetica", size=7)
    items_tec = [
        ("Rendimientos Íntegros del Trabajo (Sueldo Bruto)", f"{sb:,.2f} EUR"),
        ("Gastos deducibles (Seguridad Social estimada)", f"-{ss:,.2f} EUR"),
        ("Otros gastos deducibles (Art. 19.2 Ley IRPF)", "-2,000.00 EUR"),
        ("Base Liquidable Previa a Reducción", f"{base_pre:,.2f} EUR"),
        ("Reducción por aportaciones a PPE (Límite aplicado)", f"-{max_p:,.2f} EUR"),
        ("BASE LIQUIDABLE FINAL ESTIMADA", f"{(base_pre - max_p):,.2f} EUR")
    ]
    for i, (label, val) in enumerate(items_tec):
        pdf.set_font("helvetica", 'B' if "FINAL" in label else '', 7)
        pdf.cell(140, 6, label, border='B' if i < 5 else 0)
        pdf.cell(0, 6, val, border='B' if i < 5 else 0, align='R', ln=True)
    pdf.ln(3)
    pdf.set_font("helvetica", 'B', 9); pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 3. ESCALA DE GRAVAMEN APLICABLE (CATALUÑA 2026)", fill=True, ln=True); pdf.ln(2)
    pdf.set_font("helvetica", 'B', 6.5); pdf.set_fill_color(230, 230, 230)
    pdf.cell(60, 6, "Desde Base (EUR)", border=1, align='C', fill=True)
    pdf.cell(60, 6, "Hasta Base (EUR)", border=1, align='C', fill=True)
    pdf.cell(0, 6, "Tipo Marginal (%)", border=1, ln=True, align='C', fill=True)
    tramos_cat = [
        ("0,00", "12.450,00", "19,00%"), ("12.450,00", "17.707,00", "24,00%"),
        ("17.707,00", "20.200,00", "26,00%"), ("20.200,00", "33.007,00", "29,00%"),
        ("33.007,00", "35.200,00", "33,50%"), ("35.200,00", "53.407,00", "37,00%"),
        ("53.407,00", "60.000,00", "40,00%"), ("60.000,00", "90.000,00", "44,00%"),
        ("90.000,00", "120.000,00", "46,00%"), ("120.000,00", "150.000,00", "47,00%"),
        ("150.000,00", "175.000,00", "48,00%"), ("175.000,00", "En adelante", "50,00%")
    ]
    for b1, b2, t in tramos_cat:
        pdf.cell(60, 4.5, b1, border=1, align='R')
        pdf.cell(60, 4.5, b2, border=1, align='R')
        pdf.cell(0, 4.5, t, border=1, ln=True, align='C')
    pdf.ln(3); pdf.set_font("helvetica", 'B', 8); pdf.cell(0, 5, "ANEXO TÉCNICO Y LIMITACIONES LEGALES", ln=True)
    pdf.set_font("helvetica", size=7); pdf.set_text_color(80, 80, 80)
    legal_text = (
        "- Límite de Aportación: El límite financiero anual conjunto para planes de pensiones es de 1,500 EUR, pudiendo incrementarse en 8,500 EUR adicionales por contribuciones de empresa.\n"
        "- Coeficiente Personal: La aportación del empleado está sujeta a los multiplicadores legales basados en la contribución empresarial (Ley 12/2022).\n"
        "- Rendimientos: Los cálculos se basan en la normativa fiscal prevista para 2026 en la Comunidad Autónoma de Cataluña."
    )
    pdf.multi_cell(0, 3.5, legal_text)
    pdf.set_y(-22); pdf.set_font("helvetica", 'I', 6); pdf.cell(0, 2, "Este documento es una simulación informativa. No sustituye la consulta con un profesional fiscal.", align='C')
    return pdf.output()

@st.cache_data
def generar_pdf_visual_v2(max_p, ahorro, inversion, extra, cuota_r, meses):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 15, 297, 'F')
    pdf.set_xy(25, 20); pdf.set_font("helvetica", 'B', 28); pdf.set_text_color(30, 58, 138); pdf.cell(0, 10, "TU HOJA DE RUTA 2026", ln=True)
    pdf.set_fill_color(240, 248, 255); pdf.rect(25, 55, 165, 45, 'F')
    pdf.set_xy(30, 62); pdf.set_font("helvetica", 'B', 14); pdf.set_text_color(0, 0, 0); pdf.cell(0, 10, "OBJETIVO DE APORTACION PERSONAL:", ln=True)
    pdf.set_xy(30, 75); pdf.set_font("helvetica", 'B', 32); pdf.set_text_color(30, 58, 138); pdf.cell(0, 15, f"{max_p:,.2f} EUR", ln=True)
    pdf.set_xy(25, 115); pdf.set_font("helvetica", 'B', 18); pdf.set_text_color(0, 0, 0); pdf.cell(0, 10, "SUGERENCIAS DE ACTUACIÓN:", ln=True)
    pasos = [
        (f"Opcion 1: Aportacion Extra de {extra:,.2f} EUR", "Realizar una aportacion única y seguir con tus aportaciones mensual actuales."), 
        (f"Opcion 2: Incrementar la aportación periódica mensual hasta alcanzar {cuota_r:,.2f} EUR", "Incrementa ya tu aportación mensual este mes y los que siguen."), 
        (f"En cualquier caso, recuperarás {ahorro:,.2f} EUR en tu IRPF del ejercicio 2026.", "Dinero que dejas de pagar en impuestos y que puedes dedicar a tus necesidades actuales, ocio, o en lo que quieras.")
    ]
    for titulo, sub in pasos:
        pdf.set_x(30); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(30, 58, 138); pdf.cell(0, 8, titulo, ln=True)
        pdf.set_x(35); pdf.set_font("helvetica", '', 11); pdf.set_text_color(60, 60, 60); pdf.multi_cell(0, 6, sub); pdf.ln(5)
    return pdf.output()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ DATOS NECESARIOS PARA LA SIMULACIÓN")
    with st.expander("👤 DATOS EMPRESA", expanded=True):
        sb = st.number_input("Sueldo Bruto Anual (€)", value=60000.0, min_value=0.0, step=1000.0)
        e_ahorro = st.number_input("Aportación Mensual Empresa (€)", value=0.0, min_value=0.0, max_value=833.33, step=25.0)
        e_riesgo = st.number_input("Prima Anual Riesgo PPE (€)", value=0.0, min_value=0.0, max_value=10000.0, step=25.0)
        emp_t = e_ahorro * 12 + e_riesgo
        if emp_t > 10000.0:
            st.error("La aportación de empresa no puede superar los 10.000€")
            emp_t = 10000.0

    # Límite dinámico basado en ley
    CUOTA_SS_PRE = min(sb, 5101.0 * 12) * 0.0635 
    BASE_PRE_LIMIT = max(0.0, sb - CUOTA_SS_PRE - 2000.0)
    MAX_P_LIMIT = max(0.0, min(calcular_max_personal_adicional(emp_t, sb) + 1500, 10000.0 - emp_t))
    if (emp_t + MAX_P_LIMIT) > (BASE_PRE_LIMIT * 0.30): MAX_P_LIMIT = max(0.0, (BASE_PRE_LIMIT * 0.30) - emp_t)

    with st.expander("📅 APORTACIONES PERSONALES", expanded=True):
        c_m = st.number_input("Aport. periódica mensual (€)", value=0.0, min_value=0.0, step=50.0)
        e_y = st.number_input("Aport. Extras ya realizadas (€)", value=0.0, min_value=0.0, max_value=MAX_P_LIMIT, step=100.0)

# --- 5. LÓGICA DE CÁLCULO ---
meses_restantes = 10 
meses_pasados = 12 - meses_restantes
CUOTA_SS = min(sb, 5101.0 * 12) * 0.0635 
base_pre = max(0.0, sb - CUOTA_SS - 2000.0)
max_p = MAX_P_LIMIT

ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
eficiencia = (ahorro / max_p * 100) if max_p > 0 else 0
esfuerzo_neto = max_p - ahorro

# REVISIÓN LÓGICA PLAN DE ACCIÓN
ya_aportado = (c_m * meses_pasados) + e_y
pendiente_para_limite = max(0.0, max_p - ya_aportado)
nueva_cuota_total = pendiente_para_limite / meses_restantes if meses_restantes > 0 else 0
diferencia_mensual = nueva_cuota_total - c_m

# NUEVA LÓGICA: Extraordinaria considerando que el usuario MANTIENE su cuota mensual actual hasta fin de año
total_mensual_previsto = c_m * meses_restantes
aportacion_extraordinaria_neta = max(0.0, pendiente_para_limite - total_mensual_previsto)

# --- 6. RENDERIZADO PRINCIPAL ---
# --- 6. RENDERIZADO PRINCIPAL ---
st.markdown('<div class="main-header"><h1 style="margin:0;">📈 APORTAMAX 2026</h1></div>', unsafe_allow_html=True)

# CSS Adicional para la Tab 2
st.markdown("""
    <style>
        .stat-box {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .step-number {
            background-color: #3b82f6;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 10px;
        }
    </style>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 Cálculo del Límite", "🎯 Plan de Acción"])

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
    st.download_button("📄 Descargar Informe Fiscal Detallado", data=bytes(pdf_t), file_name="Informe_Fiscal_2026.pdf", key="tech_pdf", use_container_width=True)

with tab2:
    st.markdown("### 🎯 Tu Hoja de Ruta Personalizada")
    
    # Resumen de situación actual en columnas
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-box">Aportado hoy<br><b>{ya_aportado:,.2f} €</b></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box">Objetivo<br><b>{max_p:,.2f} €</b></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box">Pendiente<br><b>{max_p - ya_aportado:,.2f} €</b></div>', unsafe_allow_html=True)
    
    st.markdown("---")

    if ya_aportado + (c_m * meses_restantes) >= max_p:
        st.balloons()
        st.markdown(f"""
            <div class="option-card" style="border-left-color: #10B981; background-color: #f0fdf4;">
                <h3 style="color: #065f46; margin-top:0;">✅ ¡OBJETIVO EN CURSO!</h3>
                <p style="color: #065f46; font-size: 1.1em;">Con tu cuota actual de <b>{c_m} €/mes</b> alcanzarás el límite legal sin hacer nada más.</p>
                <p style="color: #374151; font-size: 0.9em;">No necesitas realizar ajustes ni aportaciones extraordinarias para agotar el beneficio fiscal.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        color_card = "#1e40af" # Azul profesional
        prefijo = "+" if diferencia_mensual >= 0 else ""
        
        st.markdown(f"""
            <div class="option-card" style="border-left-color: {color_card};">
                <p style="text-transform: uppercase; font-weight: bold; color: {color_card}; margin-bottom: 10px; font-size: 0.8em;">ESTRATEGIA RECOMENDADA</p>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h3 style="margin:0; color: #1f2937;">Ajuste de Cuota Mensual</h3>
                        <h1 style="color: {color_card}; margin: 5px 0;">{nueva_cuota_total:,.2f} €<span style="font-size: 0.4em; color: #6b7280;"> / mes</span></h1>
                    </div>
                    <div style="text-align: right; background: #eff6ff; padding: 10px 20px; border-radius: 10px;">
                        <span style="font-size: 0.8em; color: #1e40af;">INCREMENTO</span><br>
                        <b style="font-size: 1.2em; color: #1e40af;">{prefijo}{diferencia_mensual:,.2f} €</b>
                    </div>
                </div>
                <p style="font-size: 0.9em; color: #4b5563; margin-top: 15px; line-height: 1.5;">
                    <span class="step-number">1</span> Prorratea el beneficio en los <b>{meses_restantes} meses</b> que quedan del año.<br><br>
                    <span class="step-number">2</span> <b>Alternativa:</b> Si prefieres no tocar tu cuota mensual de {c_m:,.2f} €, realiza una única aportación de <b>{aportacion_extraordinaria_neta:,.2f} €</b> antes del 31 de diciembre.
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # El PDF se genera con la alternativa calculada
    pdf_v = generar_pdf_visual_v2(max_p, ahorro, (emp_t+max_p), aportacion_extraordinaria_neta, nueva_cuota_total, meses_restantes)
    st.download_button("🚀 DESCARGAR HOJA DE RUTA (PDF)", data=bytes(pdf_v), file_name="Plan_Accion_2026.pdf", key="plan_pdf", use_container_width=True, type="primary")
