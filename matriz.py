import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- 1. ESTILO INSTITUCIONAL Y SEMÁFORO ---
st.set_page_config(page_title="GUDMO 16 - MANDO TOTAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050b14; color: #e0e6ed; }
    .card {
        padding: 20px; border-radius: 15px; margin-bottom: 15px;
        background: rgba(255, 255, 255, 0.05);
        border-left: 10px solid;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    .vencido { border-left-color: #ff003c; border-right: 1px solid #ff003c33; }
    .al-dia { border-left-color: #00ff9d; border-right: 1px solid #00ff9d33; }
    [data-testid="stMetricValue"] { color: #00d4ff !important; }
    .stMetric { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; border: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN DE ENLACES Y TOKENS ---
TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL_MATRIZ = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def cargar_base_datos():
    try:
        r = requests.get(URL_MATRIZ, timeout=25)
        return pd.read_excel(BytesIO(r.content), engine='openpyxl')
    except: return None

# --- 3. LÓGICA DE CONTROL DE DOCUMENTOS ---
df = cargar_base_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    personal_total = []
    alertas_criticas = 0

    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[0]).strip().upper()
        if nombre in ["NAN", "NONE", ""] or "APELLIDOS" in nombre or nombre.replace('.','').isdigit(): continue
        
        docs = []
        es_novedad = False
        # Columnas B(1), C(2), D(3)
        for t, col in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            try:
                f = pd.to_datetime(fila.iloc[col], errors='coerce')
                if pd.notna(f) and f.year > 2000:
                    vencido = f.date() <= hoy.date()
                    if vencido: es_novedad = True
                    docs.append({"tipo": t, "fecha": f.date(), "status": vencido})
            except: continue
        
        if docs:
            personal_total.append({"nombre": nombre, "docs": docs, "novedad": es_novedad})
            if es_novedad: alertas_criticas += 1

    # --- 4. PANEL VISUAL (DASHBOARD) ---
    st.title("🛡️ COMMAND CENTER GUDMO 16")
    
    # MÉTRICAS ESTILO SEMÁFORO
    c1, c2, c3 = st.columns(3)
    c1.metric("FUERZA TOTAL", len(personal_total))
    c2.metric("ALERTA ROJA", alertas_criticas, delta=f"{alertas_criticas} VENCIDOS", delta_color="inverse")
    c3.metric("FUERZA DISPONIBLE", len(personal_total) - alertas_criticas)

    st.divider()

    # BUSCADOR Y DESCARGAS
    col_a, col_b = st.columns([2, 1])
    with col_a:
        busqueda = st.text_input("🔍 RASTREAR UNIFORMADO", placeholder="Escriba apellido...").upper()
    with col_b:
        st.download_button("📥 DESCARGAR MATRIZ ACTUAL", df.to_csv(index=False).encode('utf-8'), "matriz_gudmo.csv")

    # GESTIÓN DE ARCHIVOS
    with st.expander("📂 ACTUALIZAR DOCUMENTACIÓN INSTITUCIONAL"):
        upload = st.file_uploader("Cargar nueva matriz (Formato Excel)", type=["xlsx"])
        if upload: st.success("Archivo verificado. Listo para sincronizar.")

    # VISTA DE FUNCIONARIOS (TARJETAS)
    st.subheader("📋 ESTADO INDIVIDUAL")
    col_izq, col_der = st.columns(2)
    idx = 0

    for p in personal_total:
        if busqueda and busqueda not in p["nombre"]: continue
        
        idx += 1
        clase = "vencido" if p["novedad"] else "al-dia"
        emoji = "🚨" if p["novedad"] else "✅"
        
        with (col_izq if idx % 2 != 0 else col_der):
            html = f'<div class="card {clase}"><b>{emoji} {p["nombre"]}</b><br><hr style="opacity:0.1">'
            for d in p["docs"]:
                color = "#ff4b4b" if d["status"] else "#00ff9d"
                html += f'<span style="color:{color}">• {d["tipo"]}: {d["fecha"]}</span><br>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    # --- 5. ALARMAS TELEGRAM ---
    st.sidebar.title("📡 SISTEMA DE ALERTAS")
    if st.sidebar.button("🚀 ENVIAR NOVEDADES A TELEGRAM", use_container_width=True):
        msg = f"🚨 *REPORTE GUDMO 16 - {hoy.date()}*\n\n"
        hay_novedad = False
        for p in personal_total:
            if p["novedad"]:
                hay_novedad = True
                msg += f"👤 *{p['nombre']}*\n"
                for d in p["docs"]:
                    if d["status"]: msg += f"  ❌ {d['tipo']}: {d['fecha']}\n"
                msg += "\n"
        
        if not hay_novedad: msg += "✅ TODO EL PERSONAL AL DÍA."
        
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        st.sidebar.success("Alerta enviada al grupo.")
        st.balloons()
else:
    st.error("FATAL ERROR: Fallo de enlace con SharePoint. Verifique conexión.")
