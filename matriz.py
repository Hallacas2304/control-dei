import streamlit as st
import pandas as pd
from datetime import date, datetime
import requests
from io import BytesIO
import re

# --- ESTILOS ---
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

def limpiar_fecha(valor):
    """Fuerza la conversión de cualquier texto a una fecha real"""
    if pd.isna(valor) or str(valor).strip() == "": return None
    # Si ya es una fecha de Python
    if isinstance(valor, (datetime, date)): return pd.to_datetime(valor)
    
    # Si es texto, intentamos varios formatos comunes en la matriz
    texto = str(valor).strip()
    for formato in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
        try:
            return pd.to_datetime(texto, format=formato)
        except: continue
    # Intento final desesperado
    return pd.to_datetime(texto, errors='coerce')

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=25)
        # Leemos TODO como texto para que nada se pierda
        return pd.read_excel(BytesIO(r.content), header=None, dtype=str, engine='openpyxl')
    except: return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos, con_soporte = [], []

    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        # Filtro: Ignorar filas vacías o de encabezado
        if len(nombre) < 6 or "NAN" in nombre or "APELLIDOS" in nombre: continue

        alertas = []
        # B=1 (Lic), C=2 (Tecno), D=3 (SOAT)
        checks = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col in checks:
            f_convertida = limpiar_fecha(fila[col])
            # Validamos que sea una fecha lógica (entre 2024 y 2035)
            if f_convertida and 2024 < f_convertida.year < 2035:
                if f_convertida <= hoy:
                    alertas.append(f"• {tipo}: **{f_convertida.strftime('%d/%m/%Y')}**")

        if alertas:
            # Columna N (14) es Comunicado
            comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else ""
            tiene_oficio = len(comunicado) > 3 and "NAN" not in comunicado and "NO APLICA" not in comunicado
            
            reporte = f"👤 **{nombre}**\n" + "\n".join(alertas)
            if tiene_oficio:
                con_soporte.append(reporte + f"\n\n📜 **SOPORTE:** {comunicado}")
            else:
                criticos.append(reporte)

    # --- PANTALLA ---
    st.title("🛡️ CONSOLA DE MANDO GUDMO 16")
    st.info(f"Escaneo profundo completado el {hoy.strftime('%d/%m/%Y')}")

    if not criticos and not con_soporte:
        st.warning("⚠️ No se detectaron vencimientos. Revisa que las fechas en el Excel tengan el año actual (2025 o 2026).")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔴 ACCIÓN INMEDIATA")
        for c in criticos: st.markdown(f'<div class="card-vencido">{c.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
    with c2:
        st.subheader("🔵 CON TRÁMITE / OFICIO")
        for s in con_soporte: st.markdown(f'<div class="card-comunicado">{s.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    if st.button("🚀 ENVIAR A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            msg = "🚨 *VENCIMIENTOS GUDMO 16*\n\n"
            if criticos: msg += "*❌ SIN SOPORTE:*\n" + "\n\n".join(criticos) + "\n\n"
            if con_soporte: msg += "*ℹ️ CON OFICIO:*\n" + "\n\n".join(con_soporte)
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.success("Reporte enviado")
else:
    st.error("No se pudo leer el archivo.")
    
