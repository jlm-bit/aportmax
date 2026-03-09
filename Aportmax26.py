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

# --- 2. CONFIGURACIÓN Y ESTILO (CON FIX PARA MODO DARK) ---
st.set_page_config(page_title="AportaMax 2026", layout="wide", page_icon="📈")

# --- 2. CONFIGURACIÓN Y ESTILO ---
st.markdown("""
    <style>
        /* ... tus estilos anteriores ... */

        /* MEJORA PARA TABLETS: Ajuste de cards */
        [data-testid="stHorizontalBlock"] {
            gap: 10px;
        }
        
        @media (max-width: 992px) {
            .main-header h1 { font-size: 24px !important; }
            /* Forzamos a que las métricas tengan aire y el texto no se corte */
            div[style*="height: 160px"] {
                height: auto !important;
                padding: 15px !important;
                margin-bottom: 10px;
            }
        }
    </style>
""", unsafe_allow_html=True)
# --- 3. SIDEBAR (CON RESTRICCIÓN MIN_VALUE=0 Y TOOLTIPS) ---
with st.sidebar:
    st.markdown("### Tus datos personales. AÑO 2026")
    
    sb = st.number_input(
        "Sueldo Bruto Anual (€)", 
        value=60000.0, 
        step=1000.0, 
        min_value=0.0,
        help="Suma de todas tus retribuciones íntegras anuales (fijo + variable) antes de impuestos y SS."
    )
    
    empresa_ahorro = st.number_input(
        "Aport. prevista Empresa Jubilación (€)", 
        value=1800.0, 
        step=100.0, 
        min_value=0.0,
        help="Contribución prevista en 2026 de tu empresa a tu favor específicamente para la contingencia de jubilación en el PPE."
    )
    
    empresa_riesgo = st.number_input(
        "Prima Riesgo PPE (€)", 
        value=0.0, 
        step=50.0, 
        min_value=0.0,
        help="Aportación de la empresa destinada a cubrir una prima de seguro de vida o invalidez dentro del plan. No es frecuente, así que no te extrañe, no tenerla"
    )
    
    empresa_total = empresa_ahorro + empresa_riesgo

    # Cálculos internos
    BASE_MAX_SS = 5101 * 12
    CUOTA_SS = min(sb, BASE_MAX_SS) * 0.0635
    GASTOS_TRABAJO = 2000.0
    base_pre = max(0.0, sb - CUOTA_SS - GASTOS_TRABAJO)
    
    # Lógica de límites legales 2026
    max_personal_coef = calcular_max_personal_adicional(empresa_total, sb)
    max_personal_posible = min(max_personal_coef + 1500, 10000 - empresa_total)
    limite_30_pct = base_pre * 0.30
    inversion_total_teorica = empresa_total + max_personal_posible
    
    st.markdown("---")
    st.info("✅ Tramos IRPF Cataluña 2026")
    
    if sb > 60000:
        st.warning("⚠️ Límite 1:1 por sueldo > 60k€")
    
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

# --- 5. TÍTULO PRINCIPAL ---
st.markdown("""
    <div class="main-header">
        <h1 style='margin:0; font-size: 35px;'>📈 APORTAMAX 2026</h1>
        <p style='margin:0; opacity: 0.9;'> La APP para calcular tu aportacion personal máxima al Plan de Pensiones de Empleo y tener el máximo ahorro fiscal </p>
    </div>
""", unsafe_allow_html=True)

# --- 6. FUNCIONES PDF ---

