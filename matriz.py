import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    .card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 6px solid; background: #1c2128; }
    .vencido { border-left-color: #ff4b4b; background: #3d0a0a; }
    .al-dia { border-left-color: #00ff6a; background: #0a2d1a; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

# ENLACE ACTUALIZADO (EL QUE SÍ FUNCIONA)
URL_FINAL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def obtener_datos():
    try:
        r = requests.get(URL_FINAL, timeout=25)
        # Cargamos el Excel y eliminamos filas completamente vacías al inicio
        data = pd.read_excel(BytesIO(r.content), engine='openpyxl')
        return data.dropna(how='all').reset_index(drop=True)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

st.title("🛡️ PANEL DE CONTROL GUDMO 16")
df = obtener_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    st.success(f"✅ Matriz vinculada con éxito. Revisión: {hoy.date()}")
    
    # Lista para construir el mensaje de Telegram
    mensaje_telegram = f"🚨 *REPORTE GUDMO 16 - {hoy.date()}*\n\n"
    hay_vencidos = False

    col1, col2 = st.columns(2)
    count = 0

    # Empezamos a leer desde donde encuentre el primer nombre
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[0]).strip().upper()
        
        # Filtro flexible para detectar nombres reales
        if len(nombre) < 4 or "NAN" in nombre or "APELLIDOS" in nombre or "ORD" in nombre:
            continue
        
        count += 1
        estado_vencido = False
        docs_texto = []
        
        # Revisión de fechas (B=1, C=2, D=3)
        for tipo, idx in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            f = pd.to_datetime(fila.iloc[idx], errors='coerce')
            if pd.notna(f) and 2024 < f.year < 2035:
                if f.date() <= hoy.date():
                    status = "🔴 VENCIDO"
                    estado_vencido = True
                    hay_vencidos = True
                else:
                    status = "🟢 AL DÍA"
                docs_texto.append(f"• {tipo}: {f.date()} {status}")

        # Diseño de la tarjeta en pantalla
        clase = "vencido" if estado_vencido else "al-dia"
        card_html = f'<div class="card {clase}"><b>👤 {nombre}</b><br>{"<br>".join(docs_texto)}</div>'
        
        if count % 2 != 0: col1.markdown(card_html, unsafe_allow_html=True)
        else: col2.markdown(card_html, unsafe_allow_html=True)
        
        # Agregar al mensaje de Telegram solo si tiene algo vencido
        if estado_vencido:
            mensaje_telegram += f"👤 *{nombre}*\n" + "\n".join(docs_texto) + "\n\n"

    st.divider()
    
    # --- BOTÓN DE TELEGRAM SIEMPRE VISIBLE ---
    if st.button("🚀 ENVIAR ALERTA A TELEGRAM", use_container_width=True):
        if hay_vencidos:
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": mensaje_telegram, "parse_mode": "Markdown"})
            st.success("✅ ¡Reporte de vencimientos enviado con éxito!")
        else:
            msg_paz = "✅ *GUDMO 16:* Todo el personal se encuentra al día con su documentación."
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg_paz, "parse_mode": "Markdown"})
            st.info("No hay vencidos, se envió un reporte de tranquilidad.")

    if count == 0:
        st.warning("⚠️ El Excel parece estar vacío o los nombres no están en la primera columna.")
        
