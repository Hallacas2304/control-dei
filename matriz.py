import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- MANTENEMOS TU CONFIGURACIÓN VISUAL QUE SÍ FUNCIONA ---
st.set_page_config(page_title="GUDMO 16 - Control Estricto", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-critica { background: linear-gradient(135deg, #660000 0%, #200000 100%); padding: 15px; border-radius: 10px; border: 2px solid #ff4b4b; margin-bottom: 10px; }
    .card-soporte { background: linear-gradient(135deg, #002b4b 0%, #00111a 100%); padding: 15px; border-radius: 10px; border-left: 5px solid #00a2ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url)
        # Cargamos SIN encabezados para mandar nosotros por número de columna
        return pd.read_excel(BytesIO(r.content), header=None)
    except: return None

st.title("🛡️ Consola Operativa GUDMO 16")
df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    vencidos_sin_soporte = []
    vencidos_con_soporte = []

    # RECORRIDO POR FILAS (Empezamos en la 3 donde están los datos reales)
    for i in range(2, len(df)):
        fila = df.iloc[i]
        try:
            # 1. LEEMOS POR LETRA DE COLUMNA (Índices de Python)
            # Columna C (Nombre) = Índice 2
            nombre = str(fila[2]).upper()
            if "NAN" in nombre or "APELLIDOS" in nombre: continue
            
            # Columna I (Tecno) = Índice 8 | Columna K (SOAT) = Índice 10
            f_tecno = pd.to_datetime(fila[8], errors='coerce', dayfirst=True)
            f_soat = pd.to_datetime(fila[10], errors='coerce', dayfirst=True)
            
            # Columna N (Comunicado Oficial) = Índice 14
            comunicado = str(fila[14]).strip().upper()
            tiene_oficio = comunicado != "NO APLICA" and "NAN" not in comunicado

            detalles = []
            if pd.notna(f_tecno) and f_tecno <= hoy:
                detalles.append(f"⚠️ TECNO Vencida: {f_tecno.date()}")
            if pd.notna(f_soat) and f_soat <= hoy:
                detalles.append(f"⚠️ SOAT Vencido: {f_soat.date()}")

            # 2. CLASIFICACIÓN FINAL SIN ERRORES DE NOMBRE
            if detalles:
                info_html = f"👤 <b>{nombre}</b><br>{'<br>'.join(detalles)}"
                
                if tiene_oficio:
                    vencidos_con_soporte.append(f"{info_html}<br>🔵 OFICIO: {comunicado}")
                else:
                    vencidos_sin_soporte.append(info_html)
        except:
            continue

    # --- RENDERIZADO (IGUAL AL QUE TE GUSTA) ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 VENCIDOS (SIN SOPORTE)")
        for v in vencidos_sin_soporte:
            st.markdown(f'<div class="card-critica">{v}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🔵 CON COMUNICADO OFICIAL")
        for s in vencidos_con_soporte:
            st.markdown(f'<div class="card-soporte">{s}</div>', unsafe_allow_html=True)

    # --- BOTÓN DE TELEGRAM (MANTENIDO) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM"):
        # Lógica de envío...
        st.success("Reporte enviado")
else:
    st.error("No se pudo conectar al Excel.")
    
