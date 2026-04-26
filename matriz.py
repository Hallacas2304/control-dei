import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E"
CHAT_ID = "6198642735" 

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload)
        return r.status_code == 200, r.text
    except:
        return False, "Error de conexión"

# ... (El resto del código de carga de datos se mantiene igual) ...

# --- EN EL BOTÓN DE ENVÍO ---
if st.button("📲 ENVIAR ALERTAS AL TELEGRAM"):
    if alertas_telegram:
        # Filtramos para no repetir nombres y que el mensaje no sea gigante
        novedades = list(set(alertas_telegram))
        reporte = f"🚨 *NOVEDADES GUDMO 16* ({date.today()})\n\n" + "\n".join(novedades)
        
        exito, respuesta = enviar_telegram(reporte)
        if exito:
            st.success("✅ ¡Enviado! Revisa tu Telegram ahora.")
        else:
            st.error(f"❌ No llegó. Telegram dice: {respuesta}")
    else:
        st.info("No hay novedades para enviar hoy.")
        
