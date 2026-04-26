import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# 1. ESTILO PROFESIONAL (Directo y sin adornos extra)
st.set_page_config(page_title="GUDMO 16 - MANDO TOTAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: white; }
    .card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 6px solid; background: #1c2128; }
    .vencido { border-left-color: #ff4b4b; background: #3d0a0a; }
    .al-dia { border-left-color: #00ff6a; background: #0a2d1a; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONFIGURACIÓN DE DATOS (El link :x: que ya sabemos que abre)
TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"
URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def cargar_matriz_maestra():
    try:
        r = requests.get(URL, timeout=20)
        # Cargamos el Excel y quitamos filas totalmente vacías
        df = pd.read_excel(BytesIO(r.content), engine='openpyxl')
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

# 3. LÓGICA DE PROCESAMIENTO
st.title("🛡️ CONSOLA DE MANDO GUDMO 16")
df = cargar_matriz_maestra()

if df is not None:
    hoy = pd.Timestamp(date.today())
    st.success(f"✅ Sistema Sincronizado | {hoy.date()}")
    
    vencidos_para_telegram = []
    col1, col2 = st.columns(2)
    contador_real = 0

    for i in range(len(df)):
        fila = df.iloc[i]
        # Tomamos el nombre (Columna A)
        nombre = str(fila.iloc[0]).strip().upper()
        
        # FILTRO DEFINITIVO: Solo procesar si el nombre NO es un número y NO está vacío
        if nombre in ["NAN", "NONE", ""] or nombre.replace('.','').isdigit() or "APELLIDOS" in nombre:
            continue

        alertas = []
        esta_vencido = False
        
        # Revisión de Licencia (B), Tecno (C), SOAT (D)
        for etiqueta, idx in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            try:
                f_val = pd.to_datetime(fila.iloc[idx], errors='coerce')
                if pd.notna(f_val) and f_val.year > 2020:
                    status = "🔴 VENCIDO" if f_val.date() <= hoy.date() else "🟢 AL DÍA"
                    if f_val.date() <= hoy.date(): esta_vencido = True
                    alertas.append(f"• {etiqueta}: {f_val.date()} {status}")
            except: continue

        # Mostrar tarjetas solo si encontramos
        
