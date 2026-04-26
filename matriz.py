import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GUDMO 16 - Command Center", layout="wide")

# Estilo 2026: Moderno y de alto contraste
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { 
        background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%);
        padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.2);
    }
    .card-alerta { 
        background: linear-gradient(90deg, #3b2a00 0%, #1a1300 100%);
        padding: 20px; border-radius: 12px; border-left: 6px solid #ffa500; margin-bottom: 15px;
    }
    .status-tag { font-size: 0.85rem; font-weight: bold; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        # Tu enlace de OneDrive
        url_excel = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"
        response = requests.get(url_excel)
        # Cargamos el Excel asumiendo que la Fila 1 es el encabezado
        return pd.read_excel(BytesIO(response.content), header=0)
    except Exception as e:
        return None

st.title("🛡️ Consola Operativa GUDMO 16")
st.caption("Detección inteligente de documentación vehicular y personal")

df = cargar_datos()

if df is not None:
    # Estandarizamos nombres de columnas (Sin espacios ni saltos de línea)
    df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
    
    hoy = pd.Timestamp(date.today())
    proximo_mes = hoy + pd.Timedelta(days=30)
    
    criticos = []
    advertencias = []

    for _, fila in df.iterrows():
        # Identificamos al funcionario
        nombre = str(fila.get('APELLIDOS Y NOMBRES', '')).upper()
        if "NAN" in nombre or nombre == "": continue

        # Escaneamos las columnas clave que ya arreglaste
        for col in df.columns:
            if any(k in col for k in ["SOAT", "TECNO", "CONDUCCION"]):
                valor = fila[col]
                try:
                    # Convertimos a fecha (DD/MM/AAAA)
                    f_venc = pd.to_datetime(valor, errors='coerce', dayfirst=True)
                    
                    if pd.notna(f_venc) and f_venc.year > 2015:
                        info = f"👤 <b>{nombre}</b><br><span class='status-tag'>🚨 {col}: {f_venc.date()}</span>"
                        
                        if f_venc <= hoy:
                            criticos.append(info)
                        elif f_venc <= proximo_mes:
                            advertencias.append(info)
                except: continue

    # --- DASHBOARD DE MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("VENCIDOS", len(criticos), delta_color="inverse")
    m2.metric("A VENCER (30 DÍAS)", len(advertencias))
    m3.metric("TOTAL PERSONAL", len(df[df['APELLIDOS Y NOMBRES'].notna()]))

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("🔴 ACCIÓN INMEDIATA")
        if criticos:
            for c in list(set(criticos)):
                st.markdown(f'<div class="card-vencido">{c}</div>', unsafe_allow_html=True)
        else:
            st.success("✅ Todo el personal tiene documentación vigente.")

    with col_der:
        st.subheader("🟡 ALERTA PREVENTIVA")
        if advertencias:
            for a in list(set(advertencias)):
                st.markdown(f'<div class="card-alerta">{a}</div>', unsafe_allow_html=True)
        else:
            st.info("No hay vencimientos en los próximos 30 días.")

    st.divider()

    # --- ACCIÓN DE TELEGRAM ---
    if st.button("🚀 DISTRIBUIR ALERTAS A TELEGRAM", use_container_width=True):
        if criticos:
            # Limpiamos el mensaje para Telegram (quitamos HTML de Streamlit)
            reporte = "⚠️ <b>REPORTE DE NOVEDADES GUDMO 16</b>\n\n"
            reporte += "\n".join(list(set(criticos))).replace("<br>", "\n").replace("<span class='status-tag'>", "").replace("</span>", "")
            
            url_tg = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
            res = requests.post(url_tg, data={"chat_id": CHAT_ID, "text": reporte, "parse_mode": "HTML"})
            
            if res.status_code == 200: st.success("¡Reporte enviado al comando!")
            else: st.error("Error al conectar con Telegram.")
        else:
            st.toast("No hay registros críticos para reportar.")

    with st.expander("📊 Ver Base de Datos Cruda"):
        st.dataframe(df)

else:
    st.error("No se pudo cargar la base de datos. Verifica la conexión con OneDrive.")
    
