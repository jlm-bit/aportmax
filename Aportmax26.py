import streamlit as st
from fpdf import FPDF
import pandas as pd
import datetime

# --- 1. MOTOR FISCAL CATALUÑA 2026 ---

def calcular_irpf_cat(base):
    """
    Calcula la cuota íntegra sumando estatal y autonómica CAT 2026.
    """
    # Tramos vigentes para 2026 en Cataluña
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
    
    # Mínimo personal estándar 5.550€
    return cuota_base(base) - cuota_base(5550)

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="Límites PPE 2026", layout="wide", page_icon="⚖️")
st.title("⚖️ Aportación Personal Máxima PPE: 2026")

# --- 3. ENTRADA DE DATOS (SIDEBAR) ---
with st.sidebar:
    st.header("Datos Personales")
    sb = st.number_input("Sueldo Bruto Anual (€)", value=60000, step=1000)
    empresa_total = st.number_input("Aportación Empresa Ahorro + Riesgo (€)", value=1800, step=100)
    st.divider()
    st.info("Este simulador aplica los límites de la Ley 12/2022 para Planes de Empleo (PPE). Así como los tramos del IRPF aplicables en Catalunya en 2026 ")

# --- 4. LÓGICA DE LÍMITES LEGALES (CORREGIDA) ---
def calcular_max_personal_adicional(e, salario):
    # Regla de los 60.000€
    if salario > 60000:
        return e
    
    # Aplicación de coeficientes por tramos
    if e <= 500:
        return e * 2.5
    elif e <= 1500:
        # Los primeros 500 al 2.5 (1250) + el exceso al 0.25
        return 1250 + (0.25 * (e - 500))
    else:
        # Para aportaciones > 1500, la relación es 1:1
        return e

# Cálculo del incremento por empresa
max_personal_coef = calcular_max_personal_adicional(empresa_total, sb)

# Límite financiero: 1.500€ (bolsa general) + incremento por empresa (máximo 8.500€ adicionales)
# El total de la parte del trabajador no puede exceder los 8.500€ + 1.500€ = 10.000€, 
# pero la ley dice que la suma de empresa + trabajador es la que topa en 10.000€.
max_personal_posible = min(max_personal_coef + 1500, 10000 - empresa_total)

# Límite fiscal del 30% de los rendimientos netos
limite_30_pct = sb * 0.30
inversion_total = empresa_total + max_personal_posible

if inversion_total > limite_30_pct:
    inversion_total = limite_30_pct
    max_personal_posible = max(0.0, inversion_total - empresa_total)

# --- 5. CÁLCULOS DE IMPACTO (BASE LIQUIDABLE CON SS Y GASTOS) ---

# Parámetros SS 2026
BASE_MAX_SS = 60200.0  # Tope estimado 2026
CUOTA_SS = min(sb, BASE_MAX_SS) * 0.048  # 4.7% + 0.1% MEI trabajador
GASTOS_TRABAJO = 2000.0

# Base imponible previa a la reducción por PPE
base_pre = sb - CUOTA_SS - GASTOS_TRABAJO

# Límite fiscal del 30% sobre rendimientos netos
limite_30_pct = base_pre * 0.30
inversion_total = empresa_total + max_personal_posible

if inversion_total > limite_30_pct:
    inversion_total = limite_30_pct
    max_personal_posible = max(0.0, inversion_total - empresa_total)

# Cálculo de cuotas
cuota_inicial = calcular_irpf_cat(base_pre)
cuota_final = calcular_irpf_cat(base_pre - max_personal_posible)
ahorro_euros = cuota_inicial - cuota_final

eficiencia_fiscal_pct = (ahorro_euros / max_personal_posible * 100) if max_personal_posible > 0 else 0
coste_neto_trabajador = (max_personal_posible - ahorro_euros) if max_personal_posible > 0 else 0

# --- 6. VISUALIZACIÓN ---
st.divider()
m1, m2, m4, m3 = st.columns(4)
m1.metric("Aportación Personal Máx.", f"{max_personal_posible:,.2f} €")
m3.metric("Aportación Total (Empresa+Empleado)", f"{inversion_total:,.2f} €")
m4.metric("Coste Empleado(despues IRPF)", f"{coste_neto_trabajador:,.2f} €", delta_color="inverse")
m2.metric("Ahorro en el IRPF ", f"{ahorro_euros:,.2f} €", f"{eficiencia_fiscal_pct:.1f}% Eficiencia")

# --- 7. GRÁFICO DE IMPACTO (DISEÑO PREMIUM HORIZONTAL) ---
st.markdown("---")
st.subheader("📊 Composición de tu Aportación Anual")

