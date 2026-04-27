import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
from io import BytesIO
import zipfile

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

# ---------------- ESTILO PERSONALIZADO ----------------
st.markdown("""
<style>
    .card { background: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 14px; margin-bottom: 10px; color: #0f172a; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .nombre { font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 8px; text-transform: uppercase; }
    .semaforo { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; border: 1px solid rgba(0,0,0,0.1); }
    .bg-rojo { background-color: #dc2626; }
    .bg-amarillo { background-color: #facc15; }
    .bg-verde { background-color: #16a34a; }
    .topbar { background:#111827; padding:12px; border-radius:10px; margin-bottom:15px; color:white; text-align: center; font-weight: bold; }
    #MainMenu, footer, header {visibility:hidden;}
    .block-container {padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA DE DATOS ----------------
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
        st.error(f"Error en la conexión: {e}")
        return pd.DataFrame(columns=["Nombre", "Licencia", "Tecno", "SOAT"])

df = cargar()

if "soportes" not in st.session_state:
    st.session_state.soportes = {}

# ---------------- LÓGICA DE ALERTAS ----------------
def obtener_info_estado(fecha):
    if pd.isna(fecha):
        return "POR DEFINIR", "bg-amarillo", "⚠️"
    dias = (fecha.date() - hoy).days
    f_str = fecha.strftime('%d/%m/%Y')
    if dias < 0:
        return f"VENCIDO ({f_str})", "bg-rojo", "🔴"
    elif dias <= 5:
        return f"PRÓXIMO ({f_str})", "bg-amarillo", "🟡"
    return f"AL DÍA ({f_str})", "bg-verde", "🟢"

# ---------------- ENVÍO TELEGRAM ----------------
def enviar_telegram(lista):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "Telegram no configurado"
    if not lista:
        return False, "No hay alertas"
    
    mensaje = "🚨 *CONTROL DOCUMENTAL DEI*\n" + "_" + datetime.now().strftime('%Y-%m-%d %H:%M') + "_\n\n" + "\n\n".join(lista)
    
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        )
        return (True, "Enviado") if r.status_code == 200 else (False, f"Error {r.status_code}")
    except:
        return False, "Error de red"

# ---------------- INTERFAZ ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Excel", "⚙️ Ajustes"], horizontal=True)

# --- INICIO ---
if menu == "🏠 Inicio":
    st.markdown('<div class="topbar">📂 GESTIÓN DE DOCUMENTOS</div>', unsafe_allow_html=True)
    buscar = st.text_input("Filtrar por nombre...")
    df_view = df[df["Nombre"].str.contains(buscar, case=False)] if buscar else df

    for i, row in df_view.iterrows():
        with st.expander(f"👤 {row['Nombre']}"):
            c1, c2 = st.columns(2)
            with c1:
                f_up = st.file_uploader("Subir archivo", accept_multiple_files=True, key=f"file_{i}")
                if f_up: st.session_state.soportes[row['Nombre']] = f_up
            with c2:
                if row['Nombre'] in st.session_state.soportes:
                    for f in st.session_state.soportes[row['Nombre']]:
                        st.download_button(f"⬇️ {f.name}", f.getvalue(), file_name=f.name, key=f"btn_{i}_{f.name}")
                else: st.info("Sin archivos.")

# --- ALERTAS ---
if menu == "🚨 Alertas":
    st.subheader("⚠️ Estado de Vencimientos")
    for _, r in df.iterrows():
        persona_vencida = any(pd.notna(r[c]) and (r[c].date() - hoy).days <= 5 for c in ["Licencia", "Tecno", "SOAT"])
        if persona_vencida:
            st.markdown(f'<div class="card"><div class="nombre">{r["Nombre"]}</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            for idx, doc in enumerate(["Licencia", "Tecno", "SOAT"]):
                txt, color, _ = obtener_info_estado(r[doc])
                cols[idx].markdown(f'<span class="semaforo {color}"></span>**{doc}**: {txt}', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.subheader("📊 Análisis de Datos")
    vencidos = {c: (df[c] < pd.to_datetime(hoy)).sum() for c in ["SOAT", "Tecno", "Licencia"]}
    st.bar_chart(pd.Series(vencidos))

# --- EXCEL (AJUSTADO PARA ELIMINAR NUMERALES) ---
if menu == "✍️ Excel":
    if st.toggle("👁️ Ver/Editar base de datos", value=True):
        editado = st.data_editor(df, use_container_width=True)
        
        buf = BytesIO()
        # Usamos xlsxwriter para ajustar el ancho de columnas
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            editado.to_excel(writer, index=False, sheet_name='Reporte')
            workbook = writer.book
            worksheet = writer.sheets['Reporte']
            
            # Ajuste automático de columnas
            for i, col in enumerate(editado.columns):
                column_len = max(editado[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)
        
        st.download_button("📥 Descargar Excel Ajustado", buf.getvalue(), "control_dei.xlsx")

# --- AJUSTES ---
if menu == "⚙️ Ajustes":
    st.subheader("⚙️ Configuración y Reportes")
    ahora = datetime.now()
    st.info(f"🕒 Hora del servidor: {ahora.strftime('%H:%M:%S')}")

    if ahora.hour == 7 and ahora.minute == 0:
        if "auto_dia" not in st.session_state or st.session_state.auto_dia != ahora.day:
            lista_auto = []
            for _, r in df.iterrows():
                alertas_p = [f"  {obtener_info_estado(r[c])[2]} {c}: {obtener_info_estado(r[c])[0]}" 
                           for c in ["Licencia", "Tecno", "SOAT"] 
                           if "VENCIDO" in obtener_info_estado(r[c])[0] or "PRÓXIMO" in obtener_info_estado(r[c])[0]]
                if alertas_p: lista_auto.append(f"👤 *{r['Nombre']}*\n" + "\n".join(alertas_p))
            if lista_auto:
                enviar_telegram(lista_auto)
                st.session_state.auto_dia = ahora.day

    st.divider()
    st.subheader("📤 Enviar Reporte Manual")
    
    if st.button("🚀 Enviar a Telegram Ahora", key="manual_ajustes"):
        lista_m = []
        for _, r in df.iterrows():
            alertas_p = [f"  {obtener_info_estado(r[c])[2]} {c}: {obtener_info_estado(r[c])[0]}" 
                       for c in ["Licencia", "Tecno", "SOAT"] 
                       if "VENCIDO" in obtener_info_estado(r[c])[0] or "PRÓXIMO" in obtener_info_estado(r[c])[0]]
            if alertas_p: lista_m.append(f"👤 *{r['Nombre']}*\n" + "\n".join(alertas_p))
        
        if lista_m:
            ok, msg = enviar_telegram(lista_m)
            if ok:
                st.success("✅ Reporte enviado correctamente.")
            else:
                st.error(f"❌ Error: {msg}")
        else:
            st.info("No hay documentos vencidos.")

    st.divider()
    if st.button("🔄 Refrescar base de datos"):
        st.cache_data.clear()
        st.rerun()
