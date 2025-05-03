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
        return "No text available to summarize."
    try:
        model = genai.GenerativeModel('gemini-pro')
        # For long texts, consider breaking them into chunks if the model has input limits
        # This is a basic implementation, more advanced chunking might be needed
        response = model.generate_content(f"Summarize the following text:\n\n{text}")
        return response.text
    except Exception as e:
        return f"Error generating summary with Gemini: {e}"

st.title("AI-Powered File Report Generator")

uploaded_file = st.file_uploader("Upload a file (CSV, PDF, or Image)", type=["csv", "pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_type = uploaded_file.type

    st.write(f"Processing {uploaded_file.name} ({file_type})")

    if file_type == "text/csv":
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            st.subheader("CSV Content (First 5 rows)")
            st.write(df.head())

            st.subheader("CSV Analysis")
            st.write("Basic Statistics:")
            st.write(df.describe())

            # Simple trend identification (example: correlation matrix)
            if df.select_dtypes(include=['number']).shape[1] > 1:
                st.write("Correlation Matrix:")
                st.write(df.corr())

            # Summarize the content (using a string representation of the dataframe)
            st.subheader("CSV Summary (AI)")
            csv_summary_text = df.to_string()
            summary = summarize_text_gemini(csv_summary_text)
            st.write(summary)


        except Exception as e:
            st.error(f"Error reading CSV file: {e}")

    elif file_type == "application/pdf":
        st.subheader("PDF Content")
        try:
            reader = pypdf.PdfReader(uploaded_file)
            pdf_text = ""
            for page_num in range(len(reader.pages)):
                pdf_text += reader.pages[page_num].extract_text()

            st.text_area("Extracted Text", pdf_text, height=300)

            st.subheader("PDF Analysis (AI)")
            # Summarize the extracted text
            pdf_summary = summarize_text_gemini(pdf_text)
            st.write("Summary:")
            st.write(pdf_summary)

            # TODO: Add entity extraction for PDF

        except Exception as e:
            st.error(f"Error reading PDF file: {e}")

    elif file_type.startswith("image/"):
        try:
            # Read Image
            img = Image.open(uploaded_file)
            st.subheader("Uploaded Image")
            st.image(img, caption=uploaded_file.name, use_column_width=True)

            st.subheader("Image Analysis (AI)")
            # Perform OCR
            try:
                image_text = pytesseract.image_to_string(img)
                st.write("Extracted Text (OCR):")
                st.text_area("OCR Text", image_text, height=200)

                # Summarize the extracted text
                image_summary = summarize_text_gemini(image_text)
                st.write("Summary of Extracted Text:")
                st.write(image_summary)

            except pytesseract.TesseractNotFoundError:
                st.error("Tesseract is not installed or not in your PATH. Please install Tesseract OCR.")
            except Exception as e:
                st.error(f"Error during OCR: {e}")


            # TODO: Add image content description (requires a different model)


        except Exception as e:
            st.error(f"Error reading image file: {e}")

    else:
        st.warning(f"Unsupported file type: {file_type}")