import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# 1. Configuración de Poder
st.set_page_config(page_title="GUDMO 16 - MANDO TOTAL", layout="wide")
st.markdown("<style>.stApp{background-color:#0b0e14;color:white;}.card{padding:15px;border-radius:10px;margin-bottom:10px;border-left:6px solid;background:#1c2128;}.v{border-left-color:#ff4b4b;background:#3d0a0a;}.ok{border-left-color:#00ff6a;background:#0a2d1a;}</style>", unsafe_allow_html=True)

# 2. Credenciales y Link (El que ya verificamos que abre)
TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def master_load():
    try:
        r = requests.get(URL, timeout=20)
        df = pd.read_excel(BytesIO(r.content), engine='openpyxl')
        # Limpieza: quitamos filas totalmente vacías y detectamos dónde empiezan los nombres
        return df.dropna(subset=[df.columns[0]]).reset_index(drop=True)
    except: return None

# 3. Lógica de Control
st.title("🛡️ CONSOLA MAESTRA GUDMO 16")
df = master_load()

if df is not None:
    hoy = pd.Timestamp(date.today())
    st.success(f"✅ Sistema En Línea | {hoy.date()}")
    
    vencidos_list = []
    col1, col2 = st.columns(2)

    for i, fila in df.iterrows():
        nombre = str(fila.iloc[0]).strip().upper()
        if "APELLIDOS" in nombre or len(nombre) < 4: continue # Saltar encabezados o basura

        # Revisión de Licencia (Col B), Tecno (Col C), SOAT (Col D)
        alertas = []
        es_vencido = False
        for etiqueta, c_idx in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            f = pd.to_datetime(fila.iloc[c_idx], errors='coerce')
            if pd.notna(f) and f.year > 2000:
                status = "🔴 VENCIDO" if f.date() <= hoy.date() else "🟢 AL DÍA"
                if f.date() <= hoy.date(): es_vencido = True
                alertas.append(f"• {etiqueta}: {f.date()} {status}")

        # Estilo de Tarjeta
        clase = "v" if es_vencido else "ok"
        card = f'<div class="card {clase}"><b>👤 {nombre}</b><br>{"<br>".join(alertas)}</div>'
        
        if i % 2 == 0: col1.markdown(card, unsafe_allow_html=True)
        else: col2.markdown(card, unsafe_allow_html=True)
        
        if es_vencido: vencidos_list.append(f"👤 {nombre}\n" + "\n".join(alertas))

    # 4. Reporte Telegram (A un solo clic)
    st.divider()
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        texto = f"🚨 *REPORTE GUDMO 16 - {hoy.date()}*\n\n"
        texto += "\n\n".join(vencidos_list) if vencidos_list else "✅ Todo el personal está AL DÍA."
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})
        st.balloons()
        st.success("Reporte enviado.")
else:
    st.error("Error crítico: No se pudo conectar con la base de datos.")
    
