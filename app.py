import os
from flask import Flask, request, jsonify, render_template
import easyocr
from googletrans import Translator
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdf2image

app = Flask(__name__)

# Function to save the uploaded file
def save_uploaded_file(uploaded_file):
    if not os.path.exists('data'):
        os.makedirs('data')

    file_path = os.path.join('data', uploaded_file.filename)
    uploaded_file.save(file_path)
    return file_path

# Function to extract text from images using EasyOCR
reader = easyocr.Reader(['en'])

def extract_text_from_image(image_path):
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

# Function to extract text from PDF images using pdf2image
def extract_text_from_pdf_images(pdf_path):
    images = pdf2image.convert_from_path(pdf_path)
    extracted_text = ""
    for i, image in enumerate(images):
        temp_image_path = f"temp_page_{i}.jpg"
        image.save(temp_image_path, "JPEG")
        extracted_text += extract_text_from_image(temp_image_path) + "\n"
        os.remove(temp_image_path)
    return extracted_text

# Function to handle the translation from English to Hindi
def translate_to_hindi(file_path):
    translator = Translator()

    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        input_text = extract_text_from_image(file_path)
    elif file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        texts = text_splitter.split_documents(pages)
        input_text = "\n".join([text.page_content for text in texts])

        if not input_text.strip():
            input_text = extract_text_from_pdf_images(file_path)
    else:
        return "Unsupported file format"

    try:
        translated_text = translator.translate(input_text, src='en', dest='hi').text
    except Exception as e:
        translated_text = f"Error occurred during translation: {e}"

    return translated_text

# Route for UI
@app.route('/')
def index():
    return render_template('index.html')

# Route for Translation
@app.route('/translate', methods=['POST'])
def translate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        file_path = save_uploaded_file(file)
        translated_text = translate_to_hindi(file_path)
        os.remove(file_path)
        return jsonify({'translatedText': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
