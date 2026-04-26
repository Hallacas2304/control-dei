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
    .card-comunicado { background: linear-gradient(90deg, #002b4b 0%, #00111a 100%); padding: 15px; border-radius: 10px; border-left: 6px solid #00a2ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=25)
        # Cargamos el archivo sin procesar tipos de datos todavía
        return pd.read_excel(BytesIO(r.content), header=None)
    except: return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos = []
    con_soporte = []

    # --- ESCANEO FILA POR FILA ---
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila[0]).strip().upper()
        
        # Filtro de nombres: Ignorar basura
        if len(nombre) < 5 or "NAN" in nombre or nombre.isdigit() or "APELLIDOS" in nombre:
            continue

        alertas_funcionario = []
        # Columnas: B(1)=Licencia, C(2)=Tecno, D(3)=SOAT
        vencimientos = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col in vencimientos:
            if col < len(fila):
                valor_celda = fila[col]
                if pd.notna(valor_celda):
                    # Intentamos convertir lo que sea (texto o fecha) a formato fecha
                    f = pd.to_datetime(valor_celda, errors='coerce', dayfirst=True)
                    # Solo años reales para evitar el error de 1970
                    if pd.notna(f) and 2024 < f.year < 2035:
                        if f <= hoy:
                            alertas_funcionario.append(f"• {tipo}: {f.date()}")

        if alertas_funcionario:
            # Columna N (Índice 14) para Comunicados
            comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
            oficio_real = "NO APLICA" not in comunicado and "NAN" not in comunicado and len(comunicado) > 3
            
            resumen = f"👤 **{nombre}**\n" + "\n".join(alertas_funcionario)
            
            if oficio_real:
                con_soporte.append(resumen + f"\n📜 **OFICIO:** {comunicado}")
            else:
                criticos.append(resumen)

    # --- MOSTRAR EN PANTALLA ---
    st.title("🛡️ CONSOLA GUDMO 16")
    
    if not criticos and not con_soporte:
        st.info("No se detectaron vencimientos. Revisa que las fechas en el Excel no tengan espacios o caracteres extraños.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔴 SIN SOPORTE")
        for c in criticos:
            st.markdown(f'<div class="card-vencido">{c.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
            
    with c2:
        st.subheader("🔵 CON COMUNICADO")
        for s in con_soporte:
            st.markdown(f'<div class="card-comunicado">{s.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            msg = "🚨 *NOTIFICACIÓN GUDMO 16*\n\n"
            if criticos:
                msg += "*❌ SIN SOPORTE (URGENTE):*\n" + "\n\n".join(criticos) + "\n\n"
            if con_soporte:
                msg += "*ℹ️ CON OFICIO:* \n" + "\n\n".join(con_soporte)
            
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.success("✅ Reporte enviado.")
        else:
            st.warning("Nada para enviar.")
else:
    st.error("No se pudo leer el Excel.")
    
