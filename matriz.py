import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="DEI2 GUDMO 16", layout="wide")

# SUSTITUYE ESTOS DATOS CON LOS QUE OBTUVISTE
TOKEN_TELEGRAM = "AQUÍ_PEGA_TU_TOKEN_DE_BOTFATHER"
CHAT_ID = "AQUÍ_PEGA_TU_ID_DE_USERINFOBOT"

st.markdown("""
    <style>
    .main { background-color: #1a1d1a; color: white; }
    .vencido-card { background-color: #8c1c1c; padding: 12px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #ff4d4d; color: white; }
    </style>
    """, unsafe_allow_html=True)

ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try: requests.post(url, data=payload)
    except: pass

@st.cache_data(ttl=30) 
def cargar_datos():
    try:
        response = requests.get(ONEDRIVE_LINK)
        df = pd.read_excel(BytesIO(response.content), header=[0, 1])
        df.columns = [f"{str(a).strip()} {str(b).strip()}".upper() for a, b in df.columns]
        return df
    except: return None

with st.sidebar:
    st.markdown("## 🛡️ UNDMO")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_de_la_Polic%C3%ADa_Nacional_de_Colombia.svg", width=80)
    if st.button("🔄 ACTUALIZAR Y NOTIFICAR"):
        st.cache_data.clear()
        st.rerun()

df = cargar_datos()

if df is not None:
    hoy = date.today()
    col_nombre = next((c for c in df.columns if 'APELLIDOS Y NOMBRES' in c), df.columns[2])
    col_cedula = next((c for c in df.columns if 'IDENTIFICACIÓN' in c), df.columns[3])
    
    soat_v, tecno_v, lic_v, alertas_telegram = [], [], [], []

    for index, fila in df.iterrows():
        nombre = str(fila[col_nombre])
        if "NAN" in nombre.upper() or "NO." in nombre.upper(): continue
        cedula = str(fila[col_cedula]).split('.')[0]
        identidad = f"🎖️ {nombre} (CC. {cedula})"

        for col in df.columns:
            valor = fila[col]
            if pd.isna(valor) or "VIGENTE" in str(valor).upper(): continue
            try:
                fecha_v = pd.to_datetime(valor, errors='coerce').date()
                if fecha_v and fecha_v < hoy:
                    msg = f"📌 {nombre}\n⚠️ Venció {col}: {fecha_v}"
                    if "SOAT" in col: soat_v.append(identidad); alertas_telegram.append(msg)
                    elif "TECNO" in col: tecno_v.append(identidad); alertas_telegram.append(msg)
                    elif "LICENCIA DE CONDUCCION" in col: lic_v.append(identidad); alertas_telegram.append(msg)
            except: continue

    st.title("🛡️ Control Documentación DEI2 Gudmo 16")

    # Si hay alertas nuevas, enviar a Telegram una sola vez
    if alertas_telegram and st.sidebar.button("📲 ENVIAR REPORTE AL CELULAR"):
        reporte = "🚨 *REPORTE DE VENCIMIENTOS GUDMO 16*\n\n" + "\n\n".join(alertas_telegram[:10])
        enviar_telegram(reporte)
        st.success("✅ Alerta enviada a Telegram")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("🔴 **SOAT**")
        for m in set(soat_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
    with c2:
        st.write("🔴 **TECNOMECÁNICA**")
        for m in set(tecno_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
    with c3:
        st.write("🔴 **LICENCIA**")
        for m in set(lic_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)

    st.divider()
    st.dataframe(df.style.map(lambda x: 'background-color: #5c1414' if hasattr(x, 'date') and x.date() < hoy else ''), use_container_width=True)

else: st.error("Error cargando datos...")
    
