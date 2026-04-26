EXCEL_URL = "https://correopoliciagov-my.sharepoint.com/:x:/g/personal/omar_vela3592_correo_policia_gov_co/IQBJ321DA_EpQq6ktF9F1qMjAd8YHNp-UUwLG-uAsvmaFm8?download=1"

@st.cache_data(ttl=300)
def cargar_datos():
    import requests
    from io import BytesIO
    import pandas as pd

    response = requests.get(EXCEL_URL, timeout=20)
    response.raise_for_status()

    file = BytesIO(response.content)

    df = pd.read_excel(file, engine="openpyxl")

    # ya viene limpio
    df = df[["Nombre", "Licencia", "Tecnomecanica", "SOAT"]]

    # fechas
    for col in ["Licencia", "Tecnomecanica", "SOAT"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df
