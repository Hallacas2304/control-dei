import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- INTERFAZ PROFESIONAL ---
st.set_page_config(page_title="GUDMO 16 - CONSOLA DE MANDO", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); padding: 15px; border-radius: 10px; border-left: 6px solid #ff4b4b; margin-bottom: 10px; border-top: 1px solid #630000; }
    .card-comunicado { background: linear-gradient(90deg, #002b4b 0%, #00111a 100%); padding: 15px; border-radius: 10px; border-left: 6px solid #00a2ff; margin-bottom: 10px; border-top: 1px solid #004b63; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=1)
def cargar_datos_seguro():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url, timeout=25)
        # Forzamos motor openpyxl y lectura como texto para no perder datos
        return pd.read_excel(BytesIO(r.content), header=None, dtype=str, engine='openpyxl')
    except Exception as e:
        st.error(f"Error crítico de conexión: {e}")
        return None

df = cargar_datos_seguro()

if df is not None:
    hoy = pd.Timestamp(date.today())
    criticos, con_soporte = [], []

    for i in range(len(df)):
        fila = df.iloc[i]
        # Columna A: Apellidos y Nombres
        nombre = str(fila[0]).strip().upper()
        
        # Filtro: Solo filas que parezcan nombres reales
        if len(nombre) < 6 or "NAN" in nombre or nombre.isdigit() or "APELLIDOS" in nombre:
            continue

        alertas = []
        # Mapeo: B=1 (Licencia), C=2 (Tecno), D=3 (SOAT)
        vencimientos = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col in vencimientos:
            valor_raw = str(fila[col]).strip()
            if valor_raw and "NAN" not in valor_raw.upper():
                try:
                    # Intentamos convertir cualquier formato de fecha a algo legible
                    f = pd.to_datetime(valor_raw, errors='coerce', dayfirst=True)
                    # Filtro de seguridad 2025-2035 para evitar fechas basura
                    if pd.notna(f) and 2024 < f.year < 2035:
                        if f <= hoy:
                            alertas.append(f"• {tipo}: **{f.strftime('%d/%m/%Y')}**")
                except: continue

    # --- REVISIÓN DE COMUNICADO OFICIAL (COLUMNA N = 14) ---
        if alertas:
            comunicado = str(fila[14]).strip().upper() if len(fila) > 14 else "NO APLICA"
            # Si hay un oficio (ej: "COMUNICADO 123" o "OFICIO...")
            tiene_oficio = len(comunicado) > 3 and "NO APLICA" not in comunicado and "NAN" not in comunicado
            
            bloque = f"👤 **{nombre}**\n" + "\n".join(alertas)
            
            if tiene_oficio:
                con_soporte.append(bloque + f"\n\n📜 **SOPORTE:** {comunicado}")
            else:
                criticos.append(bloque)

    # --- PANTALLA PRINCIPAL ---
    st.title("🛡️ CONSOLA DE MANDO GUDMO 16")
    st.write(f"Verificación actualizada al: **{hoy.date()}**")
    
    if not criticos and not con_soporte:
        st.info("🔎 El archivo se leyó correctamente, pero no se encontraron documentos vencidos hoy. Verifica que las fechas en el Excel tengan el año 2025 o 2026.")
    
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.subheader("🔴 SIN SOPORTE (ACCION INMEDIATA)")
        for c in criticos:
            st.markdown(f'<div class="card-vencido">{c.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
            
    with col_der:
        st.subheader("🔵 CON COMUNICADO OFICIAL")
        for s in con_soporte:
            st.markdown(f'<div class="card-comunicado">{s.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # --- BOTÓN TELEGRAM ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        if criticos or con_soporte:
            msg = "🚨 *NOTIFICACIÓN VENCIMIENTOS GUDMO 16*\n\n"
            if criticos:
                msg += "*❌ SIN SOPORTE:*\n" + "\n\n".join(criticos) + "\n\n"
            if con_soporte:
                msg += "*ℹ️ CON OFICIO:* \n" + "\n\n".join(con_soporte)
            
            try:
                res = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                                    data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                if res.status_code == 200: st.success("✅ Reporte enviado correctamente.")
                else: st.error("Error al conectar con Telegram.")
            except: st.error("Error de conexión.")
else:
    st.error("❌ No se pudo cargar el Excel. Revisa el link de SharePoint.")
    
