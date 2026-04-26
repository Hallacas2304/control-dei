import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Sistema DEI", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

# 🔐 SEGURIDAD
TELEGRAM_TOKEN = st.secrets.get("TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Acceso")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user == "admin" and password == "1234":
            st.session_state["login"] = True
        else:
            st.error("Credenciales incorrectas")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ---------------- CARGA ----------------
@st.cache_data(ttl=300)
def cargar():
    r = requests.get(EXCEL_URL, timeout=20)
    r.raise_for_status()

    file = BytesIO(r.content)
    df = pd.read_excel(file, engine="openpyxl")

    # detectar columnas automáticamente
    nombre = next(c for c in df.columns if "nombre" in c.lower())
    licencia = next(c for c in df.columns if "licencia" in c.lower())
    tecno = next(c for c in df.columns if "tecno" in c.lower())
    soat = next(c for c in df.columns if "soat" in c.lower())

    df = df[[nombre, licencia, tecno, soat]].copy()
    df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

    for col in ["Licencia", "Tecnomecanica", "SOAT"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df.dropna(subset=["Nombre"])

df = cargar()
hoy = date.today()

# ---------------- SIDEBAR ----------------
menu = st.sidebar.radio("Menú", ["Dashboard", "Vencidos", "Exportar", "Configuración"])

# ---------------- FUNCIONES ----------------
def estado(fecha, dias_alerta=5):
    if pd.isna(fecha):
        return "SIN DATO"
    dias = (fecha.date() - hoy).days
    if dias < 0:
        return "VENCIDO"
    elif dias <= dias_alerta:
        return f"VENCE EN {dias} DÍAS"
    return "AL DÍA"

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Panel General")

    total = len(df)

    vencidos = df[
        (df["Licencia"].dt.date <= hoy) |
        (df["Tecnomecanica"].dt.date <= hoy) |
        (df["SOAT"].dt.date <= hoy)
    ]

    col1, col2 = st.columns(2)
    col1.metric("Total Personal", total)
    col2.metric("Total Vencidos", len(vencidos))

    st.dataframe(df)

# ---------------- VENCIDOS ----------------
if menu == "Vencidos":
    st.title("🚨 Documentos Vencidos")

    vencidos = df[
        (df["Licencia"].dt.date <= hoy) |
        (df["Tecnomecanica"].dt.date <= hoy) |
        (df["SOAT"].dt.date <= hoy)
    ]

    busqueda = st.text_input("🔍 Buscar")

    if busqueda:
        vencidos = vencidos[vencidos["Nombre"].str.contains(busqueda, case=False)]

    st.dataframe(vencidos)

# ---------------- EXPORTAR ----------------
if menu == "Exportar":
    st.title("📥 Exportar Datos")

    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button(
        "Descargar Excel",
        data=output,
        file_name="reporte.xlsx"
    )

# ---------------- TELEGRAM ----------------
def enviar():
    if not TELEGRAM_TOKEN:
        st.warning("Configura TOKEN en secrets")
        return

    vencidos = df[
        (df["Licencia"].dt.date <= hoy) |
        (df["Tecnomecanica"].dt.date <= hoy) |
        (df["SOAT"].dt.date <= hoy)
    ]

    lista = vencidos["Nombre"].tolist()

    mensaje = "*🚨 REPORTE DE VENCIDOS*\n\n"
    mensaje += "\n".join(f"- {n}" for n in lista)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    })

# ---------------- CONFIG ----------------
if menu == "Configuración":
    st.title("⚙️ Configuración")

    if st.button("📩 Enviar reporte ahora"):
        enviar()
        st.success("Reporte enviado")

# ---------------- AUTO ENVÍO DIARIO ----------------
if "ultimo_envio" not in st.session_state:
    st.session_state["ultimo_envio"] = ""

if st.session_state["ultimo_envio"] != str(hoy):
    enviar()
    st.session_state["ultimo_envio"] = str(hoy)
