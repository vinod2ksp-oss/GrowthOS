from pathlib import Path


class MaterialParsingService:
    """Extracts inspectable text only; it never asserts structured facts."""

    def parse(self, path: Path) -> tuple[str, dict]:
        suffix = path.suffix.lower()
        try:
            if suffix == ".pdf":
                from pypdf import PdfReader
                text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages).strip()
                return ("pending_confirmation", {"extracted_text": text, "requires_manual_confirmation": True})
            if suffix == ".docx":
                from docx import Document
                text = "\n".join(paragraph.text for paragraph in Document(path).paragraphs).strip()
                return ("pending_confirmation", {"extracted_text": text, "requires_manual_confirmation": True})
            if suffix == ".txt":
                text = path.read_text(encoding="utf-8").strip()
                return ("pending_confirmation", {"extracted_text": text, "requires_manual_confirmation": True})
            if suffix in {".png", ".jpg", ".jpeg"}:
                return ("pending_confirmation", {"extracted_text": None, "requires_manual_entry": True})
            return ("pending_confirmation", {"extracted_text": None, "requires_manual_entry": True})
        except Exception as exc:
            return ("parse_failed", {"error": str(exc), "requires_manual_entry": True})
