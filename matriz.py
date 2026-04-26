import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- ESTILOS ---
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
        r = requests.get(url, timeout=10)
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    reporte_final = []

    # --- ESCANEO AUTOMÁTICO ---
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        # Saltamos basura y encabezados
        if len(nombre) < 5 or nombre.isdigit() or "NAN" in nombre:
            continue

        alertas_usuario = []
        
        # REVISAMOS TODA LA FILA BUSCANDO FECHAS (Escaneo inteligente)
        for idx, valor in enumerate(fila):
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # Filtro: Solo fechas lógicas (Año > 2024 para evitar el error 1970)
                    if pd.notna(f) and f.year > 2024:
                        if f <= hoy:
                            # Identificamos el tipo por la posición relativa
                            tipo = "LICENCIA" if idx < 3 else ("TECNO" if idx < 6 else "SOAT")
                            alertas_usuario.append(f"🚨 {tipo} VENCIDO: {f.date()}")
                except:
                    continue

        if alertas_usuario:
            reporte_final.append(f"👤 *{nombre}*\n" + "\n".join(alertas_usuario))

    # --- INTERFAZ ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    
    if not reporte_final:
        st.success("✅ No se detectaron documentos vencidos hoy.")
    else:
        for r in reporte_final:
            st.markdown(f'<div class="card-vencido">{r.replace("*", "").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- BOTÓN TELEGRAM (RESTAURADO AL 100%) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if reporte_final:
            mensaje = "🚨 *NOTIFICACIÓN VENCIMIENTOS GUDMO 16*\n\n" + "\n\n".join(reporte_final)
            try:
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                             data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
                st.success("✅ Enviado a Telegram")
            except:
                st.error("Fallo al enviar")
        else:
            st.warning("Nada que reportar")
else:
    st.error("Error al leer el archivo.")
    
