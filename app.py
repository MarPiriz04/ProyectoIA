import streamlit as st
import pandas as pd
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
        model = genai.GenerativeModel('gemini-1.0-pro')
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

st.title("Analisis de rentabilidad")

uploaded_file = st.file_uploader("Cargar archivo para análisis", type=["csv", "xlsx", "xls", "application/pdf"])

user_prompt = st.text_area("Prompt Adicional (Opcional)", height=100)

if uploaded_file:
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    extracted_text = ""

    try:
        if file_extension == ".csv":
            df = pd.read_csv(uploaded_file)
            extracted_text = df.to_string() # Convert DataFrame to string for analysis
        elif file_extension in [".xlsx", ".xls"]:
            df = pd.read_excel(uploaded_file)
            extracted_text = df.to_string() # Convert DataFrame to string for analysis
        elif file_extension == ".pdf":
            reader = pypdf.PdfReader(uploaded_file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                extracted_text += page.extract_text() + "\n"
        else:
            st.error("Tipo de archivo no soportado.")

        if extracted_text:
            st.subheader(f"Análisis de Contenido de {uploaded_file.name}")
            # Use user prompt if provided, otherwise use a default prompt
            if user_prompt:
                # Combine user prompt with extracted text
                full_prompt = f"{user_prompt}\n\nTexto a analizar:\n{extracted_text}"
            else:
                # Use default prompt if no user prompt is provided
                default_prompt = """Actúa como un gerente comercial experto en identificar los productos con más ventas y mayor rentabilidad. Analiza el siguiente texto extraído de un documento y proporciona un resumen centrado en identificar estos productos y cualquier información relevante sobre ventas, ingresos o costos que pueda ayudar a determinar la rentabilidad.

Texto a analizar:
{text}
"""
                full_prompt = default_prompt.replace("{text}", extracted_text)

            summary = summarize_text_gemini(full_prompt)
            st.write("Resultado del Análisis:")
            st.write(summary)

    except Exception as e:
        st.error(f"Error al procesar el archivo {uploaded_file.name}: {e}")