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
def generar_informe_integral_2026(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: FISCALIDAD Y ACCIÓN ---
    pdf.add_page()
    
    # Encabezado Ejecutivo
    pdf.set_fill_color(30, 58, 138) # Azul Marino
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_xy(10, 15)
    pdf.set_font("helvetica", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "INFORME INTEGRAL DE PLANIFICACION 2026", align='C', ln=True)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 5, f"Simulacion Fiscal para Catalunya | Generado: {datetime.date.today().strftime('%d/%m/%Y')}", align='C', ln=True)

    # Bloque 1: Resumen Fiscal
    pdf.ln(25)
    pdf.set_text_color(30, 58, 138)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "1. ANALISIS DE LIMITES Y AHORRO FISCAL", ln=True)
    pdf.set_draw_color(30, 58, 138)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("helvetica", '', 10); pdf.set_text_color(0, 0, 0)
    tab_datos = [
        ("Sueldo Bruto Anual", f"{datos['sb']:,.2f} EUR"),
        ("Aportacion Empresa (PPE)", f"{datos['emp_t']:,.2f} EUR"),
        ("MAXIMA APORTACION PERSONAL LEGAL", f"{datos['max_p']:,.2f} EUR"),
        ("Ahorro Fiscal Estimado (IRPF)", f"{datos['ahorro']:,.2f} EUR"),
        ("Eficiencia (Retorno sobre inversion)", f"{datos['eficiencia']:.2f}%")
    ]
    for label, val in tab_datos:
        pdf.set_font("helvetica", 'B' if "MAXIMA" in label else '', 10)
        pdf.cell(120, 8, label, border='B')
        pdf.cell(70, 8, val, border='B', align='R', ln=True)

    # Bloque 2: Hoja de Ruta
    pdf.ln(15)
    pdf.set_text_color(30, 58, 138)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "2. HOJA DE RUTA: AJUSTES RECOMENDADOS", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("helvetica", '', 10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, f"Para alcanzar el limite legal y maximizar el ahorro, se sugiere una de estas dos vias:")
    pdf.ln(2)
    pdf.set_fill_color(245, 247, 250)
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(0, 12, f"  > OPCION A: Nueva cuota mensual: {datos['cuota_mes']:,.2f} EUR/mes", fill=True, ln=True)
    pdf.ln(2)
    pdf.cell(0, 12, f"  > OPCION B: Aportacion unica extra: {datos['extra']:,.2f} EUR", fill=True, ln=True)

    # --- PÁGINA 2: JUBILACIÓN ---
    pdf.add_page()
    pdf.set_text_color(30, 58, 138)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "3. PROYECCION DE IMPACTO EN LA JUBILACION", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", '', 10)
    pdf.multi_cell(0, 6, f"Estimacion basada en jubilacion a los {datos['edad_jub']} años con rentabilidad del {datos['rent_pct']}%.")
    
    # Cuadros de resultados
    pdf.ln(5)
    pdf.set_fill_color(240, 245, 255)
    pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(90, 10, "CAPITAL FINAL ESTIMADO:")
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(90, 10, f"{datos['cap_final']:,.0f} EUR", align='R', ln=True)
    
    pdf.set_x(15); pdf.set_font("helvetica", 'B', 12)
    pdf.cell(90, 15, "RENTA MENSUAL ADICIONAL (20A):")
    pdf.set_text_color(22, 163, 74) # Verde
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(90, 15, f"{datos['renta_mensual']:,.2f} EUR/mes", align='R', ln=True)

    # Aviso Legal
    pdf.set_y(-30)
    pdf.set_font("helvetica", 'I', 8); pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4, "Aviso: Este documento es una simulacion tecnica. Las rentabilidades pasadas no garantizan beneficios futuros. Consulte con su asesor antes de realizar operaciones.", align='C')

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
max_p12 = max_p/12
max_now = max_p * meses_pasados

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
extra_now = 


# --- CÁLCULOS GLOBALES (Poner esto ANTES de los st.tabs) ---
# Sumamos lo que pone la empresa y lo que pones tú (el máximo permitido)
total_inv = emp_t + max_p 

# Calculamos el ahorro y los meses (ya lo tienes en tu lógica anterior)
ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
# años_jub = 67 - edad  # 'edad' viene del sidebar

