import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control GUDMO 16", layout="wide")

# ✅ TU NUEVO TOKEN EXTRAÍDO DE LA IMAGEN (9:02 AM)
TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "6198642735"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code == 200:
            return True, "✅ ¡Reporte enviado con éxito!"
        return False, f"Error: {r.json().get('description')}"
    except: return False, "Fallo de conexión"

@st.cache_data(ttl=1)
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
        nombre = str(fila.iloc[2]) if len(fila) > 2 else ""
        if any(x in nombre.upper() for x in ["NONE", "NAN", "APELLIDOS", "CEDULA"]): continue
            
        for col_idx, valor in enumerate(fila):
            nombre_col = str(df.columns[col_idx]).upper()
            
            # Filtro: SOAT, TECNO y CONDUCCIÓN
            if any(p in nombre_col for p in ["SOAT", "TECNO", "CONDUCCION"]):
                try:
                    f_venc = pd.to_datetime(valor, errors='coerce', dayfirst=True)
                    # Solo fechas reales y vencidas
                    if pd.notna(f_venc) and f_venc.year > 2010 and f_venc <= hoy:
                        alertas.append(f"• <b>{nombre}</b>: {nombre_col} ({f_venc.date()})")
                except: continue

    if alertas:
        st.subheader(f"⚠️ Vencimientos Detectados ({len(alertas)}):")
        for a in alertas[:20]: st.write(a, unsafe_allow_html=True)
            
        if st.button("📲 ENVIAR REPORTE AL TELEGRAM"):
            reporte = "🚨 <b>NOVEDADES GUDMO 16</b>\n\n" + "\n".join(list(set(alertas)))
            exito, msj = enviar_telegram(reporte)
            if exito: st.success(msj)
            else: st.error(f"❌ {msj}")
    else:
        st.info("🔎 Todo al día en SOAT, Tecno y Licencias.")

    if st.button("♻️ RECARGAR DATOS"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.dataframe(df)
else:
    st.error("No se pudo conectar con el Excel.")
    
