import streamlit as st
import pandas as pd
from datetime import date
import requests
from io import BytesIO

# --- 1. CONFIGURACIÓN Y ESTILOS (RESTAURADOS) ---
st.set_page_config(page_title="GUDMO 16 - CONTROL TOTAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card-vencido { background: linear-gradient(90deg, #4b0000 0%, #1a0000 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; margin-bottom: 15px; }
    .card-comunicado { background: linear-gradient(90deg, #002b4b 0%, #00111a 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #00a2ff; margin-bottom: 15px; }
    .card-alerta { background: linear-gradient(90deg, #3b2a00 0%, #1a1300 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #ffa500; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

TOKEN_TELEGRAM = "8620464199:AAHgiGA3tGhMTpmipc7XsTtSptyF-NHjHMg"
CHAT_ID = "8081331013"

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        url = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQD9M-2uLoxfRJ_8eU_nrvxoAepaaMdolPGx0pEaYQUqMBo?download=1"
        r = requests.get(url)
        return pd.read_excel(BytesIO(r.content), header=None)
    except: return None

# --- 2. LOGICA DE PROCESAMIENTO ---
df = cargar_datos()

if df is not None:
    hoy = pd.Timestamp(date.today())
    proximo_mes = hoy + pd.Timedelta(days=30)
    
    criticos = []      # Rojos (Vencidos reales sin soporte)
    con_soporte = []   # Azules (Vencidos con comunicado)
    advertencias = []  # Amarillos (A punto de vencer)
    lista_nombres = []

    for i in range(2, len(df)):
        fila = df.iloc[i]
        try:
            nombre = str(fila[2]).upper() # Columna C
            if "NAN" in nombre or "APELLIDOS" in nombre: continue
            lista_nombres.append(nombre)
            
            # FECHAS REALES (I=8, K=10, M=12)
            f_tecno = pd.to_datetime(fila[8], errors='coerce', dayfirst=True)
            f_soat = pd.to_datetime(fila[10], errors='coerce', dayfirst=True)
            f_lic = pd.to_datetime(fila[12], errors='coerce', dayfirst=True)
            
            # COMUNICADO (N=14)
            comunicado = str(fila[14]).strip().upper()
            tiene_oficio = comunicado != "NO APLICA" and "NAN" not in comunicado

            alertas_persona = []
            es_vencido = False
            es_proximo = False

            # Validar contra el reloj, no contra el texto del excel
            documentos = [("TECNO", f_tecno), ("SOAT", f_soat), ("LICENCIA", f_lic)]
            
            for tipo, f in documentos:
                if pd.notna(f):
                    if f <= hoy:
                        alertas_persona.append(f"🚨 {tipo} VENCIDO ({f.date()})")
                        es_vencido = True
                    elif f <= proximo_mes:
                        alertas_persona.append(f"🟡 {tipo} x Vencer ({f.date()})")
                        es_proximo = True

            if alertas_persona:
                info = f"👤 <b>{nombre}</b><br>{'<br>'.join(alertas_persona)}"
                if es_vencido:
                    if tiene_oficio:
                        con_soporte.append(f"{info}<br>🔵 OFICIO: {comunicado}")
                    else:
                        criticos.append(info)
                elif es_proximo:
                    advertencias.append(info)
        except: continue

    # --- 3. INTERFAZ Y FORMULARIO DE ACTUALIZACIÓN ---
    st.title("🛡️ CONSOLA GUDMO 16 - VERIFICACIÓN REAL")
    
    with st.sidebar:
        st.header("📝 Actualizar Novedad")
        nombre_sel = st.selectbox("Seleccione Funcionario", sorted(list(set(lista_nombres))))
        nueva_novedad = st.text_input("Número de Comunicado / Oficio")
        if st.button("Guardar Cambios Localmente"):
            st.info(f"Registrado: {nombre_sel} ahora con oficio {nueva_novedad}. (Para actualizar el Excel de SharePoint directamente se requiere permiso de escritura API).")

    # MÉTRICAS
    m1, m2, m3 = st.columns(3)
    m1.metric("VENCIDOS REALES", len(criticos), delta_color="inverse")
    m2.metric("CON SOPORTE", len(con_soporte))
    m3.metric("PRÓXIMOS", len(advertencias))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 ALERTAS ROJAS (Sin Soporte)")
        for c in criticos:
            st.markdown(f'<div class="card-vencido">{c}</div>', unsafe_allow_html=True)
        
        st.subheader("🔵 CASOS CON COMUNICADO")
        for s in con_soporte:
            st.markdown(f'<div class="card-comunicado">{s}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🟡 ALERTAS AMARILLAS (Preventivas)")
        for a in advertencias:
            st.markdown(f'<div class="card-alerta">{a}</div>', unsafe_allow_html=True)

    # --- 4. TELEGRAM (RESTAURADO AL 100%) ---
    if st.button("🚀 ENVIAR REPORTE A TELEGRAM", use_container_width=True):
        reporte = "🚨 *REPORTE DE VENCIMIENTOS GUDMO 16*\n\n"
        if criticos:
            reporte += "*❌ CRÍTICOS (SIN SOPORTE):*\n" + "\n".join(criticos).replace("<br>", "\n").replace("<b>","").replace("</b>","") + "\n\n"
        if con_soporte:
            reporte += "*ℹ️ CON TRÁMITE:* \n" + "\n".join(con_soporte).replace("<br>", "\n").replace("<b>","").replace("</b>","")
        
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": reporte, "parse_mode": "Markdown"})
        st.success("¡Telegram enviado con éxito!")
else:
    st.error("Error de conexión con SharePoint.")
    
