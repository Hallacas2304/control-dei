import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- CONFIGURACIÓN ESTRATÉGICA ---
st.set_page_config(page_title="Control DEI2 GUDMO 16", layout="wide")

# 1. PEGA AQUÍ TUS DATOS DE TELEGRAM
TOKEN_TELEGRAM = "8056262271:AAGy7x3P-oN1H9T_t7pY_4iQf7-g10T_Q8E" # El que te dio BotFather
CHAT_ID = "6198642735" # El que te dio userinfobot

st.markdown("""
    <style>
    .main { background-color: #1a1d1a; color: white; }
    .vencido-card { background-color: #8c1c1c; padding: 12px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #ff4d4d; color: white; font-size: 14px; }
    .stButton>button { width: 100%; background-color: #2b302b; color: white; border: 1px solid #454d45; }
    .stButton>button:hover { background-color: #3e453e; border: 1px solid #2ecc71; }
    </style>
    """, unsafe_allow_html=True)

ONEDRIVE_LINK = "https://1drv.ms/x/c/64349795a4386b5f/IQCy6Go7F7MRQ6da_vdajGNdAYBXgQ4-3_g-dg05l_mKDCQ?download=1"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except:
        st.error("Error al enviar a Telegram. Revisa la conexión.")

@st.cache_data(ttl=30) 
def cargar_datos():
    try:
        response = requests.get(ONEDRIVE_LINK)
        # header=[0,1] porque tu excel tiene filas de títulos combinadas
        df = pd.read_excel(BytesIO(response.content), header=[0, 1])
        # Unificamos nombres de columnas
        df.columns = [f"{str(a).strip()} {str(b).strip()}".upper().replace("NAN", "").strip() for a, b in df.columns]
        return df
    except:
        return None

# --- SIDEBAR OPERATIVO ---
with st.sidebar:
    st.markdown("### 🛡️ GUDMO 16")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_de_la_Polic%C3%ADa_Nacional_de_Colombia.svg", width=80)
    st.divider()
    btn_actualizar = st.button("🔄 ACTUALIZAR BASE DE DATOS")
    if btn_actualizar:
        st.cache_data.clear()
        st.rerun()

df = cargar_datos()

if df is not None:
    hoy = date.today()
    col_nombre = next((c for c in df.columns if 'APELLIDOS Y NOMBRES' in c), df.columns[2])
    col_cedula = next((c for c in df.columns if 'IDENTIFICACIÓN' in c), df.columns[3])
    col_comunicado = next((c for c in df.columns if 'COMUNICADO' in c), None)
    
    soat_v, tecno_v, lic_v, alertas_telegram = [], [], [], []

    for index, fila in df.iterrows():
        nombre = str(fila[col_nombre])
        if "NAN" in nombre.upper() or "NO." in nombre.upper() or nombre.strip() == "": continue
        
        cedula = str(fila[col_cedula]).split('.')[0]
        identidad = f"🎖️ {nombre} (CC. {cedula})"

        # Escaneo de todas las columnas buscando fechas
        for col in df.columns:
            valor = fila[col]
            if pd.isna(valor) or "VIGENTE" in str(valor).upper(): continue
            
            try:
                # Convertimos a fecha de forma flexible
                fecha_v = pd.to_datetime(valor, errors='coerce').date()
                if fecha_v and fecha_v < hoy:
                    desc_alerta = f"⚠️ {nombre} - Vence {col}: {fecha_v}"
                    if "SOAT" in col:
                        soat_v.append(f"{identidad} - {fecha_v}")
                        alertas_telegram.append(desc_alerta)
                    elif "TECNOMECANICA" in col:
                        tecno_v.append(f"{identidad} - {fecha_v}")
                        alertas_telegram.append(desc_alerta)
                    elif "LICENCIA DE CONDUCCION" in col:
                        lic_v.append(f"{identidad} - {fecha_v}")
                        alertas_telegram.append(desc_alerta)
            except:
                continue

    st.title("🛡️ Control Documentación DEI2 Gudmo 16")

    # Botón para disparar la notificación de Telegram
    if alertas_telegram:
        if st.button("📲 ENVIAR ALERTAS AL TELEGRAM"):
            encabezado = f"🚨 *NOVEDADES DEI2 GUDMO 16* ({hoy})\n\n"
            mensaje_full = encabezado + "\n\n".join(alertas_telegram)
            enviar_telegram(mensaje_full)
            st.success("✅ Reporte enviado a tu celular.")

    # Comunicados
    if col_comunicado:
        comunicados = df[df[col_comunicado].notna() & (df[col_comunicado].str.upper() != "NO APLICA")][ [col_nombre, col_comunicado] ]
        if not comunicados.empty:
            with st.expander("🔔 COMUNICADOS OFICIALES", expanded=True):
                for _, c in comunicados.iterrows():
                    st.markdown(f"📢 **{c[col_nombre]}**: {c[col_comunicado]}")

    st.divider()

    # Columnas de Alerta
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("🔴 **SOAT VENCIDO**")
        for m in set(soat_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
    with c2:
        st.write("🔴 **TECNOMECÁNICA VENCIDA**")
        for m in set(tecno_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)
    with c3:
        st.write("🔴 **LICENCIA VENCIDA**")
        for m in set(lic_v): st.markdown(f'<div class="vencido-card">{m}</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("📋 MATRIZ INTEGRAL")
    
    # Pintar celdas vencidas en la tabla
    def resaltar_rojo(val):
        try:
            f = pd.to_datetime(val, errors='coerce').date()
            if f and f < hoy: return 'background-color: #5c1414; color: white'
        except: pass
        return ''

    st.dataframe(df.style.map(resaltar_rojo), use_container_width=True)

else:
    st.error("Conectando con la base de datos de la Unidad...")
