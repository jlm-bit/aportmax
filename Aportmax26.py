import streamlit as st
from fpdf import FPDF
import datetime
import plotly.graph_objects as go  # <--- Añade esto aquí
import pandas as pd                # <--- Y esto también


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
    
    # Encabezado Minimalista
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

    # 1. RESUMEN EJECUTIVO
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
    
    # --- GRÁFICO VISUAL (Simulado con rectángulos) ---
    pdf.ln(3)
    pdf.set_font("helvetica", 'B', 8)
    pdf.cell(0, 5, "DESGLOSE VISUAL DE LA APORTACIÓN PERSONAL:", ln=True)
    
    # Fondo de la barra (Total aportación personal)
    ancho_max = 100 
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(10, pdf.get_y() + 2, ancho_max, 6, 'F')
    
    # Parte del ahorro (Eficiencia)
    ancho_ahorro = (ahorro / max_p) * ancho_max if max_p > 0 else 0
    pdf.set_fill_color(34, 197, 94) # Verde
    pdf.rect(10, pdf.get_y() + 2, ancho_ahorro, 6, 'F')
    
    # Leyenda del gráfico
    pdf.set_xy(10, pdf.get_y() + 9)
    pdf.set_font("helvetica", '', 7)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(40, 5, f"Ahorro Fiscal ({eficiencia:.1f}%)", align='L')
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 5, f"Esfuerzo Neto ({100-eficiencia:.1f}%)", align='R', ln=True)
    pdf.set_text_color(40, 40, 40)
    pdf.ln(5)

    # 2. ANÁLISIS DE LA BASE IMPONIBLE
    pdf.set_font("helvetica", 'B', 9)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 2. CÁLCULO TÉCNICO DE LA BASE LIQUIDABLE", fill=True, ln=True)
    pdf.ln(2)
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

    # 3. ESCALA AUTONÓMICA (CATALUÑA)
    pdf.set_font("helvetica", 'B', 9)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 8, " 3. ESCALA DE GRAVAMEN APLICABLE (CATALUÑA 2026)", fill=True, ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", 'B', 6.5)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(60, 6, "Desde Base (EUR)", border=1, align='C', fill=True)
    pdf.cell(60, 6, "Hasta Base (EUR)", border=1, align='C', fill=True)
    pdf.cell(0, 6, "Tipo Marginal (%)", border=1, ln=True, align='C', fill=True)
    
    pdf.set_font("helvetica", size=6.5)
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

    # 4. CONSIDERACIONES LEGALES
    pdf.ln(3)
    pdf.set_font("helvetica", 'B', 8)
    pdf.cell(0, 5, "ANEXO TÉCNICO Y LIMITACIONES LEGALES", ln=True)
    pdf.set_font("helvetica", size=7)
    pdf.set_text_color(80, 80, 80)
    legal_text = (
        "- Límite de Aportación: El límite financiero anual conjunto para planes de pensiones es de 1,500 EUR, "
        "pudiendo incrementarse en 8,500 EUR adicionales por contribuciones de empresa y aportaciones del trabajador.\n"
        "- Coeficiente Personal: La aportación del empleado está sujeta a los multiplicadores legales basados en la contribución "
        "empresarial y el rango salarial (Ley 12/2022).\n"
        "- Rendimientos: Los cálculos se basan en la normativa fiscal prevista para 2026 en la Comunidad Autónoma de Cataluña."
    )
    pdf.multi_cell(0, 3.5, legal_text)
    
    pdf.set_y(-22)
    pdf.set_font("helvetica", 'I', 6)
    pdf.cell(0, 2, "Este documento es una simulación informativa. No sustituye la consulta con un profesional fiscal.", align='C')
    
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
    pasos = [(f"Opcion 1: Aportacion Extra de {extra:,.2f} EUR", "Realizar una aportacion única y seguir con tus aportaciones mensual actuales."), (f"Opcion 2: Incrementar la aportación periódica mensual hasta alcanzar {cuota_r:,.2f} EUR", "Incrementa ya tu aportación mensual este mes y los que siguen."), (f"En cualquier caso, recuperarás {ahorro:,.2f} EUR en tu IRPF del ejercicio 2026.", "Dinero que dejas de pagar en impuestos y que puedes dedicar a tus necesidades actuales, ocio, o en lo que quieras.")]
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
    st.markdown("#### 📁 Tus Datos Personales (Paso 1/3)")
    sb = st.number_input("Sueldo Bruto Anual (€)", value=60000.0, step=1000.0, min_value=0.0, help="Indica tu retribución bruta anual sin deducciones.")
    st.markdown('<div class="info-box-dark"><b>Aportaciones de Empresa:</b> Son las contribuciones que tu empresa realiza a tu favor en el Plan de Pensiones de Empleo. Puedes consultar estos importes en tu <b>nómina mensual</b> (apartado de aportaciones sociales) o en el <b>extracto </b> de tu plan de pensiones proporcionado por la entidad gestora. Respecto a la prima anual, la mayoria de los PPE no tienen, y tambien puede aparecer en la nómina del mes en que se ha abonado la prima y en el extracto emitido por por la gestora, en todo caso consulta a RRHH.</div>', unsafe_allow_html=True)
    e_ahorro = st.number_input("Aportación Mensual Empresa para la jubilación en el PPE (€)", value=0.0, step=25.0, min_value=0.0, max_value=833.33, help="Aportación que realiza tu empresa específicamente para jubilación.")
    e_riesgo = st.number_input("Prima Anual de las coberturas de Fallecimiento/Invalidez dentro del PPE (€)", value=0.0, step=25.0, min_value=0.0, max_value=833.33, help="Aportación que realiza tu empresa para cubrir contingencias de riesgo. No es frecuente que los PPE lo contemplen, por tanto lo habitual es dejar este campo a cero.")
    
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
    import plotly.graph_objects as go # Asegúrate de importar esto al inicio

    sb = st.session_state.sb
    emp_t = st.session_state.empresa_total
    
    # Lógica de cálculo (Mantenemos la tuya)
    CUOTA_SS = min(sb, 5101 * 12) * 0.0635
    base_pre = max(0.0, sb - CUOTA_SS - 2000.0)
    max_p = max(0.0, min(calcular_max_personal_adicional(emp_t, sb) + 1500, 10000 - emp_t))
    if (emp_t + max_p) > (base_pre * 0.30): max_p = max(0.0, (base_pre * 0.30) - emp_t)
    
    ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
    coste_neto = max_p - ahorro
    eficiencia = (ahorro / max_p * 100) if max_p > 0 else 0
    inversion_total = emp_t + max_p

    # Guardar en sesión
    st.session_state.update({
        "max_p": max_p, "ahorro": ahorro, "inversion": inversion_total,
        "cuota_ss": CUOTA_SS, "base_pre": base_pre, "eficiencia": eficiencia
    })

    st.markdown("#### 📁 Análisis de Inversión y Fiscalidad (Paso 2/3)")
    
    col_cards, col_chart = st.columns([1, 1.2])

    with col_cards:
        st.markdown(f"""
            <div class="card" style="background-color: #1E3A8A; color: white; padding: 15px;">
                <p style="margin:0; font-size: 0.9em; opacity: 0.9;">APORTACIÓN PERSONAL MÁXIMA</p>
                <h2 style="margin: 5px 0; font-size: 2.2em;">{max_p:,.2f} €</h2>
            </div>
            <div class="card" style="background-color: #F0FDF4; border: 1px solid #166534; padding: 15px; margin-top: 15px;">
                <p style="margin:0; font-size: 0.9em; color: #166534;">AHORRO FISCAL (IRPF)</p>
                <h2 style="margin: 5px 0; color: #166534; font-size: 2.2em;">{ahorro:,.2f} €</h2>
                <p style="margin:0; color: #166534; font-weight: bold;">Subvención: {eficiencia:.1f}%</p>
            </div>
        """, unsafe_allow_html=True)

    with col_chart:
        # --- Configuración del Gráfico de Tarta / Donut ---
        labels = ['Aportación Empresa', 'Ahorro Fiscal (Estado)', 'Tu Coste Neto']
        values = [emp_t, ahorro, coste_neto]
        colors = ['#1e293b', '#10B981', '#3B82F6'] 

        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.6,
            marker_colors=colors,
            textinfo='percent',
            insidetextorientation='radial',
            hovertemplate="<b>%{label}</b><br>Importe: %{value:,.2f}€<extra></extra>"
        )])
        
        fig.update_layout(
            showlegend=True, 
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=0, b=40, l=0, r=0), 
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("⬅️ ATRÁS"): 
            st.session_state.paso = 1
            st.rerun()
    with col_b2:
        if st.button("PLANIFICAR RUTA ➡️", type="primary"): 
            st.session_state.paso = 3
            st.rerun()


elif st.session_state.paso == 3:
    st.markdown("#### 📁 Tu Planificacion (Paso 3/3) ")
    st.subheader("Indica aquí lo que has hecho ya este año")
    
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








