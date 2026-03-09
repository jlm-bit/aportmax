import streamlit as st
from fpdf import FPDF
import pandas as pd
import datetime

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
        .block-container {padding-top: 1rem !important;}
        [data-testid="stSidebar"] h3 { color: var(--text-color) !important; }
        [data-testid="stSidebar"] { background-color: transparent !important; }
        .main-header {
            background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
            padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("### Tus datos personales. AÑO 2026")
    sb = st.number_input("Sueldo Bruto Anual (€)", value=60000.0, step=1000.0, min_value=0.0)
    empresa_ahorro = st.number_input("Aport. prevista Empresa Jubilación (€)", value=1800.0, step=100.0, min_value=0.0, max_value=10000.0)
    empresa_riesgo = st.number_input("Prima Riesgo PPE (€)", value=0.0, step=50.0, min_value=0.0, max_value=10000.0)
    
    empresa_total = empresa_ahorro + empresa_riesgo
    st.markdown("---")
    
    if empresa_total > 10000:
        st.error(f"❌ La aportación de empresa ({empresa_total:,.0f}€) no puede superar los 10.000€ legales.")
        empresa_total = 10000.0
    elif empresa_total > 4250:
        st.warning(f"⚠️ Aportación Empresa ({empresa_total:,.0f}€). Tope 10.000€.")

    BASE_MAX_SS = 5101 * 12
    CUOTA_SS = min(sb, BASE_MAX_SS) * 0.0635
    GASTOS_TRABAJO = 2000.0
    base_pre = max(0.0, sb - CUOTA_SS - GASTOS_TRABAJO)
    max_personal_coef = calcular_max_personal_adicional(empresa_total, sb)
    max_personal_posible = max(0.0, min(max_personal_coef + 1500, 10000 - empresa_total))
    
    limite_30_pct = base_pre * 0.30
    inversion_total_teorica = empresa_total + max_personal_posible
    
    st.info("✅ Tramos IRPF Cataluña 2026")
    if inversion_total_teorica > limite_30_pct:
        st.error(f"⚠️ Tope 30% Base: {limite_30_pct:,.0f}€")
        inversion_total = limite_30_pct
        max_personal_posible = max(0.0, inversion_total - empresa_total)
    else:
        inversion_total = inversion_total_teorica

# --- 4. CÁLCULOS FINALES ---
cuota_inicial = calcular_irpf_cat(base_pre)
cuota_final = calcular_irpf_cat(base_pre - max_personal_posible)
ahorro_euros = cuota_inicial - cuota_final
eficiencia_fiscal_pct = (ahorro_euros / max_personal_posible * 100) if max_personal_posible > 0 else 0
coste_neto_trabajador = (max_personal_posible - ahorro_euros) if max_personal_posible > 0 else 0
mes14 = max_personal_posible / 14
marginal_pdf = (calcular_irpf_cat(base_pre + 100) - calcular_irpf_cat(base_pre)) / 100 * 100

# --- 5. FUNCIONES PDF ---

@st.cache_data

def generar_pdf_tecnico(empresa_total, max_personal_posible, inversion_total, ahorro_euros, coste_neto_trabajador, sb, CUOTA_SS, GASTOS_TRABAJO, base_pre, eficiencia_fiscal_pct, marginal):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", 'B', 24); pdf.cell(0, 15, "APORTAMAX 2026", align='C', ln=True)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 5, "Informe de Optimizacion Fiscal PPE", align='C', ln=True)
    pdf.set_text_color(0, 0, 0); pdf.ln(20)

    bloques = [
        ("1. IMPACTO DE LA APORTACION Y AHORRO", [
            ("(1) Aportacion Empresa (Contribucion)", f"{empresa_total:,.2f} EUR"),
            ("(2) APORTACION PERSONAL MAXIMA POSIBLE", f"{max_personal_posible:,.2f} EUR"),
            ("(3)=(1+2) Inversion Total en el Plan", f"{inversion_total:,.2f} EUR"),
            ("(4) AHORRO FISCAL (IRPF) ESTIMADO", f"{ahorro_euros:,.2f} EUR"),
            ("(5)=(2-4) ESFUERZO NETO (Tu coste real)", f"{coste_neto_trabajador:,.2f} EUR")
        ], (230, 240, 255)),
        ("2. ESCALA DE GRAVAMEN (CATALUNYA 2026)", [
            ("Tu Tipo Marginal Aplicado", f"{marginal:.2f} %"),
            ("Ahorro Fiscal (por cada 100 EUR aportados)", f"{eficiencia_fiscal_pct:.2f} EUR")
        ], (255, 245, 220)),
        ("3. DETALLE TECNICO DE LA BASE", [
            ("Sueldo Bruto Anual", f"{sb:,.2f} EUR"),
            ("(-) Seguridad Social", f"-{CUOTA_SS:,.2f} EUR"),
            ("Base Liquidable Previa", f"{base_pre:,.2f} EUR"),
            ("(-) Reduccion PPE", f"-{max_personal_posible:,.2f} EUR"),
            ("Base Liquidable Final", f"{base_pre - max_personal_posible:,.2f} EUR")
        ], (240, 240, 240))
    ]

    for titulo, datos, color in bloques:
        pdf.set_font("helvetica", 'B', 12); pdf.set_fill_color(*color); pdf.cell(0, 10, f" {titulo}", fill=True, ln=True)
        pdf.set_font("helvetica", size=10)
        for d, v in datos:
            pdf.cell(130, 9, d, border='B'); pdf.cell(0, 9, v, border='B', align='R', ln=True)
        pdf.ln(5)

    # --- TABLA DE TRAMOS (Sin símbolos especiales) ---
    pdf.set_font("helvetica", 'B', 12); pdf.set_fill_color(220, 230, 220); pdf.cell(0, 10, " 4. TABLA DE TRAMOS IRPF CATALUNYA 2026 (Estimada)", fill=True, ln=True)
    pdf.set_font("helvetica", 'B', 9)
    pdf.cell(65, 8, "Desde Base (EUR)", border=1, align='C') # <-- '€' cambiado por 'EUR'
    pdf.cell(65, 8, "Hasta Base (EUR)", border=1, align='C') # <-- '€' cambiado por 'EUR'
    pdf.cell(60, 8, "Tipo Aplicable (%)", border=1, align='C', ln=True)
    pdf.set_font("helvetica", size=8)
    
    tramos_vis = [
        ("0", "12.450", "19,0%"), ("12.450", "17.707", "24,0%"), ("17.707", "20.200", "26,0%"),
        ("20.200", "33.007", "29,0%"), ("33.007", "35.200", "33,5%"), ("35.200", "53.407", "37,0%"),
        ("53.407", "60.000", "40,0%"), ("60.000", "90.000", "44,0%"), ("90.000", "120.000", "46,0%"),
        ("120.000", "150.000", "47,0%"), ("150.000", "175.000", "48,0%"), ("175.000", "En adelante", "50,0%")
    ]
    for d, h, t in tramos_vis:
        pdf.cell(65, 6, d, border=1, align='C')
        pdf.cell(65, 6, h, border=1, align='C')
        pdf.cell(60, 6, t, border=1, align='C', ln=True)

    # --- Aviso Legal (Sin tildes críticas si diera error) ---
    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 9); pdf.cell(0, 5, "5. AVISO LEGAL Y CLAUSULA DE RESPONSABILIDAD", ln=True)
    pdf.set_font("helvetica", size=7); pdf.set_text_color(100, 100, 100)
    aviso = ("Este informe es una simulacion basada en la normativa fiscal prevista para 2026 en Catalunya. "
             "Los resultados tienen caracter informativo y no constituyen asesoramiento financiero, legal o fiscal vinculante. "
             "Se recomienda contrastar estos datos con un asesor profesional antes de realizar cualquier operacion.")
    pdf.multi_cell(0, 4, aviso)
    pdf.ln(2)
    pdf.set_font("helvetica", 'I', 7)
    pdf.cell(0, 5, "Generado por AportaMax 2026 - Herramienta de Planificacion Financiero Fiscal", align='R', ln=True)
    return pdf.output()

