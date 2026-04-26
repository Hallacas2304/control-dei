import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# 🚨 PEGA AQUÍ EL TOKEN QUE COPIASTE DE BOTFATHER
TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E"
CHAT_ID = "6198642735"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        res = r.json()
        if r.status_code == 200:
            return True, "✅ ¡LOGRADO! Revisa tu Telegram."
        else:
            return False, f"Error: {res.get('description')}"
    except:
        return False, "Error de conexión"

@st.cache_data(ttl=15)
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        # Cargamos el Excel de forma plana para encontrar los datos más fácil
        df = pd.read_excel(BytesIO(response.content))
        return df
    except: return None

# --- INTERFAZ ---
st.title("🛡️ Control Documentación DEI2 Gudmo 16")

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    alertas_finales = []
    
    # Recorremos el Excel buscando fechas vencidas
    for i, fila in df.iterrows():
        # Buscamos el nombre (columna 2 o 3)
        nombre = str(fila.iloc[2]) if len(fila) > 2 else ""
        if "NAN" in nombre.upper() or not nombre.strip() or "APELLIDOS" in nombre.upper():
            continue

        # Revisamos cada celda de la fila
        for col_idx, valor in enumerate(fila):
            try:
                # Si la celda tiene una fecha
                if isinstance(valor, (date, pd.Timestamp)):
                    fecha_v = pd.to_datetime(valor)
                    if fecha_v < hoy:
                        # Buscamos el nombre de la columna para saber qué venció
                        nombre_col = str(df.columns[col_idx]).upper()
                        if any(x in nombre_col for x in ["SOAT", "TECNO", "LICENCIA", "VENCE"]):
                            alertas_finales.append(f"• <b>{nombre}</b>: {nombre_col} ({fecha_v.date()})")
            except: continue

    # BOTÓN DE ENVÍO
    if st.button("📲 ENVIAR ALERTAS AL TELEGRAM"):
        if alertas_finales:
            # Quitamos repetidos y armamos el reporte
            novedades = "\n".join(list(set(alertas_finales))[:25])
            reporte = f"🚨 <b>NOVEDADES GUDMO 16</b>\n\n{novedades}"
            
            exito, mensaje = enviar_telegram(reporte)
            if exito: st.success(mensaje)
            else: st.error(f"❌ {mensaje}")
        else:
            st.info("🔎 No se encontraron documentos vencidos hoy.")

    st.divider()
    st.subheader("📋 Vista Previa del Excel")
    st.dataframe(df)
else:
    st.error("No se pudo conectar con el Excel en OneDrive.")
    
