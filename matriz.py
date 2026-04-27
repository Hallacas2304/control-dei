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
        # Limpiar nombres de columnas
        df.columns = df.columns.astype(str).str.strip().str.lower()
        
        # Identificación flexible de columnas
        col_nombre = next((c for c in df.columns if "nombre" in c), None)
        col_lic = next((c for c in df.columns if "licencia" in c), None)
        col_tec = next((c for c in df.columns if "tecno" in c), None)
        col_soat = next((c for c in df.columns if "soat" in c), None)
        
        # Validar que las columnas existan
        if not col_nombre:
            st.error("No se encontró la columna de Nombres en el archivo original.")
            return pd.DataFrame()

        # Seleccionar y renombrar
        df = df[[col_nombre, col_lic, col_tec, col_soat]].copy()
        df.columns = ["Nombre", "Licencia", "Tecno", "SOAT"]
        
        # Convertir a fecha asegurando que el Nombre se mantenga como texto
        df["Nombre"] = df["Nombre"].astype(str).str.upper()
        for c in ["Licencia", "Tecno", "SOAT"]:
            df[c] = pd.to_datetime(df[c], errors="coerce")
            
        return df
    except Exception as e:
        st.error(f"Error al procesar el Excel: {e}")
        return pd.DataFrame(columns=["Nombre", "Licencia", "Tecno", "SOAT"])

df = cargar_datos()

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
        return False, "Credenciales no configuradas."
    mensaje = "🚨 *CONTROL DOCUMENTAL DEI*\n" + "_" + datetime.now().strftime('%Y-%m-%d %H:%M') + "_\n\n" + "\n\n".join(lista)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        )
        return (True, "OK") if r.status_code == 200 else (False, r.status_code)
    except:
        return False, "Error de conexión."

# ---------------- NAVEGACIÓN ----------------
menu = st.radio("", ["🏠 Inicio", "🚨 Alertas", "📊 Dashboard", "✍️ Excel", "⚙️ Ajustes"], horizontal=True)

if menu == "🏠 Inicio":
    st.markdown('<div class="topbar">📂 GESTIÓN DE SOPORTES</div>', unsafe_allow_html=True)
    buscar = st.text_input("🔍 Buscar por nombre...")
    df_v = df[df["Nombre"].str.contains(buscar, case=False, na=False)] if buscar else df
    
    for i, row in df_v.iterrows():
        with st.expander(f"👤 {row['Nombre']}"):
            c1, c2 = st.columns(2)
            with c1:
                f = st.file_uploader("Subir archivos", accept_multiple_files=True, key=f"f_{i}")
                if f: st.session_state.soportes[row['Nombre']] = f
            with c2:
                if row['Nombre'] in st.session_state.soportes:
                    for arch in st.session_state.soportes[row['Nombre']]:
                        st.download_button(f"⬇️ {arch.name}", arch.getvalue(), file_name=arch.name, key=f"b_{i}_{arch.name}")
                else: st.info("Sin archivos.")

if menu == "🚨 Alertas":
    st.subheader("⚠️ Documentos por Vencer o Vencidos")
    for _, r in df.iterrows():
        vencido = any(pd.notna(r[c]) and (r[c].date() - hoy_date).days <= 5 for c in ["Licencia", "Tecno", "SOAT"])
        if vencido:
            st.markdown(f'<div class="card"><div class="nombre">{r["Nombre"]}</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            for idx, doc in enumerate(["Licencia", "Tecno", "SOAT"]):
                txt, color, _ = obtener_info_estado(r[doc])
                cols[idx].markdown(f'<span class="semaforo {color}"></span>**{doc}**: {txt}', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

if menu == "✍️ Excel":
    st.subheader("✍️ Editor y Descarga de Reporte")
    if not df.empty:
        editado = st.data_editor(df, use_container_width=True, hide_index=True)
        
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            # Exportar asegurando que todas las columnas (incluyendo Nombre) se incluyan
            editado.to_excel(writer, index=False, sheet_name='Reporte')
            workbook = writer.book
            worksheet = writer.sheets['Reporte']

            # Estilos
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            fuente_roja = Font(color="FF0000", bold=True)

            for r_idx, row in enumerate(worksheet.iter_rows(min_row=1, max_row=len(editado)+1), start=1):
                for c_idx, cell in enumerate(row, start=1):
                    cell.border = thin_border
                    
                    # Colorear fechas vencidas (Columnas 2, 3, 4)
                    if r_idx > 1 and c_idx in [2, 3, 4]:
                        if cell.value and isinstance(cell.value, datetime):
                            if cell.value.date() < hoy_date:
                                cell.font = fuente_roja

            # Ajuste de ancho de columnas
            for column_cells in worksheet.columns:
                # Asegurar que no falle si la celda es None
                vals = [len(str(cell.value)) for cell in column_cells if cell.value is not None]
                length = max(vals) if vals else 10
                worksheet.column_dimensions[column_cells[0].column_letter].width = length + 5

        st.download_button(
            label="📥 Descargar Excel con Formato",
            data=buf.getvalue(),
            file_name=f"Reporte_DEI_{hoy_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No hay datos para mostrar en el editor.")

if menu == "⚙️ Ajustes":
    st.subheader("⚙️ Configuración")
    if st.button("🚀 Enviar Reporte a Telegram Ahora"):
        lista_m = []
        for _, r in df.iterrows():
            alrt = [f"  {obtener_info_estado(r[c])[2]} {c}: {obtener_info_estado(r[c])[0]}" for c in ["Licencia", "Tecno", "SOAT"] if "VENCIDO" in obtener_info_estado(r[c])[0] or "PRÓXIMO" in obtener_info_estado(r[c])[0]]
            if alrt: lista_m.append(f"👤 *{r['Nombre']}*\n" + "\n".join(alrt))
        
        if lista_m:
            ok, msg = enviar_telegram(lista_m)
            if ok: st.success("✅ Enviado.")
            else: st.error(f"❌ Error: {msg}")
        else:
            st.info("No hay documentos vencidos.")

    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()
