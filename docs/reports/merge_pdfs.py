import os
from pypdf import PdfWriter

def merge_pdfs():
    pdfs_to_merge = [
        "docs/reports/academiq_complete_project_audit.pdf",
        "docs/l2-sdn.pdf",
        "docs/l3-native-execve-validation.pdf",
        "docs/experiments-current-state.pdf"
    ]
    
    merger = PdfWriter()
    
    for pdf in pdfs_to_merge:
        if os.path.exists(pdf):
            print(f"Adding {pdf}...")
            merger.append(pdf)
        else:
            print(f"Warning: {pdf} not found.")
            
    output_path = "docs/reports/AcademIQ_Master_Documentation.pdf"
    merger.write(output_path)
    merger.close()
    
    print(f"\nSuccessfully created merged PDF at: {output_path}")

if __name__ == "__main__":
    merge_pdfs()
