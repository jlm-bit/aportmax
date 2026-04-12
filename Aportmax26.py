import numpy as np
import streamlit as st
from fpdf import FPDF
import io
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
        sb = st.number_input("Sueldo Bruto Anual (€)", value=0.0, step=1000.0, min_value=0.0)
        e_ahorro = st.number_input("Aportación Mensual Empresa (€)", value=0.0, step=25.0, min_value=0.0)
        e_riesgo = st.number_input("Prima Anual Riesgo PPE (€)", value=0.0, step=25.0, min_value=0.0)
        
        # --- CONTROL DE LÍMITE EMPRESA (Ahorro + Riesgo <= 10.000€) ---
        emp_t_bruta = (e_ahorro * 12) + e_riesgo
        emp_t = min(emp_t_bruta, 10000.0)
   
        if sb <= 0.0:
            st.warning(f"⚠️ Introduce tus datos personales. Salario, Aportaciones de la empresa al plan, tus aportacinoes") 
            st.stop ()
                    
        if emp_t_bruta > 10000.0:
            st.warning(f"⚠️ La aportación de la empresa se ha limitado a 10.000€ (Exceso: {emp_t_bruta - 10000.0:,.2f}€)")

    # --- LÓGICA DE LÍMITES FISCALES ---
    CUOTA_SS_PRE = min(sb, 5101.0 * 12) * 0.0635 
    BASE_PRE_LIMIT = max(0.0, sb - CUOTA_SS_PRE - 2000.0)
    
    # Cálculo del máximo personal según coeficientes
    max_personal_coef = calcular_max_personal_adicional(emp_t, sb)
    
    # --- CONTROL TOTAL: EMPRESA + PERSONAL <= 10.000€ ---
    # El límite personal es el menor de: (Coeficiente + 1500) o (Hueco hasta 10k)
    MAX_P_LIMIT = max(0.0, min(max_personal_coef + 1500, 10000.0 - emp_t))
    
    # Límite del 30% de la Base Imponible
    if (emp_t + MAX_P_LIMIT) > (BASE_PRE_LIMIT * 0.30):
        MAX_P_LIMIT = max(0.0, (BASE_PRE_LIMIT * 0.30) - emp_t)

    with st.expander("📅 APORTACIONES PERSONALES", expanded=True):
        if MAX_P_LIMIT <= 0:
            st.info("🚫 Has alcanzado el límite legal máximo de aportación anual (10.000€) con la aportación de la empresa.")
            c_m = 0.0
            e_y = 0.0
        else:
            # Aseguramos que el value no sea superior al nuevo límite calculado
            c_m = st.number_input("Aport.periódica mensual (€)", value=0.0, step=50.0, min_value=0.0)
            
            # El max_value del input se ajusta dinámicamente al límite legal real
            e_y = st.number_input(
                "Aport. Extras ya realizadas (€)", 
                value=0.0, 
                max_value=max(0.0, float(MAX_P_LIMIT)), 
                step=100.0, 
                min_value=0.0
            )


# --- 5. LÓGICA DE CÁLCULO ---
any = 2026

hoy = datetime.date.today()
meses_restantes = 12 - hoy.month + 1
meses_pasados = 12 - meses_restantes
CUOTA_SS = min(sb, 5101*12) * 0.064 
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
cumplimiento_plan = ((c_m *12 + e_y)*100)/max_p if max_p > 0 else 0

# --- CÁLCULOS GLOBALES (Poner esto ANTES de los st.tabs) ---
# Sumamos lo que pone la empresa y lo que pones tú (el máximo permitido)
total_inv = emp_t + max_p 

# Calculamos el ahorro y los meses (ya lo tienes en tu lógica anterior)
ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
# años_jub = 67 - edad  # 'edad' viene del sidebar

