def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            st.success("✅ ¡Mensaje enviado con éxito al celular!")
        else:
            st.error(f"❌ Telegram rechazó el mensaje: {r.text}")
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
