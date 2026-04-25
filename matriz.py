import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ESTILO UNDMO ---
st.set_page_config(page_title="DEI - Módulo UNDMO", layout="wide")

# CSS para estilo institucional
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
        df = pd.read_excel(BytesIO(response.content))
        df.columns = [str(c).strip().upper() for c in df.columns]
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
    col_nombre = next((c for c in df.columns if 'NOMBRE' in c), df.columns[0])
    col_cedula = next((c for c in df.columns if 'CEDULA' in c or 'DOCUMENTO' in c), None)
    col_comunicado = next((c for c in df.columns if 'COMUNICADO' in c or 'NOTA' in c), None)
    
    soat_v, tecno_v, lic_v, comunicados = [], [], [], []

    for _, fila in df.iterrows():
        nombre = fila[col_nombre]
        cedula = str(fila[col_cedula]).split('.')[0] if col_cedula and pd.notna(fila[col_cedula]) else "---"
        identidad = f"🎖️ **{nombre}** (CC. {cedula})"

        # Comunicados (Solo si hay texto)
        if col_comunicado and pd.notna(fila[col_comunicado]) and str(fila[col_comunicado]).strip() != "":
            comunicados.append(f"📢 **{nombre}**: {fila[col_comunicado]}")
        
        # Revisión de fechas
        for col in df.columns:
            try:
                f = pd.to_datetime(fila[col]).date()
                if f < hoy:
                    if 'SOAT' in col: soat_v.append(f"{identidad} - Vence: {f}")
                    elif 'TECNO' in col: tecno_v.append(f"{identidad} - Vence: {f}")
                    elif 'CONDUC' in col and 'TRANSIT' not in col: lic_v.append(f"{identidad} - Vence: {f}")
            except: pass

    st.title("🛡️ Panel de Control Operativo - UNDMO")
    
    # 1. COMUNICADOS OFICIALES (Dinámico)
    if comunicados:
        with st.expander("🔔 COMUNICADOS RECIENTES", expanded=True):
            for c in comunicados: st.markdown(c)
        st.divider()

    # 2. NOVEDADES (Nombre y Cédula)
    st.subheader("🚨 NOVEDADES CRÍTICAS")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.write("🔴 **SOAT VENCIDO**")
        for m in soat_v: st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not soat_v: st.success("Sin novedades")

    with c2:
        st.write("🔴 **TECNO VENCIDA**")
        for m in tecno_v: st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not tecno_v: st.success("Sin novedades")

    with c3:
        st.write("🔴 **LICENCIA VENCIDA**")
        for m in lic_v: st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not lic_v: st.success("Sin novedades")

    st.divider()

    # 3. TABLA GENERAL
    st.subheader("📋 MATRIZ DE SEGUIMIENTO")
    
    # Función de color corregida para evitar el AttributeError
    def color_filas(val):
        try:
            if pd.to_datetime(val).date() < hoy: return 'background-color: #5c1414; color: white'
        except: pass
        return ''

    df['FUNCIONARIO '] = df[col_nombre] # Duplicar nombre al final
    cols_finales = [col_nombre] + [c for c in df.columns if c not in [col_nombre, 'FUNCIONARIO ']] + ['FUNCIONARIO ']
    
    st.dataframe(df[cols_finales].style.map(color_filas), use_container_width=True)

else:
    st.error("Error de conexión. Verifica el archivo en OneDrive.")