@st.cache_data
def generar_pdf_visual_v2(max_p, ahorro, inversion, extra, cuota_r, meses):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 15, 297, 'F')
    pdf.set_xy(25, 20); pdf.set_font("helvetica", 'B', 28); pdf.set_text_color(30, 58, 138); pdf.cell(0, 10, "TU HOJA DE RUTA 2026", ln=True)
    pdf.set_xy(25, 32); pdf.set_font("helvetica", '', 12); pdf.set_text_color(120, 120, 120); pdf.cell(0, 10, "Sigue estos pasos para maximizar tu patrimonio", ln=True)
    
    pdf.set_fill_color(240, 248, 255); pdf.rect(25, 55, 165, 45, 'F')
    pdf.set_xy(30, 62); pdf.set_font("helvetica", 'B', 14); pdf.set_text_color(0, 0, 0); pdf.cell(0, 10, "OBJETIVO DE APORTACION PERSONAL:", ln=True)
    pdf.set_xy(30, 75); pdf.set_font("helvetica", 'B', 32); pdf.set_text_color(30, 58, 138); pdf.cell(0, 15, f"{max_p:,.2f} EUR", ln=True)
    
    pdf.set_xy(25, 115); pdf.set_font("helvetica", 'B', 18); pdf.set_text_color(0, 0, 0); pdf.cell(0, 10, "PASOS PERSONALIZADOS :", ln=True)
    pdf.ln(5)
    
    p1_txt = f"(Opción 1: Aportación Extra). Te falta aportar {extra:,.2f} EUR para el maximo fiscal." if extra > 0 else "1. Ya estas en el camino del maximo ahorro fiscal."
    p2_txt = f"(Opción 2: Aportación Mensual). Ajustar tu cuota a {cuota_r:,.2f} EUR/mes durante {meses} meses." if extra > 0 else "2. Mantén tu plan actual para consolidar tu ahorro."
    
    pasos = [
        (p1_txt, "Dirigete a tu oficina, NOW o APORTA+ para realizar una aportacion extra."),
        (p2_txt, "Asi distribuyes el esfuerzo en lo que queda de año sin imprevistos. Dirigete a tu oficina, NOW o APORTA+ para realizar el incremento aportacion periódica."),
        (f" Y vas a recuperar {ahorro:,.2f} EUR en tu Declaracion del IRPF.", "Es dinero que dejas de pagar en impuestos y se queda en tu bolsillo. Así consigues ahorrar para tu jubilación y al mismo tiempo consigues un ahorro fiscal para tus necesidades presentes, ocio, ...")
    ]
    for titulo, sub in pasos:
        pdf.set_x(30); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(30, 58, 138); pdf.cell(0, 8, titulo, ln=True)
        pdf.set_x(35); pdf.set_font("helvetica", '', 11); pdf.set_text_color(60, 60, 60); pdf.multi_cell(0, 6, sub); pdf.ln(5)
        
    pdf.set_fill_color(16, 185, 129); pdf.rect(25, 230, 165, 30, 'F')
    pdf.set_xy(25, 237); pdf.set_font("helvetica", 'B', 13); pdf.set_text_color(255, 255, 255); pdf.cell(165, 10, f"OBJETIVO: INVERSIÓN 2026 EN TU FUTURO: {inversion:,.2f} EUR", align='C', ln=True)

    # --- Warning Legal y Autoría en pie de página ---
    pdf.set_xy(25, 270)
    pdf.set_font("helvetica", 'I', 6); pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(165, 3, "Aviso: Esta simulacion no tiene validez contractual. Los calculos fiscales son estimados. Autor: AportaMax JLM 2026.", align='C')
    return pdf.output()

