import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="GUDMO 16 - CONTROL PROFESIONAL", layout="wide")
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
        r = requests.get(url, timeout=15)
        return pd.read_excel(BytesIO(r.content), header=None)
    except: return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos = []      # Sin soporte
    con_soporte = []   # Con comunicado oficial

    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        if len(nombre) < 5 or "NAN" in nombre or nombre.isdigit() or "APELLIDOS" in nombre:
            continue

        detalles = []
        # Mapeo según tu matriz: B=1 (Licencia), C=2 (Tecno), D=3 (SOAT)
        misiones = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col_idx in misiones:
            valor = fila[col_idx]
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    if pd.notna(f) and 2024 < f.year < 2035:
                        if f <= hoy:
                            detalles.append(f"• {tipo}: **{f.date()}**")
                except: continue

        if detalles:
            # Columna N (índice 14) es el Comunicado
            comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
            tiene_oficio = comunicado != "NO APLICA" and "NAN" not in comunicado
            
            info_txt = f"👤 **{nombre}**\n" + "\n".join(detalles)
            
            if tiene_oficio:
                con_soporte.append(info_txt + f"\n\n📜 **COMUNICADO:** {comunicado}")
            else:
                criticos.append(info_txt)

    # --- INTERFAZ ---
    st.title("🛡️ CONSOLA DE MANDO GUDMO 16")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔴 ACCIÓN INMEDIATA (Sin Soporte)")
        for c in criticos:
            st.markdown(f'<div class="card-vencido">{c.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
            
    with col2:
        st.subheader("🔵 CASOS CON COMUNICADO OFICIAL")
        for s in con_soporte:
            st.markdown(f'<div class="card-comunicado">{s.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE CATEGORIZADO A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            msg = "🚨 *REPORTE DE VENCIMIENTOS GUDMO 16*\n\n"
            if criticos:
                msg += "*❌ SIN SOPORTE (URGENTE):*\n" + "\n\n".join(criticos) + "\n\n"
            if con_soporte:
                msg += "*ℹ️ CON TRÁMITE / OFICIO:*\n" + "\n\n".join(con_soporte)
            
            res = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                                data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            if res.status_code == 200: st.success("✅ Enviado")
        else:
            st.warning("No hay datos")
else:
    st.error("Error al conectar.")
    
