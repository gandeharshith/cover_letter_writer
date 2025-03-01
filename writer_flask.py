import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import PyPDF2
from fpdf import FPDF
from langchain_openai import ChatOpenAI
import openai
import dotenv 
from dotenv import load_dotenv
import os
dotenv.load_dotenv()
load_dotenv(override=True)
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_resume_text(file_obj):
    """
    Extracts text from the uploaded PDF file.
    """
    resume_text = ""
    reader = PyPDF2.PdfReader(file_obj)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            resume_text += text + "\n"
    return resume_text

def generate_cover_letter(job_description, resume_text):
    """
    Generates a cover letter by constructing a prompt from the resume text and job description.
    Uses the ChatOpenAI instance to generate the cover letter.
    """
    prompt = (
        "You are a career advisor. Based on the following resume details and job description, "
        "please write a professional cover letter that highlights relevant skills and experiences. "
        "Dont give any links in the cover letter"
        "The cover letter should be simple and straight forward it should look loke human written cover letter"
        "**Write it as much concisely as possible and small easily able to fit in one page**"
        "**Dont mention any placeholders (write only the information you have). **"
        "Do not include any internal chain-of-thought or reasoning process—only output the final cover letter.\n\n"
        "Resume Details:\n"
        f"{resume_text}\n\n"
        "Job Description:\n"
        f"{job_description}\n\n"
        "Cover Letter:"
    )
    
    cover_letter = llm.predict(prompt)
    return cover_letter

def generate_pdf_from_text(text):
    # Define replacements for common Unicode characters
    replacements = {
        '\u2019': "'",  # Right single quote
        '\u2018': "'",  # Left single quote
        '\u201d': '"',  # Right double quote
        '\u201c': '"',  # Left double quote
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2026': '...', # Ellipsis
        '\u00a0': ' ',   # Non-breaking space
    }
    
    # Apply all replacements
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    # Remove any remaining non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 9, text)
    
    # Generate PDF string and encode to bytes
    pdf_str = pdf.output(dest='S')
    pdf_data = pdf_str.encode('latin-1', errors='replace')
    
    # Return as a BytesIO object
    pdf_output = io.BytesIO(pdf_data)
    pdf_output.seek(0)
    return pdf_output


# Set your custom API base and initialize the ChatOpenAI LLM instance.
openai.api_base = "https://api.groq.com/openai/v1"
llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("api_key"),  # Replace with your actual API key
    base_url="https://api.groq.com/openai/v1",
    temperature=0
)

@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover_letter_api():
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file provided.'}), 400

    resume_file = request.files['resume']
    job_description = request.form.get('jobDescription', '')
    print(job_description)
    if resume_file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(resume_file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400

    if not job_description:
        return jsonify({'error': 'Job description is required.'}), 400

    try:
        # Extract text from the resume PDF.
        resume_text = extract_resume_text(resume_file)

        # Generate the cover letter text using the resume and job description.
        cover_letter = generate_cover_letter(job_description, resume_text)
        print("pukkkk")
        # Convert the cover letter text to a PDF.
        pdf_file = generate_pdf_from_text(cover_letter)
        print("kuppppp")
        print(pdf_file)

        # Return the PDF as a downloadable file.
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='cover_letter.pdf'
        )
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the Flask development server on port 5000
    app.run(debug=True,host="0.0.0.0",port=5000)
