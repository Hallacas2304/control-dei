import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="DEI Control",
    layout="wide",
    initial_sidebar_state="collapsed"
)

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

TELEGRAM_TOKEN = st.secrets.get("TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

hoy = date.today()

# ---------------- ESTILO APP ----------------
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0f172a;
    color: white;
}

/* header */
.app-header {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 10px;
}

/* cards */
.card {
    background: #1e293b;
    padding: 14px;
    border-radius: 16px;
    margin-bottom: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

/* colores */
.rojo { color:#ef4444; font-weight:bold; }
.amarillo { color:#f59e0b; font-weight:bold; }
.verde { color:#22c55e; font-weight:bold; }

/* botón estilo app */
.stButton>button {
    border-radius: 10px;
    padding: 10px;
    font-weight: bold;
}

/* navegación */
.navbar {
    display: flex;
    justify-content: space-around;
    background: #1e293b;
    padding: 10px;
    border-radius: 15px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data(ttl=300)
def cargar():
    r = requests.get(EXCEL_URL)
    file = BytesIO(r.content)
    df = pd.read_excel(file, engine="openpyxl")

    df.columns = ["Nombre","Licencia","Tecnomecanica","SOAT"]

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

# ---------------- NAVEGACIÓN ----------------
menu = st.radio(
    "",
    ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Editar", "⚙️ Ajustes"],
    horizontal=True
)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":
    st.markdown('<div class="app-header">🚓 Control Documental</div>', unsafe_allow_html=True)

    total = len(df)
    soat_v = df[df["SOAT"].dt.date <= hoy]
    tec_v = df[df["Tecnomecanica"].dt.date <= hoy]
    lic_v = df[df["Licencia"].dt.date <= hoy]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("SOAT", len(soat_v))
    c3.metric("Tecno", len(tec_v))
    c4.metric("Licencia", len(lic_v))

    st.markdown("### 👮 Estado por funcionario")

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
    st.subheader("🚨 Alertas por documento")

    tab1, tab2, tab3 = st.tabs(["SOAT", "Tecnomecánica", "Licencia"])

    with tab1:
        st.dataframe(df[df["SOAT"].dt.date <= hoy])

    with tab2:
        st.dataframe(df[df["Tecnomecanica"].dt.date <= hoy])

    with tab3:
        st.dataframe(df[df["Licencia"].dt.date <= hoy])

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":
    st.subheader("📊 Análisis")

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
    st.subheader("Editar información")

    edit = st.data_editor(df, num_rows="dynamic")

    output = BytesIO()
    edit.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button("📥 Descargar Excel actualizado", output, "actualizado.xlsx")

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":
    st.subheader("⚙️ Acciones")

    if st.button("📩 Enviar alerta Telegram"):
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

        st.success("Enviado")
