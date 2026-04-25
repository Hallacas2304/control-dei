import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

st.set_page_config(page_title="Control DEI - Oficial", layout="wide")

ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

@st.cache_data(ttl=60) 
def cargar_datos_nube():
    try:
        response = requests.get(ONEDRIVE_LINK)
        df = pd.read_excel(BytesIO(response.content))
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except:
        return None

st.title("🛡️ CONTROL DEI - COMUNICADOS Y ALERTAS")

df = cargar_datos_nube()

if df is not None:
    hoy = date.today()
    
    # Columnas Clave
    col_nombre = next((c for c in df.columns if 'NOMBRE' in c), df.columns[0])
    col_placa = next((c for c in df.columns if 'PLACA' in c), None)
    col_comunicado = next((c for c in df.columns if 'COMUNICADO' in c or 'NOTA' in c), None)
    
    df['FUNCIONARIO FINAL'] = df[col_nombre]

    soat_vencidos, tecno_vencidos, conduc_vencidos = [], [], []
    sin_vehiculo, comunicados_oficiales = [], []

    for _, fila in df.iterrows():
        nombre = fila[col_nombre]
        
        # 1. Buscar Comunicados Oficiales (Si hay algo escrito en esa columna)
        if col_comunicado and pd.notna(fila[col_comunicado]) and str(fila[col_comunicado]).strip() != "":
            comunicados_oficiales.append(f"📢 {nombre}: {fila[col_comunicado]}")

        # 2. Buscar Sin Vehículo
        if col_placa and (pd.isna(fila[col_placa]) or str(fila[col_placa]).strip() == "" or str(fila[col_placa]).upper() == "SIN VEHICULO"):
            sin_vehiculo.append(f"👤 {nombre}")

        # 3. Vencimientos
        for col in df.columns:
            if 'SOAT' in col:
                try:
                    f = pd.to_datetime(fila[col]).date()
                    if f < hoy: soat_vencidos.append(f"👤 {nombre} ({f})")
                except: pass
            elif 'TECNO' in col:
                try:
                    f = pd.to_datetime(fila[col]).date()
                    if f < hoy: tecno_vencidos.append(f"👤 {nombre} ({f})")
                except: pass
            elif 'CONDUC' in col and 'TRANSIT' not in col:
                try:
                    f = pd.to_datetime(fila[col]).date()
                    if f < hoy: conduc_vencidos.append(f"👤 {nombre} ({f})")
                except: pass

    # --- SECCIÓN DE VENTANAS SUPERIORES ---
    
    # Ventana de Comunicados (Sola arriba para que sea lo primero que se lea)
    if comunicados_oficiales:
        st.warning("### 📢 COMUNICADOS OFICIALES")
        for com in comunicados_oficiales:
            st.write(com)
        st.divider()

    st.write("### 🚨 ALERTAS DE DOCUMENTACIÓN")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        if soat_vencidos:
            st.error(f"⚠️ SOAT ({len(soat_vencidos)})")
            for m in soat_vencidos: st.caption(m)
        else: st.success("✅ SOAT al día")

    with c2:
        if tecno_vencidos:
            st.error(f"⚠️ TECNO ({len(tecno_vencidos)})")
            for m in tecno_vencidos: st.caption(m)
        else: st.success("✅ Tecno al día")

    with c3:
        if conduc_vencidos:
            st.error(f"⚠️ CONDUCCIÓN ({len(conduc_vencidos)})")
            for m in conduc_vencidos: st.caption(m)
        else: st.success("✅ Licencias al día")

    with c4:
        st.info(f"🚲 SIN VEHÍC
        
