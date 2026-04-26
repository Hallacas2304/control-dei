import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ESTILO UNDMO ---
st.set_page_config(page_title="DEI2 GUDMO 16", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #1a1d1a; color: white; }
    .vencido-card { background-color: #8c1c1c; padding: 12px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ff4d4d; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=30) 
def cargar_datos():
    try:
        response = requests.get(ONEDRIVE_LINK)
        # Cargamos el excel sin procesar para limpiar los encabezados dobles
        df = pd.read_excel(BytesIO(response.content), header=[0, 1])
        # Aplanamos los nombres de las columnas para que sean fáciles de buscar
        df.columns = [f"{str(a).strip()} {str(b).strip()}".upper() for a, b in df.columns]
        return df
    except: return None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🛡️ UNDMO")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_de_la_Polic%C3%ADa_Nacional_de_Colombia.svg", width=80)
    st.divider()
    if st.button("🔄 ACTUALIZAR SISTEMA"):
        st.cache_data.clear()
        st.rerun()

df = cargar_datos()

if df is not None:
    hoy = date.today()
    
    # Buscamos las columnas correctas basándonos en tu archivo
    col_nombre = next((c for c in df.columns if 'APELLIDOS Y NOMBRES' in c), df.columns[2])
    col_cedula = next((c for c in df.columns if 'IDENTIFICACIÓN' in c), df.columns[3])
    col_comunicado = next((c for c in df.columns if 'COMUNICADO' in c), None)
    
    soat_v, tecno_v, lic_v, comunicados = [], [], [], []

    for index, fila in df.iterrows():
        nombre = str(fila[col_nombre])
        if "NAN" in nombre.upper() or "NO." in nombre.upper(): continue
        
        cedula = str(fila[col_cedula]).split('.')[0]
        identidad = f"🎖️ {nombre} (CC. {cedula})"

        # Comunicados
        if col_comunicado:
            com = str(fila[col_comunicado])
            if com != "nan" and com.strip() != "" and "NO APLICA" not in com.upper():
                comunicados.append(f"📢 **{nombre}**: {com}")
        
        # ESCANEO DINÁMICO DE FECHAS
        for col in df.columns:
            valor = fila[col]
            if pd.isna(valor) or str(valor).strip() == "" or "VIGENTE" in str(valor).upper():
                continue
                
            try:
                # Intentamos convertir cualquier formato de fecha
                fecha_v = pd.to_datetime(valor, errors='coerce').date()
                if fecha_v and fecha_v < hoy:
                    if "SOAT" in col:
                        soat_v.append(f"{identidad} - Vence SOAT: {fecha_v}")
                    elif "TECNO" in col:
                        tecno_v.append(f"{identidad} - Vence TECNO: {fecha_v}")
                    elif "LICENCIA DE CONDUCCION" in col:
                        lic_v.append(f"{identidad} - Vence LICENCIA: {fecha_v}")
            except:
                continue

    st.title("🛡️ Control Documentación DEI2 Gudmo 16")
    
    if comunicados:
        with st.expander("🔔 COMUNICADOS OFICIALES", expanded=True):
            for c in set(comunicados): st.markdown(c)
        st.divider()

    st.subheader("🚨 NOVEDADES POR VENCIMIENTO")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.write("🔴 **SOAT**")
        for m in set(soat_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not soat_v: st.success("SOAT al día")

    with c2:
        st.write("🔴 **TECNOMECÁNICA**")
        for m in set(tecno_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not tecno_v: st.success("Tecno al día")

    with c3:
        st.write("🔴 **LICENCIA CONDUCCIÓN**")
        for m in set(lic_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
        if not lic_v: st.success("Licencias al día")

    st.divider()

    # TABLA GENERAL
    st.subheader("📋 MATRIZ INTEGRAL")
    
    def color_rojo(val):
        try:
            f = pd.to_datetime(val, errors='coerce').date()
            if f and f < hoy: return 'background-color: #5c1414; color: white'
        except: pass
        return ''

    # Limpiar nombres de columnas para mostrar
    df_display = df.copy()
    df_display.columns = [c.replace("NAN", "").strip() for c in df_display.columns]
    
    st.dataframe(df_display.style.map(color_rojo), use_container_width=True)

else:
    st.error("Conectando con OneDrive...")
