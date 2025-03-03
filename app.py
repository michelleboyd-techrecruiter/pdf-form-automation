import os
import fitz  # PyMuPDF for PDF processing
import pdfrw  # For creating fillable PDF forms
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from pdfrw import PdfReader, PdfWriter, PageMerge
import re

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Define section headers
SECTION_HEADERS = {
    "Candidate References": "references",
    "Candidate Qualifications": "qualifications",
    "Candidate Acknowledgment": "acknowledgment"
}

def extract_solicitation_number(input_pdf):
    """Extracts the Solicitation Number from the document."""
    try:
        doc = fitz.open(input_pdf)
        for page in doc:
            text = page.get_text("text")
            print(f"Page text for solicitation extraction: {text}")  # Debugging
            match = re.search(r"Solicitation(?: Reference)? Number\s*:?[\s]*([\w-]+)", text, re.IGNORECASE)
            if match:
                print(f"Found Solicitation Number: {match.group(1)}")
                return match.group(1)
    except Exception as e:
        print(f"Error extracting solicitation number: {e}")
    return "Unknown"

def split_document(input_pdf):
    """Splits the document into sections based on predefined headers."""
    doc = fitz.open(input_pdf)
    sections = {"static": []}
    current_section = "static"
    
    for i, page in enumerate(doc):
        text = page.get_text("text")
        print(f"Processing Page {i}: {text}")  # Debugging
        for header, section_name in SECTION_HEADERS.items():
            if header in text:
                current_section = section_name
                sections[current_section] = []
                print(f"Found section {current_section} on page {i}")
        sections[current_section].append(i)
    
    return doc, sections

def create_filled_pdf(input_pdf, pages, output_pdf):
    """Creates a fillable PDF from selected pages."""
    doc = fitz.open(input_pdf)
    writer = PdfWriter()
    for page_num in pages:
        writer.addpage(PdfReader(input_pdf).pages[page_num])
    writer.write(output_pdf)

def add_form_fields(input_pdf, output_pdf, section):
    """Adds fillable form fields to PDFs with correct positions."""
    field_positions = {
        "references": [(100, 200, 400, 220)],
        "qualifications": [(100, 300, 400, 320)],
        "acknowledgment": [(150, 450, 400, 470), (150, 500, 350, 520)]  # Signature & Date Fields
    }
    
    template = PdfReader(input_pdf)
    for page in template.pages:
        for idx, rect in enumerate(field_positions.get(section, [])):
            annotation = pdfrw.PdfDict(
                Rect=rect, T=f"{section}_field_{idx}", FT="Tx", V="", Ff=1, AP=pdfrw.PdfDict(N=None)
            )
            if "Annots" in page:
                page.Annots.append(annotation)
            else:
                page.Annots = [annotation]
    
    PdfWriter(output_pdf, trailer=template).write()
    print(f"Added fillable fields to {output_pdf}")

def process_document(input_pdf):
    """Processes the input document into structured PDFs."""
    try:
        solicitation_number = extract_solicitation_number(input_pdf)
        print(f"Extracted Solicitation Number: {solicitation_number}")
        base_name = f"{solicitation_number}_TEEMAInc"
        
        doc, sections = split_document(input_pdf)
        processed_files = []
        
        for section, pages in sections.items():
            if not pages:  # Skip empty sections
                continue
            output_pdf = os.path.join(PROCESSED_FOLDER, f"{base_name}_{section.capitalize()}.pdf")
            create_filled_pdf(input_pdf, pages, output_pdf)
            if section in SECTION_HEADERS.values():
                add_form_fields(output_pdf, output_pdf, section)
            processed_files.append(os.path.basename(output_pdf))
        
        return processed_files
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
