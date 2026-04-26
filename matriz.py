import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="GUDMO 16 - CONTROL FINAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    .card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 6px solid; background: #161b22; }
    .vencido { border-left-color: #ff4b4b; background: #3d0808; }
    .al-dia { border-left-color: #00ff6a; background: #082d16; }
    </style>
    """, unsafe_allow_html=True)

# NUEVO ENLACE DE EXCEL CORREGIDO (:x:)
URL_MAESTRA = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

@st.cache_data(ttl=1)
def cargar_datos_v3():
    try:
        r = requests.get(URL_MAESTRA, timeout=25)
        # Al ser un :x:, openpyxl lo leerá perfectamente
        return pd.read_excel(BytesIO(r.content), engine='openpyxl')
    except Exception as e:
        st.error(f"Error al conectar con la nueva matriz: {e}")
        return None

st.title("🛡️ PANEL DE CONTROL GUDMO 16")
df = cargar_datos_v3()

if df is not None:
    hoy = pd.Timestamp(date.today())
    st.info(f"✅ Matriz cargada correctamente. Fecha de hoy: {hoy.date()}")

    col1, col2 = st.columns(2)
    encontrados = 0

    for i in range(len(df)):
        fila = df.iloc[i]
        # Columna A: Nombres
        nombre = str(fila.iloc[0]).strip().upper()
        
        if len(nombre) < 5 or "NAN" in nombre or "APELLIDOS" in nombre:
            continue
        
        encontrados += 1
        vencido = False
        resumen_docs = []
        
        # Columnas B(1), C(2), D(3)
        misiones = [("LICENCIA", 1), ("TECNOMECÁNICA", 2), ("SOAT", 3)]
        
        for tipo, col_idx in misiones:
            try:
                f = pd.to_datetime(fila.iloc[col_idx], errors='coerce')
                if pd.notna(f) and 2024 < f.year < 2035:
                    if f.date() <= hoy.date():
                        vencido = True
                        status = "🔴 VENCIDO"
                    else:
                        status = "🟢 AL DÍA"
                    resumen_docs.append(f"• {tipo}: {f.date()} {status}")
            except: continue

        # Mostrar en tarjetas
        clase = "vencido" if vencido else "al-dia"
        card_html = f'<div class="card {clase}"><b>👤 {nombre}</b><br>{"<br>".join(resumen_docs)}</div>'
        
        if encontrados % 2 != 0: col1.markdown(card_html, unsafe_allow_html=True)
        else: col2.markdown(card_html, unsafe_allow_html=True)

    if encontrados == 0:
        st.warning("⚠️ No se encontraron funcionarios registrados en la primera columna del archivo.")

else:
    st.error("No se pudo procesar el archivo. Revisa que el link de SharePoint siga activo.")
    
