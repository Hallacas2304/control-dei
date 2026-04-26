import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# 1. CONFIGURACIÓN DE ALTA TECNOLOGÍA
st.set_page_config(page_title="SISTEMA GUDMO 16 - ELITE", layout="wide")

st.markdown("""
    <style>
    /* Fondo y tipografía */
    .stApp { background-color: #050b14; color: #e0e6ed; }
    
    /* Tarjetas con efecto neón */
    .card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .vencido { border-right: 5px solid #ff003c; border-left: 5px solid #ff003c; box-shadow: inset 0 0 10px #ff003c33; }
    .al-dia { border-right: 5px solid #00ff9d; border-left: 5px solid #00ff9d; box-shadow: inset 0 0 10px #00ff9d33; }
    
    /* Botones tecnológicos */
    .stButton>button {
        width: 100%;
        background: linear-gradient(45deg, #004e92, #000428);
        color: white;
        border: 1px solid #00d4ff;
        border-radius: 10px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { box-shadow: 0 0 20px #00d4ff; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE DATOS
TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def cargar_master():
    try:
        r = requests.get(URL, timeout=20)
        df = pd.read_excel(BytesIO(r.content), engine='openpyxl')
        # Limpieza de encabezados y basura
        df = df.dropna(subset=[df.columns[0]])
        return df
    except: return None

# 3. INTERFAZ DE MANDO
st.title("🛡️ COMMAND CENTER GUDMO 16")
df = cargar_master()

if df is not None:
    hoy = pd.Timestamp(date.today())
    
    # --- PANEL DE MÉTRICAS (GRÁFICAS RÁPIDAS) ---
    vencidos_total = []
    lista_final = []
    
    # Procesamiento previo para estadísticas
    for _, fila in df.iterrows():
        nombre = str(fila.iloc[0]).strip().upper()
        if "APELLIDOS" in nombre or nombre.replace('.','').isdigit(): continue
        
        vencido = False
        docs = []
        for tag, idx in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            f = pd.to_datetime(fila.iloc[idx], errors='coerce')
            if pd.notna(f) and f.year > 2000:
                is_v = f.date() <= hoy.date()
                if is_v: vencido = True
                docs.append({"tipo": tag, "fecha": f.date(), "status": is_v})
        
        if docs:
            item = {"nombre": nombre, "docs": docs, "vencido": vencido}
            lista_final.append(item)
            if vencido: vencidos_total.append(item)

    # Mostrar métricas arriba
    m1, m2, m3 = st.columns(3)
    m1.metric("TOTAL PERSONAL", len(lista_final))
    m2.metric("VENCIDOS", len(vencidos_total), delta=f"{len(vencidos_total)} ALERTAS", delta_color="inverse")
    m3.metric("AL DÍA", len(lista_final) - len(vencidos_total))

    # --- BUSCADOR Y FILTROS ---
    st.divider()
    busqueda = st.text_input("🔍 BUSCAR UNIFORMADO POR NOMBRE", placeholder="Ej: PEREZ...").upper()

    # --- PANTALLA DE TARJETAS ---
    c1, c2 = st.columns(2)
    idx_col = 0
    
    for persona in lista_final:
        if busqueda and busqueda not in persona["nombre"]: continue
        
        clase = "vencido" if persona["vencido"] else "al-dia"
        emoji = "⚠️" if persona["vencido"] else "✅"
        
        with (c1 if idx_col % 2 == 0 else c2):
            html = f'<div class="card {clase}"><b>{emoji} {persona["nombre"]}</b><br><hr style="opacity:0.1">'
            for d in persona["docs"]:
                color = "#ff003c" if d["status"] else "#00ff9d"
                html += f'<span style="color:{color}">• {d["tipo"]}: {d["fecha"]}</span><br>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
        idx_col += 1

    # --- PANEL DE TELEGRAM ---
    st.sidebar.title("📤 REPORTE OFICIAL")
    if st.sidebar.button("ENVIAR A TELEGRAM"):
        msg = f"🚨 *GUDMO 16: CONTROL DE VENCIMIENTOS*\n📅 *Fecha:* {hoy.date()}\n\n"
        if vencidos_total:
            for v in vencidos_total:
                msg += f"👤 *{v['nombre']}*\n"
                for d in v['docs']:
                    if d['status']: msg += f" ❌ {d['tipo']}: {d['fecha']}\n"
                msg += "\n"
        else:
            msg += "✅ TODO EL PERSONAL SE ENCUENTRA AL DÍA."
        
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        st.sidebar.success("¡Enviado!")
        st.balloons()

else:
    st.error("SIN ACCESO A LA MATRIZ. REVISA EL ENLACE.")
    
