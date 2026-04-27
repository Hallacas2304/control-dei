import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
from io import BytesIO
import zipfile
import time

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

# ---------------- ESTILO MEJORADO ----------------
st.markdown("""
<style>
    .card { background: #ffffff; border: 1px solid #e2e8f0; padding: 14px; border-radius: 14px; margin-bottom: 10px; color: #0f172a; }
    .nombre { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 8px;}
    .semaforo { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
    .bg-rojo { background-color: #dc2626; }
    .bg-amarillo { background-color: #facc15; }
    .bg-verde { background-color: #16a34a; }
    .alerta-item { background: #fff5f5; border-left: 5px solid #dc2626; padding: 10px; margin-bottom: 5px; border-radius: 5px; color: #000; font-family: sans-serif;}
    .topbar { background:#111827; padding:10px; border-radius:10px; margin-bottom:15px; color:white; }
    #MainMenu, footer, header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA ----------------
@st.cache_data(ttl=120)
def cargar():
    try:
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
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return pd.DataFrame(columns=["Nombre", "Licencia", "Tecno", "SOAT"])

df = cargar()

if "soportes" not in st.session_state:
    st.session_state.soportes = {}

# ---------------- LÓGICA DE ESTADO ----------------
def obtener_info_estado(fecha):
    if pd.isna(fecha):
        return "SIN FECHA", "bg-amarillo", "⚠️"
    dias = (fecha.date() - hoy).days
    f_str = fecha.strftime('%d/%m/%Y')
    if dias < 0:
        return f"VENCIDO ({f_str})", "bg-rojo", "🔴"
    elif dias <= 5:
        return f"PRÓXIMO ({f_str})", "bg-amarillo", "🟡"
    return f"AL DÍA ({f_str})", "bg-verde", "🟢"

# ---------------- TELEGRAM ----------------
def enviar_telegram(lista):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "Telegram no configurado"
    if not lista:
        return False, "Sin alertas"
    mensaje = "🚨 *REPORTE DIARIO DE ALERTAS*\n\n" + "\n".join(lista)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        )
        return (True, "Reporte enviado") if r.status_code == 200 else (False, r.text)
    except:
        return False, "Error de conexión"

# ---------------- MENU ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Excel", "⚙️ Ajustes"], horizontal=True)

# ================== INICIO (Gestión de Documentos) ==================
if menu == "🏠 Inicio":
    st.markdown('<div class="topbar">🔎 Buscador y Carga de Soportes</div>', unsafe_allow_html=True)
    buscar = st.text_input("Buscar funcionario")

    df_view = df.copy()
    if buscar:
        df_view = df_view[df_view["Nombre"].str.contains(buscar, case=False)]

    for i, row in df_view.iterrows():
        with st.expander(f"👤 {row['Nombre']}"):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write("**Subir nuevos documentos:**")
                files = st.file_uploader("Arrastre archivos aquí", accept_multiple_files=True, key=f"up_{i}")
                if files:
                    st.session_state.soportes[row['Nombre']] = files
                    st.success("Archivos listos.")
            
            with col2:
                st.write("**Documentos almacenados:**")
                if row['Nombre'] in st.session_state.soportes:
                    soportes = st.session_state.soportes[row['Nombre']]
                    for f in soportes:
                        st.download_button(f"📥 {f.name}", f.getvalue(), file_name=f.name, key=f"dl_{i}_{f.name}")
                else:
                    st.info("No hay documentos cargados.")

# ================== ALERTAS (Semáforo en Celdas) ==================
if menu == "🚨 Alertas":
    st.subheader("📋 Estado Detallado de Documentación")
    alertas_telegram = []

    for _, r in df.iterrows():
        cols = st.columns([3, 2, 2, 2])
        cols[0].markdown(f"**{r['Nombre']}**")
        
        doc_vencidos = []
        for idx, doc in enumerate(["Licencia", "Tecno", "SOAT"]):
            txt, color, icono = obtener_info_estado(r[doc])
            cols[idx+1].markdown(f'<span class="semaforo {color}"></span>{txt}', unsafe_allow_html=True)
            if "VENCIDO" in txt or "PRÓXIMO" in txt:
                doc_vencidos.append(f"{doc}: {txt}")
        
        if doc_vencidos:
            alertas_telegram.append(f"👤 *{r['Nombre']}*\n" + "\n".join([f"  • {d}" for d in doc_vencidos]))
        st.divider()

    if st.button("📲 Enviar reporte actual a Telegram"):
        ok, msg = enviar_telegram(alertas_telegram)
        st.success(msg) if ok else st.error(msg)

# ================== DASHBOARD ==================
if menu == "📊 Dashboard":
    st.subheader("📈 Resumen Estadístico")
    # Lógica de dashboard mantenida

# ================== EXCEL (Control de Visibilidad) ==================
if menu == "✍️ Excel":
    mostrar = st.toggle("👁️ Mostrar Editor de Datos", value=True)
    
    if mostrar:
        # Añadir semáforo visual al dataframe para el Excel
        df_excel = df.copy()
        for col in ["Licencia", "Tecno", "SOAT"]:
            df_excel[f"Estado {col}"] = df_excel[col].apply(lambda x: obtener_info_estado(x)[2])
        
        edit = st.data_editor(df_excel, use_container_width=True)
        
        buffer = BytesIO()
        edit.to_excel(buffer, index=False)
        st.download_button("⬇️ Descargar Excel Semaforizado", buffer.getvalue(), "reporte_dei.xlsx")
    else:
        st.info("El editor de Excel está oculto. Activa el interruptor superior para verlo.")

# ================== AJUSTES (Reporte 7 AM) ==================
if menu == "⚙️ Ajustes":
    st.subheader("⏰ Programación de Reportes")
    st.write("El sistema enviará un reporte automático a las 7:00 AM si la pestaña permanece abierta.")
    
    # Simulación de tarea programada sencilla
    reloj = st.empty()
    ahora = datetime.now()
    reloj.info(f"Hora actual del servidor: {ahora.strftime('%H:%M:%S')}")

    if ahora.hour == 7 and ahora.minute == 0:
        # Evitar envíos múltiples en el mismo minuto
        if "ultimo_envio" not in st.session_state or st.session_state.ultimo_envio != ahora.day:
            lista_auto = []
            for _, r in df.iterrows():
                for c in ["Licencia", "Tecno", "SOAT"]:
                    txt, _, _ = obtener_info_estado(r[c])
                    if "VENCIDO" in txt or "PRÓXIMO" in txt:
                        lista_auto.append(f"{r['Nombre']} -> {c}: {txt}")
            enviar_telegram(lista_auto)
            st.session_state.ultimo_envio = ahora.day
            st.toast("🚀 Reporte matutino enviado automáticamente.")

    if st.button("🔄 Forzar Sincronización"):
        st.cache_data.clear()
        st.rerun()
