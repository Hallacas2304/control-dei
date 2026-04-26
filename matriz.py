import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# DATOS DE CONEXIÓN ÚNICOS (Usa solo @Gudmo16_bot)
TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E"
CHAT_ID = "6198642735"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code == 200, r.json().get('description', 'Error desconocido')
    except Exception as e:
        return False, str(e)

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        # Cargamos el Excel con los dos niveles de encabezado
        df = pd.read_excel(BytesIO(response.content), header=[0, 1])
        # Limpiamos los nombres de las columnas para que Python las entienda
        df.columns = [f"{str(a).strip()} {str(b).strip()}".upper().replace("NAN", "").strip() for a, b in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return None

# --- CUERPO DE LA APP ---
st.title("🛡️ Control Documentación DEI2 Gudmo 16")

df = cargar_datos()

if df is not None:
    hoy = date.today()
    alertas_telegram = [] # AQUÍ SE CORRIGE EL NAMEERROR
    
    # Identificar columnas clave
    col_nombre = next((c for c in df.columns if 'APELLIDOS Y NOMBRES' in c), None)

    if col_nombre:
        for _, fila in df.iterrows():
            nombre_militar = str(fila[col_nombre])
            if "NAN" in nombre_militar.upper() or not nombre_militar.strip(): continue
            
            # Revisar SOAT, TECNO y LICENCIA
            for col in df.columns:
                if any(x in col for x in ["SOAT", "TECNO", "LICENCIA"]):
                    valor = fila[col]
                    if pd.isna(valor) or "VIGENTE" in str(valor).upper(): continue
                    try:
                        fecha_vencida = pd.to_datetime(valor, errors='coerce').date()
                        if fecha_vencida and fecha_vencida < hoy:
                            alertas_telegram.append(f"• <b>{nombre_militar}</b>: {col} ({fecha_vencida})")
                    except: continue

    # BOTÓN DE ACCIÓN
    if st.button("📲 ENVIAR ALERTAS AL TELEGRAM"):
        if alertas_telegram:
            reporte = f"🚨 <b>NOVEDADES GUDMO 16</b>\n\n" + "\n".join(list(set(alertas_telegram))[:20])
            exito, respuesta = enviar_telegram(reporte)
            if exito:
                st.success("✅ ¡Reporte enviado con éxito al celular!")
            else:
                st.error(f"❌ Falló el envío: {respuesta}")
        else:
            st.info("✅ No hay documentos vencidos hoy.")

    st.divider()
    st.subheader("📋 Vista General de la Matriz")
    st.dataframe(df, use_container_width=True)

else:
    st.warning("Esperando conexión con el archivo de OneDrive...")
    
