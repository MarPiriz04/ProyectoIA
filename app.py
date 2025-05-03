import streamlit as st
import pandas as pd
from PIL import Image
import io
import pypdf
import google.generativeai as genai
import os

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

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

user_prompt = st.text_area("Prompt Adicional (Opcional)", height=100)

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
                    # Use Gemini Vision model for image analysis
                    vision_model = genai.GenerativeModel('gemini-pro-vision')
                    
                    # Prepare the image for the model
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format=img.format)
                    img_byte_arr = img_byte_arr.getvalue()

                    image_parts = [
                        {
                            "mime_type": uploaded_file.type,
                            "data": img_byte_arr
                        }
                    ]

                    # Determine which prompt to use
                    current_image_prompt = user_prompt if user_prompt else """Actúa como un gerente comercial experto en identificar los productos con más ventas y mayor rentabilidad. Analiza la siguiente imagen y extrae cualquier información relevante sobre ventas, ingresos, costos o productos que pueda ayudar a determinar la rentabilidad. Presenta la información extraída de forma clara.
"""
                    
                    response = vision_model.generate_content([current_image_prompt, image_parts[0]])
                    image_analysis_result = response.text
                    image_texts.append(image_analysis_result) # Store the analysis result as text
                    st.write("Resultado del Análisis de Imagen:")
                    st.write(image_analysis_result)

                except Exception as e:
                    st.error(f"Error durante el análisis de imagen con Gemini para {uploaded_file.name}: {e}")
                    image_texts.append(f"Error durante el análisis de imagen con Gemini para {uploaded_file.name}: {e}")


            except Exception as e:
                st.error(f"Error al leer el archivo de imagen {uploaded_file.name}: {e}")
                image_texts.append(f"Error al leer el archivo de imagen {uploaded_file.name}: {e}")


        # Perform cross-analysis if two images are uploaded and analysis was successful for both
        if len(image_texts) == 2 and not any("Error" in text for text in image_texts):
            st.subheader("Análisis Cruzado de Imágenes (IA)")
            combined_analysis_results = f"Análisis de la primera imagen ({image_names[0]}):\n{image_texts[0]}\n\nAnálisis de la segunda imagen ({image_names[1]}):\n{image_texts[1]}"

            # Determine which prompt to use for cross-analysis
            current_cross_analysis_prompt = user_prompt if user_prompt else f"""Actúa como un gerente comercial experto en identificar los productos con más ventas y mayor rentabilidad. Compara y contrasta los resultados de análisis de las siguientes dos imágenes. Identifica similitudes, diferencias, tendencias o cualquier otra información relevante que pueda ayudar a determinar qué productos son los más vendidos y rentables basándote en ambos análisis.

Análisis de la primera imagen ({image_names[0]}):
{image_texts[0]}

Análisis de la segunda imagen ({image_names[1]}):
{image_texts[1]}
"""
            try:
                model = genai.GenerativeModel('gemini-pro')
                cross_analysis_result = model.generate_content(current_cross_analysis_prompt)
                st.write("Resultado del Análisis Cruzado:")
                st.write(cross_analysis_result.text)
            except Exception as e:
                st.error(f"Error al generar el análisis cruzado con Gemini: {e}")

        elif len(image_texts) == 2 and any("Error" in text for text in image_texts):
             st.warning("No se puede realizar el análisis cruzado debido a errores en el análisis de una o ambas imágenes.")
        elif len(image_texts) == 1:
             st.info("Carga otra imagen para realizar un análisis cruzado.")