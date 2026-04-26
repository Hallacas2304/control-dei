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
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code == 200, r.json().get('description', 'Error')
    except: return False, "Error de red"

@st.cache_data(ttl=10) # Bajamos el tiempo para que refresque rápido
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        # Cargamos el Excel ignorando los encabezados complejos para buscar a mano
        df = pd.read_excel(BytesIO(response.content))
        return df
    except: return None

st.title("🛡️ Control Documentación DEI2 Gudmo 16")

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    alertas_telegram = []
    
    # --- LÓGICA DE DETECCIÓN ULTRA ---
    # Recorremos cada fila del Excel
    for index, fila in df.iterrows():
        # Buscamos el nombre (suele estar en la columna 2 o 3)
        nombre = str(fila.iloc[2]) if len(fila) > 2 else "Sin Nombre"
        if "NAN" in nombre.upper() or "APELLIDOS" in nombre.upper(): continue

        # Revisamos cada celda de esa fila buscando fechas vencidas
        for col_idx, valor in enumerate(fila):
            if pd.isna(valor): continue
            
            # Intentamos convertir lo que sea que haya en la celda a fecha
            try:
                fecha_celda = pd.to_datetime(valor, errors='coerce')
                
                # Si es una fecha válida y es menor a hoy (vencida)
                if pd.notna(fecha_celda) and hasattr(fecha_celda, 'date'):
                    if fecha_celda < hoy:
                        # Obtenemos el nombre de la columna para saber qué venció
                        nombre_columna = str(df.columns[col_idx]).upper()
                        # Solo nos interesan SOAT, TECNO y LICENCIA
                        if any(x in nombre_columna for x in ["SOAT", "TECNO", "LICENCIA", "VENCE"]):
                            alertas_telegram.append(f"• <b>{nombre}</b>: {nombre_columna} ({fecha_celda.date()})")
            except:
                continue

    # --- INTERFAZ ---
    if st.button("📲 ENVIAR ALERTAS A TELEGRAM"):
        if alertas_telegram:
            # Usamos set() para no repetir si hay varias fechas vencidas del mismo tipo
            novedades_limpias = sorted(list(set(alertas_telegram)))
            reporte = f"🚨 <b>NOVEDADES GUDMO 16</b>\n\n" + "\n".join(novedades_limpias[:25])
            
            exito, respuesta = enviar_telegram(reporte)
            if exito: st.success("✅ ¡Reporte enviado! Revisa tu Telegram.")
            else: st.error(f"❌ No se pudo enviar: {respuesta}")
        else:
            st.info("🔎 No se detectaron documentos vencidos en la matriz.")

    st.divider()
    st.subheader("📋 Matriz de Datos")
    st.dataframe(df)

else:
    st.error("No se pudo cargar el archivo desde OneDrive.")
    
