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

# --- 1. DEFINICIÓN DE FUNCIONES (Debe ir antes que el Sidebar) ---
def calcular_max_personal_adicional(e, salario):
    if salario > 60000:
        return e
    if e <= 500:
        return e * 8.5
    elif e <= 1500:
        return 1250 + (0.25 * (e - 500))
    else:
        return e


# --- 2. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Avol 2026", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    [data-testid="stAppViewBlockContainer"] {
    padding-top: 2rem;
}
        .main-header {
            background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
            padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;
        }
        .card {
            padding: 0px; border-radius: 15px; text-align: center;
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

    # --- JUBILACIÓN ---
    # pdf.add_page()
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





import streamlit as st

# 1. FUNCIÓN DE APOYO
def calcular_max_personal_adicional(e, salario):
    if salario > 60000: return e
    if e <= 500: return e * 2.5
    elif e <= 1500: return 1250 + (0.25 * (e - 500))
    else: return e

# --- 2. CONTENEDOR DE CONFIGURACIÓN ---
# Usamos un expander principal para agrupar todo
with st.expander("⚙️ CONFIGURACIÓN (Datos para realizar estimación)", expanded=True):
    
    # Creamos dos columnas para que no ocupe tanto espacio vertical
    col_emp, col_pers = st.columns(2)
    
    with col_emp:
        st.markdown("#### 👤 Empresa")
        sb = st.number_input("Sueldo Bruto Anual (€)", value=0.0, key="sb_unique")
        e_ahorro = st.number_input("Aportación Mensual Empresa (€)", value=0.0, key="ahorro_unique")
        e_riesgo = st.number_input("Prima Riesgo PPE (€)", value=0.0, key="riesgo_unique")
        
        # Cálculo inmediato
        emp_t = min((e_ahorro * 12) + e_riesgo, 10000.0)

    # --- LÓGICA INTERMEDIA (Se ejecuta aquí para que col_pers tenga los límites) ---
    ss_estimada = min(sb, 61212.0) * 0.0635
    base_imponible = max(0.0, sb - ss_estimada - 2000.0)
    max_p_coef = calcular_max_personal_adicional(emp_t, sb)
    MAX_P_LIMIT = max(0.0, min(max_p_coef + 1500.0, 10000.0 - emp_t))
    
    if (emp_t + MAX_P_LIMIT) > (base_imponible * 0.30):
        MAX_P_LIMIT = max(0.0, (base_imponible * 0.30) - emp_t)

    with col_pers:
        st.markdown("#### 📅 Personal")
        c_m = st.number_input("Aportación Mensual (€)", value=0.0, key="mensual_unique")
        
        # El límite dinámico es clave
        e_y = st.number_input(
            "Aportación Extra ya realizada (€)", 
            value=0.0, 
            max_value=max(0.1, float(MAX_P_LIMIT)), 
            key="extra_unique"
        )
        


# --- 5. LÓGICA DE CÁLCULO ---

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
aport_previstas = c_m *12 + e_y
cumplimiento_plan = ((c_m *12 + e_y)*100)/max_p if max_p > 0 else 0
extra_now = 0


# --- CÁLCULOS GLOBALES (Poner esto ANTES de los st.tabs) ---
# Sumamos lo que pone la empresa y lo que pones tú (el máximo permitido)
total_inv = emp_t + max_p 

# Calculamos el ahorro y los meses (ya lo tienes en tu lógica anterior)
ahorro = calcular_irpf_cat(base_pre) - calcular_irpf_cat(base_pre - max_p)
# años_jub = 67 - edad  # 'edad' viene del sidebar

# --- 6. RENDERIZADO PRINCIPAL ---
# --- 6. RENDERIZADO PRINCIPAL (Cabecera pegada arriba) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;500;800&display=swap');
        
        /* 1. ELIMINAR EL MARGEN SUPERIOR DE LA APP */
        [data-testid="stAppViewBlockContainer"] {
            padding-top: 1rem !important; /* El valor por defecto es 6rem */
            padding-bottom: 1rem;
        }

        /* 2. OCULTAR LA BARRA SUPERIOR DE STREAMLIT */
        [data-testid="stHeader"] {
            display: none;
        }

        .header-wrapper {
            padding: 0;
            margin-top: -15px; /* Sube el título incluso más allá del padding */
            text-align: center;
        }
        
        .main-title {
            font-family: 'Inter', sans-serif;
            font-weight: 100;
            color: #0f172a;
            letter-spacing: 5px; 
            font-size: 1.3rem;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .year-highlight {
            font-weight: 800;
            color: #1d4ed8; 
            margin-left: 10px;
            font-size: 1.5rem;
        }
        
        .subtitle-slim {
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            color: #64748b;
            letter-spacing: 1px;
            font-size: 0.55rem;
            margin-top: -2px; 
            text-transform: uppercase;
            opacity: 0.8;
        }
    </style>
    
    <div class="header-wrapper">
        <h1 class="main-title">
            AVOL <span class="year-highlight">2026</span>
        </h1>
        <p class="subtitle-slim">Aportación Voluntaria • Plan de Pensiones de Empleo (PPE) </p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([ "   Aportación Máxima     ", "   Proyección a la Jubilación     ",  "   Acerca de ...   "])


with tab1:
    # 1. Bloque de Aportación Adicional (Número destacado)
    st.markdown(
        f"""
        <hr style="margin: 1em 0; border: 0; border-top: 1px solid #f1f5f9;">
        <div style="text-align: center; padding: 10px;">
            <p style='margin:0; font-size:1.0rem; color: #64748b;'>
                <b>💰 Aportación adicional al PPE este año (máximo)</b>
            </p>
            <h4 style='margin:10px 0; font-size:2.5rem; color:#334155; line-height:1.0; font-weight:650;'>
                {aportacion_extraordinaria_neta:,.0f}€
            </h4>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # 2. Lógica y Tarjeta Ancha de Resumen
    cumplimiento_val = float(cumplimiento_plan) if cumplimiento_plan else 0.0

    if cumplimiento_val > 100.0:
        st.warning("⚠️ **Revisa tus datos:** El nivel de aportación calculado supera el límite permitido (100%). Por favor, verifica los importes en el panel lateral y/o revisa tu Plan de Accion ajustando cuotas futuras o suspendiendolas.")
    
    html_card = f"""
    <div style="display: block; text-align: left; margin-top: 10px; width: 100%; background: #f8fafc; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <h3 style="margin: 0 0 20px 0; color: #334155; font-size: 1.0rem; font-weight: 600; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
            📊 Resumen de aportaciones
        </h3>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color:#64748b; font-size:1rem;">Promotor (Empresa):</span>
            <span style="font-weight:700; color:#0f172a; font-size:1rem;">{emp_t:,.2f}€</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color:#64748b; font-size:1rem;">Máximo Personal:</span>
            <span style="font-weight:700; color:#0f172a; font-size:1rem;">{max_p:,.2f}€</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; border-top: 1px dotted #cbd5e1; padding-top: 10px; margin-top: 8px;">
            <span style="color:#64748b; font-size:1rem; font-weight:600;">Total Inversión Potencial:</span>
            <span style="font-weight:700; color:#0f172a; font-size:1rem;">{total_inv:,.2f}€</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
            <span style="color:#64748b; font-size:1rem;">Ya realizada / planificada:</span>
            <span style="font-weight:700; color:#3b82f6; font-size:1rem;">{aport_previstas:,.2f}€</span>
        </div>
        <div style="background-color: #e2e8f0; border-radius: 10px; height: 12px; width: 100%;">
            <div style="background-color: #3b82f6; width: {min(cumplimiento_val, 100.0):.0f}%; height: 12px; border-radius: 10px;"></div>
        </div>
        <p style='margin: 10px 0 0 0; color:#64748b; font-size:0.9rem; text-align: center;'>
            Estás al <b>{cumplimiento_val:,.1f}%</b> de tu capacidad de ahorro
        </p>
    </div>
    <br>
    """
    st.markdown(html_card, unsafe_allow_html=True)

 

with st.expander("ℹ️ Ahorro Fiscal", expanded=False):
    col_left, col_right = st.columns([1.1, 1])
    
    with col_left:
        # Card de Ahorro Fiscal
        st.markdown(f"""
            <div style="background-color: #ffffff; color: #0f172a; padding: 25px; 
                        border-radius: 12px; height: 180px; text-align: left; 
                        border: 1px solid #e2e8f0; display: flex; flex-direction: column; 
                        justify-content: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <p style="margin:0; font-size: 0.7rem; color: #64748b; font-weight: 800; 
                          text-transform: uppercase; letter-spacing: 1px;">AHORRO FISCAL (IRPF. Tramos Catalunya)</p>
                <h2 style="font-size: 2.1rem; margin: 10px 0; color: #10b981; border: none; font-weight: 700;">
                    {ahorro:,.2f} €
                </h2>
                <p style="margin:0; font-weight: 700; font-size: 0.85rem; color: #0f172a;">
                    Devolución estimada: <span style="color: #10b981;">{eficiencia:.1f}%</span>
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") # Espaciador más limpio que <br>
        st.info(f"⚠️ **Nota:** Cálculos basados en un Salario Bruto de **{sb:,.0f} € (tramos IRPF en Catalunya)**.")   

    with col_right:
        total_inversion = esfuerzo_neto + ahorro + emp_t
        
        fig = go.Figure(data=[go.Pie(
            labels=['Esfuerzo Neto', 'Ahorro Fiscal', 'Aport. Empresa'], 
            values=[esfuerzo_neto, ahorro, emp_t], 
            hole=.7,
            marker_colors=['#3b82f6', '#10b981', '#334155'],
            textinfo='none', 
            hoverinfo='label+value+percent',
            sort=False # Mantiene el orden de los labels
        )])
        
        fig.update_layout(
            title={'text': "Distribución de la Inversión", 'y': 0.95, 'x': 0.5, 'xanchor': 'center'},
            margin=dict(t=50, b=0, l=0, r=0), 
            height=280, 
            showlegend=True, 
            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
            annotations=[dict(
                text=f"TOTAL<br><b>{total_inversion:,.0f}€</b>", 
                x=0.5, y=0.5, 
                showarrow=False,
                font=dict(size=14, color="#334155")
            )]
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)


with st.expander("ℹ️ Tu Plan de Acción", expanded=False):
    # --- 1. CÁLCULOS DE PRECISIÓN ---
    faltante_total = max_p - ya_aportado
    
    # OPCIÓN A: Reparto lineal (Agresiva/Ajuste Directo)
    cuota_mensual_pura = faltante_total / meses_restantes if meses_restantes > 0 else 0
    
    # OPCIÓN B: Plan Sostenible (Con lógica de reajuste si hay exceso)
    cuota_ideal_estandar = max_p / 12
    total_futuro_estandar = cuota_ideal_estandar * meses_restantes
    
    # Calculamos el pago extra necesario para cuadrar el puzzle
    pago_extraordinario = max_p - ya_aportado - total_futuro_estandar
    
    if pago_extraordinario < 0:
        # CASO ESPECIAL: El usuario ya ha aportado de más.
        # La cuota sostenible se reduce para ser igual a la Opción A.
        pago_extraordinario = 0.0
        cuota_sostenible_final = cuota_mensual_pura
        subtitulo_b = "Cuota reducida por aportación previa alta"
        detalle_b = "Como ya has aportado gran parte del límite, tu cuota se ajusta al mínimo necesario, sin perjuicio de su revisión a año siguiente"
    else:
        # CASO NORMAL: Puede mantener la cuota ideal haciendo el pago extra.
        cuota_sostenible_final = cuota_ideal_estandar
        subtitulo_b = "Cuota ideal de ahorro prorrateado"
        detalle_b = f"Compensa el retraso ahora con un pago único y fija una cuota mensual futura de {cuota_sostenible_final:,.2f} €. que corresponde a 1/12 del límite máximo."

    # --- 2. INDICADOR VISUAL (Barra de progreso) ---
    proyeccion_actual = ya_aportado + (c_m * meses_restantes)
    porcentaje = min(proyeccion_actual / max_p, 1.0) if max_p > 0 else 0
    
    # (Bloque de la barra de progreso - omitido aquí para brevedad, mantén el que tienes)

    # --- 3. COMPARATIVA DE ESTRATEGIAS ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; height: 210px;">
                <p style="font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase;">Opción A: Ajuste de Cuota</p>
                <p style="font-size: 1.6rem; font-weight: 850; color: #1e293b; margin: 5px 0;">{cuota_mensual_pura:,.2f} € <span style="font-size: 0.8rem;">/mes</span></p>
                <p style="font-size: 0.75rem; color: #475569; line-height: 1.4;">Sin pagos extra. El esfuerzo se reparte linealmente en las cuotas de aquí a diciembre.</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        # El color cambia a azul suave si es un reajuste por exceso, o verde si es el plan estándar
        bg_color = "#f0f9ff" if pago_extraordinario == 0 else "#f0fdf4"
        border_color = "#bae6fd" if pago_extraordinario == 0 else "#bbf7d0"
        
        st.markdown(f"""
            <div style="background-color: {bg_color}; border: 1px solid {border_color}; padding: 20px; border-radius: 12px; height: 210px;">
                <p style="font-size: 0.7rem; font-weight: 800; color: #0369a1; text-transform: uppercase;">Opción B: {subtitulo_b} ✨</p>
                <p style="font-size: 1.6rem; font-weight: 850; color: #0369a1; margin: 5px 0;">{cuota_sostenible_final:,.2f} € <span style="font-size: 0.8rem;">/mes</span></p>
                <p style="font-size: 0.9rem; font-weight: 700; color: #0c4a6e; margin-bottom: 5px;">+ {pago_extraordinario:,.2f} € como aportación extraordinaria adicional este año </p>
                <p style="font-size: 0.75rem; color: #0369a1; opacity: 0.8; line-height: 1.4;">{detalle_b}</p>
            </div>
        """, unsafe_allow_html=True)




with st.expander("ℹ️ ¿Cómo realizar tu aportación on line?",expanded=False):
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
            <div class="label-fina">SIN APORTACIÓN PERSONAL</div>
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
