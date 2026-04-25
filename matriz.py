import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO
import plotly.express as px

# Configuración de página con estilo tecnológico
st.set_page_config(page_title="DEI - Dashboard Inteligente", layout="wide", initial_sidebar_state="expanded")

# --- CSS Personalizado para que se vea Pro ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4B5563; }
    .stDataFrame { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=60) 
def cargar_datos():
    try:
        response = requests.get(ONEDRIVE_LINK)
        df = pd.read_excel(BytesIO(response.content))
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except: return None

# --- SIDEBAR (Barra Lateral) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=100)
    st.title("Panel de Control")
    st.info("Gestión Digital de Flota - Cúcuta")
    if st.button("🔄 SINCRONIZAR DATOS"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.markdown("### Configuración")
    mostrar_todo = st.checkbox("Mostrar toda la base de datos", value=True)

# --- PROCESAMIENTO ---
df = cargar_datos()

if df is not None:
    hoy = date.today()
    col_nombre = next((c for c in df.columns if 'NOMBRE' in c), df.columns[0])
    col_placa = next((c for c in df.columns if 'PLACA' in c), None)
    col_comunicado = next((c for c in df.columns if 'COMUNICADO' in c or 'NOTA' in c), None)
    
    soat_v, tecno_v, lic_v, sin_v, comunicados = [], [], [], [], []

    for _, fila in df.iterrows():
        nombre = fila[col_nombre]
        if col_comunicado and pd.notna(fila[col_comunicado]):
            comunicados.append(f"📢 **{nombre}**: {fila[col_comunicado]}")
        if col_placa and (pd.isna(fila[col_placa]) or str(fila[col_placa]) == ""):
            sin_v.append(nombre)
        
        for col in df.columns:
            try:
                f = pd.to_datetime(fila[col]).date()
                if f < hoy:
                    if 'SOAT' in col: soat_v.append(nombre)
                    elif 'TECNO' in col: tecno_v.append(nombre)
                    elif 'CONDUC' in col and 'TRANSIT' not in col: lic_v.append(nombre)
            except: pass

    # --- DISEÑO PRINCIPAL ---
    st.title("🛡️ Dashboard Estratégico DEI")
    
    # Fila de Métricas (Tarjetas tecnológicas)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SOAT Vencidos", len(soat_v), delta="- Crítico" if soat_v else "OK", delta_color="inverse")
    m2.metric("Tecno Vencidas", len(tecno_v), delta="- Revisar" if tecno_v else "OK", delta_color="inverse")
    m3.metric("Licencias Vencidas", len(lic_v), delta="- Alerta" if lic_v else "OK", delta_color="inverse")
    m4.metric("Personal Sin Vehículo", len(sin_v))

    # Comunicados en un diseño elegante
    if comunicados:
        with st.expander("🔔 ÚLTIMOS COMUNICADOS OFICIALES", expanded=True):
            for c in comunicados: st.write(c)

    # Gráfico de dona (Esto le da el toque tecnológico)
    st.divider()
    c_graf, c_info = st.columns([1, 1])
    
    with c_graf:
        total_vencidos = len(set(soat_v + tecno_v + lic_v))
        total_al_dia = len(df) - total_vencidos
        fig = px.pie(values=[total_al_dia, total_vencidos], names=['Al Día', 'Vencidos'], 
                     color_discrete_sequence=['#2ECC71', '#E74C3C'], hole=0.6, title="Estado de la Tropa")
        fig.update_layout(showlegend=False, height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with c_info:
        st.markdown("### 🚨 Listado de Urgencia")
        if soat_v or tecno_v:
            st.error(f"Hay documentos críticos vencidos. Favor notificar a los funcionarios.")
        else:
            st.success("Toda la documentación vehicular se encuentra vigente.")

    # Tabla con el nombre al inicio y final
    if mostrar_todo:
        st.markdown("### 📋 Matriz Digital de Seguimiento")
        df['FUNCIONARIO '] = df[col_nombre] # Nombre al final
        cols = [col_nombre] + [c for c in df.columns if c not in [col_nombre, 'FUNCIONARIO ']] + ['FUNCIONARIO ']
        
        def highlight_vencidos(val):
            try:
                if pd.to_datetime(val).date() < hoy: return 'background-color: #922B21; color: white'
            except: pass
            return ''

        st.dataframe(df[cols].style.applymap(highlight_vencidos), use_container_width=True)

else:
    st.error("Error al conectar con la base de datos de OneDrive.")
            
