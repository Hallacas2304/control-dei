import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN DE APARIENCIA ---
st.set_page_config(page_title="GUDMO 16 - Command Center", layout="wide")

# Estilo visual moderno
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { 
        background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%);
        padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 10px;
    }
    .card-proximo { 
        background: linear-gradient(90deg, #3b2a00 0%, #1a1300 100%);
        padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ✅ TUS CREDENCIALES
TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try: return requests.post(url, data=payload).status_code == 200
    except: return False

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Aquí va el link de tu nuevo Excel arreglado
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        return pd.read_excel(BytesIO(response.content))
    except: return None

st.title("⚡ GUDMO 16: Sistema Inteligente de Alertas")
st.write(f"Hoy es: {date.today().strftime('%d/%m/%Y')}")

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    proximo_venc = hoy + pd.Timedelta(days=15)
    
    criticos = []
    advertencias = []

    # Lógica de detección ultra-precisa
    for _, fila in df.iterrows():
        persona = str(fila.iloc[2]).upper() # Asume que la col 3 es el nombre
        if "APELLIDOS" in persona or "NAN" in persona: continue

        for col in df.columns:
            if any(key in str(col).upper() for key in ["SOAT", "TECNO", "CONDUCCION"]):
                try:
                    fecha = pd.to_datetime(fila[col], errors='coerce', dayfirst=True)
                    if pd.notna(fecha) and fecha.year > 2010:
                        info = f"<b>{persona}</b> - {col} ({fecha.date()})"
                        if fecha <= hoy: criticos.append(info)
                        elif fecha <= proximo_venc: advertencias.append(info)
                except: continue

    # --- DASHBOARD VISUAL ---
    m1, m2, m3 = st.columns(3)
    m1.metric("ESTADO CRÍTICO", len(criticos), delta="- Vencidos", delta_color="inverse")
    m2.metric("ALERTA TEMPRANA", len(advertencias), delta="A vencer")
    m3.metric("FUERZA TOTAL", len(df))

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔴 ACCIÓN INMEDIATA")
        for c in criticos:
            st.markdown(f'<div class="card-vencido">{c}</div>', unsafe_allow_html=True)

    with col_right:
        st.subheader("🟡 PREVENCIÓN (Próximos 15 días)")
        for a in advertencias:
            st.markdown(f'<div class="card-proximo">{a}</div>', unsafe_allow_html=True)

    st.divider()

    # Botón de Notificación Pro
    if st.button("🚀 DISTRIBUIR ALERTAS A TELEGRAM", use_container_width=True):
        if criticos:
            reporte = "⚠️ <b>REPORTE CRÍTICO GUDMO 16</b>\n\n"
            reporte += "\n".join(criticos)
            if enviar_telegram(reporte): st.success("¡Alertas enviadas!")
            else: st.error("Fallo en el envío.")
        else:
            st.info("Sin novedades críticas para reportar.")

    with st.expander("🔎 Ver Base de Datos"):
        st.dataframe(df)

else:
    st.warning("Conectando con la base de datos en la nube...")
    
