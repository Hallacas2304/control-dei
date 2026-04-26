import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

st.set_page_config(page_title="Control DEI", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

TELEGRAM_TOKEN = st.secrets.get("TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

# ---------------- ESTILO ----------------
st.markdown("""
<style>
.card {
    background: #1e293b;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
}
.rojo { color: #ef4444; font-weight: bold; }
.amarillo { color: #f59e0b; font-weight: bold; }
.verde { color: #22c55e; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data
def cargar():
    r = requests.get(EXCEL_URL)
    file = BytesIO(r.content)
    df = pd.read_excel(file, engine="openpyxl")

    nombre = next(c for c in df.columns if "nombre" in c.lower())
    licencia = next(c for c in df.columns if "licencia" in c.lower())
    tecno = next(c for c in df.columns if "tecno" in c.lower())
    soat = next(c for c in df.columns if "soat" in c.lower())

    df = df[[nombre, licencia, tecno, soat]]
    df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

    for col in ["Licencia", "Tecnomecanica", "SOAT"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df.dropna(subset=["Nombre"])

df = cargar()
hoy = date.today()

# ---------------- FUNCIÓN ESTADO ----------------
def evaluar(fecha):
    if pd.isna(fecha):
        return "SIN DATO", "amarillo"

    dias = (fecha.date() - hoy).days

    if dias < 0:
        return "VENCIDO", "rojo"
    elif dias <= 5:
        return f"VENCE EN {dias} DÍAS", "amarillo"
    else:
        return "AL DÍA", "verde"

# ---------------- UI ----------------
st.title("🚓 Control de Documentos")

total = len(df)
vencidos_total = 0

col1, col2 = st.columns(2)
col1.metric("Total Personal", total)

# ---------------- TARJETAS ----------------
vencidos_lista = []

for _, row in df.iterrows():
    lic_e, lic_c = evaluar(row["Licencia"])
    tec_e, tec_c = evaluar(row["Tecnomecanica"])
    soa_e, soa_c = evaluar(row["SOAT"])

    docs_vencidos = []

    if "VENCIDO" in lic_e:
        docs_vencidos.append("Licencia")
    if "VENCIDO" in tec_e:
        docs_vencidos.append("Tecnomecánica")
    if "VENCIDO" in soa_e:
        docs_vencidos.append("SOAT")

    if docs_vencidos:
        vencidos_total += 1
        vencidos_lista.append(f"{row['Nombre']} → {', '.join(docs_vencidos)}")

    st.markdown(f"""
    <div class="card">
        <b>{row['Nombre']}</b><br>
        Licencia: <span class="{lic_c}">{lic_e}</span><br>
        Tecnomecánica: <span class="{tec_c}">{tec_e}</span><br>
        SOAT: <span class="{soa_c}">{soa_e}</span>
    </div>
    """, unsafe_allow_html=True)

col2.metric("🚨 Vencidos", vencidos_total)

# ---------------- ALERTA GENERAL ----------------
if vencidos_total > 0:
    st.error(f"⚠️ Hay {vencidos_total} funcionarios con documentos vencidos")

# ---------------- TELEGRAM ----------------
def enviar():
    if not TELEGRAM_TOKEN:
        st.warning("Falta configurar Telegram")
        return

    if not vencidos_lista:
        st.info("No hay vencidos para enviar")
        return

    mensaje = "*🚨 DOCUMENTOS VENCIDOS*\n\n"
    mensaje += "\n".join(f"- {n}" for n in vencidos_lista)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    })

# ---------------- BOTÓN ----------------
if st.button("📩 Enviar reporte a Telegram"):
    enviar()
    st.success("Reporte enviado")
