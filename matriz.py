import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

st.set_page_config(page_title="GUDMO 16 - SOLUCIÓN ERROR", layout="wide")

# Estilos visuales
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 6px solid; }
    .vencido { background: #4b0000; border-left-color: #ff4b4b; }
    .al-dia { background: #002b11; border-left-color: #00ff6a; }
    </style>
    """, unsafe_allow_html=True)

# NUEVO ENLACE CORREGIDO PARA DESCARGA
# Cambiamos manualmente el final para forzar la descarga del flujo de datos
URL_NUEVA = "https://correopoliciagov-my.sharepoint.com/:b:/g/personal/omar_vela3592_correo_policia_gov_co/IQD5eis7_cTVT5c9UHKbOte4ASqE0VAREktQMYFfmjzohwE?download=1"

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        r = requests.get(URL_NUEVA, timeout=30)
        # Si el archivo viene con error de "zip", intentamos cargarlo ignorando el motor predeterminado
        return pd.read_excel(BytesIO(r.content))
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

st.title("🛡️ CONTROL GUDMO 16")
df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    encontrados = 0
    
    col1, col2 = st.columns(2)
    
    for i in range(len(df)):
        fila = df.iloc[i]
        nombre = str(fila.iloc[0]).strip().upper()
        
        if len(nombre) < 5 or "NAN" in nombre: continue
        encontrados += 1
        
        # Procesar fechas (B=1, C=2, D=3)
        vencido = False
        info_docs = []
        for tipo, col in [("LICENCIA", 1), ("TECNO", 2), ("SOAT", 3)]:
            f = pd.to_datetime(fila.iloc[col], errors='coerce')
            if pd.notna(f):
                status = "🔴" if f.date() <= hoy.date() else "🟢"
                if f.date() <= hoy.date(): vencido = True
                info_docs.append(f"{status} {tipo}: {f.date()}")
        
        # Mostrar tarjeta
        clase = "vencido" if vencido else "al-dia"
        txt_html = f'<div class="card {clase}"><b>{nombre}</b><br>{"<br>".join(info_docs)}</div>'
        
        if i % 2 == 0: col1.markdown(txt_html, unsafe_allow_html=True)
        else: col2.markdown(txt_html, unsafe_allow_html=True)

    if encontrados == 0:
        st.warning("No se detectaron datos en las columnas. Verifica que el archivo no sea un PDF.")
        
