import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Control Documentos", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

TELEGRAM_TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

# ---------------- ESTILO OSCURO ----------------
st.markdown("""
    <style>
    body {background-color: #0e1117; color: white;}
    </style>
""", unsafe_allow_html=True)

# ---------------- CARGA DE DATOS ----------------
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        response = requests.get(EXCEL_URL, timeout=20)
        response.raise_for_status()

        file = BytesIO(response.content)
        df = pd.read_excel(file, engine="openpyxl")

        # Validar columnas
        if df.shape[1] < 4:
            st.error("El archivo no tiene al menos 4 columnas válidas.")
            return pd.DataFrame()

        # Tomar solo columnas necesarias
        df = df.iloc[:, :4].copy()
        df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

        # Limpiar datos
        df = df.dropna(subset=["Nombre"])
        df = df[df["Nombre"].astype(str).str.len() > 5]

        # Convertir fechas
        for col in ["Licencia", "Tecnomecanica", "SOAT"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

# ---------------- PROCESAMIENTO ----------------
hoy = date.today()

def estado(fecha):
    if pd.isna(fecha):
        return "SIN DATO", "gray"
    if fecha.date() <= hoy:
        return "VENCIDO", "red"
    return "AL DÍA", "green"

vencidos = []
total_vencidos = 0

# ---------------- MÉTRICAS ----------------
total = len(df)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Personal", total)

# ---------------- TARJETAS ----------------
st.markdown("## 📋 Estado de Documentos")

for _, row in df.iterrows():
    licencia_estado, licencia_color = estado(row["Licencia"])
    tecno_estado, tecno_color = estado(row["Tecnomecanica"])
    soat_estado, soat_color = estado(row["SOAT"])

    if "VENCIDO" in [licencia_estado, tecno_estado, soat_estado]:
        total_vencidos += 1
        vencidos.append(row["Nombre"])

    st.markdown(f"""
    <div style="background-color:#1e1e1e;padding:15px;border-radius:10px;margin-bottom:10px">
        <h4 style="color:white">{row['Nombre']}</h4>
        <p style="color:{licencia_color}">Licencia: {licencia_estado}</p>
        <p style="color:{tecno_color}">Tecnomecánica: {tecno_estado}</p>
        <p style="color:{soat_color}">SOAT: {soat_estado}</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- MÉTRICAS FINALES ----------------
with col2:
    st.metric("Vencidos", total_vencidos)

with col3:
    st.metric("Al Día", total - total_vencidos)

# ---------------- TELEGRAM ----------------
def enviar_telegram(lista):
    if not lista:
        return 200

    mensaje = "*🚨 DOCUMENTOS VENCIDOS*\n\n"
    for nombre in lista:
        mensaje += f"- {nombre}\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code
    except:
        return 500

# ---------------- BOTÓN ----------------
if st.button("📩 Enviar reporte a Telegram"):
    resultado = enviar_telegram(vencidos)

    if resultado == 200:
        st.success("Reporte enviado correctamente ✅")
    else:
        st.error("Error enviando el reporte ❌")
