import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# 1. ESTILO DE ALTA TECNOLOGÍA (Neon Ops)
st.set_page_config(page_title="GUDMO 16 - ELITE", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #050b14; color: #e0e6ed; }
    .card {
        padding: 15px; border-radius: 12px; margin-bottom: 10px;
        background: rgba(255, 255, 255, 0.03);
        border-left: 8px solid;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    .vencido { border-left-color: #ff003c; }
    .al-dia { border-left-color: #00ff9d; }
    .stMetric { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def cargar_datos_seguros():
    try:
        r = requests.get(URL, timeout=20)
        # Cargamos todo el excel sin filtros iniciales para no perder nada
        df = pd.read_excel(BytesIO(r.content), engine='openpyxl')
        return df
    except: return None

# 2. PROCESAMIENTO DE DATOS
df = cargar_datos_seguros()

if df is not None:
    hoy = pd.Timestamp(date.today())
    
    # Lista limpia de personal
    personal_valido = []
    vencidos_conteo = 0

    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[0]).strip().upper()
        
        # Saltamos lo que obviamente no es un nombre
        if nombre in ["NAN", "NONE", ""] or nombre.replace('.','').isdigit() or "APELLIDOS" in nombre:
            continue
            
        alertas = []
        esta_vencido = False
        
        # Revisamos B(1), C(2) y D(3)
        for tag, idx in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            try:
                f_val = pd.to_datetime(fila.iloc[idx], errors='coerce')
                if pd.notna(f_val) and f_val.year > 2000:
                    vence = f_val.date()
                    vencido_doc = vence <= hoy.date()
                    if vencido_doc: esta_vencido = True
                    alertas.append({"tipo": tag, "fecha": vence, "vencido": vencido_doc})
            except: continue
        
        # Solo agregamos si logramos leer al menos una fecha o nombre
        personal_valido.append({"nombre": nombre, "docs": alertas, "es_vencido": esta_vencido})
        if esta_vencido: vencidos_conteo += 1

    # 3. INTERFAZ VISUAL
    st.title("🛡️ COMMAND CENTER GUDMO 16")
    
    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("UNIFORMADOS", len(personal_valido))
    c2.metric("VENCIDOS", vencidos_conteo, delta=f"{vencidos_conteo} ALERTAS", delta_color="inverse")
    c3.metric("AL DÍA", len(personal_valido) - vencidos_conteo)

    st.divider()
    
    # Buscador
    busqueda = st.text_input("🔍 FILTRAR POR NOMBRE O APELLIDO").upper()

    # Tarjetas
    col_izq, col_der = st.columns(2)
    mostrados = 0

    for p in personal_valido:
        if busqueda and busqueda not in p["nombre"]: continue
        
        mostrados += 1
        clase = "vencido" if p["es_vencido"] else "al-dia"
        emoji = "🔴" if p["es_vencido"] else "🟢"
        
        with (col_izq if mostrados % 2 != 0 else col_der):
            html = f'<div class="card {clase}"><b>{emoji} {p["nombre"]}</b><br>'
            for d in p["docs"]:
                color = "#ff4b4b" if d["vencido"] else "#00ff9d"
                html += f'<span style="color:{color}">• {d["tipo"]}: {d["fecha"]}</span><br>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    # 4. BOTÓN TELEGRAM (SIEMPRE DISPONIBLE)
    st.sidebar.title("📤 REPORTE")
    if st.sidebar.button("🚀 ENVIAR A TELEGRAM"):
        txt = f"🚨 *GUDMO 16: CONTROL DE VENCIMIENTOS*\n📅 *Fecha:* {hoy.date()}\n\n"
        hay_rojos = False
        for p in personal_valido:
            if p["es_vencido"]:
                hay_rojos = True
                txt += f"👤 *{p['nombre']}*\n"
                for d in p["docs"]:
                    if d["vencido"]: txt += f"  ❌ {d['tipo']}: {d['fecha']}\n"
                txt += "\n"
        
        if not hay_rojos: txt += "✅ TODO EL PERSONAL AL DÍA."
        
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": txt, "parse_mode": "Markdown"})
        st.sidebar.success("Enviado al grupo")
        st.balloons()

    if mostrados == 0 and len(personal_valido) > 0:
        st.info("No se encontraron resultados para esa búsqueda.")
else:
    st.error("❌ ERROR CRÍTICO DE CONEXIÓN CON EL EXCEL.")
    
