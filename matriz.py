import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

st.set_page_config(page_title="Sistema DEI Realtime", layout="wide")

# ENLACE DIRECTO A TU ONEDRIVE
ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=300) # Se actualiza cada 5 minutos
def cargar_datos_nube():
    response = requests.get(ONEDRIVE_LINK)
    return pd.read_excel(BytesIO(response.content))

st.title("🛡️ CONTROL DEI - BASE DE DATOS EN VIVO")

try:
    df = cargar_datos_nube()
    hoy = date.today()

    # Filtro para saber quién está vencido
    def chequear_vencimiento(fila):
        vencido = False
        for col, valor in fila.items():
            nombre = str(col).upper()
            if ('TECNO' in nombre or 'SOAT' in nombre or 'UNNAMED' in nombre) and 'LICENCIA' not in nombre:
                try:
                    fecha = pd.to_datetime(valor).date()
                    if fecha < hoy: vencido = True
                except: continue
        return "🔴 VENCIDO" if vencido else "🟢 VIGENTE"

    df['ESTADO'] = df.apply(chequear_vencimiento, axis=1)
    
    # Botón de Sincronización
    if st.button("🔄 ACTUALIZAR DATOS DE ONEDRIVE"):
        st.cache_data.clear()
        st.rerun()

    # Tablas
    vencidos = df[df['ESTADO'] == "🔴 VENCIDO"]
    st.error(f"🚨 VEHÍCULOS CON DOCUMENTOS VENCIDOS: {len(vencidos)}")
    st.dataframe(vencidos, use_container_width=True)
    
    with st.expander("Ver flota completa"):
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error de conexión: {e}")