# Datos preparados para barra horizontal
# Invertimos el orden para que lo más importante (tu esfuerzo) quede a la izquierda
df_premium = pd.DataFrame({
    "Categoría": ["Tu Hucha Total"],
    "Aportación Neta de IRPF      ": [coste_neto_trabajador],
    "Ahorro Fiscal      ": [ahorro_euros],
    "Aportación Empresa": [empresa_total]
})

# Paleta de colores Premium: Azul Profundo, Verde Esmeralda, Gris Plata
# El gris para la empresa le da un toque muy elegante y corporativo
colores_premium = ["#1E3A8A", "#10B981", "#CBD5E1"]

st.bar_chart(
    df_premium,
    x="Categoría",
    y=["Aportación Neta de IRPF      ", "Ahorro Fiscal      ", "Aportación Empresa"],
    color=colores_premium,
    horizontal=True, # Lo hace mucho más legible y elegante
    height=200
)

# Resumen de impacto con estilo minimalista
multiplicador = inversion_total / coste_neto_trabajador if coste_neto_trabajador > 0 else 0
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-around; align-items: center; padding: 15px; border: 1px solid #e6e9ef; border-radius: 8px;">
        <div style="text-align: center;">
            <p style="margin:0; color: #64748b; font-size: 0.8em; text-transform: uppercase;">Capital Total</p>
            <p style="margin:0; font-size: 1.5em; font-weight: bold; color: #1e293b;">{inversion_total:,.2f} €</p>
        </div>
        <div style="height: 40px; border-left: 1px solid #e6e9ef;"></div>
        <div style="text-align: center;">
            <p style="margin:0; color: #64748b; font-size: 0.8em; text-transform: uppercase;">Multiplicador</p>
            <p style="margin:0; font-size: 1.5em; font-weight: bold; color: #10B981;">x{multiplicador:.2f}</p>
        </div>
        <div style="height: 40px; border-left: 1px solid #e6e9ef;"></div>
        <div style="text-align: center;">
            <p style="margin:0; color: #64748b; font-size: 0.8em; text-transform: uppercase;">Eficiencia</p>
            <p style="margin:0; font-size: 1.5em; font-weight: bold; color: #1E3A8A;">{eficiencia_fiscal_pct:.1f}%</p>
        </div>
    </div>
    """, 
    unsafe_allow_html=True
)


# --- 8. FUNCIÓN PDF OPTIMIZADA CON JERARQUÍA VISUAL AJUSTADA ---
import datetime
def generar_pdf_bytes():
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, "APORTACION MÁXIMA PLAN DE PENSIONES DE EMPLEO - 2026", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", 'I', 8)
    fecha_gen = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 5, f"Simulacion generada el: {fecha_gen}", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10) # Mayor separación inicial

    # SECCIÓN 1: IMPACTO DE LA APORTACION (SECCIÓN PRINCIPAL)
    pdf.set_font("helvetica", 'B', 12)
    pdf.set_fill_color(200, 220, 255) 
    pdf.cell(0, 10, " 1. Impacto de la Aportacion y Ahorro", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    items = [
        ("Aportacion Empresa", f"{empresa_total:,.2f} EUR"),
        ("APORTACIÓN PERSONAL MÁXIMA QUE PUEDES REALIZAR ESTE AÑO", f"{max_personal_posible:,.2f} EUR"),
        ("Total aportación", f"{inversion_total:,.2f} EUR"),
        ("AHORRO FISCAL (IRPF) OBTENIDO POR APORTAR AL MÁXIMO ", f"{ahorro_euros:,.2f} EUR"),
        ("COSTE REAL (Esfuerzo neto)", f"{coste_neto_trabajador:,.2f} EUR"),
    ]
    
    for desc, valor in items:
        if "APORTACIÓN PERSONAL MÁXIMA" in desc or "AHORRO FISCAL (IRPF) OBTENIDO POR APORTAR AL MÁXIMO " in desc:
            pdf.set_font("helvetica", 'B', 11)
        else:
            pdf.set_font("helvetica", size=10)
        
        pdf.cell(100, 10, desc, border='B')
        pdf.cell(0, 10, valor, border='B', align='R', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(22) # ESPACIADO EXTRA para separar de las secciones secundarias


  # SECCIÓN 2: ESCALA DE GRAVAMEN (MÁS PEQUEÑA)
    pdf.set_font("helvetica", 'B', 9) # Título más pequeño
    pdf.set_fill_color(255, 240, 200) 
    pdf.cell(0, 7, " 2. Escala de Gravamen e Impacto Marginal", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    marginal = (calcular_irpf_cat(base_pre + 100) - calcular_irpf_cat(base_pre)) / 100 * 100

    pdf.set_font("helvetica", size=8) # Letra más pequeña
    tramos_text = [
        ("Tu Tipo Marginal Aplicado (según el salario informado)", f"{marginal:.2f} %"),
        ("Eficiencia Fiscal (Ahorro medio por cada 100 EUR de aportación en el Plan de Pensiones)", f"{eficiencia_fiscal_pct:.2f} EUR"),
        ("Tipo Maximo de la Escala (Cataluña 2026)", "50.00 %")
    ]

    for desc, valor in tramos_text:
        pdf.set_font("helvetica", 'B' if "Marginal" in desc else '', 8)
        pdf.cell(100, 6, desc, border='B')
        pdf.cell(0, 6, valor, border='B', align='R', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    
    # Tabla de tramos para referencia visual
    pdf.set_font("helvetica", 'B', 7)
    pdf.cell(40, 4, "Desde", border=1, align='C')
    pdf.cell(40, 4, "Hasta", border=1, align='C')
    pdf.cell(40, 4, "Tipo Combinado", border=1, align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", size=6) # Letra muy pequeña para la tabla de referencia
    escalas = [
        ("20,200 EUR", "33,007 EUR", "29.0%"), ("33,007 EUR", "35,200 EUR", "33.5%"),  
        ("35,200 EUR", "53,407 EUR", "37.0%"), ("53,407 EUR", "60,000 EUR", "40.0%"),
        ("60,000 EUR", "90,000 EUR", "44.0%"), ("90,000 EUR", "120,000 EUR", "46.0%"),
        ("120,000 EUR", "150,000 EUR", "47.0%"), 
        ("150,000 EUR", "175,000 EUR", "48.0%"), ("175,000 EUR", "Adelante", "50.0%")
    ]
    
      
    
    for ex1, ex2, ex3 in escalas:
        pdf.cell(40, 4, ex1, border=1, align='C')
        pdf.cell(40, 4, ex2, border=1, align='C')
        pdf.cell(40, 4, ex3, border=1, align='C', new_x="LMARGIN", new_y="NEXT")

    # SECCIÓN 3: DATOS DE LA BASE (MÁS PEQUEÑA)
    pdf.ln(6) # ESPACIADO EXTRA para separar de las secciones secundarias
    pdf.set_font("helvetica", 'B', 9) # Título más pequeño
    pdf.set_fill_color(230, 230, 230) 
    pdf.cell(0, 7, " 3. Determinacion de la Base Liquidable (Desglose Tecnico)", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", size=7) # Letra más pequeña
    base_items = [
        ("Sueldo Bruto Anual", f"{sb:,.2f} EUR"),
        ("(-) Seguridad Social (aprox.)", f"-{CUOTA_SS:,.2f} EUR"),
        ("(-) Gastos Deducibles Trabajo (Art. 19 LIRPF)", f"-{GASTOS_TRABAJO:,.2f} EUR"),
        ("Base Liquidable Previa (A)", f"{base_pre:,.2f} EUR"),
        ("(-) Reduccion Plan de Empleo (B)", f"-{max_personal_posible:,.2f} EUR"),
        ("Base Liquidable Final (Base Imponible General)", f"{base_pre - max_personal_posible:,.2f} EUR"),
    ]

    for desc, valor in base_items:
        pdf.set_font("helvetica", 'B' if "Final" in desc else '', 7)
        pdf.cell(100, 6, desc, border='B')
        pdf.cell(0, 6, valor, border='B', align='R', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10) # Separación entre bloques secundarios

  

    # Pie de página
    pdf.ln(10)
    pdf.set_font("helvetica", 'I', 7)
    pdf.multi_cell(0, 4, "Nota: Este informe es una simulacion informativa basada en la normativa de IRPF y Seguridad Social prevista para 2026 en Cataluña.")

    return pdf.output()

# --- 9. BOTÓN DE DESCARGA ---
try:
    with st.spinner("Preparando informe..."):
        pdf_data = generar_pdf_bytes()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        nombre_archivo = f"Informe_PPE_{int(sb)}k_{timestamp}.pdf"
        
        st.download_button(
            label="📩 Descargar Informe Detallado (PDF)",
            data=bytes(pdf_data),
            file_name=nombre_archivo,
            mime="application/pdf",
            key="btn_descarga_detallada"
        )
except Exception as e:

    st.error(f"Error técnico al generar PDF: {e}")



