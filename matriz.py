import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control", layout="wide", initial_sidebar_state="collapsed")

EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

# TELEGRAM
try:
    TELEGRAM_TOKEN = st.secrets["TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    TELEGRAM_TOKEN = ""
    CHAT_ID = ""
    st.warning("⚠️ Telegram no configurado")

hoy = date.today()

# ---------------- ESTILO TECH ----------------
st.markdown("""
<style>
html, body {
    background: radial-gradient(circle at 20% 20%, #0b1220, #020617);
    color: #e2e8f0;
    font-family: 'Segoe UI', sans-serif;
}

.card {
    background: linear-gradient(145deg, #0f172a, #020617);
    border: 1px solid #1e293b;
    padding: 15px;
    border-radius: 16px;
    margin-bottom: 10px;
    box-shadow: 0 0 15px rgba(0,255,255,0.05);
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
.block-container {padding-top:1rem;padding-bottom:1rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data(ttl=120)
def cargar():
    r = requests.get(EXCEL_URL, timeout=20)
    r.raise_for_status()

    df = pd.read_excel(BytesIO(r.content), engine="openpyxl")
    df.columns = df.columns.str.strip().str.lower()

    nombre = next((c for c in df.columns if "nombre" in c), None)
    licencia = next((c for c in df.columns if "licencia" in c), None)
    tecno = next((c for c in df.columns if "tecno" in c), None)
    soat = next((c for c in df.columns if "soat" in c), None)

    df = df[[nombre, licencia, tecno, soat]]
    df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

    for col in df.columns[1:]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df.dropna(subset=["Nombre"])

df = cargar()

# ---------------- FUNCION ----------------
def evaluar(fecha):
    if pd.isna(fecha):
        return "COMUNICADO OFICIAL", "amarillo"

    dias = (fecha.date() - hoy).days

    if dias < 0:
        return f"VENCIDO ({fecha.date()})", "rojo"
    elif dias <= 5:
        return f"PRÓXIMO ({fecha.date()})", "amarillo"
    else:
        return f"AL DÍA ({fecha.date()})", "verde"

# ---------------- TELEGRAM ----------------
def enviar_telegram(lista):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "TOKEN o CHAT_ID no configurados"

    if not lista:
        return False, "No hay datos para enviar"

    mensaje = "*🚨 DOCUMENTOS VENCIDOS*\n\n"
    mensaje += "\n".join(f"- {x}" for x in lista)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    })

    return (True, "Enviado") if r.status_code == 200 else (False, r.text)

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Editar", "⚙️ Ajustes"], horizontal=True)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":

    st.title("🚓 Control Documental")

    for _, row in df.iterrows():
        lic_e, lic_c = evaluar(row["Licencia"])
        tec_e, tec_c = evaluar(row["Tecnomecanica"])
        soa_e, soa_c = evaluar(row["SOAT"])

        badge = ""
        if lic_e == "COMUNICADO OFICIAL" and tec_e == "COMUNICADO OFICIAL" and soa_e == "COMUNICADO OFICIAL":
            badge = '<span class="oficial">COMUNICADO OFICIAL</span>'

        st.markdown(f"""
        <div class="card">
            <b>{row['Nombre']}</b> {badge}<br>
            Licencia: <span class="{lic_c}">{lic_e}</span><br>
            Tecnomecánica: <span class="{tec_c}">{tec_e}</span><br>
            SOAT: <span class="{soa_c}">{soa_e}</span>
        </div>
        """, unsafe_allow_html=True)

# ---------------- ALERTAS ----------------
if menu == "🚨 Alertas":

    def estado_texto(fecha):
        if pd.isna(fecha):
            return "⚪ COMUNICADO OFICIAL"
        dias = (fecha.date() - hoy).days
        if dias < 0:
            return f"🔴 VENCIDO ({fecha.date()})"
        elif dias <= 5:
            return f"🟡 PRÓXIMO ({fecha.date()})"
        else:
            return f"🟢 AL DÍA ({fecha.date()})"

    df_alertas = df.copy()
    df_alertas["Licencia"] = df_alertas["Licencia"].apply(estado_texto)
    df_alertas["Tecnomecanica"] = df_alertas["Tecnomecanica"].apply(estado_texto)
    df_alertas["SOAT"] = df_alertas["SOAT"].apply(estado_texto)

    tab1, tab2, tab3 = st.tabs(["SOAT", "Tecnomecánica", "Licencia"])

    with tab1:
        st.dataframe(df_alertas[["Nombre", "SOAT"]], use_container_width=True)
    with tab2:
        st.dataframe(df_alertas[["Nombre", "Tecnomecanica"]], use_container_width=True)
    with tab3:
        st.dataframe(df_alertas[["Nombre", "Licencia"]], use_container_width=True)

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":

    st.bar_chart(pd.DataFrame({
        "Tipo":["SOAT","Tecno","Licencia"],
        "Cantidad":[
            len(df[df["SOAT"].dt.date <= hoy]),
            len(df[df["Tecnomecanica"].dt.date <= hoy]),
            len(df[df["Licencia"].dt.date <= hoy])
        ]
    }).set_index("Tipo"))

    # RESUMEN
    st.subheader("📋 Resumen general")

    resumen = []
    for _, row in df.iterrows():
        docs = []

        if pd.notna(row["Licencia"]) and row["Licencia"].date() <= hoy:
            docs.append("Licencia")
        if pd.notna(row["Tecnomecanica"]) and row["Tecnomecanica"].date() <= hoy:
            docs.append("Tecnomecánica")
        if pd.notna(row["SOAT"]) and row["SOAT"].date() <= hoy:
            docs.append("SOAT")

        if pd.isna(row["Licencia"]) and pd.isna(row["Tecnomecanica"]) and pd.isna(row["SOAT"]):
            estado = "COMUNICADO OFICIAL"
        elif docs:
            estado = ", ".join(docs)
        else:
            estado = "AL DÍA"

        resumen.append({"Funcionario": row["Nombre"], "Estado": estado})

    st.dataframe(pd.DataFrame(resumen), use_container_width=True)

    # LISTADO OFICIAL
    st.subheader("📢 Comunicado Oficial")
    df_oficial = df[
        df["Licencia"].isna() &
        df["Tecnomecanica"].isna() &
        df["SOAT"].isna()
    ]

    for _, row in df_oficial.iterrows():
        st.markdown(f"""
        <div class="card">
            <b>{row['Nombre']}</b><br>
            <span class="oficial">COMUNICADO OFICIAL</span>
        </div>
        """, unsafe_allow_html=True)

# ---------------- EDITAR ----------------
if menu == "✍️ Editar":
    edit = st.data_editor(df)
    buffer = BytesIO()
    edit.to_excel(buffer, index=False)
    st.download_button("Descargar Excel", buffer.getvalue(), "editado.xlsx")

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":

    if st.button("Enviar reporte Telegram"):
        lista = []

        for _, row in df.iterrows():
            docs = []

            if pd.notna(row["Licencia"]) and row["Licencia"].date() <= hoy:
                docs.append("Licencia")
            if pd.notna(row["Tecnomecanica"]) and row["Tecnomecanica"].date() <= hoy:
                docs.append("Tecnomecánica")
            if pd.notna(row["SOAT"]) and row["SOAT"].date() <= hoy:
                docs.append("SOAT")

            if docs:
                lista.append(f"{row['Nombre']} → {', '.join(docs)}")

        ok, msg = enviar_telegram(lista)

        if ok:
            st.success(msg)
        else:
            st.error(msg)
