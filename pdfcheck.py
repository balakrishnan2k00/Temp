"""
Comprehensive PDF Validation Script
Checks if a PDF is a true, pure PDF with selectable text content.
Validates against image-based PDFs, HTML content, and malformed files.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Tuple, List
import re


class PDFValidator:
    """Complete PDF validation and verification class."""
    
    def __init__(self, pdf_path: str):
        """Initialize validator with PDF file path."""
        self.pdf_path = Path(pdf_path)
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> Dict:
        """Run all validation checks."""
        print(f"\n{'='*70}")
        print(f"PDF Validation Report: {self.pdf_path.name}")
        print(f"{'='*70}\n")
        
        # Step 1: File existence and basic checks
        if not self._check_file_exists():
            return self._generate_report()
        
        # Step 2: File format validation
        self._check_file_format()
        
        # Step 3: PDF structure validation
        self._validate_pdf_structure()
        
        # Step 4: Text extraction capability
        self._check_text_extraction()
        
        # Step 5: Image-based detection
        self._detect_image_based_pdf()
        
        # Step 6: HTML content detection
        self._detect_html_content()
        
        # Step 7: Selectability check
        self._check_text_selectability()
        
        # Step 8: PDF purity check
        self._check_pdf_purity()
        
        return self._generate_report()
    
    def _check_file_exists(self) -> bool:
        """Verify file exists and is accessible."""
        print("[1/8] Checking file existence...")
        
        if not self.pdf_path.exists():
            self.errors.append(f"File not found: {self.pdf_path}")
            print(f"  ✗ File does not exist\n")
            return False
        
        if not self.pdf_path.is_file():
            self.errors.append("Path is not a file")
            print(f"  ✗ Path is not a file\n")
            return False
        
        if not os.access(self.pdf_path, os.R_OK):
            self.errors.append("File is not readable")
            print(f"  ✗ File is not readable\n")
            return False
        
        file_size = self.pdf_path.stat().st_size / (1024 * 1024)  # MB
        print(f"  ✓ File exists and is readable")
        print(f"  ✓ File size: {file_size:.2f} MB\n")
        
        self.results['file_exists'] = True
        self.results['file_size_mb'] = round(file_size, 2)
        return True
    
    def _check_file_format(self) -> None:
        """Verify file extension and magic bytes."""
        print("[2/8] Checking file format...")
        
        # Check extension
        if self.pdf_path.suffix.lower() != '.pdf':
            self.warnings.append(f"Unexpected extension: {self.pdf_path.suffix}")
            print(f"  ⚠ Unexpected file extension: {self.pdf_path.suffix}")
        else:
            print(f"  ✓ Correct file extension: .pdf")
        
        # Check magic bytes (PDF header)
        try:
            with open(self.pdf_path, 'rb') as f:
                header = f.read(10)
            
            if header.startswith(b'%PDF'):
                pdf_version = header.decode('utf-8', errors='ignore').strip()
                print(f"  ✓ Valid PDF header: {pdf_version}")
                self.results['pdf_header'] = pdf_version
                self.results['valid_header'] = True
            else:
                self.warnings.append("Invalid PDF header")
                print(f"  ⚠ Invalid or missing PDF header")
                self.results['valid_header'] = False
        except Exception as e:
            self.errors.append(f"Error reading file header: {str(e)}")
            print(f"  ✗ Error reading file header: {str(e)}\n")
    
    def _validate_pdf_structure(self) -> None:
        """Validate PDF internal structure."""
        print("[3/8] Validating PDF structure...")
        
        try:
            import PyPDF2
            
            with open(self.pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                if pdf_reader.is_encrypted:
                    self.warnings.append("PDF is encrypted")
                    print(f"  ⚠ PDF is encrypted")
                    is_encrypted = True
                else:
                    print(f"  ✓ PDF is not encrypted")
                    is_encrypted = False
                
                num_pages = len(pdf_reader.pages)
                print(f"  ✓ Valid PDF structure detected")
                print(f"  ✓ Number of pages: {num_pages}")
                
                self.results['is_encrypted'] = is_encrypted
                self.results['num_pages'] = num_pages
                self.results['valid_structure'] = True
                
        except Exception as e:
            self.warnings.append(f"PyPDF2 validation error: {str(e)}")
            print(f"  ⚠ Structure validation incomplete: {str(e)}\n")
            self.results['valid_structure'] = False
    
    def _check_text_extraction(self) -> None:
        """Check if text can be extracted from PDF."""
        print("[4/8] Checking text extraction capability...")
        
        extractable_text = ""
        has_text = False
        
        # Try pdfplumber
        try:
            import pdfplumber
            
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extractable_text += text
                        has_text = True
            
            if has_text:
                text_length = len(extractable_text.strip())
                print(f"  ✓ Text successfully extracted from PDF")
                print(f"  ✓ Total extracted characters: {text_length}")
                self.results['text_extractable'] = True
                self.results['extracted_char_count'] = text_length
            else:
                print(f"  ✗ No text could be extracted")
                self.results['text_extractable'] = False
                
        except ImportError:
            print(f"  ⚠ pdfplumber not installed, trying alternative method...")
            try:
                import PyPDF2
                with open(self.pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            extractable_text += text
                            has_text = True
                
                if has_text:
                    text_length = len(extractable_text.strip())
                    print(f"  ✓ Text successfully extracted (PyPDF2)")
                    self.results['text_extractable'] = True
                    self.results['extracted_char_count'] = text_length
                else:
                    print(f"  ✗ No text could be extracted")
                    self.results['text_extractable'] = False
            except Exception as e:
                self.errors.append(f"Text extraction failed: {str(e)}")
                print(f"  ✗ Text extraction error: {str(e)}")
                self.results['text_extractable'] = False
        
        print()
    
    def _detect_image_based_pdf(self) -> None:
        """Detect if PDF is image-based (scanned) vs text-based."""
        print("[5/8] Detecting PDF type (text-based vs image-based)...")
        
        is_image_based = False
        
        try:
            # Try pdfplumber
            try:
                import pdfplumber
                
                total_chars = 0
                total_images = 0
                
                with pdfplumber.open(self.pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            total_chars += len(text)
                        
                        if hasattr(page, 'images') and page.images:
                            total_images += len(page.images)
                
                # If minimal text but has images = likely scanned
                if total_chars < 100 and total_images > 0:
                    is_image_based = True
                    print(f"  ⚠ PDF appears to be IMAGE-BASED (likely scanned)")
                    print(f"  ⚠ Character count: {total_chars}, Images found: {total_images}")
                elif total_chars > 0:
                    print(f"  ✓ PDF is TEXT-BASED (not scanned)")
                    print(f"  ✓ Character count: {total_chars}")
                else:
                    is_image_based = True
                    print(f"  ✗ PDF appears to be IMAGE-BASED or corrupted")
            
            except ImportError:
                # Fallback to PyMuPDF
                try:
                    import fitz
                    
                    doc = fitz.open(self.pdf_path)
                    total_chars = 0
                    total_images = 0
                    
                    for page in doc:
                        text = page.get_text()
                        if text:
                            total_chars += len(text)
                        
                        images = page.get_images()
                        if images:
                            total_images += len(images)
                    
                    if total_chars < 100 and total_images > 0:
                        is_image_based = True
                        print(f"  ⚠ PDF appears to be IMAGE-BASED (PyMuPDF)")
                    elif total_chars > 0:
                        print(f"  ✓ PDF is TEXT-BASED")
                    else:
                        is_image_based = True
                        print(f"  ✗ PDF appears to be IMAGE-BASED")
                    
                    print(f"  ✓ Character count: {total_chars}")
                    print(f"  ✓ Images found: {total_images}")
                
                except ImportError:
                    print(f"  ⚠ Cannot determine PDF type (libraries not available)")
        
        except Exception as e:
            self.warnings.append(f"Image detection error: {str(e)}")
            print(f"  ⚠ Error during image detection: {str(e)}")
        
        self.results['is_image_based'] = is_image_based
        print()
    
    def _detect_html_content(self) -> None:
        """Detect HTML content or malicious elements."""
        print("[6/8] Scanning for HTML content and suspicious elements...")
        
        html_detected = False
        suspicious_elements = []
        
        try:
            with open(self.pdf_path, 'rb') as f:
                content = f.read()
            
            # Decode with error handling
            try:
                content_str = content.decode('utf-8', errors='ignore').lower()
            except:
                content_str = ""
            
            # Check for HTML patterns
            html_patterns = [
                b'<html',
                b'<!doctype html',
                b'<script',
                b'<iframe',
                b'<?xml',
                b'xmlns',
            ]
            
            for pattern in html_patterns:
                if pattern in content:
                    html_detected = True
                    suspicious_elements.append(pattern.decode('utf-8', errors='ignore'))
            
            # Check for JavaScript
            if b'javascript' in content or b'/JS' in content:
                suspicious_elements.append('JavaScript code')
                html_detected = True
            
            if html_detected:
                print(f"  ✗ HTML/Suspicious content DETECTED")
                print(f"  ✗ Found elements: {', '.join(suspicious_elements)}")
            else:
                print(f"  ✓ No HTML or malicious content detected")
            
            self.results['html_detected'] = html_detected
            self.results['suspicious_elements'] = suspicious_elements
            
        except Exception as e:
            self.warnings.append(f"HTML detection error: {str(e)}")
            print(f"  ⚠ Error during HTML scan: {str(e)}")
        
        print()
    
    def _check_text_selectability(self) -> None:
        """Check if text in PDF is selectable."""
        print("[7/8] Checking text selectability...")
        
        selectable = False
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(self.pdf_path)
            
            selectable_text = ""
            for page in doc:
                text = page.get_text("text")
                if text and len(text.strip()) > 0:
                    selectable_text += text
                    selectable = True
            
            if selectable:
                print(f"  ✓ Text is SELECTABLE (cursor can select content)")
                print(f"  ✓ Selectable content found: {len(selectable_text)} characters")
            else:
                print(f"  ✗ Text is NOT SELECTABLE")
            
            doc.close()
            
        except ImportError:
            print(f"  ⚠ PyMuPDF not installed, checking with available libraries...")
            try:
                import pdfplumber
                with pdfplumber.open(self.pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text and len(text.strip()) > 0:
                            selectable = True
                            break
                
                if selectable:
                    print(f"  ✓ Text is SELECTABLE")
                else:
                    print(f"  ✗ Text is NOT SELECTABLE")
            except:
                print(f"  ⚠ Cannot determine selectability")
        
        except Exception as e:
            self.warnings.append(f"Selectability check error: {str(e)}")
            print(f"  ⚠ Error during selectability check: {str(e)}")
        
        self.results['text_selectable'] = selectable
        print()
    
    def _check_pdf_purity(self) -> None:
        """Final check - is this a pure, true PDF?"""
        print("[8/8] Determining PDF purity status...")
        
        is_pure_pdf = True
        issues = []
        
        # Evaluate criteria
        if not self.results.get('valid_header', False):
            is_pure_pdf = False
            issues.append("Invalid PDF header")
        
        if self.results.get('is_encrypted', False):
            is_pure_pdf = False
            issues.append("PDF is encrypted")
        
        if self.results.get('html_detected', False):
            is_pure_pdf = False
            issues.append("HTML/malicious content detected")
        
        if not self.results.get('text_extractable', True):
            is_pure_pdf = False
            issues.append("No extractable text (possible corruption)")
        
        if self.results.get('is_image_based', False):
            is_pure_pdf = False
            issues.append("Image-based PDF (not selectable text)")
        
        if not self.results.get('text_selectable', False) and self.results.get('num_pages', 0) > 0:
            is_pure_pdf = False
            issues.append("Text not selectable")
        
        self.results['is_pure_pdf'] = is_pure_pdf
        self.results['purity_issues'] = issues
        
        if is_pure_pdf:
            print(f"  ✓ PDF is PURE and VALID")
            print(f"  ✓ Contains selectable text content")
            print(f"  ✓ No HTML or malicious content")
            print(f"  ✓ Suitable for text extraction and cursor selection")
        else:
            print(f"  ✗ PDF is NOT a pure text-based PDF")
            for issue in issues:
                print(f"    - {issue}")
        
        print()
    
    def _generate_report(self) -> Dict:
        """Generate final validation report."""
        print(f"{'='*70}")
        print("FINAL VERDICT")
        print(f"{'='*70}\n")
        
        is_valid = self.results.get('is_pure_pdf', False)
        
        if is_valid:
            print("✓ RESULT: TRUE PDF - Pure, text-based, selectable content")
            print("✓ This is a legitimate PDF where content can be selected via cursor")
            print("✓ No HTML, images, or corruption detected\n")
        else:
            print("✗ RESULT: NOT A PURE PDF")
            if self.results.get('is_image_based', False):
                print("✗ Reason: PDF is image-based (scanned document)")
            if self.results.get('html_detected', False):
                print("✗ Reason: Contains HTML or malicious content")
            if self.results.get('is_encrypted', False):
                print("✗ Reason: PDF is encrypted")
            if self.errors:
                print("✗ Reason: File errors detected")
            print()
        
        # Print summary table
        print(f"{'='*70}")
        print("DETAILED RESULTS")
        print(f"{'='*70}\n")
        
        detail_results = {
            'File Name': str(self.pdf_path.name),
            'File Size': f"{self.results.get('file_size_mb', 'N/A')} MB",
            'PDF Header': self.results.get('pdf_header', 'N/A'),
            'Number of Pages': self.results.get('num_pages', 'N/A'),
            'Valid Structure': '✓ Yes' if self.results.get('valid_structure') else '✗ No',
            'Encrypted': '✓ Yes' if self.results.get('is_encrypted') else '✗ No',
            'Text Extractable': '✓ Yes' if self.results.get('text_extractable') else '✗ No',
            'Extracted Characters': self.results.get('extracted_char_count', 0),
            'Image-Based PDF': '✓ Yes' if self.results.get('is_image_based') else '✗ No',
            'HTML Content Detected': '✓ Yes' if self.results.get('html_detected') else '✗ No',
            'Text Selectable': '✓ Yes' if self.results.get('text_selectable') else '✗ No',
            'Pure PDF': '✓ YES' if self.results.get('is_pure_pdf') else '✗ NO',
        }
        
        for key, value in detail_results.items():
            print(f"{key:.<40} {value}")
        
        print(f"\n{'='*70}\n")
        
        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
            print()
        
        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  ✗ {error}")
            print()
        
        return self.results


def check_pdf(pdf_file_path: str) -> bool:
    """
    Main function to validate a PDF file.
    
    Args:
        pdf_file_path: Path to the PDF file to validate
    
    Returns:
        True if PDF is pure and valid, False otherwise
    """
    validator = PDFValidator(pdf_file_path)
    results = validator.validate_all()
    return results.get('is_pure_pdf', False)


def batch_check_pdfs(directory_path: str) -> Dict[str, bool]:
    """
    Check multiple PDF files in a directory.
    
    Args:
        directory_path: Path to directory containing PDFs
    
    Returns:
        Dictionary mapping PDF filenames to validation results
    """
    results = {}
    pdf_dir = Path(directory_path)
    
    pdf_files = list(pdf_dir.glob('*.pdf'))
    
    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return results
    
    print(f"Found {len(pdf_files)} PDF file(s) to validate\n")
    
    for pdf_file in pdf_files:
        is_valid = check_pdf(str(pdf_file))
        results[pdf_file.name] = is_valid
    
    return results


# Example usage
if __name__ == "__main__":
    
    # Single file validation
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        is_valid = check_pdf(pdf_path)
        sys.exit(0 if is_valid else 1)
    
    else:
        # Example validation (modify path as needed)
        print("PDF Validator - Usage:")
        print("  python pdfcheck.py <pdf_file_path>")
        print("\nExample:")
        print("  python pdfcheck.py document.pdf")
        print("\nThe script will perform 8 comprehensive checks:")
        print("  1. File existence and accessibility")
        print("  2. File format validation")
        print("  3. PDF structure validation")
        print("  4. Text extraction capability")
        print("  5. Image-based PDF detection")
        print("  6. HTML content scanning")
        print("  7. Text selectability check")
        print("  8. PDF purity determination")
        print("\nRequired libraries:")
        print("  - PyPDF2")
        print("  - pdfplumber")
        print("  - PyMuPDF (fitz)")
        print("\nInstall with:")
        print("  pip install PyPDF2 pdfplumber PyMuPDF")
