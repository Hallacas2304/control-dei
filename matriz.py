import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Control SOAT y Tecno", layout="wide")
st.title("🛡️ CONTROL EXCLUSIVO: SOAT Y TECNO")

archivo = st.file_uploader("📂 CARGA TU EXCEL AQUÍ", type=["xlsx"])

if archivo is not None:
    try:
        df = pd.read_excel(archivo)
        hoy = date.today()

        # 1. Función para decidir quién está Vencido (Solo mira SOAT y Tecno)
        def chequear_vencimiento(fila):
            vencido = False
            # REGLA DE ORO: Solo miramos las columnas Unnamed: 9 (Tecno) y Unnamed: 11 (SOAT)
            # o cualquier columna que diga TECNO o SOAT pero NUNCA Licencia.
            for col, valor in fila.items():
                nombre = str(col).upper()
                if ('TECNO' in nombre or 'SOAT' in nombre or 'UNNAMED' in nombre) and 'LICENCIA' not in nombre:
                    try:
                        fecha = pd.to_datetime(valor).date()
                        if fecha < hoy:
                            vencido = True
                            break
                    except:
                        continue
            return "🔴 VENCIDO" if vencido else "🟢 VIGENTE"

        df['ESTADO VEHÍCULO'] = df.apply(chequear_vencimiento, axis=1)

        # 2. Función para pintar (Pintamos todo EXCEPTO Licencias e IDs)
        def colorear_final(datatable):
            estilos = pd.DataFrame('', index=datatable.index, columns=datatable.columns)
            for col in datatable.columns:
                nombre = str(col).upper()
                # BLOQUEO: Si es licencia o identificación, no se pinta nada
                if 'LICENCIA' in nombre or 'IDENTIFICACIÓN' in nombre or 'CELULAR' in nombre:
                    continue
                
                for idx in datatable.index:
                    try:
                        val = datatable.loc[idx, col]
                        f = pd.to_datetime(val).date()
                        if f < hoy:
                            estilos.loc[idx, col] = 'background-color: #ffcccc'
                        elif (f - hoy).days <= 30:
                            estilos.loc[idx, col] = 'background-color: #ffffcc'
                        else:
                            estilos.loc[idx, col] = 'background-color: #ccffcc'
                    except:
                        continue
            return estilos

        # 3. Separación Real
        vencidos = df[df['ESTADO VEHÍCULO'] == "🔴 VENCIDO"].copy()
        vigentes = df[df['ESTADO VEHÍCULO'] == "🟢 VIGENTE"].copy()

        if not vencidos.empty:
            st.error(f"🚨 VEHÍCULOS CON SOAT O TECNO VENCIDOS: {len(vencidos)}")
            st.dataframe(vencidos.style.apply(colorear_final, axis=None), use_container_width=True)
        else:
            st.success("✅ ¡Todos los vehículos tienen SOAT y Tecno al día!")
        
        with st.expander("Ver resto del personal (Vigentes o solo Licencia vencida)"):
            st.dataframe(vigentes.style.apply(colorear_final, axis=None), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")