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

st.title("Analista de Rentabilidad")

uploaded_files = st.file_uploader("Cargar imágenes para análisis", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 2:
        st.warning("Por favor, carga un máximo de 2 imágenes.")
    else:
        image_texts = []
        image_summaries = []
        image_names = []

        for uploaded_file in uploaded_files:
            image_names.append(uploaded_file.name)
            st.write(f"Procesando {uploaded_file.name}")
            try:
                img = Image.open(uploaded_file)
                st.subheader(f"Imagen Cargada: {uploaded_file.name}")
                st.image(img, caption=uploaded_file.name, use_column_width=True)

                st.subheader(f"Análisis de Imagen (IA) para {uploaded_file.name}")
                try:
                    image_text = pytesseract.image_to_string(img)
                    image_texts.append(image_text)
                    st.write("Texto Extraído (OCR):")
                    st.text_area(f"Texto OCR para {uploaded_file.name}", image_text, height=200)

                    image_summary = summarize_text_gemini(image_text)
                    image_summaries.append(image_summary)
                    st.write("Resumen del Texto Extraído:")
                    st.write(image_summary)

                except pytesseract.TesseractNotFoundError:
                    st.error("Tesseract no está instalado o no se encuentra en tu PATH. Por favor, instala Tesseract OCR.")
                    image_texts.append("") # Append empty string to maintain list length
                    image_summaries.append(f"Error: Tesseract no instalado para {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Error durante el OCR para {uploaded_file.name}: {e}")
                    image_texts.append("") # Append empty string to maintain list length
                    image_summaries.append(f"Error durante el OCR para {uploaded_file.name}: {e}")

            except Exception as e:
                st.error(f"Error al leer el archivo de imagen {uploaded_file.name}: {e}")
                image_texts.append("") # Append empty string to maintain list length
                image_summaries.append(f"Error al leer el archivo de imagen {uploaded_file.name}: {e}")


        # Perform cross-analysis if two images are uploaded
        if len(image_texts) == 2 and all(image_texts):
            st.subheader("Análisis Cruzado de Imágenes (IA)")
            combined_text = f"Texto de la primera imagen ({image_names[0]}):\n{image_texts[0]}\n\nTexto de la segunda imagen ({image_names[1]}):\n{image_texts[1]}"

            cross_analysis_prompt = f"""Actúa como un gerente comercial experto en identificar los productos con más ventas y mayor rentabilidad. Compara y contrasta la información de ventas, ingresos o costos presente en los siguientes dos textos extraídos de imágenes. Identifica similitudes, diferencias, tendencias o cualquier otra información relevante que pueda ayudar a determinar qué productos son los más vendidos y rentables basándote en ambos textos.

Texto de la primera imagen ({image_names[0]}):
{image_texts[0]}

Texto de la segunda imagen ({image_names[1]}):
{image_texts[1]}
"""
            try:
                model = genai.GenerativeModel('gemini-pro')
                cross_analysis_result = model.generate_content(cross_analysis_prompt)
                st.write("Resultado del Análisis Cruzado:")
                st.write(cross_analysis_result.text)
            except Exception as e:
                st.error(f"Error al generar el análisis cruzado con Gemini: {e}")

        elif len(image_texts) == 2 and (not all(image_texts)):
             st.warning("No se puede realizar el análisis cruzado porque no se pudo extraer texto de ambas imágenes.")
        elif len(image_texts) == 1:
             st.info("Carga otra imagen para realizar un análisis cruzado.")