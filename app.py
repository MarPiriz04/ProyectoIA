import streamlit as st
import pandas as pd
import google.generativeai as genai
from docx import Document
from io import BytesIO
import re
import requests
from bs4 import BeautifulSoup
import PyPDF2
import os

# Configuración inicial de la API de Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("La clave de la API de Gemini no está configurada. Por favor, configúrala en las variables de entorno.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Validar URLs
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# Función para leer archivos
def read_file(file, file_type):
    try:
        if file_type in ["xlsx", "xls"]:  # Para Excel
            return pd.read_excel(file, engine='openpyxl'), "excel/csv"
        elif file_type == "csv":  # Para CSV
            return pd.read_csv(file, encoding='latin1', on_bad_lines='skip'), "excel/csv"
        elif file_type == "docx":  # Para Word
            document = Document(file)
            text = "\n".join([paragraph.text for paragraph in document.paragraphs])
            return pd.DataFrame([text], columns=['text']), "word"
        elif file_type == "pdf":  # Para PDF
            pdf_reader = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            return pd.DataFrame([text], columns=['text']), "pdf"
        elif file_type == "web":  # Para URL
            response = requests.get(file, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(separator='\n')
            return pd.DataFrame([text], columns=['text']), "web"
        else:
            st.error("Tipo de archivo no soportado.")
            return pd.DataFrame(), "none"
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame(), "none"

# Función para filtrar columnas por tipo de dato
def filter_columns(df):
    filtered_df = df.copy()

    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):  # Filtro para columnas numéricas
            min_value = df[column].min()
            max_value = df[column].max()
            filter_value = st.slider(f"Selecciona el rango para filtrar '{column}'", min_value=min_value, max_value=max_value, value=(min_value, max_value))
            filtered_df = filtered_df[(filtered_df[column] >= filter_value[0]) & (filtered_df[column] <= filter_value[1])]
        elif pd.api.types.is_string_dtype(df[column]):  # Filtro para columnas de texto
            unique_values = df[column].dropna().unique()
            selected_values = st.multiselect(f"Selecciona los valores de la columna '{column}'", unique_values)
            if selected_values:
                filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
        elif pd.api.types.is_datetime64_any_dtype(df[column]):  # Filtro para columnas de fecha
            min_date = df[column].min()
            max_date = df[column].max()
            filter_date = st.date_input(f"Selecciona las fechas para filtrar '{column}'", value=(min_date, max_date))
            filtered_df = filtered_df[(df[column] >= filter_date[0]) & (df[column] <= filter_date[1])]

    return filtered_df

# Función para generar el informe
def generate_prompt(context_text, df_display):
    prompt = f"""
        Eres un analista experto en análisis de ventas. Realiza un análisis exhaustivo de los datos de ventas proporcionados.
        **Contexto:** {context_text}.
        **Datos:** {df_display.to_string()}.
        Identifica los productos más vendidos, los que generaron mayor rentabilidad y cualquier otra observación relevante sobre el rendimiento de ventas.
        Proporciona insights clave y recomendaciones estratégicas basadas en el análisis.
    """
    return prompt

# Interfaz de usuario
uploaded_file = st.file_uploader("Carga tu archivo (Excel, CSV, Word, PDF)", type=["xls", "xlsx", "csv", "docx", "pdf"])
web_url = st.text_input("O ingresa una URL")
context_text = st.text_area("Describe el contexto del análisis")

df, data_type = pd.DataFrame(), "none"

# Gestión de la carga de archivos
if uploaded_file:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df, data_type = read_file(uploaded_file, file_extension)
elif web_url and is_valid_url(web_url):
    df, data_type = read_file(web_url, "web")

# Mostrar los datos cargados
if data_type != "none" and not df.empty:
    st.success("Datos cargados correctamente.")
    df = df.astype(str) if data_type in ["pdf", "word", "web"] else df
    st.dataframe(df)

    filtered_df = filter_columns(df)
    st.write(f"Datos después del filtrado: {filtered_df.shape[0]} filas restantes")

    if filtered_df.empty:
        st.warning("Los filtros aplicados han dejado el conjunto de datos vacío. Intenta ajustar los filtros.")
    else:
        df_display = filtered_df.head(100)
        if st.button("Empezar el análisis de ventas 🚀"):
            prompt = generate_prompt(context_text, df_display)
            try:
                contents = [
                    {"role": "user", "parts": [prompt]}
                ]
                response = model.generate_content(contents)
                informe = response.text
                st.write("## Informe de Análisis de Ventas Generado")
                st.caption("Informe generado por Veracierto AI")
                st.markdown(informe)

                # Guardar como Word
                doc = Document()
                doc.add_heading('Informe Generado por Veracierto AI', 0)
                for line in informe.splitlines():
                    doc.add_paragraph(line)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button("Descargar informe Word", buffer, "informe.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            except Exception as e:
                st.error(f"Error al generar informe: {e}")
else:
    st.info("Cargá un archivo o ingresá una URL para comenzar.")