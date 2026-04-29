import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO
import zipfile

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control", layout="wide")

# 🔥 GOOGLE SHEETS COMO CSV (ESTABLE)
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
body { background: #0b1220; color: #e5e7eb; }

.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    color: #0f172a;
}

.nombre { font-size: 18px; font-weight: 700; color: #0f172a; }

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
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
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
        st.error("❌ Columnas no encontradas")
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
        data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    )

    return (True, "Enviado") if r.status_code == 200 else (False, r.text)

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Datos", "⚙️ Ajustes"], horizontal=True)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":

    st.markdown('<div class="topbar">🔎 Buscador de funcionarios</div>', unsafe_allow_html=True)

    buscar = st.text_input("Buscar")

    def alerta(r):
        return any(pd.notna(r[c]) and r[c].date() <= hoy for c in ["Licencia","Tecno","SOAT"])

    df2 = df.copy()
    df2["ALERTA"] = df2.apply(alerta, axis=1)

    if buscar:
        df2 = df2[df2["Nombre"].str.contains(buscar, case=False)]
    else:
        df2 = df2[df2["ALERTA"]]

    for i, row in df2.iterrows():

        nombre = row["Nombre"]

        lic, lc = estado(row["Licencia"])
        tec, tc = estado(row["Tecno"])
        soa, sc = estado(row["SOAT"])

        st.markdown(f"""
        <div class="card">
            <div class="nombre">{nombre}</div>
            Licencia: <span class="{lc}">{lic}</span><br>
            Tecno: <span class="{tc}">{tec}</span><br>
            SOAT: <span class="{sc}">{soa}</span>
        </div>
        """, unsafe_allow_html=True)

        files = st.file_uploader(f"📎 Documentos {nombre}", accept_multiple_files=True, key=i)

        if files:
            st.session_state.soportes[nombre] = files

        if st.session_state.soportes.get(nombre):
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for f in st.session_state.soportes[nombre]:
                    zipf.writestr(f.name, f.getvalue())

            st.download_button("⬇️ Descargar soportes", zip_buffer.getvalue(), f"{nombre}.zip")

# ---------------- ALERTAS ----------------
if menu == "🚨 Alertas":

    lista = []

    for _, r in df.iterrows():
        for c in ["Licencia","Tecno","SOAT"]:
            if pd.notna(r[c]) and r[c].date() <= hoy:
                lista.append(f"{r['Nombre']} → {c}")

    st.error("\n".join(lista) if lista else "Sin alertas")

    if st.button("📲 Enviar Telegram"):
        ok, msg = enviar_telegram(lista)
        st.success(msg) if ok else st.error(msg)

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":

    st.bar_chart(pd.DataFrame({
        "Tipo":["SOAT","Tecno","Licencia"],
        "Vencidos":[
            (df["SOAT"] < pd.to_datetime(hoy)).sum(),
            (df["Tecno"] < pd.to_datetime(hoy)).sum(),
            (df["Licencia"] < pd.to_datetime(hoy)).sum()
        ]
    }).set_index("Tipo"))

# ---------------- DATOS ----------------
if menu == "✍️ Datos":

    edit = st.data_editor(df, use_container_width=True)

    csv = edit.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Descargar CSV",
        csv,
        "base.csv",
        "text/csv"
    )

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":

    st.subheader("Panel del sistema")

    st.success("Sistema activo")

    if TELEGRAM_TOKEN:
        st.success("Telegram OK")
    else:
        st.warning("Telegram no configurado")
