import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); padding: 15px; border-radius: 10px; border-left: 6px solid #ff4b4b; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=15)
        # Cargamos el Excel limpio
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    # Esta es la lista única que usaremos para pantalla y Telegram
    infractores_detectados = []

    # --- ESCANEO FILA POR FILA ---
    for i in range(len(df)):
        fila = df.iloc[i]
        # El nombre siempre suele estar en la primera columna con texto (Índice 0)
        nombre = str(fila[0]).strip().upper()
        
        # Filtro para ignorar basura, números de fila o encabezados
        if len(nombre) < 5 or nombre.isdigit() or "NAN" in nombre or "APELLIDOS" in nombre:
            continue

        alertas_fila = []
        
        # Escaneamos TODA la fila buscando fechas
        for idx, valor in enumerate(fila):
            # Solo si la celda tiene un valor que no sea texto
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # Filtro anti-1970: Solo fechas de este año en adelante
                    if pd.notna(f) and f.year >= 2024:
                        if f <= hoy:
                            # Identificar qué es por la columna (B=Licencia, C=Tecno, D=Soat)
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else ("SOAT" if idx == 3 else "DOC"))
                            alertas_fila.append(f"🚨 {tipo} VENCIDO ({f.date()})")
                except:
                    continue

        if alertas_fila:
            # Guardamos el bloque de texto para enviarlo tal cual
            reporte_persona = f"👤 *{nombre}*\n" + "\n".join(alertas_fila)
            infractores_detectados.append(reporte_persona)

    # --- MOSTRAR EN PANTALLA ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    
    if not infractores_detectados:
        st.success("✅ No se detectaron documentos vencidos hoy.")
    else:
        for item in infractores_detectados:
            st.markdown(f'<div class="card-vencido">{item.replace("*", "").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- ENVIAR A TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if infractores_detectados:
            mensaje_completo = "🚨 *NOTIFICACIÓN VENCIMIENTOS GUDMO 16*\n\n" + "\n\n".join(infractores_detectados)
            
            try:
                res = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                                    data={"chat_id": CHAT_ID, "text": mensaje_completo, "parse_mode": "Markdown"})
                if res.status_code == 200:
                    st.success("✅ Reporte enviado a Telegram.")
                else:
                    st.error(f"Error de Telegram: {res.status_code}")
            except:
                st.error("Error de conexión con Telegram.")
        else:
            st.warning("No hay infractores detectados para enviar.")
else:
    st.error("No se pudo leer el Excel. Verifica que el link de SharePoint siga activo.")
    
