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

# ---------------- ESTILO LIMPIO ----------------
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

    return (True, "Enviado") if r.status_code == 200 else (False, r.text)

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Excel", "⚙️ Ajustes"], horizontal=True)

# ================== INICIO ==================
if menu == "🏠 Inicio":

    st.markdown('<div class="topbar">🔎 Buscador inteligente de funcionarios</div>', unsafe_allow_html=True)

    buscar = st.text_input("Buscar funcionario (opcional)")

    def tiene_alerta(r):
        for c in ["Licencia", "Tecno", "SOAT"]:
            if pd.notna(r[c]) and r[c].date() <= hoy:
                return True
        return False

    df2 = df.copy()
    df2["ALERTA"] = df2.apply(tiene_alerta, axis=1)

    if buscar:
        df2 = df2[df2["Nombre"].str.contains(buscar, case=False)]
    else:
        df2 = df2[df2["ALERTA"] == True]

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

        # 📎 SUBIDA DIRECTA POR FUNCIONARIO
        files = st.file_uploader(
            f"📎 Subir documentos - {nombre}",
            accept_multiple_files=True,
            key=f"file_{i}"
        )

        if files:
            st.session_state.soportes[nombre] = files

        # 📦 DESCARGA ZIP
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

# ================== ALERTAS + TELEGRAM ==================
if menu == "🚨 Alertas":

    lista = []

    for _, r in df.iterrows():
        for c in ["Licencia", "Tecno", "SOAT"]:
            if pd.notna(r[c]) and r[c].date() <= hoy:
                lista.append(f"{r['Nombre']} → {c} vencido o próximo")

    st.error("\n".join(lista) if lista else "Sin alertas 🚀")

    if st.button("📲 Enviar Telegram"):
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

    st.info("Sistema estable 🚀 listo para escalar a base de datos o login")
