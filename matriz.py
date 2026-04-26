import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# Credenciales (Asegúrate de que el Token sea el de @Gudmo16_bot)
TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E"
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
        return False, "Error de conexión con Telegram"

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        # Cargamos sin encabezados fijos para mapear manualmente
        df = pd.read_excel(BytesIO(response.content))
        return df
    except:
        return None

# --- INICIO DE LA APP ---
st.title("🛡️ Control Documentación DEI2 Gudmo 16")

df = cargar_datos()

if df is not None:
    hoy = pd.to_datetime(date.today())
    alertas_encontradas = []
    
    # 1. Limpiamos nombres de columnas para que sean fáciles de buscar
    columnas_limpias = [str(c).upper() for c in df.columns]

    # 2. Recorremos cada fila
    for i, fila in df.iterrows():
        # Intentamos obtener el nombre (columna 2 o 3 según la estructura)
        nombre_raw = str(fila.iloc[2]) if len(fila) > 2 else ""
        if any(x in nombre_raw.upper() for x in ["NONE", "NAN", "APELLIDOS", "UNIFORMADO", "CEDULA"]):
            continue
        
        # 3. Revisamos cada celda de la fila
        for col_idx, valor in enumerate(fila):
            if pd.isna(valor) or str(valor).strip() == "":
                continue
            
            nombre_col = columnas_limpias[col_idx]
            
            # Solo analizamos columnas que tengan que ver con vencimientos
            if any(palabra in nombre_col for palabra in ["SOAT", "TECNO", "LICENCIA", "VENCE", "VENCIMIENTO"]):
                try:
                    # Intento de conversión robusto (soporta día/mes/año y año/mes/día)
                    fecha_vencimiento = pd.to_datetime(valor, errors='coerce
                                                       
