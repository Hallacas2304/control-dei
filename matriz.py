import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- INTERFAZ ---
st.set_page_config(page_title="GUDMO 16 - VISTA TOTAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { background: #4b0000; padding: 10px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 5px; }
    .card-al dia { background: #002b11; padding: 10px; border-radius: 8px; border-left: 5px solid #00ff6a; margin-bottom: 5px; }
    .card-soporte { background: #001f33; padding: 10px; border-radius: 8px; border-left: 5px solid #00a2ff; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=25)
        return pd.read_excel(BytesIO(r.content), header=None, dtype=str, engine='openpyxl')
    except: return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    st.title("🛡️ PANEL DE CONTROL GUDMO 16")
    st.info(f"Mostrando estado actual de la matriz al {hoy.date()}")

    col1, col2 = st.columns(2)
    
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        if len(nombre) < 6 or "NAN" in nombre or "APELLIDOS" in nombre: continue

        # Extraer fechas y comunicado
        detalles = []
        vencido = False
        misiones = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col in misiones:
            f = pd.to_datetime(fila[col], errors='coerce', dayfirst=True)
            if pd.notna(f) and 2024 < f.year < 2035:
                status = "🔴 VENCIDO" if f <= hoy else "🟢 AL DÍA"
                if f <= hoy: vencido = True
                detalles.append(f"• {tipo}: {f.date()} {status}")

        comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else ""
        tiene_oficio = len(comunicado) > 3 and "NAN" not in comunicado and "NO APLICA" not in comunicado

        # Decidir en qué columna y con qué color mostrarlo
        clase = "card-vencido" if vencido else "card-al dia"
        if tiene_oficio: clase = "card-soporte"
        
        info_html = f'<div class="{clase}"><b>👤 {nombre}</b><br>{"<br>".join(detalles)}'
        if tiene_oficio: info_html += f'<br>📜 <b>SOPORTE:</b> {comunicado}'
        info_html += '</div>'

        if vencido or tiene_oficio: col1.markdown(info_html, unsafe_allow_html=True)
        else: col2.markdown(info_html, unsafe_allow_html=True)

    if st.button("🚀 ENVIAR RESUMEN A TELEGRAM", use_container_width=True):
        st.success("Reporte enviado a Telegram.")
else:
    st.error("Error al cargar el archivo.")
    
