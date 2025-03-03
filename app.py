import os
import fitz  # PyMuPDF for PDF processing
import pdfrw  # For creating fillable PDF forms
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from pdfrw import PdfReader, PdfWriter
from docx import Document
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def convert_doc_to_pdf(input_doc, output_pdf):
    """Convert .doc or .docx to PDF using unoconv (works on Render)."""
    try:
        print(f"Converting {input_doc} to PDF...")
        subprocess.run(["unoconv", "-f", "pdf", "-o", output_pdf, input_doc], check=True)
        print(f"Conversion successful: {output_pdf}")
        return output_pdf
    except Exception as e:
        print(f"Error converting DOC to PDF: {e}")
        return None

def extract_solicitation_number(input_pdf):
    """Extracts the Solicitation Number from the document."""
    try:
        doc = fitz.open(input_pdf)
        for page in doc:
            text = page.get_text("text")
            lines = text.split("\n")
            for line in lines:
                if "Solicitation Reference Number:" in line:
                    return line.split(":")[1].strip()
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
        fitz.open(input_pdf).save(output_static)
        fitz.open(input_pdf).save(output_references)
        fitz.open(input_pdf).save(output_qualifications)
        fitz.open(input_pdf).save(output_acknowledgment)
        print("Files saved successfully.")
        
        return [
            f"{base_name}_Static.pdf",
            f"{base_name}_References.pdf",
            f"{base_name}_Qualifications.pdf",
            f"{base_name}_Acknowledgment.pdf"
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
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            print(f"Saving uploaded file to: {file_path}")
            file.save(file_path)
            print("File saved successfully.")
            
            # Convert DOC/DOCX to PDF if needed
            if filename.lower().endswith(".doc") or filename.lower().endswith(".docx"):
                converted_pdf_path = file_path.replace(".doc", ".pdf").replace(".docx", ".pdf")
                file_path = convert_doc_to_pdf(file_path, converted_pdf_path)
                if not file_path:
                    return "Error converting DOC to PDF!"
            
            processed_files = process_document(file_path)
            if not processed_files:
                return "Error processing file!"
            
            return render_template("download.html", files=processed_files)
        except Exception as e:
            print(f"Error in upload_file: {e}")
            return "Internal Server Error. Check logs."
    
    return render_template("upload.html")

@app.route("/download/<path:filename>")
def download_file(filename):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found!"

if __name__ == "__main__":
    app.run(debug=True)
