import streamlit as st import requests

Configuración de página

st.set_page_config(page_title="Reportes", layout="wide")

Estilo para botones rojos

st.markdown(""" <style> div.stButton > button { background-color: red; color: white; border-radius: 8px; height: 3em; width: 100%; font-weight: bold; } </style> """, unsafe_allow_html=True)

Función Telegram (ya funcionando)

def enviar_telegram(mensaje): TOKEN = "TU_BOT_TOKEN" CHAT_ID = "TU_CHAT_ID" url = f"https://api.telegram.org/bot{TOKEN}/sendMessage" payload = { "chat_id": CHAT_ID, "text": mensaje } requests.post(url, data=payload)

Datos simulados (puedes conectar los tuyos)

reportes = [ {"nombre": "Reporte 1", "estado": "Vacío"}, {"nombre": "Reporte 2", "estado": "Completo"}, {"nombre": "Reporte 3", "estado": "Vacío"}, ]

st.title("Panel de Reportes")

Mostrar reportes en columnas

cols = st.columns(len(reportes))

for i, reporte in enumerate(reportes): with cols[i]: estado = reporte["estado"]

# Reemplazo de texto
    if estado.lower() == "vacío":
        estado_mostrar = "En resumen comunicado oficial"
    else:
        estado_mostrar = estado

    st.write(f"**{reporte['nombre']}**")
    st.write(estado_mostrar)

    if st.button(f"Enviar {reporte['nombre']}", key=i):
        mensaje = f"{reporte['nombre']} - {estado_mostrar}"
        enviar_telegram(mensaje)
        st.success("Enviado correctamente")
