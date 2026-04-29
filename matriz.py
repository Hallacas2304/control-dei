import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# 1. CONFIGURACIÓN DE INTERFAZ TECNOLÓGICA
st.set_page_config(page_title="GUDMO 16 - COMMAND CENTER", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050b14; color: #e0e6ed; }
    .card {
        padding: 20px; border-radius: 15px; margin-bottom: 15px;
        background: rgba(255, 255, 255, 0.05);
        border-left: 8px solid;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }
    .vencido { border-left-color: #ff003c; border-right: 1px solid #ff003c33; }
    .al-dia { border-left-color: #00ff9d; border-right: 1px solid #00ff9d33; }
    .stMetric { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; border: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# 2. CREDENCIALES Y ENLACE DE EXCEL
TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL_EXCEL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def descargar_datos():
    try:
        # Descarga directa desde SharePoint
        r = requests.get(URL_EXCEL, timeout=25)
        # Cargamos el Excel. Pandas usará openpyxl internamente (debe estar en requirements.txt)
        df = pd.read_excel(BytesIO(r.content), engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return None

# 3. PROCESAMIENTO E INTERFAZ
df = descargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    personal_data = []
    vencidos_conteo = 0

    # Limpieza y escaneo de la matriz
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[0]).strip().upper()
        
        # Filtro de seguridad para ignorar basura y filas vacías
        if nombre in ["NAN", "NONE", ""] or "APELLIDOS" in nombre or nombre.replace('.','').isdigit():
            continue
            
        docs_status = []
        es_novedad = False
        
        # Columnas: B(1)=Licencia, C(2)=Tecno, D(3)=SOAT
        for titulo, col_idx in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            try:
                f_vence = pd.to_datetime(fila.iloc[col_idx], errors='coerce')
                if pd.notna(f_vence) and f_vence.year > 2000:
                    vence_date = f_vence.date()
                    esta_vencido = vence_date <= hoy.date()
                    if esta_vencido: es_novedad = True
                    docs_status.append({"tipo": titulo, "fecha": vence_date, "vencido": esta_vencido})
            except: continue
        
        personal_data.append({"nombre": nombre, "docs": docs_status, "novedad": es_novedad})
        if es_novedad: vencidos_conteo += 1

    # RENDERIZADO DE PANTALLA
    st.title("🛡️ COMMAND CENTER GUDMO 16")
    
    # Métricas de Mando
    m1, m2, m3 = st.columns(3)
    m1.metric("TOTAL PERSONAL", len(personal_data))
    m2.metric("ALERTAS CRÍTICAS", vencidos_conteo, delta=f"{vencidos_conteo} VENCIMIENTOS", delta_color="inverse")
    m3.metric("EN REGLA", len(personal_data) - vencidos_conteo)

    st.divider()
    
    # Buscador Activo
    busqueda = st.text_input("🔍 BUSCAR FUNCIONARIO (APELLIDOS / NOMBRES)").upper()

    # Despliegue de Tarjetas
    c_izq, c_der = st.columns(2)
    mostrados = 0

    for p in personal_data:
        if busqueda and busqueda not in p["nombre"]: continue
        
        mostrados += 1
        clase = "vencido" if p["novedad"] else "al-dia"
        emoji = "🚨" if p["novedad"] else "✅"
        
        with (c_izq if mostrados % 2 != 0 else c_der):
            card_html = f'<div class="card {clase}"><b>{emoji} {p["nombre"]}</b><br><hr style="opacity:0.1">'
            for d in p["docs"]:
                color = "#ff4b4b" if d["vencido"] else "#00ff9d"
                card_html += f'<span style="color:{color}">• {d["tipo"]}: {d["fecha"]}</span><br>'
            card_html += '</div>'
            st.markdown(card_html, unsafe_allow_html=True)

    # 4. SISTEMA DE REPORTES TELEGRAM
    st.sidebar.title("📤 COMUNICACIONES")
    if st.sidebar.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        msg = f"🚨 *GUDMO 16 - REPORTE DE NOVEDADES*\n📅 *Fecha:* {hoy.date()}\n\n"
        novedades_encontradas = False
        
        for p in personal_data:
            if p["novedad"]:
                novedades_encontradas = True
                msg += f"👤 *{p['nombre']}*\n"
                for d in p["docs"]:
                    if d["vencido"]: msg += f"  ❌ {d['tipo']}: {d['fecha']}\n"
                msg += "\n"
        
        if not novedades_encontradas:
            msg += "✅ *SIN NOVEDADES:* Todo el personal se encuentra al día."
        
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.sidebar.success("Reporte enviado al grupo.")
            st.balloons()
        except:
            st.sidebar.error("Error al conectar con Telegram.")

else:
    st.error("No se pudo cargar la base de datos. Verifique la conexión a SharePoint.")
