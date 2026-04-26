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
html, body {
    background-color: #0f172a;
    color: white;
}

.card {
    background: #1e293b;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
}

.rojo { color:#ef4444; font-weight:bold; }
.amarillo { color:#f59e0b; font-weight:bold; }
.verde { color:#22c55e; font-weight:bold; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA SEGURA ----------------
@st.cache_data(ttl=300)
def cargar():
    try:
        r = requests.get(EXCEL_URL, timeout=20)
        r.raise_for_status()

        file = BytesIO(r.content)
        df = pd.read_excel(file, engine="openpyxl")

        # limpiar columnas
        df.columns = df.columns.str.strip().str.lower()

        # detectar columnas automáticamente
        nombre = next((c for c in df.columns if "nombre" in c), None)
        licencia = next((c for c in df.columns if "licencia" in c), None)
        tecno = next((c for c in df.columns if "tecno" in c), None)
        soat = next((c for c in df.columns if "soat" in c), None)

        if not all([nombre, licencia, tecno, soat]):
            st.error("❌ El Excel no tiene las columnas necesarias")
            st.stop()

        df = df[[nombre, licencia, tecno, soat]].copy()
        df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

        for col in ["Licencia", "Tecnomecanica", "SOAT"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        df = df.dropna(subset=["Nombre"])
        df = df[df["Nombre"].astype(str).str.len() > 3]

        return df

    except Exception as e:
        st.error(f"❌ Error cargando Excel: {e}")
        st.stop()

df = cargar()

# ---------------- FUNCION ESTADO ----------------
def evaluar(fecha):
    if pd.isna(fecha):
        return "VACÍO", "amarillo"

    dias = (fecha.date() - hoy).days

    if dias < 0:
        return "VENCIDO", "rojo"
    elif dias <= 5:
        return f"VENCE EN {dias} DÍAS", "amarillo"
    else:
        return "AL DÍA", "verde"

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Editar", "⚙️ Ajustes"], horizontal=True)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":

    st.title("🚓 Control Documental")

    soat_v = df[df["SOAT"].dt.date <= hoy]
    tec_v = df[df["Tecnomecanica"].dt.date <= hoy]
    lic_v = df[df["Licencia"].dt.date <= hoy]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(df))
    c2.metric("SOAT vencido", len(soat_v))
    c3.metric("Tecnomecánica", len(tec_v))
    c4.metric("Licencias", len(lic_v))

    st.subheader("👮 Estado por funcionario")

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

    st.subheader("🚨 Listados de alerta")

    tab1, tab2, tab3 = st.tabs(["SOAT", "Tecnomecánica", "Licencia"])

    with tab1:
        st.dataframe(df[df["SOAT"].dt.date <= hoy])

    with tab2:
        st.dataframe(df[df["Tecnomecanica"].dt.date <= hoy])

    with tab3:
        st.dataframe(df[df["Licencia"].dt.date <= hoy])

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":

    st.subheader("📊 Estadísticas")

    chart = pd.DataFrame({
        "Tipo": ["SOAT","Tecno","Licencia"],
        "Cantidad": [
            len(df[df["SOAT"].dt.date <= hoy]),
            len(df[df["Tecnomecanica"].dt.date <= hoy]),
            len(df[df["Licencia"].dt.date <= hoy])
        ]
    })

    st.bar_chart(chart.set_index("Tipo"))

# ---------------- EDITAR ----------------
if menu == "✍️ Editar":

    st.subheader("Editar Excel")

    edit = st.data_editor(df, num_rows="dynamic")

    output = BytesIO()
    edit.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button("📥 Descargar Excel actualizado", output, "actualizado.xlsx")

# ---------------- TELEGRAM ----------------
def enviar():
    if not TELEGRAM_TOKEN:
        st.warning("Configura TOKEN en secrets")
        return

    mensaje = "*🚨 DOCUMENTOS VENCIDOS*\n\n"

    for _, row in df.iterrows():
        if pd.notna(row["SOAT"]) and row["SOAT"].date() <= hoy:
            mensaje += f"- {row['Nombre']} → SOAT\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    })

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":

    if st.button("📩 Enviar reporte Telegram"):
        enviar()
        st.success("Enviado")
