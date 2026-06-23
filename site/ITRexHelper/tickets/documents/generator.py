import os
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from django.conf import settings

TEMPLATE_DIR = Path(settings.BASE_DIR) / 'document_templates'


class DocumentGenerationError(Exception):
    """Ошибка формирования или конвертации документа."""


def _render_docx(template_name, context):
    from docxtpl import DocxTemplate

    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise DocumentGenerationError(f'Шаблон не найден: {template_name}')

    doc = DocxTemplate(str(template_path))
    doc.render(context)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def _convert_docx_to_pdf(docx_buffer):
    with tempfile.TemporaryDirectory() as tmp:
        docx_path = os.path.join(tmp, 'document.docx')
        pdf_path = os.path.join(tmp, 'document.pdf')

        with open(docx_path, 'wb') as file:
            file.write(docx_buffer.getvalue())

        try:
            from docx2pdf import convert

            convert(docx_path, pdf_path)
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as file:
                    return file.read()
        except Exception:
            pass

        try:
            result = subprocess.run(
                [
                    'soffice',
                    '--headless',
                    '--convert-to',
                    'pdf',
                    '--outdir',
                    tmp,
                    docx_path,
                ],
                capture_output=True,
                timeout=60,
                check=False,
            )
            if result.returncode == 0 and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as file:
                    return file.read()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return None


def generate_pdf_from_template(template_name, context):
    docx_buffer = _render_docx(template_name, context)
    pdf_bytes = _convert_docx_to_pdf(docx_buffer)
    if pdf_bytes:
        return pdf_bytes

    from .pdf_fallback import render_pdf_fallback

    return render_pdf_fallback(template_name, context)
