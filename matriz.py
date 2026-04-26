import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO
import zipfile

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control", layout="wide")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

try:
    TELEGRAM_TOKEN = st.secrets["TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    TELEGRAM_TOKEN = ""
    CHAT_ID = ""

hoy = date.today()

# ---------------- ESTILO NUEVO MÁS LIMPIO ----------------
st.markdown("""
<style>
body {
    background: #0f172a;
    color: #e5e7eb;
}

.card {
    background: #111827;
    border: 1px solid #1f2937;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

.nombre {
    font-size: 18px;
    font-weight: 700;
    color: #93c5fd;
}

.badge-rojo { color:#ef4444; font-weight:bold; }
.badge-amarillo { color:#fbbf24; font-weight:bold; }
.badge-verde { color:#22c55e; font-weight:bold; }

.topbar {
    background:#0b1220;
    padding:10px;
    border-radius:10px;
    margin-bottom:15px;
}

#MainMenu, footer, header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data(ttl=120)
def cargar():
    r = requests.get(EXCEL_URL)
    df = pd.read_excel(BytesIO(r.content), engine="openpyxl")

    df.columns = df.columns.str.strip().str.lower()

    nombre = next(c for c in df.columns if "nombre" in c)
    lic = next(c for c in df.columns if "licencia" in c)
    tec = next(c for c in df.columns if "tecno" in c)
    soat = next(c for c in df.columns if "soat" in c)

    df = df[[nombre, lic, tec, soat]]
    df.columns = ["Nombre", "Licencia", "Tecno", "SOAT"]

    for c in ["Licencia", "Tecno", "SOAT"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    return df

df = cargar()

# ---------------- STATE SOPORTES ----------------
if "soportes" not in st.session_state:
    st.session_state.soportes = {}

# ---------------- FUNCION ESTADO ----------------
def estado(fecha):
    if pd.isna(fecha):
        return "COMUNICADO", "badge-amarillo"
    dias = (fecha.date() - hoy).days
    if dias < 0:
        return "VENCIDO", "badge-rojo"
    elif dias <= 5:
        return "PRÓXIMO", "badge-amarillo"
    return "AL DÍA", "badge-verde"

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Excel", "⚙️ Ajustes"], horizontal=True)

# ================== INICIO (BUSCADOR + ALERTAS) ==================
if menu == "🏠 Inicio":

    st.markdown('<div class="topbar">🔎 Buscar funcionario o ver alertas críticas</div>', unsafe_allow_html=True)

    busqueda = st.text_input("Buscar nombre (opcional)")

    df_view = df.copy()

    # 🔥 detectar alertas
    def es_alerta(row):
        for c in ["Licencia", "Tecno", "SOAT"]:
            if pd.notna(row[c]) and row[c].date() <= hoy:
                return True
        return False

    df_view["ALERTA"] = df_view.apply(es_alerta, axis=1)

    # FILTRO
    if busqueda:
        df_view = df_view[df_view["Nombre"].str.contains(busqueda, case=False)]
    else:
        df_view = df_view[df_view["ALERTA"] == True]  # SOLO ALERTAS EN INICIO

    for i, row in df_view.iterrows():

        lic, lic_c = estado(row["Licencia"])
        tec, tec_c = estado(row["Tecno"])
        soa, soa_c = estado(row["SOAT"])

        nombre = row["Nombre"]

        if nombre not in st.session_state.soportes:
            st.session_state.soportes[nombre] = []

        st.markdown(f"""
        <div class="card">
            <div class="nombre">{nombre}</div>
            Licencia: <span class="{lic_c}">{lic}</span><br>
            Tecno: <span class="{tec_c}">{tec}</span><br>
            SOAT: <span class="{soa_c}">{soa}</span>
        </div>
        """, unsafe_allow_html=True)

        # 📎 BOTÓN SIEMPRE FRENTE AL FUNCIONARIO
        files = st.file_uploader(
            f"📎 Subir documentos para {nombre}",
            accept_multiple_files=True,
            key=f"file_{i}"
        )

        if files:
            st.session_state.soportes[nombre] = files

        # 📦 descarga
        if st.session_state.soportes.get(nombre):

            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for f in st.session_state.soportes[nombre]:
                    zipf.writestr(f.name, f.getvalue())

            st.download_button(
                "⬇️ Descargar soportes",
                zip_buffer.getvalue(),
                file_name=f"{nombre}_soportes.zip"
            )

# ================== ALERTAS ==================
if menu == "🚨 Alertas":

    st.subheader("🚨 Funcionarios con vencimientos")

    for _, r in df.iterrows():

        for c in ["Licencia", "Tecno", "SOAT"]:
            if pd.notna(r[c]) and r[c].date() <= hoy:

                st.error(f"{r['Nombre']} → {c} VENCIDO / PRÓXIMO")

# ================== DASHBOARD ==================
if menu == "📊 Dashboard":

    st.bar_chart(pd.DataFrame({
        "Tipo": ["SOAT", "Tecno", "Licencia"],
        "Vencidos": [
            (df["SOAT"] < pd.to_datetime(hoy)).sum(),
            (df["Tecno"] < pd.to_datetime(hoy)).sum(),
            (df["Licencia"] < pd.to_datetime(hoy)).sum()
        ]
    }).set_index("Tipo"))

# ================== EXCEL (OCULTAR COLUMNAS) ==================
if menu == "✍️ Excel":

    st.subheader("📁 Edición avanzada")

    ocultar = st.multiselect("Ocultar columnas", df.columns.tolist())

    df_show = df.drop(columns=ocultar)

    edit = st.data_editor(df_show, use_container_width=True)

    buffer = BytesIO()
    edit.to_excel(buffer, index=False)

    st.download_button("⬇️ Descargar Excel", buffer.getvalue(), "base.xlsx")

# ================== AJUSTES ==================
if menu == "⚙️ Ajustes":

    st.info("Sistema listo para expansión (Telegram / BD / login)")
