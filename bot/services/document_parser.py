import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self):
        self.supported_formats = {'.pdf', '.docx', '.doc', '.txt'}
    
    def is_supported_document(self, filename: str) -> bool:
        """Check if document format is supported"""
        if not filename:
            return False
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.supported_formats
    
    def extract_text(self, file_path: str, filename: str) -> Tuple[Optional[str], int]:
        """Extract text from document and return text with word count - NO LIMITS"""
        try:
            ext = os.path.splitext(filename.lower())[1]
            
            if ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif ext in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif ext == '.txt':
                return self._extract_from_txt(file_path)
            else:
                logger.error(f"Unsupported file format: {ext}")
                return None, 0
                
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {e}")
            return None, 0
    
    def _extract_from_pdf(self, file_path: str) -> Tuple[Optional[str], int]:
        """Extract text from PDF using PyMuPDF - NO LIMITS"""
        try:
            import fitz  # PyMuPDF
            
            text = ""
            with fitz.open(file_path) as doc:
                total_pages = len(doc)
                logger.info(f"Processing PDF with {total_pages} pages")
                
                for page_num, page in enumerate(doc):
                    # Extract text from page
                    page_text = page.get_text()
                    text += page_text + "\n"
                    
                    # Log progress for large documents
                    if total_pages > 20 and page_num % 20 == 0:
                        logger.info(f"Processed {page_num + 1}/{total_pages} pages")
            
            if not text.strip():
                logger.warning("No text extracted from PDF - might be scanned/image-based")
                return None, 0
            
            # Clean up the text
            text = self._clean_text(text)
            word_count = len(text.split())
            
            logger.info(f"Extracted {word_count:,} words from PDF")
            return text, word_count
            
        except ImportError:
            logger.error("PyMuPDF not installed")
            return None, 0
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return None, 0
    
    def _extract_from_docx(self, file_path: str) -> Tuple[Optional[str], int]:
        """Extract text from DOCX/DOC files - NO LIMITS"""
        try:
            if file_path.lower().endswith('.docx'):
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # For .doc files, we might need antiword or other tools
                logger.error("DOC format requires additional tools")
                return None, 0
            
            if not text.strip():
                return None, 0
            
            text = self._clean_text(text)
            word_count = len(text.split())
            
            logger.info(f"Extracted {word_count:,} words from DOCX")
            return text, word_count
            
        except ImportError:
            logger.error("python-docx not installed")
            return None, 0
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return None, 0
    
    def _extract_from_txt(self, file_path: str) -> Tuple[Optional[str], int]:
        """Extract text from TXT files - NO LIMITS"""
        try:
            # For very large files, read in chunks to avoid memory issues
            file_size = os.path.getsize(file_path)
            
            if file_size > 5 * 1024 * 1024:  # If file > 5MB
                logger.info(f"Large text file detected: {file_size:,} bytes - reading in chunks")
                text = ""
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    while True:
                        chunk = f.read(16384)  # 16KB chunks
                        if not chunk:
                            break
                        text += chunk
            else:
                # Normal reading for smaller files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            
            if not text.strip():
                return None, 0
            
            text = self._clean_text(text)
            word_count = len(text.split())
            
            logger.info(f"Extracted {word_count:,} words from TXT")
            return text, word_count
            
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            return None, 0
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace but preserve paragraphs
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = ' '.join(line.split())  # Remove extra spaces
            if line.strip():  # Keep non-empty lines
                cleaned_lines.append(line)
        
        # Join with double newlines to preserve paragraphs
        cleaned_text = '\n\n'.join(cleaned_lines)
        
        # Remove control characters but keep basic formatting
        cleaned_text = ''.join(char for char in cleaned_text if ord(char) >= 32 or char in '\n\t')
        
        return cleaned_text.strip()

# Global document parser instance
document_parser = DocumentParser()