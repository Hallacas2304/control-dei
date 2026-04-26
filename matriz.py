import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="GUDMO 16 - CONTROL FINAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { 
        background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); 
        padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; 
        margin-bottom: 15px; 
    }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=10)
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    infractores_lista = []

    # --- 2. PROCESAMIENTO SIN ERRORES ---
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        # Filtro: Ignorar si no es un nombre real o es encabezado
        if len(nombre) < 5 or nombre.isdigit() or "NAN" in nombre or "APELLIDOS" in nombre:
            continue

        alertas_txt = []
        
        # Columnas B(1), C(2), D(3) para Licencia, Tecno y SOAT
        for idx in [1, 2, 3]:
            valor = fila[idx]
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # Filtro Año > 2024 para eliminar el error 1970
                    if pd.notna(f) and f.year > 2024:
                        if f <= hoy:
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else "SOAT")
                            alertas_txt.append(f"🚨 {tipo} VENCIDO: {f.date()}")
                except:
                    continue

        if alertas_txt:
            info_final = f"👤 *{nombre}*\n" + "\n".join(alertas_txt)
            infractores_lista.append(info_final)

    # --- 3. INTERFAZ ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    st.write(f"Fecha de verificación: {hoy.date()}")

    if not infractores_lista:
        st.success("✅ No se detectaron documentos vencidos hoy.")
    else:
        for item in infractores_lista:
            # Mostramos en pantalla (limpiando los asteriscos de Markdown)
            st.markdown(f'<div class="card-vencido">{item.replace("*", "").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- 4. TELEGRAM (EL QUE FUNCIONA) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if infractores_lista:
            mensaje = "🚨 *NOTIFICACIÓN GUDMO 16*\n\n" + "\n\n".join(infractores_lista)
            
            try:
                res = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                                    data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
                if res.status_code == 200:
                    st.success("✅ Reporte enviado a Telegram.")
                else:
                    st.error(f"Error Telegram: {res.status_code}")
            except:
                st.error("No hay conexión con Telegram.")
        else:
            st.warning("Nada que reportar.")
else:
    st.error("No se pudo cargar el archivo desde SharePoint.")
    
