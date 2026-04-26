import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="GUDMO 16 - CONTROL REAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; margin-bottom: 15px; }
    .card-comunicado { background: linear-gradient(90deg, #002b4b 0%, #00111a 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #00a2ff; margin-bottom: 15px; }
    .card-alerta { background: linear-gradient(90deg, #3b2a00 0%, #1a1300 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #ffa500; margin-bottom: 15px; }
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
    proximo_mes = hoy + pd.Timedelta(days=30)
    
    criticos, con_soporte, advertencias = [], [], []

    # RECORRIDO SEGÚN TU IMAGEN (A=0, B=1, C=2, D=3, E=4)
    # Empezamos en la fila 2 para saltar el encabezado
    for i in range(1, len(df)):
        fila = df.iloc[i]
        try:
            nombre = str(fila[0]).upper() # Columna A
            if "NAN" in nombre or "APELLIDOS" in nombre or "ENDER" in nombre: continue
            
            # MAPEO EXACTO SEGÚN TU CAPTURA:
            f_licencia = pd.to_datetime(fila[1], errors='coerce', dayfirst=True) # Columna B
            f_tecno = pd.to_datetime(fila[2], errors='coerce', dayfirst=True)    # Columna C
            f_soat = pd.to_datetime(fila[3], errors='coerce', dayfirst=True)     # Columna D
            
            # Nota: Si agregas la columna de comunicados, asegúrate que sea la F (índice 5)
            # Por ahora, como no la veo en la imagen, el código marcará todo como crítico si vence.
            comunicado = "NO APLICA" 

            alertas_persona = []
            es_vencido = False
            es_proximo = False

            documentos = [("LICENCIA", f_licencia), ("TECNO", f_tecno), ("SOAT", f_soat)]
            
            for tipo, f in documentos:
                if pd.notna(f):
                    if f <= hoy:
                        alertas_persona.append(f"🚨 {tipo} VENCIDO ({f.date()})")
                        es_vencido = True
                    elif f <= proximo_mes:
                        alertas_persona.append(f"🟡 {tipo} x Vencer ({f.date()})")
                        es_proximo = True

            if alertas_persona:
                info = f"👤 <b>{nombre}</b><br>{'<br>'.join(alertas_persona)}"
                if es_vencido:
                    criticos.append(info)
                elif es_proximo:
                    advertencias.append(info)
        except: continue

    # --- MÉTRICAS ---
    st.title("🛡️ CONTROL GUDMO 16 - DETECCIÓN REAL")
    m1, m2, m3 = st.columns(3)
    m1.metric("VENCIDOS REALES", len(criticos))
    m2.metric("CON SOPORTE", len(con_soporte))
    m3.metric("PRÓXIMOS", len(advertencias))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 ALERTAS ROJAS (Sin Soporte)")
        for c in criticos:
            st.markdown(f'<div class="card-vencido">{c}</div>', unsafe_allow_html=True)
    with col2:
        st.subheader("🟡 ALERTAS AMARILLAS (Preventivas)")
        for a in advertencias:
            st.markdown(f'<div class="card-alerta">{a}</div>', unsafe_allow_html=True)

    # --- BOTÓN TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        reporte = "🚨 *REPORTE DE VENCIMIENTOS GUDMO 16*\n\n"
        if criticos:
            reporte += "*❌ CRÍTICOS:*\n" + "\n".join(criticos).replace("<br>", "\n").replace("<b>","").replace("</b>","")
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": reporte, "parse_mode": "Markdown"})
        st.success("Reporte enviado")
        
