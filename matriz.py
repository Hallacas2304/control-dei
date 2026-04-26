import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# 1. Configuración de Pantalla (Modo Oscuro Policía)
st.set_page_config(page_title="GUDMO 16 - MANDO TOTAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    .card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 6px solid; background: #1c2128; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); }
    .v { border-left-color: #ff4b4b; background: #3d0a0a; }
    .ok { border-left-color: #00ff6a; background: #0a2d1a; }
    </style>
    """, unsafe_allow_html=True)

TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def carga_maestra():
    try:
        r = requests.get(URL, timeout=20)
        # Cargamos el Excel sin basura
        df = pd.read_excel(BytesIO(r.content), engine='openpyxl')
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

st.title("🛡️ CONSOLA DE MANDO GUDMO 16")
df = carga_maestra()

if df is not None:
    hoy = pd.Timestamp(date.today())
    vencidos_total = []
    col1, col2 = st.columns(2)
    
    # Contador para alternar columnas
    items_mostrados = 0

    for i in range(len(df)):
        fila = df.iloc[i]
        # Limpieza absoluta de nombres
        nombre_raw = str(fila.iloc[0]).strip().upper()
        
        # REGLA DE ORO: Si es un número, está vacío o es un encabezado, SE IGNORA
        if nombre_raw in ["NAN", "", "None"] or nombre_raw.replace('.','').isdigit() or "APELLIDOS" in nombre_raw:
            continue

        alertas = []
        es_vencido = False
        # Columnas fijas: 1=Licencia, 2=Tecno, 3=SOAT
        for etiqueta, c_idx in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            try:
                f = pd.to_datetime(fila.iloc[c_idx], errors='coerce')
                if pd.notna(f) and f.year > 2020:
                    vence = f.date()
                    status = "🔴 VENCIDO" if vence <= hoy.date() else "🟢 AL DÍA"
                    if vence <= hoy.date(): es_vencido = True
                    alertas.append(f"• {etiqueta}: {vence} {status}")
            except: continue

        # Solo mostramos si logramos extraer al menos una fecha
        if alertas:
            items_mostrados += 1
            clase = "v" if es_vencido else "ok"
            card_html = f'<div class="card {clase}"><b>👤 {nombre_raw}</b><br>{"<br>".join(alertas)}</div>'
            
            if items_mostrados % 2 != 0: col1.markdown(card_html, unsafe_allow_html=True)
            else: col2.markdown(card_html, unsafe_allow_html=True)
            
            if es_vencido:
                vencidos_total.append(f"👤 {nombre_raw}\n" + "\n".join(alertas))

    # --- BOTÓN DE ACCIÓN ---
    st.divider()
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        mensaje = f"🚨 *NOTIFICACIÓN GUDMO 16 - {hoy.date()}*\n\n"
        mensaje += "\n\n".join(vencidos_total) if vencidos_total else "✅ TODO EL PERSONAL AL DÍA."
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
        st.success("✅ Reporte enviado a Telegram")

    if items_mostrados == 0:
        st.warning("⚠️ No se encontraron datos válidos. Revisa que las fechas estén en las columnas B, C y D.")
else:
    st.error("No se pudo conectar con el archivo Excel.")
    
