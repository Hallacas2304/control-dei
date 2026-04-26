import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Sistema DEI", layout="wide")

EXCEL_URL = "TU_LINK"

# 🔐 secretos
TELEGRAM_TOKEN = st.secrets["TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Acceso al Sistema")

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
    r = requests.get(EXCEL_URL)
    file = BytesIO(r.content)
    df = pd.read_excel(file, engine="openpyxl")

    df = df[[
        next(c for c in df.columns if "nombre" in c.lower()),
        next(c for c in df.columns if "licencia" in c.lower()),
        next(c for c in df.columns if "tecno" in c.lower()),
        next(c for c in df.columns if "soat" in c.lower())
    ]]

    df.columns = ["Nombre","Licencia","Tecnomecanica","SOAT"]

    for col in df.columns[1:]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

df = cargar()

hoy = date.today()

# ---------------- SIDEBAR ----------------
menu = st.sidebar.selectbox("Menú", ["Dashboard", "Reportes", "Configuración"])

# ---------------- LÓGICA ----------------
def vencido(fecha):
    return pd.notna(fecha) and fecha.date() <= hoy

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("🚓 Control Documental")

    vencidos = df[
        df["Licencia"].apply(vencido) |
        df["Tecnomecanica"].apply(vencido) |
        df["SOAT"].apply(vencido)
    ]

    col1, col2 = st.columns(2)
    col1.metric("Total", len(df))
    col2.metric("Vencidos", len(vencidos))

    st.dataframe(vencidos)

# ---------------- PDF ----------------
def generar_pdf(lista):
    doc = SimpleDocTemplate("reporte.pdf")
    styles = getSampleStyleSheet()

    content = [Paragraph("REPORTE DE DOCUMENTOS VENCIDOS", styles["Title"])]

    for nombre in lista:
        content.append(Paragraph(nombre, styles["Normal"]))

    doc.build(content)

    with open("reporte.pdf", "rb") as f:
        return f.read()

# ---------------- REPORTES ----------------
if menu == "Reportes":
    st.title("📄 Reportes")

    vencidos = df[
        df["Licencia"].apply(vencido) |
        df["Tecnomecanica"].apply(vencido) |
        df["SOAT"].apply(vencido)
    ]

    lista = vencidos["Nombre"].tolist()

    if st.button("📥 Descargar PDF"):
        pdf = generar_pdf(lista)
        st.download_button("Descargar", pdf, file_name="reporte.pdf")

# ---------------- TELEGRAM ----------------
def enviar(lista):
    mensaje = "*🚨 REPORTE OFICIAL*\n\n"
    mensaje += "\n".join(f"- {n}" for n in lista)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    })

if menu == "Configuración":
    st.title("⚙️ Configuración")

    if st.button("📩 Enviar reporte ahora"):
        lista = df["Nombre"].tolist()
        enviar(lista)
        st.success("Enviado")
