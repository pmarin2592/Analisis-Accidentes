import streamlit as st
import os
import sys

from PIL import Image

# Añadir la raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Clases internas
from basedatos import GestorBaseDatos as BD
from modelos import ModeloML as ML
# Calcula la ruta absoluta de main.py
BASE_DIR = os.path.dirname(__file__)

# Abre la imagen desde la misma carpeta que main.py
logo_path = os.path.join(BASE_DIR, "cuc.png")
logo = Image.open(logo_path)

st.set_page_config(page_title="Informe Ejecutivo", layout="wide", page_icon="📊")
# Cachear modelo para no reentrenar cada vez
@st.cache_resource
def cargar_modelo():
    return ML.procesar_modelo_ml()
# Menú lateral
st.sidebar.image(logo, width=100)
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Seleccione una opción", ["Inicio", "Formulario de Predicción","Analisis EDA"])

if opcion == "Inicio":
    col1, col2, col3 = st.columns(3)
    col1.metric("Accidentes (últ. mes)", 120, "-5%")
    col2.metric("Tasa (% población)", 0.03, "+0.2pp")
    col3.metric("Tiempo resp. medio", "14 min", "-1 min")
    st.markdown("---")
    st.subheader("Tendencia de Accidentes por Provincia")
    # Aquí añadirías un gráfico Plotly con st.plotly_chart(...)
    st.write("En el último trimestre, la provincia X acumuló un 20 % más de incidentes que…")

elif opcion == "Formulario de Predicción":
    st.title("Formulario para Predecir Accidentes")
    st.write("Complete los campos para obtener una predicción.")

    # Campos del formulario
    provincia = st.selectbox("Provincia", BD.obtener_list_provincias())
    if provincia:
        canton = st.selectbox("Cantón", BD.obtener_list_cantones(provincia))
    else:
        canton = st.selectbox("Cantón", ["Seleccione una provincia primero"], disabled=True)

    if provincia and canton:
        distrito = st.selectbox("Distrito", BD.obtener_list_distritos(provincia, canton))
    else:
        distrito = st.selectbox("Distrito", ["Seleccione un cantón primero"], disabled=True)

    tipo_ruta = st.selectbox("Tipo de Ruta", ["Nacional", "Cantonal"])
    dia_semana = st.selectbox("Día de la Semana",
                              ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"])
    lluvia_acumulada = st.number_input("Lluvia Acumulada (mm)", min_value=0.0, step=0.1, max_value=100)
    hora = st.time_input("Hora del Evento")

    if st.button("Predecir"):
        datos = {
            'provincia': provincia,
            'canton': canton,
            'distrito': distrito,
            'tipo_ruta': tipo_ruta,
            'dia_semana': dia_semana,
            'lluvia_acumulada': lluvia_acumulada,
            'hora': hora.strftime('%H:%M:%S')
        }
        # Cargar modelo y log del entrenamiento
        modelo, log = cargar_modelo()

        # Realizar predicción
        resultado = ML.predecir_nuevo(modelo, **datos)

        st.success("✅ Predicción realizada con éxito")

        with st.expander("Ver resultados de la predicción", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Predicción", "🚨 Accidente" if resultado['prediccion'] == 'SI' else "✅ No Accidente")
            with col2:
                st.write("**Probabilidades por clase:**")
                st.json(resultado['probabilidad'])

        with st.expander("🔍 Detalles del entrenamiento y validación"):
            st.code(log)

        st.toast(f"Resultado: {'Accidente' if resultado['prediccion'] == 1 else 'No Accidente'}", icon="📊")

elif opcion == "Analisis EDA":
    st.title("Analisis EDA")
    st.write("Bienvenido al Analisis EDA. Aquí podrás ver estadísticas clave del negocio.")