import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- 1. CONFIGURACIÓN ELITE Y ESTILOS ---
st.set_page_config(page_title="GUDMO 16 - SISTEMA INTEGRAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050b14; color: #e0e6ed; }
    /* Tarjetas Tipo Cristal */
    .card {
        padding: 20px; border-radius: 15px; margin-bottom: 15px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    .vencido { border-left: 10px solid #ff003c; border-right: 2px solid #ff003c; }
    .al-dia { border-left: 10px solid #00ff9d; border-right: 2px solid #00ff9d; }
    /* Métricas Neón */
    [data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 35px !important; }
    .stMetric { background: rgba(255,255,255,0.03); padding: 20px; border-radius: 15px; border: 1px solid #1f2937; }
    /* Botones Pro */
    .stButton>button {
        width: 100%; background: linear-gradient(45deg, #004e92, #000428);
        color: white; border: 1px solid #00d4ff; border-radius: 8px; height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN DE DATOS ---
TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL_BASE = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def fetch_data():
    try:
        r = requests.get(URL_BASE, timeout=25)
        return pd.read_excel(BytesIO(r.content), engine='openpyxl')
    except: return None

# --- 3. LOGICA DE CONTROL ---
df = fetch_data()

if df is not None:
    hoy = pd.Timestamp(date.today())
    personal_total = []
    vencidos_count = 0

    # Procesar Matriz
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[0]).strip().upper()
        if nombre in ["NAN", "NONE", ""] or "APELLIDOS" in nombre or nombre.replace('.','').isdigit(): continue
        
        docs = []
        is_novedad = False
        for tag, col in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            try:
                f = pd.to_datetime(fila.iloc[col], errors='coerce')
                if pd.notna(f) and f.year > 2000:
                    v = f.date() <= hoy.date()
                    if v: is_novedad = True
                    docs.append({"label": tag, "fecha": f.date(), "status": v})
            except: continue
        
        if docs:
            personal_total.append({"nombre": nombre, "docs": docs, "novedad": is_novedad})
            if is_novedad: vencidos_count += 1

    # --- 4. PANEL DE CONTROL (INTERFAZ) ---
    st.title("🛡️ COMMAND CENTER GUDMO 16")
    
    # SEMÁFORO DE MANDO
    m1, m2, m3 = st.columns(3)
    m1.metric("FUERZA TOTAL", len(personal_total))
    m2.metric("NOVEDADES", vencidos_count, delta=f"{vencidos_count} CRÍTICOS", delta_color="inverse")
    m3.metric("EN REGLA", len(personal_total) - vencidos_count)

    st.divider()

    # ZONA DE OPERACIONES (Buscador y Archivos)
    col_bus, col_file = st.columns([2, 1])
    with col_bus:
        search = st.text_input("🔍 RASTREADOR DE PERSONAL", placeholder="Ingrese apellidos...").upper()
    with col_file:
        # Descarga de la matriz actual
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DESCARGAR MATRIZ", csv, "matriz_gudmo.csv", "text/csv")

    # CARGA DE DOCUMENTOS (Opcional en interfaz)
    with st.expander("📂 SUBIR / ACTUALIZAR DOCUMENTACIÓN"):
        uploaded_file = st.file_uploader("Cargar nueva matriz (Excel)", type=["xlsx"])
        if uploaded_file: st.success("Archivo listo para procesamiento.")

    # VISTA DE TARJETAS
    st.subheader("📋 ESTADO DE LA FUERZA")
    c1, c2 = st.columns(2)
    display_idx = 0

    for p in personal_total:
        if search and search not in p["nombre"]: continue
        
        display_idx += 1
        clase = "vencido" if p["novedad"] else "al-dia"
        icon = "🚨" if p["novedad"] else "✅"
        
        with (c1 if display_idx % 2 != 0 else c2):
            html = f'<div class="card {clase}"><b>{icon} {p["nombre"]}</b><br><hr style="opacity:0.1">'
            for d in p["docs"]:
                color = "#ff4b4b" if d["status"] else "#00ff9d"
                html += f'<span style="color:{color}">• {d["label"]}: {d["fecha"]}</span><br>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    # --- 5. SISTEMA DE ALARMAS TELEGRAM ---
    st.sidebar.title("📡 CANAL DE ALARMAS")
    st.sidebar.info("Envía el reporte detallado al grupo de mando.")
    
    if st.sidebar.button("🚀 DISPARAR ALERTA TELEGRAM", use_container_width=True):
        mensaje = f"🚨 *GUDMO 16 - REPORTE DE NOVEDADES*\n📅 *FECHA:* {hoy.date()}\n"
        mensaje += "----------------------------------\n\n"
        
        found = False
        for p in personal_total:
            if p["novedad"]:
                found = True
                mensaje += f"👤 *{p['nombre']}*\n"
                for d in p["docs"]:
                    if d["status"]: mensaje += f" ❌ {d['label']}: {d['fecha']}\n"
                mensaje += "\n"
        
        if not found: mensaje += "✅ *SIN NOVEDADES:* Todo el personal al día."
        
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
            st.sidebar.success("¡Alerta enviada!")
            st.balloons()
        except:
            st.sidebar.error("Falla en el enlace satelital (Telegram).")

else:
    st.error("FATAL ERROR: No se detecta la matriz en SharePoint. Verifique el enlace.")