# --- 6. RENDERIZADO PRINCIPAL ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;500;800&display=swap');
        
        .header-wrapper {
            padding: 10px 0 5px 0; /* Altura mínima absoluta */
            text-align: center;
            background: transparent;
        }
        
        .main-title {
            font-family: 'Inter', sans-serif;
            font-weight: 100;
            color: #0f172a;
            letter-spacing: 5px; 
            font-size: 1.5rem; /* Letra más pequeña y fina */
            margin: 0;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .year-highlight {
            font-weight: 800;
            color: #1d4ed8; /* Azul más fuerte (cobalto) */
            margin-left: 10px;
            letter-spacing: 1px;
            font-size: 1.5rem;
        }
        
        .subtitle-slim {
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            color: #64748b;
            letter-spacing: 1px;
            font-size: 0.55rem;
            margin-top: 2px; /* Espacio mínimo */
            text-transform: uppercase;
            opacity: 0.8;
        }
    </style>
    
    <div class="header-wrapper">
        <h1 class="main-title">
            AVOL <span class="year-highlight">2026</span>
        </h1>
        <p class="subtitle-slim">Aportación Voluntaria • Plan de Pensiones de Empleo</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💰 Aportación Máxima ", "🚀 Proyección a la Jubilación ", "🎯 Acerca de Fes... "])

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
    # pdf_t = generar_pdf_tecnico(emp_t, max_p, (emp_t+max_p), ahorro, esfuerzo_neto, sb, CUOTA_SS, 2000.0, base_pre, eficiencia)
    # st.download_button("📄 Informe Fiscal Detallado", data=pdf_t, file_name="informe_fiscal_2026.pdf", mime="application/pdf")

with st.expander("ℹ️ Te recomiendo como lograr que tu ahorro sea máximo y de forma facil"):
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
        msg_estado = f"💡 Puedes aportar hasta {max_p - proyeccion_final:,.2f} € adicionales (hasta 31 de diciembre)"
        icon_estado = "ℹ️"

    # --- 2. INDICADOR VISUAL DE PROGRESO (Estilo Minimal) ---
    st.markdown(f"""
        <div style="margin-bottom: 25px; padding: 10px 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.9rem; color: #475569; font-weight: 500;">
                    {icon_estado} {msg_estado}
                </span>
                <span style="font-size: 0.85rem; color: #94a3b8;">
                    {proyeccion_final:,.0f} € de {max_p:,.0f} €
                </span>
            </div>
            <div style="background-color: #f1f5f9; border-radius: 20px; height: 8px; width: 100%;">
                <div style="background-color: #64748b; width: {min(porcentaje_uso * 100, 100):.1f}%; height: 8px; border-radius: 20px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


    # --- 3. RECOMENDACIÓN DE AJUSTE (Estilo Elegante) ---
    if proyeccion_final != max_p:
        if abs(proyeccion_final - max_p) > 1.0:
            # Definimos una sutileza de color según la acción
            color_acentuado = "#334155" # Gris oscuro profesional
            
            st.markdown(f"""
                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 12px; margin: 15px 0;">
                    <p style="text-transform: uppercase; letter-spacing: 1px; font-size: 0.7rem; color: #64748b; font-weight: 700; margin-bottom: 15px;">
                        Estrategia Sugerida    {"🔼 (<b> Incrementar</b>" if diferencia_mensual > 0 else "🔽 <b>reducir</b>"} la cuota actual en <b>{abs(diferencia_mensual):,.2f} €</b> durante {meses_restantes} meses).
                    </p>
                  #  <p style="font-size: 0.95rem; color: #1e293b; line-height: 1.5; margin-bottom: 20px;">
                  #      Para ajustarte al límite de <b>{max_p:,.2f} €</b>, la nueva cuota mensual recomendada es:
                  #  </p>
                    <div style="margin-bottom: 10px;">
                        <span style="font-size: 1.4rem; font-weight: 350; color: {color_acentuado};">{nueva_cuota_total:,.2f} €</span>
                        <span style="font-size: 1rem; color: #94a3b8;"> / mes (durante los meses que quedan del año)</span>
                    </div>
                                                 
                </div>
            """, unsafe_allow_html=True)
   
            st.markdown(f"""
                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 12px; margin: 15px 0;">
                    <p style="text-transform: uppercase; letter-spacing: 1px; font-size: 0.7rem; color: #64748b; font-weight: 700; margin-bottom: 15px;">
                        Estrategia Sugerida 🔼 Combinar aportaciones extraordinaria con aportaciones periodicas.
                    </p>
                    <p style="font-size: 0.95rem; color: #1e293b; line-height: 1.5; margin-bottom: 20px;">
                        Para ajustarte al límite de <b>{max_p:,.2f} €</b>, la nueva cuota mensual recomendada es:
                    </p>
                    <div style="margin-bottom: 10px;">
                        <span style="font-size: 1.4rem; font-weight: 300; color: {color_acentuado};">{nueva_cuota_total:,.2f} €</span>
                        <span style="font-size: 1rem; color: #94a3b8;"> / mes (durante los meses que quedan del año)</span>
                    </div>
                                                 
                </div>
            """, unsafe_allow_html=True)
        
    
    else:
        st.success("Planificación optimizada al 100%")
    



with st.expander("ℹ️ ¿Cómo realizar tu aportación on line?"):
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

# pdf_v = generar_pdf_visual_v2(max_p, ahorro, (emp_t+max_p), aportacion_extraordinaria_neta, nueva_cuota_total, meses_restantes, ya_aportado)
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
    

    # --- SECCIÓN DE REUSLTADO: IMPACTO FINAL (DISEÑO ULTRA-FINO) ---
    st.markdown("<br><h4 style='text-align: center; font-weight: 300; color: #1e293b; letter-spacing: 1px;'>EL VALOR DE TU ESTRATEGIA A LARGO PLAZO</h4>", unsafe_allow_html=True)

    # Estilos CSS de alta fidelidad
    st.markdown("""
        <style>
        .premium-card {
            background: #ffffff;
            padding: 25px;
            border-radius: 16px;
            border: 1px solid #f1f5f9;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02), 0 4px 6px -2px rgba(0, 0, 0, 0.01);
            transition: all 0.3s ease;
        }
        .premium-card:hover {
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
            transform: translateY(-2px);
        }
        .label-fina {
            font-size: 0.7rem;
            letter-spacing: 1.5px;
            color: #94a3b8;
            font-weight: 700;
            margin-bottom: 12px;
            text-transform: uppercase;
        }
        .valor-fino {
            font-size: 2.2rem;
            font-weight: 200;
            color: #1e293b;
            margin: 5px 0;
        }
        .subtexto-fino {
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 10px;
        }
        .delta-positiva {
            color: #10b981;
            font-weight: 600;
            font-size: 0.85rem;
            background: #f0fdf4;
            padding: 4px 10px;
            border-radius: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- FILA 1: PATRIMONIO ---
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f"""<div class="premium-card">
            <div class="label-fina">Capital Proyectado</div>
            <div class="valor-fino">{cap_a:,.0f}<span style="font-size: 1rem;"> €</span></div>
            <div class="subtexto-fino">Rentabilidad estimada del {rent_pct}%</div>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""<div class="premium-card">
            <div class="label-fina">Sin Aportación Personal</div>
            <div class="valor-fino" style="color: #cbd5e1;">{cap_b:,.0f}<span style="font-size: 1rem;"> €</span></div>
            <div style="margin-top: 10px;"><span style="color: #ef4444; font-size: 0.8rem;">✕ Pérdida de {dif_cap:,.0f} €</span></div>
        </div>""", unsafe_allow_html=True)
        
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- FILA 2: CALIDAD DE VIDA ---
    r1, r2 = st.columns(2)
    
    with r1:
        st.markdown(f"""<div class="premium-card">
            <div class="label-fina">Renta Mensual</div>
            <div class="valor-fino" style="color: #10b981;">{renta_a:,.0f}<span style="font-size: 1rem;"> €/mes</span></div>
            <div class="subtexto-fino">Complemento vitalicio estimado</div>
        </div>""", unsafe_allow_html=True)

    with r2:
        st.markdown(f"""<div class="premium-card">
            <div class="label-fina">Diferencial</div>
            <div class="valor-fino" style="color: #cbd5e1;">{renta_b:,.0f}<span style="font-size: 1rem;"> €</span></div>
            <div style="margin-top: 10px;"><span style="color: #ef4444; font-size: 0.8rem;">✕ {dif_renta:,.0f} € menos al mes</span></div>
        </div>""", unsafe_allow_html=True)

 
    st.markdown("<br><br>", unsafe_allow_html=True)
    
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
    st.markdown("---") # Separador visual

# Recopilación de todas las variables calculadas
datos_pdf = {
    'sb': sb,
    'emp_t': emp_t,
    'max_p': max_p,
    'ahorro': ahorro,
    'eficiencia': eficiencia,
    'cuota_mes': nueva_cuota_total,
    'extra': aportacion_extraordinaria_neta,
    'edad_jub': edad_jub,
    'rent_pct': rent_pct,
    'cap_final': cap_a,
    'renta_mensual': renta_a
}

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Exportar Resultados")
if st.sidebar.button("📄 GENERAR INFORME UNIFICADO (PDF)", use_container_width=True, type="primary"):
    informe_pdf = generar_informe_integral_2026(datos_pdf)
    st.sidebar.download_button(
        label="⬇️ Descargar PDF",
        data=informe_pdf,
        file_name=f"Informe_AportaMax_2026_{hoy.strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
