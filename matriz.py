import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control", layout="wide", initial_sidebar_state="collapsed")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

TELEGRAM_TOKEN = st.secrets.get("TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

hoy = date.today()

# ---------------- ESTILO ----------------
st.markdown("""
<style>
html, body {background-color:#0f172a;color:white;}
.card {background:#1e293b;padding:15px;border-radius:15px;margin-bottom:10px;}
.rojo {color:#ef4444;font-weight:bold;}
.amarillo {color:#f59e0b;font-weight:bold;}
.verde {color:#22c55e;font-weight:bold;}
#MainMenu, footer, header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data(ttl=300)
def cargar():
    r = requests.get(EXCEL_URL, timeout=20)
    r.raise_for_status()

    df = pd.read_excel(BytesIO(r.content), engine="openpyxl")

    df.columns = df.columns.str.strip().str.lower()

    nombre = next((c for c in df.columns if "nombre" in c), None)
    licencia = next((c for c in df.columns if "licencia" in c), None)
    tecno = next((c for c in df.columns if "tecno" in c), None)
    soat = next((c for c in df.columns if "soat" in c), None)

    df = df[[nombre, licencia, tecno, soat]]
    df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

    for col in df.columns[1:]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df.dropna(subset=["Nombre"])

df = cargar()

# ---------------- FUNCIONES ----------------
def evaluar(fecha):
    if pd.isna(fecha):
        return "VACÍO", "amarillo"
    dias = (fecha.date() - hoy).days
    if dias < 0:
        return "VENCIDO", "rojo"
    elif dias <= 5:
        return f"{dias} días", "amarillo"
    return "AL DÍA", "verde"

# ---------------- TELEGRAM FIX ----------------
def enviar_telegram(lista):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "TOKEN o CHAT_ID no configurados"

    if not lista:
        return False, "No hay datos para enviar"

    mensaje = "*🚨 DOCUMENTOS VENCIDOS*\n\n"
    mensaje += "\n".join(f"- {x}" for x in lista)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        })

        if r.status_code == 200:
            return True, "Mensaje enviado correctamente"
        else:
            return False, r.text

    except Exception as e:
        return False, str(e)

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Editar", "⚙️ Ajustes"], horizontal=True)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":

    st.title("🚓 Control Documental")

    vencidos_lista = []

    for _, row in df.iterrows():
        lic_e, lic_c = evaluar(row["Licencia"])
        tec_e, tec_c = evaluar(row["Tecnomecanica"])
        soa_e, soa_c = evaluar(row["SOAT"])

        docs = []
        if "VENCIDO" in lic_e: docs.append("Licencia")
        if "VENCIDO" in tec_e: docs.append("Tecnomecánica")
        if "VENCIDO" in soa_e: docs.append("SOAT")

        if docs:
            vencidos_lista.append(f"{row['Nombre']} → {', '.join(docs)}")

        st.markdown(f"""
        <div class="card">
            <span class="{lic_c}"><b>{row['Nombre']}</b></span><br>
            Licencia: <span class="{lic_c}">{lic_e}</span><br>
            Tecnomecánica: <span class="{tec_c}">{tec_e}</span><br>
            SOAT: <span class="{soa_c}">{soa_e}</span>
        </div>
        """, unsafe_allow_html=True)

# ---------------- ALERTAS ----------------
if menu == "🚨 Alertas":
    st.tabs(["SOAT", "Tecno", "Licencia"])

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":
    st.bar_chart(pd.DataFrame({
        "Tipo":["SOAT","Tecno","Licencia"],
        "Cantidad":[
            len(df[df["SOAT"].dt.date <= hoy]),
            len(df[df["Tecnomecanica"].dt.date <= hoy]),
            len(df[df["Licencia"].dt.date <= hoy])
        ]
    }).set_index("Tipo"))

# ---------------- EDITAR ----------------
if menu == "✍️ Editar":
    edit = st.data_editor(df)
    buffer = BytesIO()
    edit.to_excel(buffer, index=False)
    st.download_button("Descargar Excel", buffer.getvalue(), "editado.xlsx")

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":

    st.subheader("📩 Telegram")

    if st.button("Enviar reporte completo"):
        lista = []

        for _, row in df.iterrows():
            docs = []

            if pd.notna(row["Licencia"]) and row["Licencia"].date() <= hoy:
                docs.append("Licencia")
            if pd.notna(row["Tecnomecanica"]) and row["Tecnomecanica"].date() <= hoy:
                docs.append("Tecnomecánica")
            if pd.notna(row["SOAT"]) and row["SOAT"].date() <= hoy:
                docs.append("SOAT")

            if docs:
                lista.append(f"{row['Nombre']} → {', '.join(docs)}")

        ok, msg = enviar_telegram(lista)

        if ok:
            st.success(msg)
        else:
            st.error(f"❌ Error Telegram: {msg}")
