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
        return pd.read_excel(BytesIO(r.content), header=None)
    except:
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    # Listas simples para asegurar que Telegram las lea bien
    reporte_criticos = []
    reporte_tramite = []

    # --- 2. LÓGICA DE DETECCIÓN (SIN DAÑAR NADA) ---
    for i in range(len(df)):
        fila = df.iloc[i]
        
        # Captura de nombre: Columna A (Índice 0)
        nombre = str(fila[0]).strip().upper()
        
        # Filtro: Solo nombres reales, nada de números de fila o encabezados
        if nombre in ["NAN", "APELLIDOS", "ENDER", "PLACA", "NO.", ""] or len(nombre) < 6 or nombre.isdigit():
            continue

        alertas = []
        # Comunicado en Columna N (Índice 14)
        comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
        tiene_oficio = comunicado != "NO APLICA" and "NAN" not in comunicado

        # Escaneo de fechas en columnas B, C, D (Índices 1, 2, 3)
        for idx in [1, 2, 3]:
            valor = fila[idx]
            if pd.notna(valor) and not isinstance(valor, str):
                try:
                    f = pd.to_datetime(valor, errors='coerce')
                    # Filtro de año para matar el 1970
                    if pd.notna(f) and f.year > 2024:
                        if f <= hoy:
                            tipo = "LICENCIA" if idx == 1 else ("TECNO" if idx == 2 else "SOAT")
                            alertas.append(f"{tipo} VENCIDO ({f.date()})")
                except:
                    continue

        if alertas:
            resumen = f"👤 {nombre}\n" + "\n".join(alertas)
            if tiene_oficio:
                reporte_tramite.append(resumen + f"\n📜 OFICIO: {comunicado}")
            else:
                reporte_criticos.append(resumen)

    # --- 3. PANTALLA ---
    st.title("🛡️ DETECCIÓN DE INFRACTORES GUDMO 16")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 ACCIÓN INMEDIATA")
        for c in reporte_criticos:
            st.markdown(f'<div class="card-vencido">{c.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🔵 CON COMUNICADO OFICIAL")
        for s in reporte_tramite:
            st.markdown(f'<div class="card-comunicado">{s.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- 4. TELEGRAM (EL QUE SI FUNCIONABA) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if reporte_criticos or reporte_tramite:
            # Construcción limpia del mensaje
            texto_final = "🚨 *NOVEDADES GUDMO 16*\n\n"
            
            if reporte_criticos:
                texto_final += "*❌ SIN SOPORTE:*\n" + "\n\n".join(reporte_criticos) + "\n\n"
            
            if reporte_tramite:
                texto_final += "*ℹ️ CON TRÁMITE:* \n" + "\n\n".join(reporte_tramite)

            # Envío directo sin rodeos
            res = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                                data={"chat_id": CHAT_ID, "text": texto_final, "parse_mode": "Markdown"})
            
            if res.status_code == 200:
                st.success("✅ Notificación enviada.")
            else:
                st.error(f"Error: {res.status_code}")
        else:
            st.warning("No hay novedades para enviar.")
else:
    st.error("No se pudo conectar al Excel.")
                
