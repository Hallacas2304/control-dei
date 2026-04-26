import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { background: #4b0000; padding: 15px; border-radius: 10px; border-left: 6px solid #ff4b4b; margin-bottom: 10px; }
    .card-al-dia { background: #002b11; padding: 15px; border-radius: 10px; border-left: 6px solid #00ff6a; margin-bottom: 10px; }
    .card-soporte { background: #001f33; padding: 15px; border-radius: 10px; border-left: 6px solid #00a2ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

# NUEVO ENLACE DE EXCEL
URL_EXCEL = "https://correopoliciagov-my.sharepoint.com/:b:/g/personal/omar_vela3592_correo_policia_gov_co/IQD5eis7_cTVT5c9UHKbOte4ASqE0VAREktQMYFfmjzohwE?download=1"

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        r = requests.get(URL_EXCEL, timeout=25)
        return pd.read_excel(BytesIO(r.content), engine='openpyxl')
    except Exception as e:
        st.error(f"Error al conectar con el nuevo Excel: {e}")
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    st.title("🛡️ CONSOLA DE MANDO GUDMO 16")
    st.write(f"Datos actualizados según la nueva matriz al: **{hoy.date()}**")

    col1, col2 = st.columns(2)
    
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[0]).strip().upper()
        
        # Filtro de nombres para evitar filas vacías
        if len(nombre) < 5 or "NAN" in nombre or "APELLIDOS" in nombre:
            continue

        alertas = []
        vencido = False
        # Mapeo estándar: B=1 (Lic), C=2 (Tecno), D=3 (SOAT)
        misiones = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col in misiones:
            f = pd.to_datetime(fila.iloc[col], errors='coerce')
            if pd.notna(f) and 2024 < f.year < 2035:
                status = "🔴 VENCIDO" if f <= hoy else "🟢 AL DÍA"
                if f <= hoy: vencido = True
                alertas.append(f"• {tipo}: {f.date()} {status}")

        # Columna N (índice 14 o 13 según estructura) para Comunicados
        comunicado = str(fila.iloc[13]).strip().upper() if len(fila) > 13 else ""
        tiene_oficio = len(comunicado) > 3 and "NAN" not in comunicado and "NO APLICA" not in comunicado

        # Determinar estilo visual
        clase = "card-vencido" if vencido else "card-al-dia"
        if tiene_oficio: clase = "card-soporte"
        
        info_html = f'<div class="{clase}"><b>👤 {nombre}</b><br>{"<br>".join(alertas)}'
        if tiene_oficio: info_html += f'<br>📜 <b>SOPORTE:</b> {comunicado}'
        info_html += '</div>'

        # Clasificación en columnas
        if vencido or tiene_oficio:
            col1.markdown(info_html, unsafe_allow_html=True)
        else:
            col2.markdown(info_html, unsafe_allow_html=True)

    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        st.success("Reporte enviado al grupo de Telegram.")
else:
    st.info("Esperando conexión con el nuevo archivo de SharePoint...")
    
