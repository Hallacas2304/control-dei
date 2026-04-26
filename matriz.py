import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- INTERFAZ ---
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

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=25)
        # Cargamos el excel ignorando formatos de celda para limpiar manualmente
        return pd.read_excel(BytesIO(r.content), header=None, dtype=str)
    except: return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos, con_soporte = [], []

    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        # Filtro de seguridad para filas vacías
        if len(nombre) < 5 or "NAN" in nombre or nombre.isdigit(): continue

        alertas = []
        # Columnas fijas: 1=Licencia, 2=Tecno, 3=SOAT
        misiones = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col in misiones:
            valor_raw = str(fila[col]).strip()
            if valor_raw and "NAN" not in valor_raw.upper():
                try:
                    # Forzamos la conversión de cualquier texto a fecha
                    f = pd.to_datetime(valor_raw, errors='coerce', dayfirst=True)
                    # Solo procesamos si el año es real (2024-2035) para evitar el error de 1970
                    if pd.notna(f) and 2024 < f.year < 2035:
                        if f <= hoy:
                            alertas.append(f"• {tipo}: **{f.date()}**")
                except: continue

        if alertas:
            # Columna N (14) es el comunicado
            comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
            tiene_oficio = "NO APLICA" not in comunicado and "NAN" not in comunicado and len(comunicado) > 3
            
            texto = f"👤 **{nombre}**\n" + "\n".join(alertas)
            if tiene_oficio:
                con_soporte.append(texto + f"\n\n📜 **OFICIO:** {comunicado}")
            else:
                criticos.append(texto)

    # --- PANTALLA ---
    st.title("🛡️ CONSOLA GUDMO 16")
    
    if not criticos and not con_soporte:
        st.warning("⚠️ Sin resultados. Verifica que las fechas en el Excel tengan un formato claro (ej: 25/04/2026).")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔴 SIN SOPORTE")
        for c in criticos: st.markdown(f'<div class="card-vencido">{c.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
    with c2:
        st.subheader("🔵 CON COMUNICADO")
        for s in con_soporte: st.markdown(f'<div class="card-comunicado">{s.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            msg = "🚨 *NOTIFICACIÓN VENCIMIENTOS GUDMO 16*\n\n"
            if criticos: msg += "*❌ SIN SOPORTE:*\n" + "\n\n".join(criticos) + "\n\n"
            if con_soporte: msg += "*ℹ️ CON OFICIO:*\n" + "\n\n".join(con_soporte)
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.success("✅ Enviado")
else:
    st.error("No hay lectura del Excel.")
    
