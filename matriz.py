import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO
import zipfile

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control", layout="wide")

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
body { background: #0b1220; }

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
    font-weight: bold;
}

.rojo { color:#dc2626; font-weight:bold; }
.amarillo { color:#d97706; font-weight:bold; }
.verde { color:#16a34a; font-weight:bold; }

#MainMenu, footer, header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data(ttl=120)
def cargar():
    df = pd.read_csv(EXCEL_URL)
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
        return "COMUNICADO", "amarillo"
    dias = (fecha.date() - hoy).days
    if dias < 0:
        return "VENCIDO", "rojo"
    elif dias <= 5:
        return "PRÓXIMO", "amarillo"
    return "AL DÍA", "verde"

# ---------------- TELEGRAM ----------------
def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "Telegram no configurado"

    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    )

    return (True, "Enviado") if r.status_code == 200 else (False, r.text)

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Datos", "⚙️ Ajustes"], horizontal=True)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":

    buscar = st.text_input("🔎 Buscar funcionario")

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

        files = st.file_uploader(f"📎 Subir documentos", accept_multiple_files=True, key=i)

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

    st.subheader("🚨 Alertas organizadas")

    data = []

    for _, r in df.iterrows():
        for tipo in ["Licencia", "Tecno", "SOAT"]:
            fecha = r[tipo]

            if pd.notna(fecha):
                dias = (fecha.date() - hoy).days

                if dias < 0:
                    estado_txt = "🔴 VENCIDO"
                elif dias <= 5:
                    estado_txt = "🟡 PRÓXIMO"
                else:
                    continue

                data.append({
                    "Funcionario": r["Nombre"],
                    "Documento": tipo,
                    "Fecha": fecha.date(),
                    "Estado": estado_txt,
                    "Días": dias
                })

    if data:
        df_alertas = pd.DataFrame(data).sort_values(by="Días")
        st.dataframe(df_alertas, use_container_width=True)
    else:
        st.success("Sin alertas")

    if st.button("📲 Enviar Telegram"):
        if data:
            mensaje = "🚨 ALERTAS\n\n"
            for d in data:
                mensaje += f"{d['Funcionario']} → {d['Documento']} ({d['Estado']} {d['Fecha']})\n"

            ok, msg = enviar_telegram(mensaje)
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

    st.download_button("⬇️ Descargar CSV", csv, "base.csv", "text/csv")

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":

    st.success("Sistema activo")

    if TELEGRAM_TOKEN:
        st.success("Telegram configurado")
    else:
        st.warning("Telegram no configurado")
