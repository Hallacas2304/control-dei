import streamlit as st
import pd as pd # Usamos alias estándar
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN VISUAL (LA QUE TE GUSTA) ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { 
        background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); 
        padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; 
        margin-bottom: 15px; 
    }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=1) # Actualización casi instantánea
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=10)
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    # Lista para Telegram - LA CLAVE QUE SE HABÍA DAÑADO
    lista_para_telegram = []

    # --- PROCESAMIENTO ---
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        # Filtro de nombres: Si es muy corto o es un número, saltar
        if len(nombre) < 5 or nombre.isdigit() or "NAN" in nombre:
            continue

        detalles_vencidos = []
        
        # Escaneo de columnas de fechas (1, 2, 3 según tu Excel)
        for idx in [1, 2, 3]:
            valor = fila[idx]
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # FILTRO ANTI-1970: Solo fechas de este año en adelante
                    if pd.notna(f) and f.year >= 2025:
                        if f <= hoy:
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else "SOAT")
                            detalles_vencidos.append(f"🚨 {tipo} VENCIDO: {f.date()}")
                except:
                    continue

        if detalles_vencidos:
            texto_persona = f"👤 *{nombre}*\n" + "\n".join(detalles_vencidos)
            lista_para_telegram.append(texto_persona)

    # --- PANTALLA ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    
    if not lista_para_telegram:
        st.info("No se detectaron documentos vencidos hoy.")
    else:
        for item in lista_para_telegram:
            st.markdown(f'<div class="card-vencido">{item.replace("*", "").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- BOTÓN DE TELEGRAM (RESTAURADO) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if lista_para_telegram:
            mensaje_completo = "🚨 *NOTIFICACIÓN GUDMO 16*\n\n" + "\n\n".join(lista_para_telegram)
            
            url_api = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
            res = requests.post(url_api, data={"chat_id": CHAT_ID, "text": mensaje_completo, "parse_mode": "Markdown"})
            
            if res.status_code == 200:
                st.success("✅ Reporte enviado a Telegram correctamente.")
            else:
                st.error(f"Error de envío: {res.status_code}")
        else:
            st.warning("No hay nada que reportar.")
else:
    st.error("Error al conectar con el archivo Excel.")
        
