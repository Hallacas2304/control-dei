import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ESTILO UNDMO ---
st.set_page_config(page_title="DEI - Módulo UNDMO", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #1a1d1a; color: white; }
    .stMetric { background-color: #2b302b; padding: 15px; border-radius: 5px; border: 1px solid #454d45; }
    .vencido-card { background-color: #8c1c1c; padding: 12px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ff4d4d; color: white; }
    </style>
    """, unsafe_allow_html=True)

ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=60) 
def cargar_datos():
    try:
        response = requests.get(ONEDRIVE_LINK)
        # Cargamos el excel saltando la fila de encabezados extra si es necesario
        df = pd.read_excel(BytesIO(response.content))
        return df
    except: return None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🛡️ UNDMO")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_de_la_Polic%C3%ADa_Nacional_de_Colombia.svg", width=80)
    st.divider()
    if st.button("🔄 ACTUALIZAR DATOS"):
        st.cache_data.clear()
        st.rerun()

df = cargar_datos()

if df is not None:
    hoy = date.today()
    
    # Mapeo exacto según tu archivo Excel
    col_nombre = "APELLIDOS Y NOMBRES"
    col_cedula = "IDENTIFICACIÓN"
    col_comunicado = "COMUNICADO OFICIAL"
    
    # Identificar columnas de fechas por posición o nombre aproximado
    # En tu excel las fechas de vencimiento están en columnas específicas
    soat_v, tecno_v, lic_v, comunicados = [], [], [], []

    for index, fila in df.iterrows():
        nombre = str(fila.get(col_nombre, "DESCONOCIDO"))
        if nombre == "nan" or "FECHA" in nombre: continue
        
        cedula = str(fila.get(col_cedula, "---")).split('.')[0]
        identidad = f"🎖️ **{nombre}** (CC. {cedula})"

        # Comunicados
        com = str(fila.get(col_comunicado, ""))
        if com != "nan" and com.strip() != "" and com.upper() != "NO APLICA":
            comunicados.append(f"📢 **{nombre}**: {com}")
        
        # Lógica de fechas (buscando en las columnas del excel)
        for col in df.columns:
            valor = fila[col]
            nombre_col = str(col).upper()
            try:
                # Intentamos convertir a fecha
                fecha_v = pd.to_datetime(valor).date()
                if fecha_v < hoy:
                    # Clasificamos según el nombre de la columna en tu excel
                    if "SOAT" in nombre_col:
                        soat_v.append(f"{identidad} - Vence: {fecha_v}")
                    elif "TECNO" in nombre_col:
                        tecno_v.append(f"{identidad} - Vence: {fecha_v}")
                    elif "LICENCIA DE CONDUCCION" in nombre_col:
                        lic_v.append(f"{identidad} - Vence: {fecha_v}")
            except: pass

    st.title("🛡️ Panel de Control Operativo - UNDMO")
    
    if comunicados:
        with st.expander("🔔 COMUNICADOS OFICIALES", expanded=True):
            for c in comunicados: st.markdown(c)
        st.divider()

    st.subheader("🚨 NOVEDADES CRÍTICAS")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.write("🔴 **SOAT VENCIDO**")
        for m in set(soat_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not soat_v: st.success("Sin novedades")

    with c2:
        st.write("🔴 **TECNOMECÁNICA VENCIDA**")
        for m in set(tecno_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not tecno_v: st.success("Sin novedades")

    with c3:
        st.write("🔴 **LICENCIA VENCIDA**")
        for m in set(lic_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not lic_v: st.success("Sin novedades")

    st.divider()

    # TABLA GENERAL
    st.subheader("📋 MATRIZ DE SEGUIMIENTO (ESTILO EXCEL)")
    
    def color_vencido(val):
        try:
            if pd.to_datetime(val).date() < hoy: return 'background-color: #5c1414; color: white'
        except: pass
        return ''

    # Añadimos el nombre al final para que sea igual al inicio
    df['APELLIDOS Y NOMBRES '] = df[col_nombre]
    
    st.dataframe(df.style.map(color_vencido), use_container_width=True)

else:
    st.error("Error al cargar el archivo. Revisa el enlace de OneDrive.")
