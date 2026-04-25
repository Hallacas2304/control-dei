import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

st.set_page_config(page_title="Control DEI - Final", layout="wide")

# ENLACE DE ONEDRIVE
ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=60) 
def cargar_datos_nube():
    try:
        response = requests.get(ONEDRIVE_LINK)
        df = pd.read_excel(BytesIO(response.content))
        # Limpiar nombres de columnas (quitar espacios y poner en mayúsculas)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except:
        return None

st.title("🛡️ CONTROL DEI - SISTEMA DE ALERTAS")

df = cargar_datos_nube()

if df is not None:
    hoy = date.today()
    
    # Identificar columna de NOMBRE
    col_nombre = next((c for c in df.columns if 'NOMBRE' in c), df.columns[0])
    
    # Repetir el nombre al final para facilitar la lectura
    if 'FUNCIONARIO ' not in df.columns:
        df['FUNCIONARIO '] = df[col_nombre]

    soat_vencidos = []
    tecno_vencidos = []
    conduc_vencidos = []

    # Escaneo para las alertas superiores
    for _, fila in df.iterrows():
        nombre = fila[col_nombre]
        for col in df.columns:
            # Lógica para SOAT
            if 'SOAT' in col:
                try:
                    f = pd.to_datetime(fila[col]).date()
                    if f < hoy: soat_vencidos.append(f"👤 {nombre} (Vence: {f})")
                except: pass
            # Lógica para TECNO
            elif 'TECNO' in col:
                try:
                    f = pd.to_datetime(fila[col]).date()
                    if f < hoy: tecno_vencidos.append(f"👤 {nombre} (Vence: {f})")
                except: pass
            # Lógica para LIC. CONDUCCIÓN (Ignora Tránsito)
            elif 'CONDUC' in col and 'TRANSIT' not in col:
                try:
                    f = pd.to_datetime(fila[col]).date()
                    if f < hoy: conduc_vencidos.append(f"👤 {nombre} (Vence: {f})")
                except: pass

    # MOSTRAR LAS 3 VENTANAS DE ALERTAS
    st.write("### 🚨 DOCUMENTOS VENCIDOS")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if soat_vencidos:
            st.error(f"⚠️ SOAT ({len(soat_vencidos)})")
            for m in soat_vencidos: st.caption(m)
        else: st.success("✅ SOAT al día")

    with c2:
        if tecno_vencidos:
            st.error(f"⚠️ TECNOMECÁNICA ({len(tecno_vencidos)})")
            for m in tecno_vencidos: st.caption(m)
        else: st.success("✅ Tecno al día")

    with c3:
        if conduc_vencidos:
            st.error(f"⚠️ LIC. CONDUCCIÓN ({len(conduc_vencidos)})")
            for m in conduc_vencidos: st.caption(m)
        else: st.success("✅ Licencias al día")

    st.divider()

    # TABLA GENERAL CON COLORES
    st.write("### 📋 VISTA GENERAL (Nombre al inicio y al final)")
    
    def aplicar_colores(datatable):
        estilos = pd.DataFrame('', index=datatable.index, columns=datatable.columns)
        for col in datatable.columns:
            # Solo pintar si es SOAT, TECNO o CONDUCCIÓN
            if any(p in col for p in ['SOAT', 'TECNO', 'CONDUC']) and 'TRANSIT' not in col:
                for idx in datatable.index:
                    try:
                        if pd.to_datetime(datatable.loc[idx, col]).date() < hoy:
                            estilos.loc[idx, col] = 'background-color: #ffcccc; color: black'
                    except: pass
        return estilos

    # Reordenar para que el nombre esté primero y último
    columnas = list(df.columns)
    # Movemos el nombre al principio si no está
    columnas.insert(0, columnas.pop(columnas.index(col_nombre)))
    
    st.dataframe(df[columnas].style.apply(aplicar_colores, axis=None), use_container_width=True)

    if st.button("🔄 ACTUALIZAR DESDE ONEDRIVE"):
        st.cache_data.clear()
        st.rerun()
else:
    st.error("No se pudo leer el archivo. Verifica el enlace de OneDrive.")
    
