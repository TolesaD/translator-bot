import os
import logging
from typing import Tuple, Optional
import tempfile

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
        """Extract text from document and return text with word count"""
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
        """Extract text from PDF using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
            
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            
            if not text.strip():
                logger.warning("No text extracted from PDF - might be scanned/image-based")
                return None, 0
            
            # Clean up the text
            text = self._clean_text(text)
            word_count = len(text.split())
            
            logger.info(f"Extracted {word_count} words from PDF")
            return text, word_count
            
        except ImportError:
            logger.error("PyMuPDF not installed")
            return None, 0
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return None, 0
    
    def _extract_from_docx(self, file_path: str) -> Tuple[Optional[str], int]:
        """Extract text from DOCX/DOC files"""
        try:
            if file_path.lower().endswith('.docx'):
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # For .doc files, we might need antiword or other tools
                # For now, return error
                logger.error("DOC format requires additional tools")
                return None, 0
            
            if not text.strip():
                return None, 0
            
            text = self._clean_text(text)
            word_count = len(text.split())
            
            logger.info(f"Extracted {word_count} words from DOCX")
            return text, word_count
            
        except ImportError:
            logger.error("python-docx not installed")
            return None, 0
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return None, 0
    
    def _extract_from_txt(self, file_path: str) -> Tuple[Optional[str], int]:
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            if not text.strip():
                return None, 0
            
            text = self._clean_text(text)
            word_count = len(text.split())
            
            logger.info(f"Extracted {word_count} words from TXT")
            return text, word_count
            
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            return None, 0
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove control characters but keep basic formatting
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text.strip()

# Global document parser instance
document_parser = DocumentParser()