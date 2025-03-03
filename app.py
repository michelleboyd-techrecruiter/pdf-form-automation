import os
import fitz  # PyMuPDF for PDF processing
import pdfrw  # For creating fillable PDF forms
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from pdfrw import PdfReader, PdfWriter

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def extract_solicitation_number(input_pdf):
    """Extracts the Solicitation Number from the document."""
    doc = fitz.open(input_pdf)
    for page in doc:
        text = page.get_text("text")
        lines = text.split("\n")
        for line in lines:
            if "Solicitation Reference Number:" in line:
                return line.split(":")[1].strip()
    return "Unknown"

def process_document(input_pdf):
    """Process the input document to generate structured PDFs."""
    solicitation_number = extract_solicitation_number(input_pdf)
    base_name = f"{solicitation_number}_TEEMAInc"
    output_static = os.path.join(PROCESSED_FOLDER, f"{base_name}_Static.pdf")
    output_references = os.path.join(PROCESSED_FOLDER, f"{base_name}_References.pdf")
    output_qualifications = os.path.join(PROCESSED_FOLDER, f"{base_name}_Qualifications.pdf")
    output_acknowledgment = os.path.join(PROCESSED_FOLDER, f"{base_name}_Acknowledgment.pdf")
    
    # Copy input PDF as output for now (Placeholder for extraction logic)
    fitz.open(input_pdf).save(output_static)
    fitz.open(input_pdf).save(output_references)
    fitz.open(input_pdf).save(output_qualifications)
    fitz.open(input_pdf).save(output_acknowledgment)
    
    return [output_static, output_references, output_qualifications, output_acknowledgment]

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded!"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file!"
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        processed_files = process_document(file_path)
        return render_template("download.html", files=processed_files)
    
    return render_template("upload.html")

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
