import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Control Documentos", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

TELEGRAM_TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

# ---------------- ESTILO OSCURO ----------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.card {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
def cargar_datos():
    try:
        response = requests.get(EXCEL_URL, timeout=20)
        response.raise_for_status()

        file = BytesIO(response.content)
        df = pd.read_excel(file, engine="openpyxl")

        df = df[["Nombre", "Licencia", "Tecnomecanica", "SOAT"]]

        for col in ["Licencia", "Tecnomecanica", "SOAT"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        df = df.dropna(subset=["Nombre"])

        return df

    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return pd.DataFrame()

df = cargar_datos()

# DEBUG opcional
with st.expander("🔍 Ver datos"):
    st.dataframe(df)

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

# ---------------- UI ----------------
st.markdown("## 📋 Estado de Documentos")

for _, row in df.iterrows():
    lic_e, lic_c = estado(row["Licencia"])
    tec_e, tec_c = estado(row["Tecnomecanica"])
    soa_e, soa_c = estado(row["SOAT"])

    if "VENCIDO" in [lic_e, tec_e, soa_e]:
        total_vencidos += 1
        vencidos.append(row["Nombre"])

    st.markdown(f"""
    <div class="card">
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
        return False, "No hay documentos vencidos"

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
        respuesta = r.json()

        if respuesta.get("ok"):
            return True, "Enviado correctamente"
        else:
            return False, str(respuesta)

    except Exception as e:
        return False, str(e)

# ---------------- BOTÓN ----------------
if st.button("📩 Enviar reporte a Telegram"):
    ok, msg = enviar_telegram(vencidos)

    if ok:
        st.success("Reporte enviado correctamente ✅")
    else:
        st.error(f"Error: {msg}")