@st.cache_data
def generar_pdf_tecnico(empresa_total, max_personal_posible, inversion_total, ahorro_euros, coste_neto_trabajador, sb, CUOTA_SS, GASTOS_TRABAJO, base_pre, eficiencia_fiscal_pct, marginal):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 24)
    pdf.cell(0, 15, "APORTAMAX 2026", align='C', ln=True)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 5, "Informe de Optimizacion Fiscal PPE", align='C', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)

    bloques = [
        ("1. IMPACTO DE LA APORTACION Y AHORRO", [
            ("Aportacion Empresa (Contribucion)", f"{empresa_total:,.2f} EUR"),
            ("APORTACION PERSONAL MAXIMA POSIBLE", f"{max_personal_posible:,.2f} EUR"),
            ("Inversion Total en el Plan", f"{inversion_total:,.2f} EUR"),
            ("AHORRO FISCAL (IRPF) ESTIMADO", f"{ahorro_euros:,.2f} EUR"),
            ("ESFUERZO NETO (Tu coste real)", f"{coste_neto_trabajador:,.2f} EUR")
        ], (230, 240, 255)),
        ("2. ESCALA DE GRAVAMEN (CATALUÑA 2026)", [
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
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_fill_color(*color)
        pdf.cell(0, 10, f" {titulo}", fill=True, ln=True)
        pdf.set_font("helvetica", size=10)
        for d, v in datos:
            pdf.cell(130, 9, d, border='B')
            pdf.cell(0, 9, v, border='B', align='R', ln=True)
        pdf.ln(5)

    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 9)
    pdf.cell(0, 5, "4. AVISO LEGAL", ln=True)
    pdf.set_font("helvetica", size=7)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Informe generado mediante simulacion con tramos de Cataluña 2026. Los resultados son estimativos y no vinculantes.")
    return pdf.output()

@st.cache_data
def generar_pdf_visual(max_p, ahorro, inversion, mes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(0, 0, 15, 297, 'F')
    
    pdf.set_xy(25, 20)
    pdf.set_font("helvetica", 'B', 28)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, "TU HOJA DE RUTA 2026", ln=True)
    
    pdf.set_xy(25, 32)
    pdf.set_font("helvetica", '', 12)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 10, "Sigue estos pasos para maximizar tu patrimonio", ln=True)
    
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(25, 55, 165, 45, 'F')
    pdf.set_xy(30, 62)
    pdf.set_font("helvetica", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "LA CANTIDAD RECOMENDADA A DESTINAR AL PPE:", ln=True)
    pdf.set_xy(30, 75)
    pdf.set_font("helvetica", 'B', 32)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 15, f"{max_p:,.2f} EUR", ln=True)
    
    pdf.set_xy(25, 115)
    pdf.set_font("helvetica", 'B', 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "PROXIMOS PASOS:", ln=True)
    
    pdf.ln(5)
    pasos = [
        (f"1. Ve a Now, Aporta+ o Oficina de CaixaBank y aporta hasta llegar a los {max_p:,.2f} EUR.", "Es el limite maximo legal para optimizar tu fiscalidad este año."),
        (f"2. O fraccionar durante todo el año, tu inversion mensual sera de solo {mes:,.2f} EUR.", "Distribuido en 14 pagas para que apenas lo notes en tu dia a dia."),
        (f"3. Y vas a recuperar {ahorro:,.2f} EUR en tu Declaracion de Renta.", "Es dinero que dejas de pagar en impuestos y se queda en tu bolsillo.")
    ]
    
    for titulo, sub in pasos:
        pdf.set_x(30)
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 8, titulo, ln=True)
        pdf.set_x(35)
        pdf.set_font("helvetica", '', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 6, sub)
        pdf.ln(5)
        
    pdf.set_fill_color(16, 185, 129)
    pdf.rect(25, 230, 165, 30, 'F')
    pdf.set_xy(25, 237)
    pdf.set_font("helvetica", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(165, 10, f"INVERSION PARA TU FUTURO: {inversion:,.2f} EUR", align='C', ln=True)

    pdf.set_xy(25, 265)
    pdf.set_font("helvetica", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(165, 4, "Aviso Legal: Este documento es una simulacion informativa basada en la normativa fiscal prevista para 2026 en Cataluña. Los resultados reales pueden variar segun sus circunstancias personales. Se recomienda validacion con un experto fiscal.")
  
    return pdf.output()
# --- 7. BOTONES DE DESCARGA ---
st.markdown("#### 📁 Revisa datos personales sidebar izquierda. Descarga PDF")
c_tec, c_vis, _ = st.columns([1, 1, 2])
with c_tec:
    pdf_t = generar_pdf_tecnico(empresa_total, max_personal_posible, inversion_total, ahorro_euros, coste_neto_trabajador, sb, CUOTA_SS, GASTOS_TRABAJO, base_pre, eficiencia_fiscal_pct, marginal_pdf)
    st.download_button("📄 Informe Técnico Completo", data=bytes(pdf_t), file_name=f"Detalle_Fiscal_{int(sb)}k.pdf", use_container_width=True)
with c_vis:
    pdf_v = generar_pdf_visual(max_personal_posible, ahorro_euros, inversion_total, mes14)
    st.download_button("🚀 Descargar Plan de Acción", data=bytes(pdf_v), file_name="Plan_Accion_PPE.pdf", use_container_width=True)

st.divider()

# --- 8. DASHBOARD ---
c1, c2, c3 = st.columns(3)
card = "padding: 20px; border-radius: 15px; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e2e8f0;"

with c1:
    st.markdown(f'<div style="background-color: #1E3A8A; color: white; {card}"><p style="font-size: 13px; font-weight: bold; margin:0;">LO MÁXIMO QUE PUEDES APORTAR, Y NO MÁS</p><h2 style="font-size: 32px; margin: 10px 0;">{max_personal_posible:,.2f} €</h2><p style="font-size: 11px; opacity: 0.8; margin:0;">{mes14:,.2f} €/mes (14 pagas)</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div style="background-color: #F0FDF4; color: #166534; {card}"><p style="font-size: 13px; font-weight: bold; margin:0;">Y LO QUE TE AHORRAS DE IMPUESTOS (IRPF)</p><h2 style="font-size: 32px; margin: 10px 0;">{ahorro_euros:,.2f} €</h2><p style="font-size: 11px; font-weight: bold; margin:0;"> AHORRO DE LO APORTADO: {eficiencia_fiscal_pct:.1f}%</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div style="background-color: #1e293b; color: white; {card}"><p style="font-size: 13px; font-weight: bold; color: #10B981; margin:0;">INVERSIÓN TOTAL</p><h2 style="font-size: 32px; margin: 10px 0;">{inversion_total:,.2f} €</h2><p style="font-size: 12px; opacity: 0.8; margin:0;">!SIGUE ASI!</p></div>', unsafe_allow_html=True)

# --- 9. GRÁFICO ---
st.subheader("📊 Composición del Ahorro")
df_graf = pd.DataFrame({
    "Eje": ["Plan 2026"],
    "Esfuerzo Neto": [coste_neto_trabajador],
    "Ahorro Hacienda": [ahorro_euros],
    "Aportación Empresa": [empresa_total]
})
st.bar_chart(df_graf, x="Eje", y=["Esfuerzo Neto", "Ahorro Hacienda", "Aportación Empresa"], color=["#1E3A8A", "#10B981", "#CBD5E1"], horizontal=True, height=200)

