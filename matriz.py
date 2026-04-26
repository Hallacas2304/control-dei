import streamlit as st
import pandas as pd
import requests
from datetime import date
from io import BytesIO

st.set_page_config(page_title="Control Documentos", layout="wide")

EXCEL_URL = "TU_LINK_AQUI"

# ---------------- CARGAR Y LIMPIAR ----------------
@st.cache_data(ttl=300)
def cargar_y_limpiar():
    try:
        response = requests.get(EXCEL_URL, timeout=20)
        response.raise_for_status()

        file = BytesIO(response.content)

        df = pd.read_excel(file, engine="openpyxl", header=None)

        # 🔥 FILTRAR FILAS QUE REALMENTE TENGAN NOMBRES
        df = df[df[0].astype(str).str.contains(" ", na=False)]

        # Tomar solo primeras 4 columnas
        df = df.iloc[:, :4].copy()

        df.columns = ["Nombre", "Licencia", "Tecnomecanica", "SOAT"]

        # Convertir fechas (aunque estén mal)
        for col in ["Licencia", "Tecnomecanica", "SOAT"]:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        # Eliminar filas completamente vacías
        df = df.dropna(subset=["Nombre"])

        return df

    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = cargar_y_limpiar()

# ---------------- MOSTRAR ----------------
st.subheader("📊 Datos limpios")
st.dataframe(df)

# ---------------- CREAR EXCEL NUEVO ----------------
def generar_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output

if not df.empty:
    excel_file = generar_excel(df)

    st.download_button(
        label="📥 Descargar Excel limpio",
        data=excel_file,
        file_name="documentos_limpios.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
