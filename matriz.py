import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO
import zipfile

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control", layout="wide")

# 🔥 GOOGLE SHEETS EN FORMATO CSV (ESTABLE)
EXCEL_URL = "https://docs.google.com/spreadsheets/d/1E0nFTEfPtrxPNK-fdSuq9hGMFDFN_znD/gviz/tq?tqx=out:csv"

try:
    TELEGRAM_TOKEN = st.secrets["TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    TELEGRAM_TOKEN = ""
    CHAT_ID = ""

hoy = date.today()

# ---------------- ESTILO ----------------
st.markdown("""
<style>
body {
    background: #0b1220;
    color: #e5e7eb;
}

.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    color: #0f172a;
}

.nombre {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
}

.badge-rojo { color:#dc2626; font-weight:bold; }
.badge-amarillo { color:#d97706; font-weight:bold; }
.badge-verde { color:#16a34a; font-weight:bold; }

.topbar {
    background:#111827;
    padding:10px;
    border-radius:10px;
    margin-bottom:15px;
    color:white;
}

#MainMenu, footer, header {visibility:hidden;}
.block-container {padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA CSV ----------------
@st.cache_data(ttl=120)
def cargar():
    try:
        df = pd.read_csv(EXCEL_URL)
    except:
        st.error("❌ Error cargando datos desde Google Sheets")
        st.stop()

    df.columns = df.columns.str.strip().str.lower()

    nombre = next((c for c in df.columns if "nombre" in c), None)
    lic = next((c for c in df.columns if "licencia" in c), None)
    tec = next((c for c in df.columns if "tecno" in c), None)
    soat = next((c for c in df.columns if "soat" in c), None)

    if not all([nombre, lic, tec, soat]):
        st.error("❌ El archivo no tiene las columnas necesarias")
        st.stop()

    df = df[[nombre, lic, tec, soat]]
    df.columns = ["Nombre", "Licencia", "Tecno", "SOAT"]

    for c in ["Licencia", "Tecno", "SOAT"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    return df

df = cargar()

# ---------------- SOPORTES ----------------
if "soportes" not in st.session_state:
    st.session_state.soportes = {}

# ---------------- ESTADO ----------------
def estado(fecha):
    if pd.isna(fecha):
        return "COMUNICADO", "badge-amarillo"
    dias = (fecha.date() - hoy).days
    if dias < 0:
        return "VENCIDO", "badge-rojo"
    elif dias <= 5:
        return "PRÓXIMO", "badge-amarillo"
    return "AL DÍA", "badge-verde"

# ---------------- TELEGRAM ----------------
def enviar_telegram(lista):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "Telegram no configurado"

    if not lista:
        return False, "Sin alertas"

    mensaje = "🚨 *ALERTAS DOCUMENTALES*\n\n" + "\n".join(lista)

    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
    )

    return (True, "Enviado a Telegram") if r.status_code == 200 else (False, r.text)

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Excel", "⚙️ Ajustes"], horizontal=True)

# ================== INICIO ==================
if menu == "🏠 Inicio":

    st.markdown('<div class="topbar">🔎 Buscador de funcionarios con alertas</div>', unsafe_allow_html=True)

    buscar = st.text_input("Buscar funcionario")

    def alerta(r):
        return any(pd.notna(r[c]) and r[c].date() <= hoy for c in ["Licencia", "Tecno", "SOAT"])

    df2 = df.copy()
    df2["ALERTA"] = df2.apply(alerta, axis=1)

    if buscar:
        df2 = df2[df2["Nombre"].str.contains(buscar, case=False)]
    else:
        df2 = df2[df2["ALERTA"]]

    for i, row in df2.iterrows():

        nombre = row["Nombre"]

        lic, lic_c = estado(row["Licencia"])
        tec, tec_c = estado(row["Tecno"])
        soa, soa_c = estado(row["SOAT"])

        st.markdown(f"""
        <div class="card">
            <div class="nombre">{nombre}</div>
            Licencia: <span class="{lic_c}">{lic}</span><br>
            Tecno: <span class="{tec_c}">{tec}</span><br>
            SOAT: <span class="{soa_c}">{soa}</span>
        </div>
        """, unsafe_allow_html=True)

        files = st.file_uploader(
            f"📎 Documentos de {nombre}",
            accept_multiple_files=True,
            key=f"file_{i}"
        )

        if files:
            st.session_state.soportes[nombre] = files

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

    lista = []

    for _, r in df.iterrows():
        for c in ["Licencia", "Tecno", "SOAT"]:
            if pd.notna(r[c]) and r[c].date() <= hoy:
                lista.append(f"{r['Nombre']} → {c} vencido o próximo")

    if lista:
        st.error("\n".join(lista))
    else:
        st.success("Sin alertas 🚀")

    if st.button("📲 Enviar a Telegram"):
        ok, msg = enviar_telegram(lista)
        st.success(msg) if ok else st.error(msg)

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

# ================== EXCEL ==================
if menu == "✍️ Excel":

    edit = st.data_editor(df, use_container_width=True)

    buffer = BytesIO()
    edit.to_excel(buffer, index=False)

    st.download_button("⬇️ Descargar Excel", buffer.getvalue(), "base.xlsx")

# ================== AJUSTES ==================
if menu == "⚙️ Ajustes":

    st.subheader("⚙️ Panel del sistema")

    st.success("✔ Sistema activo")

    if TELEGRAM_TOKEN and CHAT_ID:
        st.success("✔ Telegram configurado")
    else:
        st.warning("⚠ Telegram no configurado")

    st.divider()

    if st.button("📲 Enviar reporte completo a Telegram"):

        lista = []

        for _, r in df.iterrows():
            for c in ["Licencia", "Tecno", "SOAT"]:
                if pd.notna(r[c]) and r[c].date() <= hoy:
                    lista.append(f"{r['Nombre']} → {c} vencido/próximo")

        if lista:
            ok, msg = enviar_telegram(lista)
            st.success(msg) if ok else st.error(msg)
        else:
            st.info("No hay alertas para enviar")
