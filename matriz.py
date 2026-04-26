import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# 🚨 USA ESTE TOKEN (Actualizado de @Gudmo16_bot)
TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E"
CHAT_ID = "6198642735"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        res = r.json()
        if r.status_code == 200:
            return True, "✅ ¡Reporte enviado!"
        else:
            return False, f"Telegram dice: {res.get('description')}"
    except: return False, "Error de red"

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        df = pd.read_excel(BytesIO(response.content))
        return df
    except: return None

# --- INICIO APP ---
st.title("🛡️ Control Documentación DEI2 Gudmo 16")

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    alertas_encontradas = []
    
    # 1. Buscamos las columnas de interés
    columnas = [str(c).upper() for c in df.columns]
    
    # 2. Procesamos fila por fila
    for i, fila in df.iterrows():
        # Buscamos el nombre (Columna 'APELLIDOS Y NOMBRES')
        nombre = str(fila.iloc[2]) if len(fila) > 2 else ""
        
        # Ignoramos filas vacías o con títulos
        if any(x in nombre.upper() for x in ["NONE", "NAN", "APELLIDOS", "GR", "CEDULA"]):
            continue
            
        for col_idx, valor in enumerate(fila):
            nombre_col = columnas[col_idx]
            # Solo si la columna es de las que queremos vigilar
            if any(palabra in nombre_col for palabra in ["SOAT", "TECNO", "LICENCIA", "VENCE"]):
                try:
                    fecha_v = pd.to_datetime(valor, errors='coerce', dayfirst=True)
                    if pd.notna(fecha_v) and fecha_v <= hoy:
                        alertas_encontradas.append(f"• <b>{nombre}</b>: {nombre_col} ({fecha_v.date()})")
                except: continue

    # --- MOSTRAR RESULTADOS ANTES DE ENVIAR ---
    if alertas_encontradas:
        st.subheader(f"⚠️ Se detectaron {len(alertas_encontradas)} documentos vencidos:")
        for a in alertas_encontradas[:10]: # Muestra los primeros 10 en la web
            st.write(a, unsafe_allow_html=True)
            
        if st.button("📲 ENVIAR ESTE LISTADO AL TELEGRAM"):
            reporte = "🚨 <b>NOVEDADES GUDMO 16</b>\n\n" + "\n".join(list(set(alertas_encontradas))[:25])
            exito, mensaje = enviar_telegram(reporte)
            if exito: st.success(mensaje)
            else: st.error(f"❌ {mensaje}")
    else:
        st.info("🔎 El sistema no ve documentos vencidos. Si hay alguno, verifica la fecha en el Excel.")
        st.button("📲 PROBAR CONEXIÓN (Enviar Hola)")

    st.divider()
    st.dataframe(df)
else:
    st.error("No hay conexión con OneDrive.")
    