# --- 6. CABECERA PRINCIPAL E INSTRUCCIÓN ---
st.markdown("""
    <div class="main-header">
        <h1 style='margin:0; font-size: 35px;'>📈 APORTAMAX 2026</h1>
        <p style='margin:0; opacity: 0.9;'> La APP para calcular tu aportacion personal máxima al Plan de Pensiones de Empleo y obtener el máximo ahorro fiscal </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("#### 📁 Importante. Ajusta los datos personales en sidebar izquierdo que vienen por defecto")

st.markdown("""
    <style>
        .dashboard-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: space-between;
        }
        .card {
            flex: 1 1 300px;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            min-height: 160px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border: 1px solid #e2e8f0;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="dashboard-container">
        <div class="card" style="background-color: #1E3A8A; color: white;">
            <p style="font-size: 13px; font-weight: bold; margin:0;">LO MÁXIMO QUE PUEDES APORTAR</p>
            <h2 style="font-size: 32px; margin: 10px 0;">{max_personal_posible:,.2f} €</h2>
            <p style="font-size: 11px; opacity: 0.8; margin:0;">{mes14:,.2f} €/mes (14 pagas)</p>
        </div>
        <div class="card" style="background-color: #F0FDF4; color: #166534;">
            <p style="font-size: 13px; font-weight: bold; margin:0;">AHORRO FISCAL ESTIMADO (IRPF)</p>
            <h2 style="font-size: 32px; margin: 10px 0;">{ahorro_euros:,.2f} €</h2>
            <p style="font-size: 11px; font-weight: bold; margin:0;"> EFICIENCIA: {eficiencia_fiscal_pct:.1f}%</p>
        </div>
        <div class="card" style="background-color: #1e293b; color: white;">
            <p style="font-size: 13px; font-weight: bold; color: #10B981; margin:0;">INVERSIÓN TOTAL ACUMULADA</p>
            <h2 style="font-size: 32px; margin: 10px 0;">{inversion_total:,.2f} €</h2>
            <p style="font-size: 12px; opacity: 0.8; margin:0;">!SIGUE ASI!</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 8. MÓDULO DE PLANIFICACIÓN ---
st.divider()
st.subheader("🎯 ¿Quieres que te ayude a alcanzar este objetivo?")
with st.expander("Abrir Asistente de Planificación", expanded=False):
    col_plan1, col_plan2 = st.columns(2)
    with col_plan1:
        cuota_mensual = st.number_input("¿Qué cuota mensual (periódica) tienes programada desde enero? (€)", min_value=0.0, value=0.0, step=50.0)
        aportacion_extra = st.number_input("¿Qué aportaciones extraordinarias has realizado ya? (€)", min_value=0.0, value=0.0, step=100.0)
    with col_plan2:
        meses_restantes = st.number_input("Meses que faltan para acabar el año", min_value=1, max_value=12, value=12 - datetime.datetime.now().month if datetime.datetime.now().month <= 12 else 1)
        st.info("💡 Este cálculo te dirá cuánto extra necesitas aportar para no perder ni un euro de ahorro fiscal.")

    proyeccion_periodica = cuota_mensual * 12
    total_proyectado = aportacion_extra + proyeccion_periodica
    extra_necesario = max(0.0, max_personal_posible - total_proyectado)
    
    cuota_ajustada = cuota_mensual+((extra_necesario) / meses_restantes) 
    incremento_cuota = cuota_ajustada - cuota_mensual

    st.markdown("---")
    if extra_necesario <= 0:
        st.success("✅ **¡Vas por buen camino!** Con tus cuotas actuales alcanzarás (o superarás) el máximo de optimización fiscal.")
    else:
        c_res1, c_res2 = st.columns(2)
        with c_res1: st.metric("Pendiente para el máximo", f"{extra_necesario:,.2f} €")
        with c_res2: st.metric("Nueva cuota mensual recomendada", f"{cuota_ajustada:,.2f} €")
        st.warning(f"👉 Para maximizar tu ahorro, deberías hacer una aportación extraordinaria de **{extra_necesario:,.2f} €** o subir tu cuota mensual en **{incremento_cuota:,.2f} €**.")

# --- 10. BOTONES DE DESCARGA ---
st.divider()
c_tec, c_vis, _ = st.columns([1, 1, 2])
with c_tec:
    pdf_t = generar_pdf_tecnico(empresa_total, max_personal_posible, inversion_total, ahorro_euros, coste_neto_trabajador, sb, CUOTA_SS, GASTOS_TRABAJO, base_pre, eficiencia_fiscal_pct, marginal_pdf)
    st.download_button("📄 Informe Técnico Completo", data=bytes(pdf_t), file_name=f"Detalle_Fiscal_{int(sb)}k.pdf", use_container_width=True)
with c_vis:
    pdf_v = generar_pdf_visual_v2(max_personal_posible, ahorro_euros, inversion_total, extra_necesario, cuota_ajustada, meses_restantes)
    st.download_button("🚀 Descargar Plan de Acción", data=bytes(pdf_v), file_name="Plan_Accion_PPE.pdf", use_container_width=True)


