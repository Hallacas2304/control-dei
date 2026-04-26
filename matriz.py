import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO
import zipfile

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control", layout="wide", initial_sidebar_state="collapsed")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

try:
    TELEGRAM_TOKEN = st.secrets["TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    TELEGRAM_TOKEN = ""
    CHAT_ID = ""
    st.warning("⚠️ Telegram no configurado")

hoy = date.today()

# ---------------- ESTILO ----------------
st.markdown("""
<style>
html, body {
    background: radial-gradient(circle at 20% 20%, #0b1220, #020617);
    color: #e2e8f0;
}

.card {
    background: linear-gradient(145deg, #0f172a, #020617);
    border: 1px solid #1e293b;
    padding: 15px;
    border-radius: 16px;
    margin-bottom: 10px;
}

.rojo { color:#ff4d4d; font-weight:bold; }
.amarillo { color:#facc15; font-weight:bold; }
.verde { color:#22c55e; font-weight:bold; }

.oficial {
    background: linear-gradient(90deg, #1e3a8a, #06b6d4);
    color: white;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
}

#MainMenu, footer, header {visibility:hidden;}
.block-container {padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data(ttl=120)
def cargar():
    r = requests.get(EXCEL_URL, timeout=20)
    df = pd.read_excel(BytesIO(r.content), engine="openpyxl")

    df.columns = df.columns.str.strip().str.lower()

    nombre = next(c for c in df.columns if "nombre" in c)
    licencia = next(c for c in df.columns if "licencia" in c)
    tecno = next(c for c in df.columns if "tecno" in c)
    soat = next(c for c in df.columns if "soat" in c)

    df = df[[nombre, licencia, tecno, soat]]
    df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

    for c in ["Licencia", "Tecnomecanica", "SOAT"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    return df

df = cargar()

# ---------------- SESSION STATE ----------------
if "soportes" not in st.session_state:
    st.session_state.soportes = {}

# ---------------- FUNCION ----------------
def estado(fecha):
    if pd.isna(fecha):
        return "COMUNICADO OFICIAL", "amarillo"
    dias = (fecha.date() - hoy).days
    if dias < 0:
        return f"VENCIDO ({fecha.date()})", "rojo"
    elif dias <= 5:
        return f"PRÓXIMO ({fecha.date()})", "amarillo"
    return f"AL DÍA ({fecha.date()})", "verde"

# ---------------- TELEGRAM ----------------
def enviar(lista):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "Telegram no configurado"

    msg = "🚨 *DOCUMENTOS VENCIDOS*\n\n" + "\n".join(lista)

    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    )

    return (True, "Enviado") if r.status_code == 200 else (False, r.text)

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Editar", "⚙️ Ajustes"], horizontal=True)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":
    st.title("🚓 Control Documental")

    for i, row in df.iterrows():

        nombre = row["Nombre"]

        lic, lic_c = estado(row["Licencia"])
        tec, tec_c = estado(row["Tecnomecanica"])
        soa, soa_c = estado(row["SOAT"])

        if nombre not in st.session_state.soportes:
            st.session_state.soportes[nombre] = {
                "visible": False,
                "files": []
            }

        col1, col2 = st.columns([3,1])

        with col1:
            st.markdown(f"""
            <div class="card">
                <b>{nombre}</b><br>
                Licencia: <span class="{lic_c}">{lic}</span><br>
                Tecno: <span class="{tec_c}">{tec}</span><br>
                SOAT: <span class="{soa_c}">{soa}</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            vis = st.checkbox("👁️ Soportes", key=f"v_{i}")
            st.session_state.soportes[nombre]["visible"] = vis

        # 📎 SOPORTES
        if st.session_state.soportes[nombre]["visible"]:

            files = st.file_uploader(
                "📎 Subir fotocopias",
                accept_multiple_files=True,
                key=f"f_{i}"
            )

            if files:
                st.session_state.soportes[nombre]["files"] = files

            if st.session_state.soportes[nombre]["files"]:

                zip_buffer = BytesIO()

                with zipfile.ZipFile(zip_buffer, "w") as zipf:
                    for f in st.session_state.soportes[nombre]["files"]:
                        zipf.writestr(f.name, f.getvalue())

                st.download_button(
                    "⬇️ Descargar soportes",
                    zip_buffer.getvalue(),
                    file_name=f"{nombre}_soportes.zip"
                )

# ---------------- ALERTAS ----------------
if menu == "🚨 Alertas":

    df2 = df.copy()

    for c in ["Licencia", "Tecnomecanica", "SOAT"]:
        df2[c] = df2[c].apply(lambda x: estado(x)[0])

    st.dataframe(df2, use_container_width=True)

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":

    st.bar_chart(pd.DataFrame({
        "Tipo": ["SOAT", "Tecno", "Licencia"],
        "Vencidos": [
            (df["SOAT"] < pd.to_datetime(hoy)).sum(),
            (df["Tecnomecanica"] < pd.to_datetime(hoy)).sum(),
            (df["Licencia"] < pd.to_datetime(hoy)).sum()
        ]
    }).set_index("Tipo"))

    st.subheader("📋 Resumen")

    resumen = []
    for _, r in df.iterrows():
        docs = []

        if pd.notna(r["Licencia"]) and r["Licencia"].date() <= hoy:
            docs.append("Licencia")
        if pd.notna(r["Tecnomecanica"]) and r["Tecnomecanica"].date() <= hoy:
            docs.append("Tecno")
        if pd.notna(r["SOAT"]) and r["SOAT"].date() <= hoy:
            docs.append("SOAT")

        estado_txt = "COMUNICADO OFICIAL" if len(docs) == 0 and pd.isna(r["Licencia"]) else (", ".join(docs) or "AL DÍA")

        resumen.append({"Funcionario": r["Nombre"], "Estado": estado_txt})

    st.dataframe(pd.DataFrame(resumen), use_container_width=True)

# ---------------- EDITAR ----------------
if menu == "✍️ Editar":

    edit = st.data_editor(df, use_container_width=True)

    buffer = BytesIO()
    edit.to_excel(buffer, index=False)

    st.download_button("⬇️ Descargar Excel", buffer.getvalue(), "base.xlsx")

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":

    if st.button("🚨 Enviar Telegram"):
        lista = []

        for _, r in df.iterrows():
            docs = []

            if pd.notna(r["Licencia"]) and r["Licencia"].date() <= hoy:
                docs.append("Licencia")
            if pd.notna(r["Tecnomecanica"]) and r["Tecnomecanica"].date() <= hoy:
                docs.append("Tecno")
            if pd.notna(r["SOAT"]) and r["SOAT"].date() <= hoy:
                docs.append("SOAT")

            if docs:
                lista.append(f"{r['Nombre']} → {', '.join(docs)}")

        ok, msg = enviar(lista)
        st.success(msg) if ok else st.error(msg)
