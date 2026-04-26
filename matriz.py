import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# ✅ TOKEN ACTUALIZADO (Verifícalo una última vez en BotFather)
TOKEN_TELEGRAM = "8243677891:AAHdEtdsBTI2ALOrAc_uAPNwWxB5KUzWYHE"
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

@st.cache_data(ttl=2) # Casi sin caché para que veas cambios al instante
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        return pd.read_excel(BytesIO(response.content))
    except: return None

st.title("🛡️ Control Documentación DEI2 Gudmo 16")

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    alertas = []
    
    for i, fila in df.iterrows():
        # Buscamos el nombre (Columna 3)
        nombre = str(fila.iloc[2]) if len(fila) > 2 else ""
        if any(x in nombre.upper() for x in ["NONE", "NAN", "APELLIDOS"]): continue
            
        for col_idx, valor in enumerate(fila):
            nombre_col = str(df.columns[col_idx]).upper()
            
            # FILTRO DE BÚSQUEDA: Buscamos palabras clave en las columnas
            if any(p in nombre_col for p in ["SOAT", "TECNO", "CONDUCCION", "VENCE"]):
                try:
                    f_venc = pd.to_datetime(valor, errors='coerce', dayfirst=True)
                    # Solo fechas reales vencidas (evitamos el 1970)
                    if pd.notna(f_venc) and f_venc.year > 2010 and f_venc <= hoy:
                        alertas.append(f"• <b>{nombre}</b>: {nombre_col} ({f_venc.date()})")
                except: continue

    if alertas:
        st.subheader(f"⚠️ Documentos Vencidos Detectados ({len(alertas)}):")
        # Aquí verás el listado en la pantalla de la App
        for a in alertas[:20]:
            st.write(a, unsafe_allow_html=True)
            
        if st.button("📲 ENVIAR REPORTE AL TELEGRAM"):
            reporte = "🚨 <b>NOVEDADES GUDMO 16</b>\n\n" + "\n".join(list(set(alertas))[:30])
            exito, mensaje = enviar_telegram(reporte)
            if exito: st.success(mensaje)
            else: st.error(f"❌ Error: {mensaje}")
    else:
        st.info("🔎 No se encontraron SOAT, Tecno o Licencias vencidas.")
        # BOTÓN DE PRUEBA RÁPIDA
        if st.button("📡 PROBAR CONEXIÓN"):
            exito, mensaje = enviar_telegram("✅ El Bot Gudmo16 está en línea.")
            if exito: st.success("¡Te debió llegar un mensaje al Telegram!")
            else: st.error(f"Sigue fallando: {mensaje}")

    st.divider()
    st.dataframe(df)
else:
    st.error("Error al conectar con OneDrive.")
    
