import re
import docx
from pdfminer.high_level import extract_text
import os 

def process_clean_text(text):
    # Define the regex pattern for special characters
    pattern = r'[^a-zA-Z0-9\s]'

    # Replace the special characters with whitespace
    clean_text = re.sub(pattern, ' ', text)

    clean_text = clean_text.strip() 

    final_doc = []
    for line in clean_text.split("\n"):
        final_doc.append(" ".join([x.strip() for x in line.split(" ")]))

    clean_text = "\n".join(final_doc)

    # Define the regex pattern for multiple spaces
    pattern = r'\s+'

    # Remove multiple spaces in each line of text
    lines = clean_text.split('\n')

    clean_lines = []
    for line in lines:
        clean_line = re.sub(pattern, ' ', line.strip())
        if clean_line:
            clean_lines.append(clean_line)

    # Concatenate the cleaned lines into a single string
    clean_text = '\n'.join(clean_lines)

    return clean_text

def parse_pdf(pdf_file_path):
    # Extract the text from the PDF file
    text = extract_text(pdf_file_path)
    text = process_clean_text(text)
    return text

def parse_docx(docx_file_path):
    # Open the docx file
    doc = docx.Document(docx_file_path)
    # Extract all paragraphs from the document
    paragraphs = [para.text for para in doc.paragraphs]
    text = "\n".join(paragraphs)
    text = process_clean_text(text)
    return text

def convert_filepath_to_json(file_path):
    # Extract the directory, file name, and extension from the input path
    directory, file_with_ext = os.path.split(file_path)
    file_name, _ = os.path.splitext(file_with_ext)
    
    # Replace spaces with underscores in the file name
    modified_file_name = file_name.replace(' ', '_')
    
    # Construct the new path with the .json extension in the "backup_folder" directory
    json_file_path = os.path.join("backup_folder", f"{modified_file_name}.json")
    
    return json_file_path