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
        r = requests.get(url, timeout=15)
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    reporte_final = []

    # RECORRIDO CELDA POR CELDA (Para no fallar puntería)
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        # Filtro para solo procesar filas con nombres de funcionarios
        if len(nombre) < 5 or "NAN" in nombre or nombre.isdigit() or "APELLIDOS" in nombre:
            continue

        alertas_funcionario = []
        
        # Revisamos desde la columna 1 en adelante buscando fechas
        for idx in range(1, len(fila)):
            valor = fila[idx]
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # Filtro de seguridad: Solo años actuales (evita el 1970)
                    if pd.notna(f) and 2024 < f.year < 2030:
                        if f <= hoy:
                            # Detectar qué documento es según la posición
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else "SOAT")
                            alertas_funcionario.append(f"🚨 {tipo} VENCIDO ({f.date()})")
                except:
                    continue

        if alertas_funcionario:
            reporte_final.append(f"👤 *{nombre}*\n" + "\n".join(alertas_funcionario))

    # --- PANTALLA ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    
    if not reporte_final:
        st.info("No se detectaron documentos vencidos. Verifica que las fechas en el Excel estén en formato de fecha (DD/MM/AAAA).")
    else:
        for r in reporte_final:
            st.markdown(f'<div class="card-vencido">{r.replace("*", "").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if reporte_final:
            mensaje = "🚨 *NOTIFICACIÓN VENCIMIENTOS GUDMO 16*\n\n" + "\n\n".join(reporte_final)
            try:
                res = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                                    data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
                if res.status_code == 200: st.success("✅ Enviado")
                else: st.error(f"Error TG: {res.status_code}")
            except:
                st.error("Error de conexión")
        else:
            st.warning("Nada que enviar")
else:
    st.error("No se pudo cargar el archivo.")
    
