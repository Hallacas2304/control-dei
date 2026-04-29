import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO
import zipfile
import subprocess
import sys

# ---------------- INSTALAR FIREBASE SI FALTA ----------------
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_OK = True
except ModuleNotFoundError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "firebase-admin"])
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
        FIREBASE_OK = True
    except:
        FIREBASE_OK = False

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DEI Control PRO", layout="wide")

EXCEL_URL = "https://docs.google.com/spreadsheets/d/1E0nFTEfPtrxPNK-fdSuq9hGMFDFN_znD/gviz/tq?tqx=out:csv"

TOKEN = st.secrets.get("TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

hoy = date.today()

# ---------------- FIREBASE INIT ----------------
if FIREBASE_OK and "FIREBASE_CREDENTIALS" in st.secrets:
    try:
        import json
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_CREDENTIALS"]))
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'tu-bucket.appspot.com'
            })
        db = firestore.client()
        bucket = storage.bucket()
    except:
        FIREBASE_OK = False

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

.nombre { font-size:18px; font-weight:bold; }

.rojo { color:#dc2626; font-weight:bold; }
.amarillo { color:#d97706; font-weight:bold; }
.verde { color:#16a34a; font-weight:bold; }
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

# ---------------- SOPORTES LOCAL ----------------
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
def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
        return r.status_code == 200
    except:
        return False

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio","🚨 Alertas","📊 Dashboard","📁 Soportes","✍️ Datos","⚙️ Ajustes"], horizontal=True)

# ---------------- INICIO ----------------
if menu == "🏠 Inicio":

    buscar = st.text_input("🔎 Buscar funcionario")

    df2 = df.copy()
    if buscar:
        df2 = df2[df2["Nombre"].str.contains(buscar, case=False)]
    else:
        df2 = df2[df2.apply(lambda r: any(pd.notna(r[c]) and r[c].date() <= hoy for c in ["Licencia","Tecno","SOAT"]), axis=1)]

    for i, row in df2.iterrows():

        lic, lc = estado(row["Licencia"])
        tec, tc = estado(row["Tecno"])
        soa, sc = estado(row["SOAT"])

        st.markdown(f"""
        <div class="card">
            <div class="nombre">{row['Nombre']}</div>
            Licencia: <span class="{lc}">{lic}</span><br>
            Tecno: <span class="{tc}">{tec}</span><br>
            SOAT: <span class="{sc}">{soa}</span>
        </div>
        """, unsafe_allow_html=True)

        files = st.file_uploader("📎 Subir documentos", accept_multiple_files=True, key=i)

        if files:
            st.session_state.soportes[row["Nombre"]] = files

        if st.session_state.soportes.get(row["Nombre"]):
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as z:
                for f in st.session_state.soportes[row["Nombre"]]:
                    z.writestr(f.name, f.getvalue())

            st.download_button("⬇️ Descargar soportes", zip_buffer.getvalue(), f"{row['Nombre']}.zip")

# ---------------- ALERTAS ----------------
if menu == "🚨 Alertas":

    data = []

    for _, r in df.iterrows():
        for t in ["Licencia","Tecno","SOAT"]:
            f = r[t]
            if pd.notna(f):
                dias = (f.date() - hoy).days
                if dias < 0 or dias <= 5:
                    estado_txt = "VENCIDO" if dias < 0 else "PRÓXIMO"
                    data.append({
                        "Funcionario": r["Nombre"],
                        "Documento": t,
                        "Fecha": f.date(),
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
            msg = "🚨 ALERTAS\n\n"
            for d in data:
                msg += f"{d['Funcionario']} → {d['Documento']} ({d['Estado']} {d['Fecha']})\n"

            if enviar_telegram(msg):
                st.success("Mensaje enviado")
            else:
                st.error("No se pudo enviar")

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

# ---------------- SOPORTES CLOUD (SI FIREBASE OK) ----------------
if menu == "📁 Soportes":

    if not FIREBASE_OK:
        st.warning("Firebase no activo, usando almacenamiento local")
    else:
        nombre = st.selectbox("Funcionario", df["Nombre"])

        files = st.file_uploader("Subir a la nube", accept_multiple_files=True)

        if files:
            for f in files:
                blob = bucket.blob(f"{nombre}/{f.name}")
                blob.upload_from_string(f.getvalue())
            st.success("Subido a la nube")

# ---------------- DATOS ----------------
if menu == "✍️ Datos":

    edit = st.data_editor(df)

    csv = edit.to_csv(index=False).encode("utf-8")

    st.download_button("⬇️ Descargar CSV", csv, "base.csv")

# ---------------- AJUSTES ----------------
if menu == "⚙️ Ajustes":

    st.success("Sistema activo")

    if TOKEN:
        st.success("Telegram activo")
    else:
        st.warning("Telegram no configurado")

    if FIREBASE_OK:
        st.success("Firebase conectado")
    else:
        st.warning("Firebase no disponible")
