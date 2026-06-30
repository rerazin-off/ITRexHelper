import os
import subprocess
import tempfile
import time
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


def _read_pdf_file(pdf_path):
    if not os.path.exists(pdf_path):
        return None
    with open(pdf_path, 'rb') as file:
        return file.read()


def _convert_with_docx2pdf(docx_path, pdf_path):
    try:
        from docx2pdf import convert

        convert(docx_path, pdf_path)
        return _read_pdf_file(pdf_path)
    except Exception:
        return None


def _convert_with_libreoffice(tmp_dir, docx_path, pdf_path):
    try:
        result = subprocess.run(
            [
                'soffice',
                '--headless',
                '--convert-to',
                'pdf',
                '--outdir',
                tmp_dir,
                docx_path,
            ],
            capture_output=True,
            timeout=60,
            check=False,
        )
        if result.returncode == 0:
            return _read_pdf_file(pdf_path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _convert_docx_to_pdf(docx_buffer):
    # docx2pdf on Windows keeps Word open on the temp file; ignore cleanup errors.
    pdf_bytes = None

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        docx_path = os.path.join(tmp, 'document.docx')
        pdf_path = os.path.join(tmp, 'document.pdf')

        with open(docx_path, 'wb') as file:
            file.write(docx_buffer.getvalue())

        pdf_bytes = _convert_with_docx2pdf(docx_path, pdf_path)
        if not pdf_bytes:
            pdf_bytes = _convert_with_libreoffice(tmp, docx_path, pdf_path)

    return pdf_bytes


def generate_pdf_from_template(template_name, context):
    docx_buffer = _render_docx(template_name, context)
    pdf_bytes = _convert_docx_to_pdf(docx_buffer)
    if pdf_bytes:
        return pdf_bytes

    from .pdf_fallback import render_pdf_fallback

    return render_pdf_fallback(template_name, context)
