import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

st.set_page_config(page_title="Control Documentos", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

TELEGRAM_TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

# ---------------- CARGA ROBUSTA ----------------
def cargar_datos():
    try:
        response = requests.get(EXCEL_URL, timeout=20)

        # 🔥 DEBUG CLAVE
        st.write("Status code:", response.status_code)
        st.write("Content-Type:", response.headers.get("Content-Type"))

        if "html" in response.headers.get("Content-Type", ""):
            st.error("❌ SharePoint está devolviendo una página web, no el Excel.")
            st.info("👉 Debes configurar el archivo como 'Cualquiera con el enlace puede ver'")
            return pd.DataFrame()

        file = BytesIO(response.content)

        df = pd.read_excel(file, engine="openpyxl")

        st.success("✅ Excel cargado correctamente")

        # Ver columnas reales
        st.write("Columnas detectadas:", df.columns.tolist())

        # Intentar seleccionar columnas correctas
        columnas = [c.lower() for c in df.columns]

        nombre_col = next((c for c in df.columns if "nombre" in c.lower()), None)
        lic_col = next((c for c in df.columns if "licencia" in c.lower()), None)
        tec_col = next((c for c in df.columns if "tecno" in c.lower()), None)
        soat_col = next((c for c in df.columns if "soat" in c.lower()), None)

        if not all([nombre_col, lic_col, tec_col, soat_col]):
            st.error("❌ No se encontraron las columnas necesarias")
            return pd.DataFrame()

        df = df[[nombre_col, lic_col, tec_col, soat_col]].copy()
        df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

        for col in ["Licencia", "Tecnomecanica", "SOAT"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        df = df.dropna(subset=["Nombre"])

        return df

    except Exception as e:
        st.error(f"🔥 Error real: {e}")
        return pd.DataFrame()

df = cargar_datos()

# ---------------- LÓGICA ----------------
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
col1.metric("Total Personal", total)

st.markdown("## 📋 Estado de Documentos")

for _, row in df.iterrows():
    lic_e, lic_c = estado(row["Licencia"])
    tec_e, tec_c = estado(row["Tecnomecanica"])
    soa_e, soa_c = estado(row["SOAT"])

    if "VENCIDO" in [lic_e, tec_e, soa_e]:
        total_vencidos += 1
        vencidos.append(row["Nombre"])

    st.markdown(f"""
    <div style="background:#1e1e1e;padding:15px;border-radius:10px;margin-bottom:10px">
        <b>{row['Nombre']}</b><br>
        <span style="color:{lic_c}">Licencia: {lic_e}</span><br>
        <span style="color:{tec_c}">Tecnomecánica: {tec_e}</span><br>
        <span style="color:{soa_c}">SOAT: {soa_e}</span>
    </div>
    """, unsafe_allow_html=True)

col2.metric("Vencidos", total_vencidos)
col3.metric("Al Día", total - total_vencidos)

# ---------------- TELEGRAM ----------------
def enviar_telegram(lista):
    if not lista:
        return False, "No hay vencidos"

    mensaje = "*🚨 DOCUMENTOS VENCIDOS*\n\n"
    for nombre in lista:
        mensaje += f"- {nombre}\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    r = requests.post(url, data=payload)
    return r.json()

if st.button("📩 Enviar reporte a Telegram"):
    resp = enviar_telegram(vencidos)
    st.write(resp)
