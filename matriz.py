import streamlit as st
import requests

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Panel de Reportes", layout="wide")

# 🔴 ESTILO BOTONES ROJOS
st.markdown("""
    <style>
    div.stButton > button {
        background-color: red;
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- TELEGRAM ----------------
def enviar_telegram(mensaje):
    TOKEN = "TU_BOT_TOKEN"
    CHAT_ID = "TU_CHAT_ID"

    if not TOKEN or not CHAT_ID:
        st.error("Token o Chat ID no configurado")
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        return True
    else:
        st.error("Error enviando a Telegram")
        st.write(response.text)
        return False

# ---------------- DATOS ----------------
# (Esto puedes conectarlo a tus inputs reales)
reportes = [
    {"nombre": "Reporte Ventas", "estado": "Vacío"},
    {"nombre": "Reporte Clientes", "estado": "Completo"},
    {"nombre": "Reporte Inventario", "estado": "Vacío"},
    {"nombre": "Reporte Diario", "estado": "En proceso"},
]

# ---------------- UI ----------------
st.title("📊 Panel de Reportes")

cols = st.columns(len(reportes))

for i, reporte in enumerate(reportes):
    with cols[i]:

        nombre = reporte["nombre"]
        estado = reporte["estado"]

        # 🧾 CAMBIO DE TEXTO
        if estado.lower() == "vacío":
            estado_mostrar = "En resumen comunicado oficial"
        else:
            estado_mostrar = estado

        st.subheader(nombre)
        st.write(estado_mostrar)

        # 🔑 KEY ÚNICA (evita errores)
        boton_key = f"btn_{i}_{nombre}"

        if st.button(f"Enviar {nombre}", key=boton_key):
            mensaje = f"{nombre} - {estado_mostrar}"

            if enviar_telegram(mensaje):
                st.success("✅ Enviado correctamente")
            else:
                st.error("❌ No se pudo enviar")

# ---------------- EXTRA (OPCIONAL PERO ÚTIL) ----------------
st.markdown("---")
st.info("Si no llegan los mensajes, revisa que el bot haya iniciado conversación contigo en Telegram.")
