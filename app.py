import streamlit as st
import pandas as pd
from PIL import Image
import io
import pypdf
import google.generativeai as genai
import pytesseract
import os

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Configure pytesseract (you might need to change the path to the tesseract executable)
# For Windows, you might need to install Tesseract separately and provide the path
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to generate summary using Gemini
def summarize_text_gemini(text):
    if not text.strip():
        return "No hay texto disponible para resumir."
    try:
        model = genai.GenerativeModel('gemini-pro')
        # For long texts, consider breaking them into chunks if the model has input limits
        # This is a basic implementation, more advanced chunking might be needed
        prompt = f"""Actúa como un gerente comercial experto en identificar los productos con más ventas y mayor rentabilidad. Analiza el siguiente texto y proporciona un resumen centrado en identificar estos productos y cualquier información relevante sobre ventas, ingresos o costos que pueda ayudar a determinar la rentabilidad.

Texto a analizar:
{text}
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al generar resumen con Gemini: {e}"

st.title("Generador de Informes de Archivos con IA")

uploaded_file = st.file_uploader("Cargar un archivo (CSV, PDF o Imagen)", type=["csv", "pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_type = uploaded_file.type

    st.write(f"Procesando {uploaded_file.name} ({file_type})")

    if file_type == "text/csv":
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            st.subheader("Contenido del CSV (Primeras 5 filas)")
            st.write(df.head())

            st.subheader("Análisis del CSV")
            st.write("Estadísticas Básicas:")
            st.write(df.describe())

            # Simple trend identification (example: correlation matrix)
            if df.select_dtypes(include=['number']).shape[1] > 1:
                st.write("Matriz de Correlación:")
                st.write(df.corr())

            # Summarize the content (using a string representation of the dataframe)
            st.subheader("Resumen del CSV (IA)")
            csv_summary_text = df.to_string()
            summary = summarize_text_gemini(csv_summary_text)
            st.write(summary)


        except Exception as e:
            st.error(f"Error al leer el archivo CSV: {e}")

    elif file_type == "application/pdf":
        st.subheader("Contenido del PDF")
        try:
            reader = pypdf.PdfReader(uploaded_file)
            pdf_text = ""
            for page_num in range(len(reader.pages)):
                pdf_text += reader.pages[page_num].extract_text()

            st.text_area("Texto Extraído", pdf_text, height=300)

            st.subheader("Análisis del PDF (IA)")
            # Summarize the extracted text
            pdf_summary = summarize_text_gemini(pdf_text)
            st.write("Resumen:")
            st.write(pdf_summary)

            # TODO: Add entity extraction for PDF

        except Exception as e:
            st.error(f"Error al leer el archivo PDF: {e}")

    elif file_type.startswith("image/"):
        try:
            # Read Image
            img = Image.open(uploaded_file)
            st.subheader("Imagen Cargada")
            st.image(img, caption=uploaded_file.name, use_column_width=True)

            st.subheader("Análisis de Imagen (IA)")
            # Perform OCR
            try:
                image_text = pytesseract.image_to_string(img)
                st.write("Texto Extraído (OCR):")
                st.text_area("Texto OCR", image_text, height=200)

                # Summarize the extracted text
                image_summary = summarize_text_gemini(image_text)
                st.write("Resumen del Texto Extraído:")
                st.write(image_summary)

            except pytesseract.TesseractNotFoundError:
                st.error("Tesseract no está instalado o no se encuentra en tu PATH. Por favor, instala Tesseract OCR.")
            except Exception as e:
                st.error(f"Error durante el OCR: {e}")


            # TODO: Add image content description (requires a different model)


        except Exception as e:
            st.error(f"Error al leer el archivo de imagen: {e}")

    else:
        st.warning(f"Tipo de archivo no compatible: {file_type}")