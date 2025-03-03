import os
import fitz  # PyMuPDF for PDF processing
import pdfrw  # For creating fillable PDF forms
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from pdfrw import PdfReader, PdfWriter
import re

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def extract_solicitation_number(input_pdf):
    """Extracts the Solicitation Number from the document."""
    try:
        doc = fitz.open(input_pdf)
        for page in doc:
            text = page.get_text("text")
            match = re.search(r"Solicitation Reference Number\s*:?\s*(\S+)", text, re.IGNORECASE)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error extracting solicitation number: {e}")
    return "Unknown"

def process_document(input_pdf):
    """Process the input document to generate structured PDFs."""
    try:
        solicitation_number = extract_solicitation_number(input_pdf)
        print(f"Extracted Solicitation Number: {solicitation_number}")
        base_name = f"{solicitation_number}_TEEMAInc"
        
        output_static = os.path.join(PROCESSED_FOLDER, f"{base_name}_Static.pdf")
        output_references = os.path.join(PROCESSED_FOLDER, f"{base_name}_References.pdf")
        output_qualifications = os.path.join(PROCESSED_FOLDER, f"{base_name}_Qualifications.pdf")
        output_acknowledgment = os.path.join(PROCESSED_FOLDER, f"{base_name}_Acknowledgment.pdf")
        
        print("Saving processed files...")
        doc = fitz.open(input_pdf)
        doc.save(output_static)
        doc.save(output_references)
        doc.save(output_qualifications)
        doc.save(output_acknowledgment)
        print("Files saved successfully.")
        
        return [
            os.path.basename(output_static),
            os.path.basename(output_references),
            os.path.basename(output_qualifications),
            os.path.basename(output_acknowledgment)
        ]
    except Exception as e:
        print(f"Error processing document: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        try:
            if "file" not in request.files:
                return "No file uploaded!"
            
            file = request.files["file"]
            if file.filename == "":
                return "No selected file!"
            
            filename = secure_filename(file.filename)
            if not filename.lower().endswith(".pdf"):
                return "Only PDF files are allowed!"
            
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            print(f"Saving uploaded file to: {file_path}")
            file.save(file_path)
            print("File saved successfully.")
            
            processed_files = process_document(file_path)
            if not processed_files:
                return "Error processing file!"
            
            return render_template("download.html", files=processed_files)
        except Exception as e:
            print(f"Error in upload_file: {e}")
            return "Internal Server Error. Check logs."
    
    return render_template("upload.html")

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found!"

if __name__ == "__main__":
    app.run(debug=True)
