import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# ✅ TOKEN NUEVO DE TU CAPTURA DE PANTALLA
TOKEN_TELEGRAM = "8243677891:AAHdEtdsBTI2ALOrAc_uAPNwWxB5KUzWYHE"
CHAT_ID = "6198642735"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        res = r.json()
        if r.status_code == 200:
            return True, "✅ ¡Reporte enviado con éxito!"
        else:
            return False, f"Error: {res.get('description')}"
    except:
        return False, "Error de conexión"

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        df = pd.read_excel(BytesIO(response.content))
        return df
    except:
        return None

st.title("🛡️ Control Documentación DEI2 Gudmo 16")

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    alertas_encontradas = []
    
    for i, fila in df.iterrows():
        # Extraer nombre del uniformado
        nombre = str(fila.iloc[2]) if len(fila) > 2 else ""
        if any(x in nombre.upper() for x in ["NONE", "NAN", "APELLIDOS", "CEDULA"]):
            continue
            
        for col_idx, valor in enumerate(fila):
            nombre_col = str(df.columns[col_idx]).upper()
            
            # 🎯 BUSQUEDA FILTRADA POR TUS REQUERIMIENTOS
            if any(p in nombre_col for p in ["SOAT", "TECNO", "CONDUCCION", "VENCE"]):
                try:
                    f_venc = pd.to_datetime(valor, errors='coerce', dayfirst=True)
                    # Filtramos fechas reales (posteriores a 1990) y vencidas
                    if pd.notna(f_venc) and f_venc.year > 1990 and f_venc <= hoy:
                        alertas_encontradas.append(f"• <b>{nombre}</b>: {nombre_col} ({f_venc.date()})")
                except:
                    continue

    if alertas_encontradas:
        st.subheader(f"⚠️ Se detectaron {len(alertas_encontradas)} vencimientos (SOAT, Tecno, Conducción):")
        for alerta in alertas_encontradas[:15]:
            st.write(alerta, unsafe_allow_html=True)
            
        if st.button("📲 ENVIAR REPORTE COMPLETO AL TELEGRAM"):
            reporte = "🚨 <b>NOVEDADES GUDMO 16</b>\n\n" + "\n".join(list(set(alertas_encontradas)))
            exito, mensaje = enviar_telegram(reporte)
            if exito: st.success(mensaje)
            else: st.error(f"❌ {mensaje}")
    else:
        st.info("🔎 No hay SOAT, Tecno o Licencias de Conducción vencidas hoy.")

    st.divider()
    st.dataframe(df)
else:
    st.error("No se pudo conectar con el Excel.")
    
