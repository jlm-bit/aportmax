import streamlit as st
from fpdf import FPDF
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
st.set_page_config(page_title="AportaMax 2026", layout="centered", page_icon="📈")

if 'paso' not in st.session_state:
    st.session_state.paso = 1

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
        .stButton button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; margin-top: 10px;}
        .info-box-dark { 
            background-color: #1e293b; 
            color: #f8fafc; 
            padding: 15px; 
            border-radius: 10px; 
            border-left: 5px solid #3b82f6; 
            margin-bottom: 20px; 
            font-size: 0.9em; 
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES PDF ---
@st.cache_data
def generar_pdf_tecnico(empresa_total, max_p, inversion_t, ahorro, esfuerzo, sb, ss, gastos, base_pre, eficiencia, marginal):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", 'B', 24); pdf.cell(0, 15, "APORTAMAX 2026", align='C', ln=True)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 5, "Informe de Optimizacion Fiscal PPE", align='C', ln=True)
    pdf.set_text_color(0, 0, 0); pdf.ln(15)
    
    bloques = [
        ("1. IMPACTO DE LA APORTACION Y AHORRO", [
            ("(1) Aportacion Empresa (Contribucion)", f"{empresa_total:,.2f} EUR"),
            ("(2) APORTACION PERSONAL MAXIMA POSIBLE", f"{max_p:,.2f} EUR"),
            ("(3)=(1+2) Inversion Total en el Plan", f"{inversion_t:,.2f} EUR"),
            ("(4) AHORRO FISCAL (IRPF) ESTIMADO", f"{ahorro:,.2f} EUR"),
            ("(5)=(2-4) ESFUERZO NETO (Tu coste real)", f"{esfuerzo:,.2f} EUR")
        ], (230, 240, 255)),
        ("2. DETALLE TECNICO DE LA BASE", [
            ("Sueldo Bruto Anual", f"{sb:,.2f} EUR"),
            ("(-) Seguridad Social", f"-{ss:,.2f} EUR"),
            ("Base Liquidable Previa", f"{base_pre:,.2f} EUR"),
            ("(-) Reduccion PPE", f"-{max_p:,.2f} EUR"),
            ("Base Liquidable Final", f"{base_pre - max_p:,.2f} EUR")
        ], (240, 240, 240))
    ]
    for titulo, datos, color in bloques:
        pdf.set_font("helvetica", 'B', 11); pdf.set_fill_color(*color); pdf.cell(0, 8, f" {titulo}", fill=True, ln=True)
        pdf.set_font("helvetica", size=9)
        for d, v in datos:
            pdf.cell(140, 7, d, border='B'); pdf.cell(0, 7, v, border='B', align='R', ln=True)
        pdf.ln(4)

    pdf.set_font("helvetica", 'B', 11); pdf.set_fill_color(255, 245, 220); pdf.cell(0, 8, " 3. ESCALA DE GRAVAMEN APLICADA (CATALUNA 2026)", fill=True, ln=True)
    pdf.set_font("helvetica", 'B', 8)
    pdf.cell(60, 6, "Tramo Base (EUR)", border=1); pdf.cell(60, 6, "Hasta (EUR)", border=1); pdf.cell(0, 6, "Tipo (%)", border=1, ln=True)
    pdf.set_font("helvetica", size=8)
    tramos_cat = [
        ("0,00", "12.450,00", "19,00%"), ("12.450,00", "17.707,00", "24,00%"),
        ("17.707,00", "20.200,00", "26,00%"), ("20.200,00", "33.007,00", "29,00%"),
        ("33.007,00", "35.200,00", "33,50%"), ("35.200,00", "53.407,00", "37,00%"),
        ("53.407,00", "60.000,00", "40,00%"), ("60.000,00", "90.000,00", "44,00%"),
        ("90.000,00", "120.000,00", "46,00%"), ("120.000,00", "150.000,00", "47,00%"),
        ("150.000,00", "175.000,00", "48,00%"), ("175.000,00", "En adelante", "50,00%")
    ]
    for b1, b2, t in tramos_cat:
        pdf.cell(60, 5, b1, border=1); pdf.cell(60, 5, b2, border=1); pdf.cell(0, 5, t, border=1, ln=True)

    pdf.ln(5); pdf.set_font("helvetica", 'B', 8); pdf.cell(0, 5, "4. AVISO LEGAL Y CLAUSULA DE RESPONSABILIDAD", ln=True)
    pdf.set_font("helvetica", size=7); pdf.set_text_color(100, 100, 100)
    aviso = ("Este informe es una simulacion basada en la normativa fiscal prevista para 2026 en Cataluña. "
             "Los resultados tienen caracter informativo y no constituyen asesoramiento financiero, legal o fiscal vinculante.")
    pdf.multi_cell(0, 4, aviso); pdf.ln(2); pdf.set_font("helvetica", 'I', 7)
    pdf.cell(0, 5, "Generado por AportaMax 2026", align='R', ln=True)
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
    pdf.set_xy(25, 115); pdf.set_font("helvetica", 'B', 18); pdf.set_text_color(0, 0, 0); pdf.cell(0, 10, "PASOS PERSONALIZADOS :", ln=True)
    pasos = [(f"Opcion 1: Aportacion Extra de {extra:,.2f} EUR", "Realiza una aportacion unica."), (f"Opcion 2: Nueva cuota de {cuota_r:,.2f} EUR", "Incrementa tu aportacion mensual."), (f"Recuperaras {ahorro:,.2f} EUR en tu IRPF.", "Dinero que dejas de pagar en impuestos.")]
    for titulo, sub in pasos:
        pdf.set_x(30); pdf.set_font("helvetica", 'B', 12); pdf.set_text_color(30, 58, 138); pdf.cell(0, 8, titulo, ln=True)
        pdf.set_x(35); pdf.set_font("helvetica", '', 11); pdf.set_text_color(60, 60, 60); pdf.multi_cell(0, 6, sub); pdf.ln(5)
    return pdf.output()

# --- 4. RENDERIZADO ---
st.markdown("""
    <div class="main-header">
        <h1 style='margin:0; font-size: 35px;'>📈 APORTAMAX 2026</h1>
        <p style='margin:0; opacity: 0.9;'> La APP para calcular tu aportacion personal máxima al Plan de Pensiones de Empleo y obtener el máximo ahorro fiscal </p>
    </div>
""", unsafe_allow_html=True)

if st.session_state.paso == 1:
    st.markdown("#### 📁 Tus Datos Personales")
    
    sb = st.number_input("Sueldo Bruto Anual (€)", value=60000.0, step=1000.0, min_value=0.0, help="Indica tu retribución bruta anual sin deducciones.")
    
    st.markdown('<div class="info-box-dark"><b>Aportaciones de Empresa:</b> Son las contribuciones que tu empresa realiza a tu favor en el Plan de Pensiones de Empleo. Puedes consultar estos importes en tu <b>nómina mensual</b> (apartado de aportaciones sociales) o en el <b>extracto </b> de tu plan de pensiones proporcionado por la entidad gestora.</div>', unsafe_allow_html=True)
    e_ahorro = st.number_input("Aportación Mensual Empresa para la jubilación (€)", value=0.0, step=25.0, min_value=0.0, max_value=833.33, help="Aportación que realiza tu empresa específicamente para jubilación.")
    e_riesgo = st.number_input("Prima Anual Riesgo Fallecimiento/Ianvlidez dentro del PPE (€)", value=0.0, step=25.0, min_value=0.0, max_value=833.33, help="Aportación que realiza tu empresa para cubrir contingencias de riesgo.")
    
    suma_empresa = e_ahorro*12 + e_riesgo
    if suma_empresa > 10000.0:
        st.error("⚠️ La aportación total de la empresa (Jubilación + Riesgo) no puede superar los 10000 euros.")
    
    if suma_empresa > 4250.0:
        st.warning("ℹ️ Advertencia: al superar la aportación total de la empresa los 4250 euros, tu aportación personal se ve limitada por efecto del límite conjunto de 10000 euros.")

    if st.button("SIGUIENTE: CALCULAR RESULTADOS ➡️", disabled=(suma_empresa > 10000.0)): 
        st.session_state.sb = sb
        st.session_state.empresa_total = suma_empresa
        st.session_state.paso = 2
        st.rerun()

elif st.session_state.paso == 2:
    sb = st.session_state.sb
    emp_t = st.session_state.empresa_total
    CUOTA_SS = min(sb, 5101 * 12) * 0.0635
    base_pre = max(0.0, sb - CUOTA_SS - 2000.0)
    max_p = max(0.0, min(calcular_max_personal_adicional(emp_t, sb) + 1500, 10000 - emp_t))
    if (emp_t + max_p) > (base_pre * 0.30): max_p = max(0.0, (base_pre * 0.30) - emp_t)
    ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
    eficiencia = (ahorro / max_p * 100) if max_p > 0 else 0
    
    st.session_state.max_p, st.session_state.ahorro, st.session_state.inversion = max_p, ahorro, (emp_t + max_p)
    st.session_state.cuota_ss, st.session_state.base_pre, st.session_state.eficiencia = CUOTA_SS, base_pre, eficiencia

    st.markdown("#### 📁 Aportación Máxima (recomendada) y Fiscalidad")
    st.markdown(f"""
        <div class="card" style="background-color: #1E3A8A; color: white;">
            <p style="margin:0;">MÁXIMA APORTACIÓN PERSONAL POSIBLE</p>
            <h2 style="font-size: 32px; margin: 10px 0;">{max_p:,.2f} €</h2>
        </div>
        <div class="card" style="background-color: #F0FDF4; color: #166534;">
            <p style="margin:0;">AHORRO FISCAL ESTIMADO (IRPF)</p>
            <h2 style="font-size: 32px; margin: 10px 0;">{ahorro:,.2f} €</h2>
            <p style="margin:0; font-size: 1.0em; font-weight: bold;">EFICIENCIA FISCAL (Tramos IRPF Catalunya): {eficiencia:.1f}%</p>
        </div>
        <div class="card" style="background-color: #1e293b; color: #10B981;">
            <p style="margin:0;">INVERSIÓN TOTAL (EMPRESA + TÚ)</p>
            <h2 style="font-size: 32px; margin: 10px 0;">{(emp_t + max_p):,.2f} €</h2>
        </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ ATRÁS"): st.session_state.paso = 1; st.rerun()
    with col2:
        if st.button("PLANIFICAR RUTA ➡️", type="primary"): st.session_state.paso = 3; st.rerun()

elif st.session_state.paso == 3:
    st.markdown("#### 📁 Tu Planificacion ")
    st.subheader("Lo que has hecho ya esta año")
    
    mes_actual = datetime.datetime.now().month
    meses_restantes = max(1, 12 - mes_actual)
    
    c_m = st.number_input("Aportación mensual actual (€)", value=0.0, step=100.0, min_value=0.0)
    e_y = st.number_input("Aportaciones extras ya realizadas este año (€)", value=0.0, step=100.0, min_value=0.0)
    
    total_anual_previsto = (c_m * 12) + e_y
    extra_necesario = max(0.0, st.session_state.max_p - total_anual_previsto)
    nueva_cuota_total = c_m + (extra_necesario / meses_restantes) if extra_necesario > 0 else max(0.0, (st.session_state.max_p - e_y) / 12)

    if extra_necesario <= 0:
        st.success("✅ ¡Felicidades! Con tus cuotas actuales ya alcanzan el objetivo fiscal para este año.")

    st.markdown("### Dos caminos para tu tranquilidad futura")
    colA, colB = st.columns(2)
    with colA:
        st.info("**OPCIÓN A: Aportación Única**")
        st.metric("Realizar un pago de", f"{extra_necesario:,.2f} €")
    with colB:
        st.success("**OPCIÓN B: Ajuste Mensual**")
        st.metric(f"Subir cuota a (durante {meses_restantes} meses)" if extra_necesario > 0 else "Ajustar cuota a", f"{nueva_cuota_total:,.2f} €/mes")

    st.divider()
    pdf_t = generar_pdf_tecnico(st.session_state.empresa_total, st.session_state.max_p, st.session_state.inversion, st.session_state.ahorro, (st.session_state.max_p - st.session_state.ahorro), st.session_state.sb, st.session_state.cuota_ss, 2000.0, st.session_state.base_pre, st.session_state.eficiencia, 40.0)
    pdf_v = generar_pdf_visual_v2(st.session_state.max_p, st.session_state.ahorro, st.session_state.inversion, extra_necesario, nueva_cuota_total, meses_restantes)
    st.download_button("📄 Descargar Informe Técnico", data=bytes(pdf_t), file_name="Tecnico_AportaMax.pdf", use_container_width=True)
    st.download_button("🚀 Descargar Plan de Acción (CTA)", data=bytes(pdf_v), file_name="Plan_Accion.pdf", use_container_width=True)
    if st.button("⬅️ VOLVER A RESULTADOS"): st.session_state.paso = 2; st.rerun()


