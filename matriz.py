import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
from io import BytesIO
from openpyxl.styles import Font, Border, Side

# ---------------- CONFIGURACIÓN INICIAL ----------------
st.set_page_config(page_title="DEI Control", layout="wide")

# URL de descarga directa de tu Excel en SharePoint
EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

# Intentar cargar credenciales de Telegram desde Secrets
try:
    TELEGRAM_TOKEN = st.secrets["TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    TELEGRAM_TOKEN = ""
    CHAT_ID = ""

hoy_dt = datetime.now()
hoy_date = date.today()

# ---------------- ESTILO CSS PERSONALIZADO ----------------
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
</style>
""", unsafe_allow_html=True)

# ---------------- CARGA Y PROCESAMIENTO DE DATOS ----------------
@st.cache_data(ttl=120)
def cargar_datos():
    try:
        r = requests.get(EXCEL_URL)
        df = pd.read_excel(BytesIO(r.content), engine="openpyxl")
        df.columns = df.columns.str.strip().str.lower()
        
        # Identificación dinámica de columnas
        nombre = next(c for c in df.columns if "nombre" in c)
        lic = next(c for c in df.columns if "licencia" in c)
        tec = next(c for c in df.columns if "tecno" in c)
        soat = next(c for c in df.columns if "soat" in c)
        
        df = df[[nombre, lic, tec, soat]]
        df.columns = ["Nombre", "Licencia", "Tecno", "SOAT"]
        
        # Convertir a fecha
        for c in ["Licencia", "Tecno", "SOAT"]:
            df[c] = pd.to_datetime(df[c], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return pd.DataFrame(columns=["Nombre", "Licencia", "Tecno", "SOAT"])

df = cargar_datos()

# Estado para la bandeja de soportes (archivos subidos)
if "soportes" not in st.session_state:
    st.session_state.soportes = {}

# ---------------- FUNCIONES DE APOYO ----------------
def obtener_info_estado(fecha):
    if pd.isna(fecha):
        return "POR DEFINIR", "bg-amarillo", "⚠️"
    dias = (fecha.date() - hoy_date).days
    f_str = fecha.strftime('%d/%m/%Y')
    if dias < 0:
        return f"VENCIDO ({f_str})", "bg-rojo", "🔴"
    elif dias <= 5:
        return f"PRÓXIMO ({f_str})", "bg-amarillo", "🟡"
    return f"AL DÍA ({f_str})", "bg-verde", "🟢"

def enviar_telegram(lista):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "Credenciales de Telegram no configuradas."
    
    mensaje = "🚨 *CONTROL DOCUMENTAL DEI*\n" + "_" + datetime.now().strftime('%Y-%m-%d %H:%M') + "_\n\n" + "\n\n".join(lista)
    
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        )
        return (True, "OK") if r.status_code == 200 else (False, f"Error {r.status_code}")
    except:
        return False, "Error de red al conectar con Telegram."

# ---------------- INTERFAZ NAVEGACIÓN ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Excel", "⚙️ Ajustes"], horizontal=True)

# SECCIÓN 1: GESTIÓN DE DOCUMENTOS
if menu == "🏠 Inicio":
    st.markdown('<div class="topbar">📂 GESTIÓN DE FUNCIONARIOS Y SOPORTES</div>', unsafe_allow_html=True)
    buscar = st.text_input("🔍 Buscar funcionario por nombre...")
    
    df_v = df[df["Nombre"].str.contains(buscar, case=False)] if buscar else df
    
    for i, row in df_v.iterrows():
        with st.expander(f"👤 {row['Nombre']}"):
            c1, c2 = st.columns(2)
            with c1:
                f = st.file_uploader("Subir soportes (PDF/JPG)", accept_multiple_files=True, key=f"f_{i}")
                if f: st.session_state.soportes[row['Nombre']] = f
            with c2:
                if row['Nombre'] in st.session_state.soportes:
                    for arch in st.session_state.soportes[row['Nombre']]:
                        st.download_button(f"⬇️ {arch.name}", arch.getvalue(), file_name=arch.name, key=f"b_{i}_{arch.name}")
                else: st.info("No hay archivos cargados para este funcionario.")

# SECCIÓN 2: VISTA DE ALERTAS (SEMÁFOROS)
if menu == "🚨 Alertas":
    st.subheader("⚠️ Estado de Vencimientos")
    for _, r in df.iterrows():
        vencido = any(pd.notna(r[c]) and (r[c].date() - hoy_date).days <= 5 for c in ["Licencia", "Tecno", "SOAT"])
        if vencido:
            st.markdown(f'<div class="card"><div class="nombre">{r["Nombre"]}</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            for idx, doc in enumerate(["Licencia", "Tecno", "SOAT"]):
                txt, color, _ = obtener_info_estado(r[doc])
                cols[idx].markdown(f'<span class="semaforo {color}"></span>**{doc}**: {txt}', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# SECCIÓN 3: DASHBOARD
if menu == "📊 Dashboard":
    st.subheader("📊 Resumen Estadístico")
    vencidos = {c: (df[c] < pd.to_datetime(hoy_date)).sum() for c in ["SOAT", "Tecno", "Licencia"]}
    st.bar_chart(pd.Series(vencidos))

# SECCIÓN 4: EXCEL CON FORMATO (BORDES Y ROJO)
if menu == "✍️ Excel":
    if st.toggle("👁️ Mostrar Editor de Datos", value=True):
        editado = st.data_editor(df, use_container_width=True)
        
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            editado.to_excel(writer, index=False, sheet_name='Reporte')
            workbook = writer.book
            worksheet = writer.sheets['Reporte']

            # Estilos: Bordes y Fuente Roja
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            fuente_roja = Font(color="FF0000", bold=True)

            for r_idx, row in enumerate(worksheet.iter_rows(min_row=1, max_row=len(editado)+1), start=1):
                for c_idx, cell in enumerate(row, start=1):
                    cell.border = thin_border # Cuadrícula para todas las celdas
                    
                    # Colorear de rojo las fechas vencidas (Columnas 2, 3, 4)
                    if r_idx > 1 and c_idx in [2, 3, 4]:
                        if cell.value and isinstance(cell.value, datetime):
                            if cell.value.date() < hoy_date:
                                cell.font = fuente_roja

            # Ajuste de ancho de columnas para evitar ####
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = length + 3

        st.download_button(
            label="📥 Descargar Excel con Formato",
            data=buf.getvalue(),
            file_name=f"Reporte_DEI_{hoy_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# SECCIÓN 5: AJUSTES Y ENVÍO MANUAL
if menu == "⚙️ Ajustes":
    st.subheader("⚙️ Configuración de Reportes")
    st.info(f"🕒 Hora del servidor: {hoy_dt.strftime('%H:%M:%S')}")
    
    # Reporte Automático 7 AM
    if hoy_dt.hour == 7 and hoy_dt.minute == 0:
        if "auto_enviado" not in st.session_state or st.session_state.auto_enviado != hoy_date.day:
            lista_auto = []
            for _, r in df.iterrows():
                alrt = [f" • {c}: {obtener_info_estado(r[c])[0]}" for c in ["Licencia", "Tecno", "SOAT"] if "VENCIDO" in obtener_info_estado(r[c])[0] or "PRÓXIMO" in obtener_info_estado(r[c])[0]]
                if alrt: lista_auto.append(f"👤 *{r['Nombre']}*\n" + "\n".join(alrt))
            if lista_auto:
                enviar_telegram(lista_auto)
                st.session_state.auto_enviado = hoy_date.day

    st.divider()
    st.subheader("📤 Envío Manual a Telegram")
    if st.button("🚀 Enviar Reporte Ahora", key="manual_btn"):
        lista_m = []
        for _, r in df.iterrows():
            alrt = [f"  {obtener_info_estado(r[c])[2]} {c}: {obtener_info_estado(r[c])[0]}" for c in ["Licencia", "Tecno", "SOAT"] if "VENCIDO" in obtener_info_estado(r[c])[0] or "PRÓXIMO" in obtener_info_estado(r[c])[0]]
            if alrt: lista_m.append(f"👤 *{r['Nombre']}*\n" + "\n".join(alrt))
        
        if lista_m:
            with st.spinner("Conectando con Telegram..."):
                ok, msg = enviar_telegram(lista_m)
                if ok: st.success("✅ Reporte enviado con éxito.")
                else: st.error(f"❌ Error: {msg}")
        else:
            st.info("No se encontraron documentos vencidos para reportar.")

    if st.button("🔄 Forzar Actualización de Base de Datos"):
        st.cache_data.clear()
        st.rerun()
