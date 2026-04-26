import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ESTRATÉGICA ---
st.set_page_config(page_title="DEI2 GUDMO 16", layout="wide")

# 1. VERIFICA ESTOS DATOS (Asegúrate que no tengan espacios al inicio o final)
TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E"
CHAT_ID = "6198642735" 

st.markdown("""
    <style>
    .main { background-color: #1a1d1a; color: white; }
    .vencido-card { background-color: #8c1c1c; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #ff4d4d; color: white; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

# FUNCIÓN CON VERIFICACIÓN DE ENTREGA
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            return True, "✅ ¡Mensaje entregado al celular!"
        else:
            return False, f"❌ Telegram rechazó: {r.json().get('description')}"
    except Exception as e:
        return False, f"❌ Error de red: {e}"

@st.cache_data(ttl=30) 
def cargar_datos():
    try:
        response = requests.get(ONEDRIVE_LINK)
        df = pd.read_excel(BytesIO(response.content), header=[0, 1])
        df.columns = [f"{str(a).strip()} {str(b).strip()}".upper().replace("NAN", "").strip() for a, b in df.columns]
        return df
    except: return None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🛡️ GUDMO 16")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_de_la_Polic%C3%ADa_Nacional_de_Colombia.svg", width=80)
    if st.button("🔄 ACTUALIZAR DATOS"):
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
        if "NAN" in nombre.upper() or "NO." in nombre.upper() or not nombre.strip(): continue
        
        cedula = str(fila[col_cedula]).split('.')[0]
        identidad = f"🎖️ {nombre} (CC. {cedula})"

        for col in df.columns:
            valor = fila[col]
            if pd.isna(valor) or "VIGENTE" in str(valor).upper(): continue
            try:
                fecha_v = pd.to_datetime(valor, errors='coerce').date()
                if fecha_v and fecha_v < hoy:
                    alerta = f"• {nombre}: Venció {col} ({fecha_v})"
                    if "SOAT" in col: soat_v.append(identidad); alertas_telegram.append(alerta)
                    elif "TECNO" in col: tecno_v.append(identidad); alertas_telegram.append(alerta)
                    elif "LICENCIA DE CONDUCCION" in col: lic_v.append(identidad); alertas_telegram.append(alerta)
            except: continue

    st.title("🛡️ Control Documentación DEI2 Gudmo 16")

    # BOTÓN DE ENVÍO CON DIAGNÓSTICO
    if alertas_telegram:
        if st.button("📲 ENVIAR REPORTE AL TELEGRAM"):
            msg_final = f"🚨 *GUDMO 16 - VENCIDOS*\n\n" + "\n".join(set(alertas_telegram))
            exito, respuesta = enviar_telegram(msg_final)
            if exito: st.success(respuesta)
            else: st.error(respuesta)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("🔴 **SOAT**")
        for m in set(soat_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
    with c2:
        st.write("🔴 **TECNO**")
        for m in set(tecno_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
    with c3:
        st.write("🔴 **LICENCIA**")
        for m in set(lic_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)

    st.divider()
    st.dataframe(df.style.map(lambda x: 'background-color: #5c1414' if hasattr(x, 'date') and x.date() < hoy else ''), use_container_width=True)
    
