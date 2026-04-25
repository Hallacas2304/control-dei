import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

st.set_page_config(page_title="Sistema DEI Realtime", layout="wide")

# ENLACE DIRECTO A TU ONEDRIVE
ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=60) 
def cargar_datos_nube():
    try:
        response = requests.get(ONEDRIVE_LINK)
        return pd.read_excel(BytesIO(response.content))
    except:
        return None

st.title("🛡️ CONTROL DEI - ALERTAS DE VENCIMIENTO")

df = cargar_datos_nube()

if df is not None:
    hoy = date.today()
    
    # 1. IDENTIFICAR COLUMNAS (Limpieza de nombres)
    col_nombre = next((c for c in df.columns if 'NOMBRE' in str(c).upper()), df.columns[0])
    
    soat_vencidos = []
    tecno_vencidos = []
    conduc_vencidos = []

    # 2. ESCANEO DE DATOS
    for index, fila in df.iterrows():
        nombre_persona = fila[col_nombre]
        
        for col in df.columns:
            nombre_col = str(col).upper()
            valor = fila[col]
            
            try:
                fecha_venc = pd.to_datetime(valor).date()
                if fecha_venc < hoy:
                    info = f"👤 {nombre_persona} (Venció: {fecha_venc})"
                    
                    if 'SOAT' in nombre_col:
                        soat_vencidos.append(info)
                    elif 'TECNO' in nombre_col:
                        tecno_vencidos.append(info)
                    elif 'CONDUC' in nombre_col:
                        conduc_vencidos.append(info)
            except:
                continue

    # 3. VENTANAS EMERGENTES (Alertas)
    st.write("### 🚨 ESTADO DE DOCUMENTACIÓN")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if soat_vencidos:
            st.error("⚠️ SOAT VENCIDOS")
            for item in soat_vencidos:
                st.write(item)
        else:
            st.success("✅ SOAT al día")

    with col2:
        if tecno_vencidos:
            st.error("⚠️ TECNOMECÁNICA VENCIDA")
            for item in tecno_vencidos:
                st.write(item)
        else:
            st.success("✅ Tecno al día")

    with col3:
        if conduc_vencidos:
            st.error("⚠️ LIC. CONDUCCIÓN VENCIDA")
            for item in conduc_vencidos:
                st.write(item)
        else:
            st.success("✅ Licencias al día")

    # 4. BOTONES Y TABLA GENERAL
    st.divider()
    if st.button("🔄 SINCRONIZAR CON ONEDRIVE"):
        st.cache_data.clear()
        st.rerun()

    st.write("### 📋 VISTA GENERAL DE LA MATRIZ")
    
    def pintar_rojo(val):
        try:
            if pd.to_datetime(val).date() < hoy:
                return 'background-color: #ffcccc'
        except: pass
        return ''

    st.dataframe(df.style.applymap(pintar_rojo), use_container_width=True)

else:
    st.warning("Conectando con la base de datos de OneDrive... Pulsa actualizar si tarda mucho.")
    
