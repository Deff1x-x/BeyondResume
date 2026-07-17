import re
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class UnsupportedResumeParserTypeError(Exception):
    pass


class ResumeFileReadError(Exception):
    pass


class ResumeDocumentParseError(Exception):
    pass


class EmptyExtractedResumeTextError(Exception):
    pass


def normalize_resume_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _extract_pdf(path: Path) -> str:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise ResumeDocumentParseError
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ResumeDocumentParseError:
        raise
    except FileNotFoundError as error:
        raise ResumeFileReadError from error
    except OSError as error:
        raise ResumeFileReadError from error
    except Exception as error:
        raise ResumeDocumentParseError from error


def _extract_docx(path: Path) -> str:
    try:
        document = Document(str(path))
        parts: list[str] = []
        for child in document.element.body.iterchildren():
            if child.tag.endswith("}p"):
                parts.append(Paragraph(child, document).text)
            elif child.tag.endswith("}tbl"):
                table = Table(child, document)
                parts.extend(cell.text for row in table.rows for cell in row.cells)
        return "\n".join(parts)
    except FileNotFoundError as error:
        raise ResumeFileReadError from error
    except OSError as error:
        raise ResumeFileReadError from error
    except Exception as error:
        raise ResumeDocumentParseError from error


def extract_resume_text(path: Path, mime_type: str) -> str:
    if mime_type == PDF_MIME:
        extracted = _extract_pdf(path)
    elif mime_type == DOCX_MIME:
        extracted = _extract_docx(path)
    else:
        raise UnsupportedResumeParserTypeError
    normalized = normalize_resume_text(extracted)
    if not normalized:
        raise EmptyExtractedResumeTextError
    return normalized
