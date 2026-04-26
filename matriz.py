import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN VISUAL (Mantenida) ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); padding: 15px; border-radius: 10px; border-left: 6px solid #ff4b4b; margin-bottom: 10px; }
    .card-comunicado { background: linear-gradient(90deg, #002b4b 0%, #00111a 100%); padding: 15px; border-radius: 10px; border-left: 6px solid #00a2ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url)
        return pd.read_excel(BytesIO(r.content), header=None)
    except: return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos, con_soporte = [], []

    for i, fila in df.iterrows():
        # 1. Captura del nombre (Columna A = Índice 0)
        nombre = str(fila[0]).strip().upper()
        
        # Filtro para ignorar encabezados o filas vacías
        if any(x in nombre for x in ["NAN", "APELLIDOS", "PLACA", "No.", "ENDER"]): continue
        if len(nombre) < 5: continue # Evita que salgan solo números de fila

        alertas_persona = []
        # Comunicado en Columna N (Índice 14)
        comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
        tiene_oficio = comunicado != "NO APLICA" and "NAN" not in comunicado

        # 2. Escaneo de fechas con Filtro Anti-1970
        for idx, valor in enumerate(fila):
            try:
                # Solo intentamos convertir si la celda no está vacía
                if pd.notna(valor) and not isinstance(valor, str):
                    f = pd.to_datetime(valor, errors='coerce')
                    
                    # FILTRO CRÍTICO: Solo fechas lógicas (Año entre 2021 y 2035)
                    if pd.notna(f) and 2021 < f.year < 2035:
                        if f <= hoy:
                            # Identificación por columna según tu Excel
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else ("SOAT" if idx == 3 else "DOC"))
                            alertas_persona.append(f"🚨 {tipo} VENCIDO ({f.date()})")
            except: continue

        if alertas_persona:
            info = f"👤 <b>{nombre}</b><br>{'<br>'.join(alertas_persona)}"
            if tiene_oficio:
                con_soporte.append(f"{info}<br>🔵 OFICIO: {comunicado}")
            else:
                criticos.append(info)

    # --- MÉTRICAS ---
    st.title("🛡️ DETECCIÓN REAL GUDMO 16")
    m1, m2 = st.columns(2)
    m1.metric("VENCIDOS SIN SOPORTE", len(criticos))
    m2.metric("CON TRÁMITE", len(con_soporte))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 ACCIÓN INMEDIATA")
        for c in criticos: st.markdown(f'<div class="card-vencido">{c}</div>', unsafe_allow_html=True)
    with col2:
        st.subheader("🔵 CON COMUNICADO")
        for s in con_soporte: st.markdown(f'<div class="card-comunicado">{s}</div>', unsafe_allow_html=True)

    # --- TELEGRAM (Sin cambios en tu lógica) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            reporte = "🚨 *NOVEDADES GUDMO 16*\n\n"
            if criticos:
                reporte += "*❌ SIN SOPORTE:*\n" + "\n".join(criticos).replace("<br>", "\n").replace("<b>","").replace("</b>","")
            if con_soporte:
                reporte += "\n\n*ℹ️ CON TRÁMITE:*\n" + "\n".join(con_soporte).replace("<br>", "\n").replace("<b>","").replace("</b>","")
            
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": reporte, "parse_mode": "Markdown"})
            st.success("Reporte enviado")
else:
    st.error("No se pudo conectar al Excel.")
    
