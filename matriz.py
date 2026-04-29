import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
from io import BytesIO
import zipfile
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_CREDENTIALS"]))
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'TU_BUCKET.appspot.com'
    })

db = firestore.client()
bucket = storage.bucket()

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")
hoy = date.today()

TOKEN = st.secrets.get("TOKEN")
CHAT_ID = st.secrets.get("CHAT_ID")

# ---------------- LOGIN ----------------
def login(email, password):
    # simulación simple (puedes conectar con API real de Firebase Auth)
    user = db.collection("usuarios").where("email", "==", email).get()
    return len(user) > 0

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Login Corporativo")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Ingresar"):
        if login(email, password):
            st.session_state.user = email
            st.rerun()
        else:
            st.error("Acceso denegado")

    st.stop()

# ---------------- CARGA DESDE FIRESTORE ----------------
@st.cache_data(ttl=60)
def cargar():
    docs = db.collection("funcionarios").stream()
    data = []

    for d in docs:
        r = d.to_dict()
        data.append(r)

    df = pd.DataFrame(data)

    for c in ["Licencia","Tecno","SOAT"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    return df

df = cargar()

# ---------------- ESTADO ----------------
def estado(fecha):
    if pd.isna(fecha):
        return "COMUNICADO"
    dias = (fecha.date() - hoy).days
    if dias < 0: return "VENCIDO"
    if dias <= 5: return "PRÓXIMO"
    return "AL DÍA"

# ---------------- TELEGRAM ----------------
def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ---------------- MENU ----------------
menu = st.sidebar.selectbox("Menú", ["Inicio","Alertas","Soportes","Admin"])

# ---------------- INICIO ----------------
if menu == "Inicio":

    buscar = st.text_input("Buscar")

    df2 = df[df["Nombre"].str.contains(buscar, case=False)] if buscar else df

    for _, r in df2.iterrows():
        st.write(f"### {r['Nombre']}")
        st.write("Licencia:", estado(r["Licencia"]))
        st.write("Tecno:", estado(r["Tecno"]))
        st.write("SOAT:", estado(r["SOAT"]))
        st.divider()

# ---------------- ALERTAS ----------------
if menu == "Alertas":

    data = []

    for _, r in df.iterrows():
        for t in ["Licencia","Tecno","SOAT"]:
            f = r[t]
            if pd.notna(f) and f.date() <= hoy:
                data.append({
                    "Nombre": r["Nombre"],
                    "Documento": t,
                    "Fecha": f.date()
                })

    if data:
        df_alertas = pd.DataFrame(data)
        st.dataframe(df_alertas)

        if st.button("Enviar Telegram"):
            msg = "\n".join([f"{x['Nombre']} → {x['Documento']}" for x in data])
            enviar_telegram(msg)

# ---------------- SOPORTES CLOUD ----------------
if menu == "Soportes":

    nombre = st.selectbox("Funcionario", df["Nombre"])

    files = st.file_uploader("Subir", accept_multiple_files=True)

    if files:
        for f in files:
            blob = bucket.blob(f"{nombre}/{f.name}")
            blob.upload_from_string(f.getvalue())
        st.success("Subido a la nube")

    blobs = bucket.list_blobs(prefix=nombre)

    for b in blobs:
        url = b.generate_signed_url(datetime.timedelta(seconds=3600))
        st.write(f"[Descargar {b.name}]({url})")

# ---------------- ADMIN ----------------
if menu == "Admin":

    st.subheader("Agregar funcionario")

    nombre = st.text_input("Nombre")
    lic = st.date_input("Licencia")
    tec = st.date_input("Tecno")
    soat = st.date_input("SOAT")

    if st.button("Guardar"):
        db.collection("funcionarios").add({
            "Nombre": nombre,
            "Licencia": lic.isoformat(),
            "Tecno": tec.isoformat(),
            "SOAT": soat.isoformat()
        })
        st.success("Guardado")
