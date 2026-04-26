import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- 1. CONFIGURACIÓN VISUAL (RESTAURADA) ---
st.set_page_config(page_title="GUDMO 16 - Sistema de Control", layout="wide")

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
        # Cargamos el Excel completo
        return pd.read_excel(BytesIO(r.content), header=None)
    except: return None

st.title("🛡️ Consola Operativa GUDMO 16")
df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    proximo_mes = hoy + pd.Timedelta(days=30)
    
    criticos = []      # Rojos (Sin soporte)
    con_soporte = []   # Azules (Con comunicado)
    advertencias = []  # Amarillos (Próximos)

    # RECORRIDO QUIRÚRGICO (Empezamos en fila 3 para evitar logos/títulos)
    for i in range(2, len(df)):
        fila = df.iloc[i]
        try:
            # Columna C (Nombre) = Índice 2
            nombre = str(fila[2]).upper()
            if "NAN" in nombre or "APELLIDOS" in nombre: continue
            
            # Columna I (Tecno) = Índice 8 | Columna K (SOAT) = Índice 10
            f_tecno = pd.to_datetime(fila[8], errors='coerce', dayfirst=True)
            f_soat = pd.to_datetime(fila[10], errors='coerce', dayfirst=True)
            
            # Columna N (Comunicado Oficial) = Índice 14
            comunicado = str(fila[14]).strip().upper()
            tiene_oficio = comunicado != "NO APLICA" and "NAN" not in comunicado

            alertas_persona = []
            es_critico = False
            es_advertencia = False

            # Validar Tecno
            if pd.notna(f_tecno):
                if f_tecno <= hoy:
                    alertas_persona.append(f"🚨 TECNO Vencida: {f_tecno.date()}")
                    es_critico = True
                elif f_tecno <= proximo_mes:
                    alertas_persona.append(f"🟡 TECNO x Vencer: {f_tecno.date()}")
                    es_advertencia = True

            # Validar SOAT
            if pd.notna(f_soat):
                if f_soat <= hoy:
                    alertas_persona.append(f"🚨 SOAT Vencido: {f_soat.date()}")
                    es_critico = True
                elif f_soat <= proximo_mes:
                    alertas_persona.append(f"🟡 SOAT x Vencer: {f_soat.date()}")
                    es_advertencia = True

            # CLASIFICACIÓN SEGÚN COMUNICADO
            if alertas_persona:
                info = f"👤 <b>{nombre}</b><br>{'<br>'.join(alertas_persona)}"
                if es_critico:
                    if tiene_oficio:
                        con_soporte.append(f"{info}<br>🔵 OFICIO: {comunicado}")
                    else:
                        criticos.append(info)
                elif es_advertencia:
                    advertencias.append(info)
        except: continue

    # --- 2. DASHBOARD DE MÉTRICAS (RESTAURADO) ---
    m1, m2, m3 = st.columns(3)
    m1.metric("CRÍTICOS (SIN SOPORTE)", len(criticos))
    m2.metric("CON TRÁMITE OFICIAL", len(con_soporte))
    m3.metric("PRÓXIMOS A VENCER", len(advertencias))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 ACCIÓN INMEDIATA")
        for c in criticos:
            st.markdown(f'<div class="card-vencido">{c}</div>', unsafe_allow_html=True)
        
        st.subheader("🔵 CON COMUNICADO OFICIAL")
        for s in con_soporte:
            st.markdown(f'<div class="card-comunicado">{s}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🟡 ALERTA PREVENTIVA")
        for a in advertencias:
            st.markdown(f'<div class="card-alerta">{a}</div>', unsafe_allow_html=True)

    # --- 3. BOTÓN TELEGRAM (RESTAURADO) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            reporte = "🚨 <b>NOVEDADES GUDMO 16</b>\n\n"
            if criticos:
                reporte += "<b>❌ SIN SOPORTE:</b>\n" + "\n".join(criticos).replace("<br>", "\n") + "\n\n"
            if con_soporte:
                reporte += "<b>ℹ️ CON TRÁMITE:</b>\n" + "\n".join(con_soporte).replace("<br>", "\n")
            
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": CHAT_ID, "text": reporte, "parse_mode": "HTML"})
            st.success("Reporte enviado")

else:
    st.error("No se pudo conectar al archivo de SharePoint.")
    
