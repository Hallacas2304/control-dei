import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# DATOS DE CONEXIÓN (Verificados)
TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E"
CHAT_ID = "6198642735"

def enviar_telegram(mensaje):
    # Usamos una URL limpia sin caracteres raros
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    datos = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }
    try:
        # Forzamos el envío limpio
        r = requests.post(url, data=datos, timeout=15)
        res_json = r.json()
        if r.status_code == 200:
            return True, "✅ ¡LOGRADO! Revisa tu Telegram."
        else:
            return False, f"❌ Telegram dice: {res_json.get('description')}"
    except Exception as e:
        return False, f"❌ Error de conexión: {str(e)}"

# --- CARGA DE DATOS ---
@st.cache_data(ttl=30)
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        df = pd.read_excel(BytesIO(response.content), header=[0, 1])
        df.columns = [f"{str(a).strip()} {str(b).strip()}".upper().replace("NAN", "").strip() for a, b in df.columns]
        return df
    except: return None

df = cargar_datos()

# --- DISEÑO DE LA APP ---
st.title("🛡️ Control Documentación DEI2 Gudmo 16")

if df is not None:
    hoy = date.today()
    alertas = []
    
    # Buscamos vencidos (Simplificado para evitar errores)
    for _, fila in df.iterrows():
        nombre = str(fila.get('APELLIDOS Y NOMBRES', ''))
        if "NAN" in nombre.upper() or not nombre.strip(): continue
        
        for col in df.columns:
            if any(palabra in col for palabra in ["SOAT", "TECNO", "LICENCIA"]):
                try:
                    fecha = pd.to_datetime(fila[col], errors='coerce').date()
                    if fecha and fecha < hoy:
                        alertas.append(f"⚠️ {nombre}: Venció {col} el {fecha}")
                except: pass

    if st.button("📲 ENVIAR REPORTE A TELEGRAM"):
        if alertas:
            # Enviamos solo los primeros 10 para no saturar
            texto_reporte = "🚨 REPORTE GUDMO 16\n\n" + "\n".join(list(set(alertas))[:15])
            exito, msj = enviar_telegram(texto_reporte)
            if exito: st.success(msj)
            else: st.error(msj)
        else:
            st.info("No hay documentos vencidos hoy.")

    st.divider()
    st.dataframe(df)
else:
    st.error("Error al conectar con el Excel.")
    
