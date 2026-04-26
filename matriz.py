import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="GUDMO 16 - LECTURA ACTIVA", layout="wide")
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
        r = requests.get(url, timeout=20)
        # Forzamos la lectura de todas las celdas como objetos para no perder datos
        return pd.read_excel(BytesIO(r.content), header=None, engine='openpyxl')
    except Exception as e:
        st.error(f"Fallo de conexión con Excel: {e}")
        return None

df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos = []
    con_soporte = []

    # RECORRIDO DE FILAS
    for i in range(len(df)):
        fila = df.iloc[i]
        
        # 1. Identificar Nombre (Columna A)
        nombre = str(fila[0]).strip().upper()
        if len(nombre) < 5 or "NAN" in nombre or nombre.isdigit() or "APELLIDOS" in nombre:
            continue

        alertas_txt = []
        # 2. Revisar Fechas: Columna B(1)=Licencia, C(2)=Tecno, D(3)=SOAT
        vencimientos = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col in vencimientos:
            try:
                # Intentamos convertir a fecha ignorando errores de texto
                fecha_val = pd.to_datetime(fila[col], errors='coerce', dayfirst=True)
                
                # Filtro de Seguridad: Solo años reales (2025-2030)
                if pd.notna(fecha_val) and 2024 < fecha_val.year < 2032:
                    if fecha_val <= hoy:
                        alertas_txt.append(f"• {tipo}: **{fecha_val.date()}**")
            except:
                continue

        if alertas_txt:
            # 3. Revisar Comunicado (Columna N = Índice 14)
            comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
            tiene_oficio = "NO APLICA" not in comunicado and "NAN" not in comunicado and len(comunicado) > 3
            
            info = f"👤 **{nombre}**\n" + "\n".join(alertas_txt)
            
            if tiene_oficio:
                con_soporte.append(info + f"\n\n📜 **OFICIO:** {comunicado}")
            else:
                criticos.append(info)

    # --- MOSTRAR RESULTADOS ---
    st.title("🛡️ CONTROL DE VENCIMIENTOS GUDMO 16")
    
    if not criticos and not con_soporte:
        st.warning("El archivo se leyó pero no se encontraron fechas vencidas con los filtros actuales.")
    
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
    if st.button("🚀 ENVIAR A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            msg = "🚨 *REPORTE GUDMO 16*\n\n"
            if criticos:
                msg += "*❌ SIN SOPORTE:*\n" + "\n\n".join(criticos) + "\n\n"
            if con_soporte:
                msg += "*ℹ️ CON OFICIO:*\n" + "\n\n".join(con_soporte)
            
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.success("Enviado")

else:
    st.error("No hay lectura del Excel. Verifica que el enlace sea público.")
    
