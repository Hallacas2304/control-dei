import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- 1. ESTILOS Y CONFIGURACIÓN (RESTAURADOS) ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { 
        background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); 
        padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; 
        margin-bottom: 15px; 
    }
    .card-comunicado { 
        background: linear-gradient(90deg, #002b4b 0%, #00111a 100%); 
        padding: 20px; border-radius: 12px; border-left: 6px solid #00a2ff; 
        margin-bottom: 15px; 
    }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=2)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=15)
        # Cargamos el Excel sin encabezados para mapear manualmente
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos = []
    con_soporte = []

    # --- 2. LÓGICA DE DETECCIÓN INTELIGENTE ---
    for i in range(len(df)):
        fila = df.iloc[i]
        
        # Captura de nombre (buscamos en la primera columna con texto largo)
        nombre = str(fila[0]).strip().upper()
        if nombre in ["NAN", "APELLIDOS", "ENDER", "PLACA", "No.", ""] or len(nombre) < 6:
            continue

        alertas_persona = []
        # Buscamos comunicado en la columna N (índice 14)
        comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
        tiene_oficio = comunicado != "NO APLICA" and "NAN" not in comunicado

        # Escaneo de fechas en las columnas B, C y D (índices 1, 2, 3)
        for idx in [1, 2, 3]:
            valor = fila[idx]
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # Filtro estricto para evitar el error de 1970
                    if pd.notna(f) and f.year > 2024:
                        if f <= hoy:
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else "SOAT")
                            alertas_persona.append(f"🚨 {tipo} VENCIDO ({f.date()})")
                except:
                    continue

        if alertas_persona:
            info = {"nombre": nombre, "detalles": "\n".join(alertas_persona), "oficio": comunicado}
            if tiene_oficio:
                con_soporte.append(info)
            else:
                criticos.append(info)

    # --- 3. DASHBOARD ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🔴 SIN SOPORTE (ACCIÓN INMEDIATA)")
        if not criticos: st.write("✅ Todo al día")
        for c in criticos:
            st.markdown(f'<div class="card-vencido"><b>👤 {c["nombre"]}</b><br>{c["detalles"].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    with col_b:
        st.subheader("🔵 CON COMUNICADO OFICIAL")
        if not con_soporte: st.write("✅ Sin trámites pendientes")
        for s in con_soporte:
            st.markdown(f'<div class="card-comunicado"><b>👤 {s["nombre"]}</b><br>{s["detalles"].replace("\n", "<br>")}<br><br>📜 OFICIO: {s["oficio"]}</div>', unsafe_allow_html=True)

    # --- 4. TELEGRAM (RESTAURADO) ---
    if st.button("🚀 ENVIAR REPORTES A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            msg = "🚨 *REPORTE GUDMO 16*\n\n"
            if criticos:
                msg += "*❌ CRÍTICOS:*\n"
                for c in criticos: msg += f"👤 {c['nombre']}\n{c['detalles']}\n\n"
            
            if con_soporte:
                msg += "*ℹ️ CON TRÁMITE:*\n"
                for s in con_soporte: msg += f"👤 {s['nombre']}\n{s['detalles']}\n📜 OFICIO: {s['oficio']}\n\n"

            res = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                                data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            
            if res.status_code == 200: st.success("✅ Reporte enviado a Telegram")
            else: st.error("❌ Error al enviar")

else:
    st.error("No se pudo leer el Excel. Verifica el link.")
    
