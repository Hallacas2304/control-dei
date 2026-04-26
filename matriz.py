import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- 1. ESTILOS ORIGINALES (RESTAURADOS) ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")

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

@st.cache_data(ttl=2)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=10)
        # Cargamos el Excel respetando la estructura de filas
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos = []

    # --- 2. LÓGICA DE DETECCIÓN CORREGIDA ---
    # Empezamos en la fila donde están los nombres reales
    for i in range(1, len(df)):
        fila = df.iloc[i]
        
        # Captura de nombre en la Columna A (Índice 0)
        nombre = str(fila[0]).strip().upper()
        if nombre in ["NAN", "APELLIDOS", "ENDER", ""] or len(nombre) < 5:
            continue

        alertas_txt = []
        
        # Escaneamos columnas B(1), C(2) y D(3) para Licencia, Tecno y SOAT
        for idx in [1, 2, 3]:
            valor = fila[idx]
            
            # Solo procesamos si hay algo en la celda
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # FILTRO ANTI-1970: Solo años coherentes
                    if pd.notna(f) and f.year > 2024:
                        if f <= hoy:
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else "SOAT")
                            alertas_txt.append(f"🚨 {tipo} VENCIDO: {f.date()}")
                except:
                    continue

        if alertas_txt:
            criticos.append({"nombre": nombre, "mensaje": "\n".join(alertas_txt)})

    # --- 3. PANTALLA ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    st.info(f"Reporte generado el: {hoy.date()}")

    if not criticos:
        st.success("No hay documentos vencidos detectados.")
    else:
        for c in criticos:
            st.markdown(f'''<div class="card-vencido">
                <b>👤 {c['nombre']}</b><br>{c['mensaje'].replace("\n", "<br>")}
            </div>''', unsafe_allow_html=True)

    # --- 4. TELEGRAM (RESTAURADO) ---
    if st.button("🚀 ENVIAR ALERTAS A TELEGRAM", use_container_width=True):
        if criticos:
            # Construcción del mensaje para Telegram
            msg = "🚨 *VENCIMIENTOS DETECTADOS GUDMO 16*\n\n"
            for c in criticos:
                msg += f"👤 *{c['nombre']}*\n{c['mensaje']}\n\n"
            
            # Envío directo
            url_tg = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
            try:
                res = requests.post(url_tg, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                if res.status_code == 200:
                    st.success("✅ Notificaciones enviadas correctamente.")
                else:
                    st.error("Error al enviar a Telegram.")
            except:
                st.error("Fallo de conexión con Telegram.")
else:
    st.warning("Cargando base de datos...")
    
