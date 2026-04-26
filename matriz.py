import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

st.set_page_config(page_title="Control Documentos", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQCCZGsB1iWWSJAoFXkDTUhbAUamuiPdwJbuvD4YBw37ubc?download=1"

TELEGRAM_TOKEN = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

# ---------------- CARGA ROBUSTA ----------------
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        response = requests.get(EXCEL_URL, timeout=20)
        response.raise_for_status()

        file = BytesIO(response.content)

        # Leer sin asumir encabezado
        df = pd.read_excel(file, engine="openpyxl", header=None)

        # Buscar fila donde empiezan los nombres (heurística)
        inicio = None
        for i, row in df.iterrows():
            if isinstance(row[0], str) and len(row[0]) > 5:
                inicio = i
                break

        if inicio is None:
            st.error("No se encontró inicio de datos válido")
            return pd.DataFrame()

        df = df.iloc[inicio:, :4].copy()
        df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

        # Limpiar
        df = df.dropna(subset=["Nombre"])
        df = df[df["Nombre"].astype(str).str.len() > 5]

        # Convertir fechas correctamente
        for col in ["Licencia", "Tecnomecanica", "SOAT"]:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        return df

    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

# DEBUG (puedes quitar luego)
with st.expander("🔍 Ver datos cargados"):
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
    <div style="background:#1e1e1e;padding:15px;border-radius:10px;margin-bottom:10px">
        <b>{row['Nombre']}</b><br>
        <span style="color:{lic_c}">Licencia: {lic_e}</span><br>
        <span style="color:{tec_c}">Tecnomecánica: {tec_e}</span><br>
        <span style="color:{soa_c}">SOAT: {soa_e}</span>
    </div>
    """, unsafe_allow_html=True)

col2.metric("Vencidos", total_vencidos)
col3.metric("Al Día", total - total_vencidos)

# ---------------- TELEGRAM REAL ----------------
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
