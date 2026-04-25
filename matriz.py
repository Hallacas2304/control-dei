import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ESTILO UNDMO ---
st.set_page_config(page_title="DEI - Módulo UNDMO", layout="wide")

# CSS para estilo institucional y moderno
st.markdown("""
    <style>
    .main { background-color: #1a1d1a; color: white; } /* Fondo verde oscuro blindado */
    h1, h2, h3 { color: #d4d8d4 !important; }
    .stMetric { background-color: #2b302b; padding: 15px; border-radius: 5px; border: 2px solid #454d45; }
    .stDataFrame { border: 1px solid #454d45; }
    .vencido-card { background-color: #8c1c1c; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ff4d4d; }
    </style>
    """, unsafe_allow_html=True)

# ENLACE ONEDRIVE
ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=60) 
def cargar_datos():
    try:
        response = requests.get(ONEDRIVE_LINK)
        df = pd.read_excel(BytesIO(response.content))
        # Limpieza estándar de columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except: return None

# --- SIDEBAR OPERATIVO ---
with st.sidebar:
    st.markdown("## 🛡️ UNDMO")
    st.markdown("### Unidad Nacional de Diálogo y Mantenimiento del Orden")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_de_la_Polic%C3%ADa_Nacional_de_Colombia.svg", width=100)
    st.divider()
    st.info("Cúcuta - Sección Logística")
    if st.button("🔄 SINCRONIZAR CON BASE DE DATOS"):
        st.cache_data.clear()
        st.rerun()

# --- PROCESAMIENTO DE INFORMACIÓN ---
df = cargar_datos()

if df is not None:
    hoy = date.today()
    
    # Identificar columnas clave (Asegúrate que se llamen así en el Excel)
    col_nombre = next((c for c in df.columns if 'NOMBRE' in c), df.columns[0])
    col_cedula = next((c for c in df.columns if 'CEDULA' in c or 'DOCUMENTO' in c), None)
    col_comunicado = next((c for c in df.columns if 'COMUNICADO' in c or 'NOTA' in c), None)
    
    # Repetir nombre al final para la tabla
    df['FUNCIONARIO '] = df[col_nombre]

    soat_v, tecno_v, lic_v, comunicados = [], [], [], []

    for _, fila in df.iterrows():
        nombre = fila[col_nombre]
        # Obtener cédula de forma segura
        cedula = str(fila[col_cedula]).split('.')[0] if col_cedula and pd.notna(fila[col_cedula]) else "N/A"
        
        info_funcionario = f"🎖️ **{nombre}** - CC. {cedula}"

        if col_comunicado and pd.notna(fila[col_comunicado]) and str(fila[col_comunicado]).strip() != "":
            comunicados.append(f"📢 **{nombre}**: {fila[col_comunicado]}")
        
        for col in df.columns:
            try:
                f = pd.to_datetime(fila[col]).date()
                if f < hoy:
                    if 'SOAT' in col: soat_v.append(f"{info_funcionario} (Vence SOAT: {f})")
                    elif 'TECNO' in col: tecno_v.append(f"{info_funcionario} (Vence TECNO: {f})")
                    elif 'CONDUC' in col and 'TRANSIT' not in col: lic_v.append(f"{info_funcionario} (Vence LICENCIA: {f})")
            except: pass

    # --- DISEÑO DEL MÓDULO UNDMO ---
    st.title("🛡️ Módulo de Control de Flota - DEI UNDMO")
    
    # 1. COMUNICADOS OFICIALES (Solo si hay)
    if comunicados:
        with st.expander("🔔 COMUNICADOS DE LA SECCIÓN", expanded=True):
            for c in comunicados:
                st.markdown(c)
        st.divider()

    # 2. SECCIÓN DE VENCIMIENTOS (Nombre y Cédula)
    st.write("### 🚨 NOVEDADES CRÍTICAS DETECTADAS")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.write("#### ⚠️ SOAT VENCIDOS")
        if soat_v:
            for m in soat_v:
                st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        else: st.success("Todo el SOAT está al día")

    with c2:
        st.write("#### ⚠️ TECNOMECÁNICA VENCIDA")
        if tecno_v:
            for m in tecno_v:
                st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        else: st.success("Todo el material de Tecno está al día")

    with c3:
        st.write("#### ⚠️ LICENCIAS DE CONDUCCIÓN")
        if lic_v:
            for m in lic_v:
                st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        else: st.success("Todas las licencias están vigentes")

    st.divider()

    # 3. TABLA GENERAL OPERATIVA
    st.write("### 📋 MATRIZ INTEGRAL DE SEGUIMIENTO (Nombre al inicio y final)")
    
    def highlight_vencidos(val):
        try:
            if pd.to_datetime(val).date() < hoy: return 'background-color: #8c1c1c; color: white'
        except: pass
        return ''

    # Reordenar: Nombre al principio
    cols = list(df.columns)
    cols.insert(0, cols.pop(cols.index(col_nombre)))
    
    st.dataframe(df[cols].style.applymap(highlight_vencidos), use_container_width=True)

else:
    st.error("Error al conectar con la base de datos de OneDrive.")
                            
