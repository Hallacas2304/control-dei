import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Sistema DEI", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

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

    nombre = next(c for c in df.columns if "nombre" in c.lower())
    licencia = next(c for c in df.columns if "licencia" in c.lower())
    tecno = next(c for c in df.columns if "tecno" in c.lower())
    soat = next(c for c in df.columns if "soat" in c.lower())
    comunicado = next((c for c in df.columns if "comunicado" in c.lower()), None)

    cols = [nombre, licencia, tecno, soat]
    if comunicado:
        cols.append(comunicado)

    df = df[cols].copy()
    df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"] + (["Comunicado"] if comunicado else [])

    for col in ["Licencia", "Tecnomecanica", "SOAT"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df.dropna(subset=["Nombre"])

df = cargar()
hoy = date.today()

# ---------------- MENÚ ----------------
menu = st.sidebar.radio(
    "Menú",
    ["Dashboard", "Vencidos", "Próximos", "Comunicados", "Exportar", "Configuración"]
)

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

# ---------------- VENCIDOS DETALLADOS ----------------
if menu == "Vencidos":
    st.title("🚨 Documentos Vencidos")

    registros = []

    for _, row in df.iterrows():
        docs = []

        if pd.notna(row["Licencia"]) and row["Licencia"].date() <= hoy:
            docs.append("Licencia")

        if pd.notna(row["Tecnomecanica"]) and row["Tecnomecanica"].date() <= hoy:
            docs.append("Tecnomecánica")

        if pd.notna(row["SOAT"]) and row["SOAT"].date() <= hoy:
            docs.append("SOAT")

        if docs:
            registros.append({
                "Nombre": row["Nombre"],
                "Documentos vencidos": ", ".join(docs)
            })

    vencidos_df = pd.DataFrame(registros)

    st.metric("Total vencidos", len(vencidos_df))

    busqueda = st.text_input("🔍 Buscar funcionario")

    if busqueda:
        vencidos_df = vencidos_df[vencidos_df["Nombre"].str.contains(busqueda, case=False)]

    st.dataframe(vencidos_df)

# ---------------- PRÓXIMOS ----------------
if menu == "Próximos":
    st.title("🟡 Próximos a Vencer")

    dias_alerta = 5

    proximos = df[
        ((df["Licencia"] - pd.Timestamp(hoy)).dt.days.between(0, dias_alerta)) |
        ((df["Tecnomecanica"] - pd.Timestamp(hoy)).dt.days.between(0, dias_alerta)) |
        ((df["SOAT"] - pd.Timestamp(hoy)).dt.days.between(0, dias_alerta))
    ]

    st.metric("Próximos a vencer", len(proximos))
    st.dataframe(proximos)

# ---------------- COMUNICADOS ----------------
if menu == "Comunicados":
    st.title("📄 Comunicados Oficiales")

    if "Comunicado" not in df.columns:
        st.warning("No existe columna de comunicados en el Excel")
    else:
        comunicados = df[
            df["Comunicado"].astype(str).str.strip().notna() &
            (df["Comunicado"].astype(str).str.lower() != "nan") &
            (df["Comunicado"].astype(str).str.strip() != "")
        ]

        st.metric("Total con comunicado", len(comunicados))
        st.dataframe(comunicados)

# ---------------- EXPORTAR ----------------
if menu == "Exportar":
    st.title("📥 Exportar Datos")

    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button("Descargar Excel", data=output, file_name="reporte.xlsx")

# ---------------- TELEGRAM ----------------
def enviar_personalizado(tipo):
    registros = []

    for _, row in df.iterrows():
        docs = []

        if pd.notna(row["Licencia"]) and row["Licencia"].date() <= hoy:
            docs.append("Licencia")

        if pd.notna(row["Tecnomecanica"]) and row["Tecnomecanica"].date() <= hoy:
            docs.append("Tecnomecánica")

        if pd.notna(row["SOAT"]) and row["SOAT"].date() <= hoy:
            docs.append("SOAT")

        if tipo == "Vencidos" and docs:
            registros.append(f"{row['Nombre']} → {', '.join(docs)}")

        elif tipo == "Próximos":
            dias_alerta = 5
            proximos = []

            for doc, fecha in [
                ("Licencia", row["Licencia"]),
                ("Tecnomecánica", row["Tecnomecanica"]),
                ("SOAT", row["SOAT"])
            ]:
                if pd.notna(fecha):
                    dias = (fecha.date() - hoy).days
                    if 0 <= dias <= dias_alerta:
                        proximos.append(f"{doc} ({dias} días)")

            if proximos:
                registros.append(f"{row['Nombre']} → {', '.join(proximos)}")

        elif tipo == "Todos":
            registros.append(row["Nombre"])

    if not registros:
        st.warning("No hay datos para enviar")
        return

    mensaje = f"*📋 REPORTE {tipo.upper()}*\n\n"
    mensaje += "\n".join(f"- {r}" for r in registros)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    })

# ---------------- CONFIG ----------------
if menu == "Configuración":
    st.title("⚙️ Envío de Reportes")

    opcion = st.selectbox("Tipo de reporte", ["Vencidos", "Próximos", "Todos"])

    if st.button("📩 Enviar reporte ahora"):
        enviar_personalizado(opcion)
        st.success("Reporte enviado ✅")

# ---------------- AUTO ENVÍO ----------------
if "ultimo_envio" not in st.session_state:
    st.session_state["ultimo_envio"] = ""

if st.session_state["ultimo_envio"] != str(hoy):
    enviar_personalizado("Vencidos")
    st.session_state["ultimo_envio"] = str(hoy)
