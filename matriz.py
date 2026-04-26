import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")

# Estilos visuales
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
URL_FINAL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def obtener_datos():
    try:
        r = requests.get(URL_FINAL, timeout=25)
        return pd.read_excel(BytesIO(r.content), engine='openpyxl')
    except: return None

df = obtener_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    st.success(f"✅ Conexión establecida. Revisión: {hoy.date()}")
    
    # --- BUSCADOR INTELIGENTE DE COLUMNAS ---
    # Buscamos en qué columna están los nombres y las fechas
    col_nombre = 0
    col_licencia = 1
    col_tecno = 2
    col_soat = 3
    col_comunicado = 13

    # Escaneamos las primeras filas para encontrar los encabezados reales
    for r in range(min(len(df), 10)):
        fila_str = [str(x).upper() for x in df.iloc[r]]
        for idx, texto in enumerate(fila_str):
            if "APELLIDO" in texto or "NOMBRE" in texto: col_nombre = idx
            if "LICENCIA" in texto: col_licencia = idx
            if "TECNO" in texto: col_tecno = idx
            if "SOAT" in texto: col_soat = idx
            if "COMUNICADO" in texto or "OFICIO" in texto: col_comunicado = idx

    reporte_vencidos = []
    count = 0
    c1, c2 = st.columns(2)

    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[col_nombre]).strip().upper()
        
        # Si es un número o está vacío, saltar
        if nombre == "NAN" or nombre.replace('.','').isdigit() or len(nombre) < 4:
            continue

        count += 1
        alertas = []
        vencido_total = False
        
        # Procesar las 3 fechas clave
        for tipo, c_idx in [("LICENCIA", col_licencia), ("TECNO", col_tecno), ("SOAT", col_soat)]:
            try:
                f_val = fila.iloc[c_idx]
                f = pd.to_datetime(f_val, errors='coerce')
                if pd.notna(f) and 2024 < f.year < 2035:
                    status = "🔴 VENCIDO" if f.date() <= hoy.date() else "🟢 AL DÍA"
                    if f.date() <= hoy.date(): 
                        vencido_total = True
                    alertas.append(f"• {tipo}: {f.date()} {status}")
            except: continue

        # Identificar si tiene oficio/comunicado
        com = str(fila.iloc[col_comunicado]).strip().upper() if len(fila) > col_comunicado else ""
        tiene_soporte = len(com) > 3 and "NAN" not in com

        # Dibujar en pantalla
        clase = "vencido" if vencido_total else "al-dia"
        card_html = f'<div class="card {clase}"><b>👤 {nombre}</b><br>{"<br>".join(alertas)}'
        if tiene_soporte: card_html += f'<br>📜 <b>SOPORTE:</b> {com}'
        card_html += '</div>'

        if count % 2 != 0: c1.markdown(card_html, unsafe_allow_html=True)
        else: c2.markdown(card_html, unsafe_allow_html=True)
        
        if vencido_total:
            reporte_vencidos.append(f"👤 {nombre}\n" + "\n".join(alertas))

    st.divider()
    
    # --- BOTÓN TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        txt = f"🚨 *REPORTE GUDMO 16 - {hoy.date()}*\n\n"
        if reporte_vencidos:
            txt += "\n\n".join(reporte_vencidos)
        else:
            txt += "✅ Todo el personal se encuentra al día."
        
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": txt, "parse_mode": "Markdown"})
        st.success("✅ Enviado.")

else:
    st.error("Error al cargar el archivo.")
    