# --- 6. RENDERIZADO PRINCIPAL ---
st.markdown('<div class="main-header"><h1 style="margin:0;">📈 APORTAMAX 2026</h1></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💰 Aportación Máxima ", "🚀 Proyección a la Jubilación ", "🎯 Acerca de "])

with tab1:

    st.markdown(
    f"""
    <hr style="margin: 1em 0;">
    <div style="text-align: center;">
        <p style='margin:0; font-size:1.0rem;'>
            <b>💰 Aportación adicional que puedes realizar este año (como máximo)</b>
        </p>
        <h4 style='margin:0; font-size:2.0rem; color:#1e40af; line-height:1.1;'>
            {aportacion_extraordinaria_neta:,.0f}€
        </h4>
        <p style='margin:0; color:#64748b; font-size:0.9rem;'>
            Aportación que debes realizar para alcanzar el límite
        </p>
    </div>
    <hr style="margin: 1em 0;">
    """, 
    unsafe_allow_html=True
)
    
    col_left, col_right = st.columns([1.2, 1]) # Invertimos un poco el ratio para que los cuadros tengan aire
    
    with col_left:
        # --- SUB-COLUMNAS PARA LOS CUADROS ---
        sub_col1, sub_col2 = st.columns(2)
        
        with sub_col1:
            st.markdown(f"""
                <div style="background-color: #1E3A8A; color: white; padding: 20px; border-radius: 11px; height: 200px; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <p style="margin:0; font-size: 12px; opacity: 0.8; font-weight: bold;">MÁXIMA APORTACIÓN PERSONAL</p>
                    <h2 style="font-size: 22px; margin: 10px 0; color: white;">{max_p:,.2f} €</h2>
                </div>
            """, unsafe_allow_html=True)

        with sub_col2:
            st.markdown(f"""
                <div style="background-color: #F0FDF4; color: #166534; padding: 20px; border-radius: 11px; height: 190px; text-align: center; border: 1px solid #DCFCE7; display: flex; flex-direction: column; justify-content: center;">
                    <p style="margin:0; font-size: 11px; opacity: 0.9; font-weight: bold;">AHORRO FISCAL (IRPF Catalunya)</p>
                    <h2 style="font-size: 22px; margin: 10px 0; color: #166534;">{ahorro:,.2f} €</h2>
                    <p style="margin:0; font-weight: bold; font-size: 14px;">Tax Return: {eficiencia:.1f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
        # --- AVISO Y BOTÓN DE DESCARGA ---
        st.warning("")   
        st.warning("⚠️ **Nota: Los resultados mostrados se basan en los datos facilitados en el panel lateral. Revisar si son correctos.**")   
    with col_right:
        # --- EL DONUT SE MANTIENE AQUÍ ---
        total_inversion = esfuerzo_neto + ahorro + emp_t
        fig = go.Figure(data=[go.Pie(
            labels=['Esfuerzo Neto', 'Ahorro Fiscal', 'Empresa'], 
            values=[esfuerzo_neto, ahorro, emp_t], 
            hole=.65,
            marker_colors=['#3B82F6', '#10B981', '#1E293B'],
            textinfo='percent', 
            hoverinfo='label+value',
            insidetextorientation='horizontal'
        )])
        
        fig.update_layout(
            title={'text': "<b>Distribución de tu Inversión Anual</b>", 'y': 0.98, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 16}},
            margin=dict(t=80, b=20, l=10, r=10), 
            height=400, 
            showlegend=True, 
            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
            annotations=[dict(text=f'TOTAL ANUAL<br><b>{total_inversion:,.0f} €</b>', x=0.5, y=0.5, showarrow=False, font_size=16)]
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
      
 # --- 3. DESGLOSE COMPACTO (4 COLUMNAS) ---

    import datetime
    hoy = datetime.date.today()
    meses_nombres_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    
    c1, c2, c3, c4  = st.columns(4)
    
    with c1:
        mes_fin_ya = meses_nombres_es[hoy.month - 2] if hoy.month > 1 else "Ene"
        st.markdown(f"<p style='margin:0; font-size:0.6rem;'><b>✅ Ya aportado</b></p><h4 style='margin:0; font-size:1.1rem;'>{ya_aportado:,.0f}€</h4><small style='color:#64748b; font-size:0.6rem;'>Ene-{mes_fin_ya[:3]}</small>", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"<p style='margin:0; font-size:0.6rem;'><b>⏳ Ya planificado (resto de año)</b></p><h4 style='margin:0; font-size:1.1rem;'>{c_m * meses_restantes:,.0f}€</h4><small style='color:#64748b; font-size:0.6rem;'>{meses_restantes} mes. x {c_m:,.0f}€</small>", unsafe_allow_html=True)
  
    with c3:
        st.markdown(f"<p style='margin:0; font-size:0.6rem;'><b>✅ % cumplimiento</b></p><h4 style='margin:0; font-size:1.1rem;'>{cumplimiento_plan:,.0f}%</h4>", unsafe_allow_html=True) 
    with c4:
        # Aportación extraordinaria única
        st.markdown(f"<p style='margin:0; font-size:0.6rem;'><b>💰 APORTACIÓN ÚNICA (para máximo)</b></p><h4 style='margin:0; font-size:1.8rem; color:#1e40af;'>{aportacion_extraordinaria_neta:,.0f}€</h4><small style='color:#64748b; font-size:0.65rem;'>Aport.para alcanzar el límite</small>", unsafe_allow_html=True)

     
       
    
    st.markdown("---")
    pdf_t = generar_pdf_tecnico(emp_t, max_p, (emp_t+max_p), ahorro, esfuerzo_neto, sb, CUOTA_SS, 2000.0, base_pre, eficiencia)
    # st.download_button("📄 Informe Fiscal Detallado", data=pdf_t, file_name="informe_fiscal_2026.pdf", mime="application/pdf")


# with tab2:
    with st.expander("🚀 ¿Te recomiendo conmo hacerlo?"):
    # --- 0. PREPARACIÓN DE DATOS (Evita NameError) ---
    import datetime
    hoy = datetime.date.today()
    meses_nombres_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    # 1. Cálculos base
    proyeccion_final = ya_aportado + (c_m * meses_restantes)
    porcentaje_uso = min(proyeccion_final / max_p, 1.0) if max_p > 0 else 0

    # 2. Definición de Estados (Crítico para evitar NameError)
    if proyeccion_final > max_p:
        color_alerta, icon_estado = "#ef4444", "⚠️"
        msg_estado = f"EXCESO: +{proyeccion_final - max_p:,.0f}€"
    elif proyeccion_final >= max_p * 0.98:
        color_alerta, icon_estado = "#22c55e", "🎯"
        msg_estado = "PLAN ÓPTIMO"
    else:
        color_alerta, icon_estado = "#f59e0b", "💡"
        msg_estado = f"OPORTUNIDAD: +{max_p - proyeccion_final:,.0f}€"

  #  st.markdown("### 🎯 Plan de Acción Personal")
    
 
    # --- 1. LÓGICA DE PROYECCIÓN MES A MES ---
    proyeccion_final = ya_aportado + (c_m * meses_restantes)
    porcentaje_uso = min(proyeccion_final / max_p, 1.1) if max_p > 0 else 0
    
    # Determinamos el color y el mensaje según el estado
    if proyeccion_final > max_p:
        color_alerta = "#ef4444"  # Rojo
        msg_estado = f"⚠️ EXCESO DETECTADO: Superarás el límite en {proyeccion_final - max_p:,.2f} €"
        icon_estado = "🚨"
    elif proyeccion_final >= max_p * 0.99:
        color_alerta = "#22c55e"  # Verde
        msg_estado = "✅ PLAN ÓPTIMO: Estás maximizando tu ahorro fiscal según los datos informados"
        icon_estado = "🎯"
    else:
        color_alerta = "#f59e0b"  # Ámbar
        msg_estado = f"💡 Puedes aportar hasta {max_p - proyeccion_final:,.2f} € (hasta 31 de diciembre)"
        icon_estado = "ℹ️"

    # --- 2. INDICADOR VISUAL DE PROGRESO ---
    st.markdown(f"""
        <div style="background: #f8fafc; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="font-weight: bold; color: #1e293b;">{icon_estado} {msg_estado}</span>
                <span style="font-weight: bold; color: {color_alerta};">{proyeccion_final:,.2f} / {max_p:,.2f} €</span>
            </div>
            <div style="background-color: #e2e8f0; border-radius: 10px; height: 12px; width: 100%;">
                <div style="background-color: {color_alerta}; width: {porcentaje_uso*100}%; height: 12px; border-radius: 10px; transition: width 0.5s;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. RECOMENDACIÓN DE AJUSTE ---
   
    if proyeccion_final != max_p:
        if abs(proyeccion_final - max_p) > 1.0:
     
            st.markdown(f"""
                <div style="border-left: 12px solid #1e40af; background: #f0f7ff; padding: 30px; border-radius: 0 10px 10px 0; margin: 10px 0;">
                    <div style="background: #1e40af; color: white; padding: 8px 18px; border-radius: 25px; font-size: 1.0rem; font-weight: bold; display: inline-block; margin-bottom: 20px; letter-spacing: 0.5px;">
                        🎯 ALTERNATIVA RECOMENDADA:   Ajustar la aportación voluntaria mensual a tu plan de pensiones de empleo
                    </div>
                    <p style="margin-bottom: 5px; font-size: 1.0rem; color: #1e293b; line-height: 1.4;">
                        De acuerdo a nuestra recomendación, para alcanzar exactamente el límite de aportación máxima al Plan de Pensiones de Empleo de <b>{max_p:,.2f} €</b> sin pasarte, debes ajustar tu aportación mensual a un total de:
                    </p>
                    <div style="display: flex; align-items: baseline; gap: 3px; margin: 0px 0;">
                        <h1 style="color: #1e40af; margin:0; font-size: 1.6rem; font-weight: 800;">{nueva_cuota_total:,.2f} €</h1>
                        <span style="font-size: 1.4rem; color: #64748b; font-weight: 600;">/mes durante los {meses_restantes} meses restantes de este año</span>
                    </div>
                    <p style="font-size: 1.0rem; color: #1e3a8a; margin-top: 10px; font-weight: 500;">
                        {"🔼 <b>ACCIÓN: Incrementa</b>" if diferencia_mensual > 0 else "🔽 <b>Reduce</b>"} tu aportación actual al Plan de Pensiones en 
                        <span style="font-size: 1.4rem; border-bottom: 3px solid #1e40af;">{abs(diferencia_mensual):,.2f} €</span> 
                        durante los {meses_restantes} meses restantes de este año. Ya al año siguente tu aportación va a ser menor al poder prorratear por los 12 meses del año. 
                    </p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.balloons()
        st.success("¡Tu planificación es exacta!")

    
    st.markdown("---")


with st.expander("🚀 ¿Cómo realizar tu aportación?"):
    col_web, col_steps = st.columns([1, 1.5], gap="large")
    
    with col_web:
        st.markdown("**Vías de Acceso Online**")
        st.link_button("✨ Acceder a Aporta+", "https://...", use_container_width=True, type="primary")
        st.link_button("🏦 Ir a CaixaBankNow", "https://...", use_container_width=True)
        # Un pequeño divisor visual ayuda a separar la info del botón
        st.divider()
        st.caption("💡 **Dato:** Aporta+ es la plataforma de VidaCaixa para gestionar tus planes de empleo.")
        
    with col_steps:
        st.markdown("**Pasos a seguir:**")
        # El uso de contenedores aquí ayuda a que el texto no se vea "flotando"
        with st.container(border=True):
            st.markdown("""
            1. **Identifícate** en la plataforma elegida.
            2. Localiza la sección de **'Pensiones'** o **'Mis Planes'**.
            3. Selecciona tu **Plan de Empleo (PPE)** y pulsa **'Gestionar'**.
            4. Elige **'Aportación Única'** o **'Modificar periódica'**.
            5. Introduce el importe y **firma la operación**.
            """)

pdf_v = generar_pdf_visual_v2(max_p, ahorro, (emp_t+max_p), aportacion_extraordinaria_neta, nueva_cuota_total, meses_restantes, ya_aportado)
# st.download_button("🚀 DESCARGAR HOJA DE RUTA (PDF)", data=pdf_v, file_name="hoja_ruta_2026.pdf", mime="application/pdf")

import plotly.graph_objects as go
import numpy as np
import streamlit as st
from fpdf import FPDF
import io

# --- Asumimos que estas variables vienen calculadas de tabs anteriores ---
# emp_t: Aportación anual total de la empresa (Tab 1)
# max_p: Aportación personal máxima anual permitida (Tab 1)
# e_riesgo: Coste anual del seguro de riesgo (Tab 1)
# ------------------------------------------------------------------------
with tab2:
  #  st.markdown("### 🔮 SIMULADOR JUBILACIÓN: Impacto de aportaciones voluntarias")
    
    # 0. Recuperar variables de otros Tabs
    t_marginal_uso = st.session_state.get('tipo_marginal', 30.0) 

    # 1. Entradas de Datos
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        edad_act = st.number_input("Tu Edad Actual", value=40, min_value=18, max_value=64, key="edad_final")
        saldo_existente = st.number_input("Saldo acumulado actual en el Plan (€)", value=0.0, step=1000.0, min_value=0.0, key="saldo_final")
        
        modo_aportacion = st.radio(
            "Tu aportación personal anual:",
            ["Aportación Máxima", "Cantidad Personalizada"],
            horizontal=True,
            key="modo_aport_final"
        )
        
        max_legal_anual_neta = float(MAX_P_LIMIT)
        
        if modo_aportacion == "Aportación Máxima":
            mi_aportacion_anual_neta = max_legal_anual_neta
            st.info(f"✨ Aportación Máxima: **{mi_aportacion_anual_neta:,.2f} €/año**.")
        else:
            mi_aportacion_anual_neta = st.slider(
                "Aportación anual personalizada (€)", 
                min_value=0.0, 
                max_value=max_legal_anual_neta if max_legal_anual_neta > 0 else 1.0, 
                value=float(max_legal_anual_neta / 2),
                step=100.0,
                key="aport_pers_final"
            )

    with col_in2:
        edad_jub = st.radio("Edad de jubilación", [63, 64, 65, 66, 67], index=4, horizontal=True, key="jub_final")
        rent_pct = st.slider("Rentabilidad anual estimada (%)", 0.0, 10.0, 4.0, key="rent_final")
    
    # 2. Lógica de Simulación
    rent_dec = rent_pct / 100
    edades = np.arange(edad_act, edad_jub + 1)
    cap_total_evol, solo_capital_evol, interes_evol, cap_solo_empresa_evol = [], [], [], []
    saldo_a, saldo_b, aport_acum_a = saldo_existente, saldo_existente, saldo_existente
    cuota_empresa_fija = e_ahorro * 12
    cuota_empleado_fija = mi_aportacion_anual_neta 
    años_plan = edad_jub - edad_act
   
    
    for i in range(len(edades)):
        int_a = saldo_a * rent_dec
        cap_total_evol.append(saldo_a)
        solo_capital_evol.append(aport_acum_a)
        interes_evol.append(saldo_a - aport_acum_a)
        
        int_b = saldo_b * rent_dec
        cap_solo_empresa_evol.append(saldo_b)
        
        saldo_a += (cuota_empresa_fija + cuota_empleado_fija) + int_a
        saldo_b += cuota_empresa_fija + int_b
        aport_acum_a += (cuota_empresa_fija + cuota_empleado_fija)
       
    st.markdown("---") # Separador visual antes de entrar en el gráfico
    
    # 3. Gráfico de Evolución
    fig_j = go.Figure()
    fig_j.add_trace(go.Scatter(x=edades, y=solo_capital_evol, mode='lines', name='CAPITAL APORTADO', stackgroup='one', fillcolor='#1E3A8A', line=dict(width=0)))
    fig_j.add_trace(go.Scatter(x=edades, y=interes_evol, mode='lines', name='INTERESES GENERADOS', stackgroup='one', fillcolor='rgba(147, 197, 253, 0.6)', line=dict(width=0)))
    fig_j.add_trace(go.Scatter(x=edades, y=cap_solo_empresa_evol, mode='lines', name='ESCENARIO SIN TU APORTACIÓN', line=dict(color='#EF4444', width=2, dash='dot')))

    fig_j.update_layout(
        title={
            'text': f"<b>PROYECCIÓN DE FONDOS HASTA LOS {edad_jub} AÑOS</b><br><span style='font-size:14px; color:#64748b;'>Aportación Total destinada al ahorro (Tú + Empresa): {cuota_empresa_fija + cuota_empleado_fija:,.2f} €/año</span>",
            'y': 0.94, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top',
            'font': dict(size=20, color='#1e293b')
        },
        xaxis_title="Edad del partícipe",
        yaxis_title="Capital acumulado (€)",
        hovermode='x unified', height=500, margin=dict(t=120, b=60, l=60, r=40),
        plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', linecolor='#cbd5e1', dtick=5),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', linecolor='#cbd5e1', tickformat=',.0f'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=11, color='#64748b'))
    )

    st.plotly_chart(fig_j, use_container_width=True, config={'displayModeBar': False})

 # 4. Cálculos finales y Comparativa Visual
    cap_a = cap_total_evol[-1]
    cap_b = cap_solo_empresa_evol[-1]
    dif_cap = cap_a - cap_b
    renta_a = cap_a / 240
    renta_b = cap_b / 240 
    dif_renta = renta_a - renta_b

    st.markdown("---")
    
    # --- FILA 1: COMPARATIVA DE CAPITALES ---
    st.markdown("#### 💰 Comparativa de Capitales al Jubilarte")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("CAPITAL TOTAL FINAL", f"{cap_a:,.0f} €")
    with c2:
        st.metric("CAPITAL (Si dejas de aportar)", f"{cap_b:,.0f} €", delta=f"-{dif_cap:,.0f} €", delta_color="inverse")
    with c3:
        st.info(f"**Patrimonio Extra:** +{dif_cap:,.0f} € acumulados gracias a tu aportación.")
     
    # --- FILA 2: COMPARATIVA DE RENTAS ---
    st.markdown("#### 📅 Comparativa de Renta Mensual (20 años)")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("RENTA PLAN ELEGIDO", f"{renta_a:,.2f} €/mes")
    with r2:
        st.metric("RENTA (Si dejas de aportar)", f"{renta_b:,.2f} €/mes", delta=f"-{dif_renta:,.2f} €/mes", delta_color="inverse")
    with r3:
        st.success(f"**Sobresueldo:** +{dif_renta:,.2f} € al mes adicionales para tu jubilación.")
 
    st.markdown("---")
    
    
    # --- FILA 4: Definición de Hipótesis ---
    st.markdown("#### ⚙️ Hipótesis y Bases del Modelo")
    h1, h2, h3 = st.columns(3)
    with h1:
        st.write("**⏳ Horizonte Temporal**")
        st.caption(f"El plan contempla un periodo de acumulación de **{años_plan} años** (hasta los {edad_jub}). Los cálculos asumen aportaciones constantes y reinversión total de dividendos.")  
    with h2:
        st.write("**📈 Rentabilidad Proyectada**")
        st.caption(f"Se ha aplicado una tasa anual media del **{rent_pct}%**. Esta rentabilidad es neta de comisiones de gestión y custodia estimadas.")
    with h3:
        st.write("**💶 Fiscalidad y Retiros**")
        st.caption("La renta mensual se calcula sobre un periodo de **20 años de desinversión**. No se considera rentabilidad durante este periodo (se confeccionará módulo específico). No se descuentan impuestos finales (IRPF/Plusvalías), que dependerán de la normativa vigente.")
        # --- CUADRO DE AVISO LEGAL (Opcional pero recomendado) ---
    st.warning("⚠️ **Nota importante:** Estas proyecciones son simulaciones basadas en datos históricos. Rentabilidades pasadas no garantizan resultados futuros. El capital final puede variar según la evolución real del mercado.")

import matplotlib
matplotlib.use('Agg') # CRITICO: Configura Matplotlib para trabajar en servidores sin pantalla
import matplotlib.pyplot as plt
import io
from fpdf import FPDF
import datetime

# --- 5. Función de Generación de PDF (VERSIÓN DEFINITIVA CORREGIDA) ---

import os
import io
import matplotlib.pyplot as plt
from fpdf import FPDF
import streamlit as st

# --- 1. PRIMERO DEFINES LA FUNCIÓN (Margen izquierdo, columna 0) ---
def generar_pdf_comparativo_v4(edad_act, edad_jub, cap_a, cap_b, renta_a, renta_b, dif_cap, dif_renta, rent_pct, aport_elegida):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabecera
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 20, txt="PROYECCIÓN DE LA PLANIFICACIÓN DE TU JUBILACION", ln=True, align='C')
    pdf.ln(15)
    
    # Datos
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, f"Simulacion para Edad {edad_act} -> {edad_jub} anos", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Aportacion Personal: {aport_elegida:,.2f} EUR/ano | Rentabilidad: {rent_pct}%", ln=True)
    pdf.ln(5)

    # Gráfico con solución temporal
    plt.figure(figsize=(6, 4))
    plt.bar(['Sin tu Aportacion', 'Con tu Plan'], [cap_b, cap_a], color=['#cbd5e1', '#1e40af'], width=0.6)
    plt.title('Capital Acumulado al Jubilarte (EUR)', fontsize=12, fontweight='bold')
    
    temp_img = f"temp_grafico_{edad_act}.png" # Nombre dinámico para evitar conflictos
    plt.savefig(temp_img, format='png', bbox_inches='tight', dpi=150)
    plt.close()
    
    pdf.image(temp_img, x=55, y=pdf.get_y(), w=100)
    if os.path.exists(temp_img):
        os.remove(temp_img)
    pdf.ln(75) 

    # Tabla
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(60, 10, " Concepto", 1, 0, 'L', True)
    pdf.cell(65, 10, "CON TU PLAN", 1, 0, 'C', True)
    pdf.cell(65, 10, "SIN TU APORTACION", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 10, " Capital Final", 1)
    pdf.cell(65, 10, f"{cap_a:,.0f} EUR", 1, 0, 'C')
    pdf.cell(65, 10, f"{cap_b:,.0f} EUR", 1, 1, 'C')
    
    pdf.cell(60, 10, " Renta Mensual (20a)", 1)
    pdf.cell(65, 10, f"{renta_a:,.2f} EUR", 1, 0, 'C')
    pdf.cell(65, 10, f"{renta_b:,.2f} EUR", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_fill_color(239, 246, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(30, 58, 138)
    texto_concl = (f"INCREMENTO PATRIMONIAL: Realizar este plan te permite jubilarte con "
                   f"{dif_cap:,.0f} EUR adicionales, mejorando tu renta en {dif_renta:,.2f} EUR/mes.")
    pdf.multi_cell(0, 10, txt=texto_concl, border='L', align='L', fill=True)

    return pdf.output(dest='S').encode('latin-1')

# --- 2. DESPUÉS COLOCAS EL BOTÓN (Dentro de tu Tab o sección de resultados) ---
st.markdown("---")
if st.button("🚀 GENERAR INFORME DE LA PROYECCIÓN (pdf)", use_container_width=True):
    with st.spinner("⏳ Procesando datos y dibujando gráficos..."):
        try:
            # Asegúrate de que las variables (edad_act, cap_a, etc.) estén definidas antes
            pdf_bytes = generar_pdf_comparativo_v4(
                edad_act, edad_jub, cap_a, cap_b, 
                renta_a, renta_b, dif_cap, dif_renta, 
                rent_pct, mi_aportacion_anual_neta
            )
            
            st.success("✅ ¡Informe generado con éxito!")
            st.download_button(
                label="📥 DESCARGAR MI INFORME (PDF)",
                data=pdf_bytes,
                file_name=f"Informe_Jubilacion_AportMax_{edad_act}anos.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_final" # Clave única para evitar errores de duplicidad
            )
        except NameError as e:
            st.error(f"Faltan datos para generar el informe. Asegúrate de completar los cálculos. ({e})")
        except Exception as e:
            st.error(f"❌ Error al crear el PDF: {e}")


with tab3:
    # --- RESUMEN EJECUTIVO DEL PROGRAMA ---
    # st.info("### 📋 Funcionalidades de la plataforma AportaMax")
    
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        st.markdown("""
        **¿Qué hace este programa?**
        * **Calcular la Aportación Máxima Personal a tu Plan de Pensiones de Empleo:** Calcula la devolución del ÏRPF que supone.
        * **Ayudarte a planificar tu ahorro:** Define un plan para que puedas ahorrar hasta lo máximo permitido.
        * **Proyectar los fondos a tu jubilación:** Calcula cuánto dinero tendrás al jubilarte basándose en tu ahorro actual y aportaciones futuras.
     
        """)

    with col_res2:
        st.markdown("""
        **Aspectos Técnicos y Legales:**
        * **Actualización 2026:** Cálculos ajustados a los límites legales vigentes en 2026.
        * **Matemática Financiera:** Uso de fórmulas de capitalización compuesta y rentas constantes.
        * **Fiscalidad:** Información detallada sobre fiscalidad (Catalunya).
        """)
    
    st.markdown("---") # Separador visual antes de entrar en el detalle legal
 
    st.markdown("### 📚 Información Legal y Metodología")
    
    # --- SECCIÓN: LEGISLACIÓN Y LÍMITES ---
    with st.expander("⚖️ Notas Legales", expanded=False):
        st.markdown(f"""
       
        La simulación se rige por la normativa vigente en **marzo de 2026** sobre el Impuesto sobre IRPF (tramos en Catalunya) y la Ley de Planes y Fondos de Pensiones:

        1.  **Límite General de Aportación:** * El límite máximo de reducción en la base imponible por aportaciones individuales a sistemas de previsión social es de **1.500 € anuales**.
            * Este límite puede incrementarse en hasta **8.500 € adicionales** (total 10.000 €) mediante contribuciones empresariales o planes de empleo.

        2.  **Tratamiento Fiscal (Diferimiento):**
            * Las aportaciones reducen la base imponible del IRPF, generando un **ahorro fiscal inmediato** según tu tipo marginal (entre el 19% y el 50% en Catalunya).
            * *Nota:* Los resultados de este simulador se muestran en valores brutos. El ahorro fiscal real supone un "descuento" extra en tu esfuerzo de ahorro anual.

        3.  **Liquidez y Contingencias:**
            * El rescate está vinculado a: jubilación, incapacidad, fallecimiento o dependencia.
        
        
        Estas proyecciones son cálculos matemáticos basados en la legislación de **marzo de 2026**. Cambios legislativos futuros podrían alterar los límites de aportación o el tratamiento fiscal del rescate.
        """)

    # --- SECCIÓN: ACERCA DE (Opcional, si quieres tenerlo aquí también) ---
    with st.expander("ℹ️ Acerca de esta Herramienta"):
        st.write("""
        Este simulador ha sido desarrollado para ilustrar el impacto del interés compuesto y la constancia en el ahorro a largo plazo. 
        Para consultas vinculantes, se recomienda acudir a un asesor fiscal o financiero.
        """)
