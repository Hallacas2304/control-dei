import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

st.set_page_config(page_title="Sistema DEI Realtime", layout="wide")

# ENLACE DIRECTO A TU ONEDRIVE
ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=300) 
def cargar_datos_nube():
    try:
        response = requests.get(ONEDRIVE_LINK)
        return pd.read_excel(BytesIO(response.content))
    except Exception as e:
        st.error(f"Error al conectar con OneDrive: {e}")
        return None

st.title("🛡️ CONTROL DEI - BASE DE DATOS EN VIVO")

df = cargar_datos_nube()

if df is not None:
    hoy = date.today()

    # Función para detectar vencimientos (SOAT, TECNO y LIC. CONDUCCIÓN)
    def analizar_fila(fila):
        vencido = False
        for col, valor in fila.items():
            nombre = str(col).upper()
            # Filtramos: Buscamos SOAT, TECNO o CONDUCCION (Ignoramos Lic. Tránsito)
            if any(palabra in nombre for palabra in ['SOAT', 'TECNO', 'CONDUCCION', 'CONDUCCIÓN']):
                try:
                    fecha = pd.to_datetime(valor).date()
                    if fecha < hoy:
                        vencido = True
                except: continue
        return "🔴 VENCIDO" if vencido else "🟢 VIGENTE"

    df['ESTADO GENERAL'] = df.apply(analizar_fila, axis=1)
    
    # Botón de actualización
    if st.button("🔄 ACTUALIZAR DATOS DE ONEDRIVE"):
        st.cache_data.clear()
        st.rerun()

    # Mostrar alertas de vencidos
    vencidos = df[df['ESTADO GENERAL'] == "🔴 VENCIDO"]
    if not vencidos.empty:
        st.error(f"🚨 ATENCIÓN: Hay {len(vencidos)} registros con documentos vencidos (SOAT, Tecno o Lic. Conducción).")
    else:
        st.success("✅ Todos los documentos (SOAT, Tecno y Lic. Conducción) están al día.")

    # Función para pintar las celdas vencidas
    def pintar_celdas(datatable):
        estilos = pd.DataFrame('', index=datatable.index, columns=datatable.columns)
        for col in datatable.columns:
            nombre_col = str(col).upper()
            # Solo evaluamos fechas de SOAT, TECNO y LIC. CONDUCCIÓN
            if any(p in nombre_col for p in ['SOAT', 'TECNO', 'CONDUCCION', 'CONDUCCIÓN']):
                for idx in datatable.index:
                    try:
                        f = pd.to_datetime(datatable.loc[idx, col]).date()
                        if f < hoy: 
                            estilos.loc[idx, col] = 'background-color: #ffcccc; color: black'
                    except: continue
        return estilos

    # Mostrar la tabla principal
    st.write("### 📋 Listado de Control")
    st.dataframe(df.style.apply(pintar_celdas, axis=None), use_container_width=True)

    # Opción para ver solo los problemas
    if not vencidos.empty:
        with st.expander("🔍 Ver solo los que están VENCIDOS"):
            st.dataframe(vencidos.style.apply(pintar_celdas, axis=None), use_container_width=True)
            
