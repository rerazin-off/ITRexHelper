import os
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _register_fonts():
    font_paths = [
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/times.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    for path in font_paths:
        if path.endswith('arial.ttf') and os.path.exists(path):
            pdfmetrics.registerFont(TTFont('DocFont', path))
            pdfmetrics.registerFont(TTFont('DocFontBold', 'C:/Windows/Fonts/arialbd.ttf'))
            return 'DocFont', 'DocFontBold'
        if path.endswith('DejaVuSans.ttf') and os.path.exists(path):
            pdfmetrics.registerFont(TTFont('DocFont', path))
            pdfmetrics.registerFont(TTFont('DocFontBold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
            return 'DocFont', 'DocFontBold'
    return 'Helvetica', 'Helvetica-Bold'


def _build_styles(font_name, font_bold):
    styles = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'title',
            parent=styles['Heading1'],
            fontName=font_bold,
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        'heading': ParagraphStyle(
            'heading',
            parent=styles['Heading2'],
            fontName=font_bold,
            fontSize=12,
            spaceBefore=12,
            spaceAfter=8,
        ),
        'body': ParagraphStyle(
            'body',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            alignment=TA_JUSTIFY,
            leading=14,
            spaceAfter=8,
        ),
        'center': ParagraphStyle(
            'center',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            alignment=TA_CENTER,
        ),
    }


def _render_contract_pdf(context):
    font_name, font_bold = _register_fonts()
    styles = _build_styles(font_name, font_bold)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph('ДОГОВОР ОКАЗАНИЯ УСЛУГ № {{ contract_number }}'.replace('{{ contract_number }}', context['contract_number']), styles['title']),
        Paragraph(f"г. Нижний Новгород&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{context['contract_date']}", styles['center']),
        Spacer(1, 0.5 * cm),
        Paragraph(
            f"<b>{context['contractor_name']}</b>, именуемое в дальнейшем «Исполнитель», "
            f"и <b>{context['client_company']}</b> в лице {context['client_name']}, "
            f"именуемый(ая) в дальнейшем «Заказчик», заключили настоящий договор о нижеследующем:",
            styles['body'],
        ),
        Paragraph('1. Предмет договора', styles['heading']),
        Paragraph(
            f"1.1. Исполнитель обязуется оказать услуги технической поддержки по заявке "
            f"№ {context['ticket_id']} от {context['ticket_date']}: {context['ticket_description']}.",
            styles['body'],
        ),
        Paragraph('2. Стороны договора', styles['heading']),
        Paragraph(f"2.1. Исполнитель: {context['contractor_name']}, {context['contractor_details']}.", styles['body']),
        Paragraph(f"2.2. Заказчик: {context['client_company']}, контакт: {context['client_contact']}.", styles['body']),
        Paragraph('3. Сроки и порядок исполнения', styles['heading']),
        Paragraph(
            f"3.1. Услуги оказываются в рамках заявки № {context['ticket_id']}. "
            f"Статус заявки: {context['ticket_status']}.",
            styles['body'],
        ),
        Paragraph('4. Подписи сторон', styles['heading']),
        Spacer(1, 1 * cm),
    ]

    sign_table = Table(
        [
            ['Исполнитель', 'Заказчик'],
            [context['contractor_name'], context['client_company']],
            ['________________ / ITREX /', f"________________ / {context['client_name']} /"],
        ],
        colWidths=[8 * cm, 8 * cm],
    )
    sign_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 2), (-1, 2), 24),
    ]))
    story.append(sign_table)
    doc.build(story)
    return buffer.getvalue()


def _render_analytics_pdf(context):
    font_name, font_bold = _register_fonts()
    styles = _build_styles(font_name, font_bold)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph('IT REX HELPER', styles['center']),
        Paragraph('Отчёт по аналитике заявок', styles['title']),
        Paragraph(f"Дата формирования: {context['report_date']}", styles['center']),
        Spacer(1, 0.5 * cm),
        Paragraph('Сводные показатели', styles['heading']),
    ]

    metrics = [
        ['Показатель', 'Значение'],
        ['Всего заявок', context['total_count']],
        ['В работе', context['in_progress_count']],
        ['Просрочено', context['overdue_count']],
        ['Заявок в этом месяце', context['tickets_month']],
        ['Обработано за месяц', context['processed_month']],
    ]
    table = Table(metrics, colWidths=[10 * cm, 6 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 0.5 * cm), Paragraph('Динамика за последние 6 месяцев', styles['heading'])])

    months_table_data = [['Месяц', 'Количество заявок']]
    for month, count in zip(context['chart_months'], context['chart_values']):
        months_table_data.append([month, str(count)])
    months_table = Table(months_table_data, colWidths=[10 * cm, 6 * cm])
    months_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
    ]))
    story.extend([months_table, Spacer(1, 0.5 * cm), Paragraph('Журнал аудита (последние изменения)', styles['heading'])])

    audit_data = [['Заявка', 'Было', 'Стало', 'Когда']]
    for row in context['audit_rows']:
        audit_data.append([row['ticket'], row['old_status'], row['new_status'], row['changed_at']])
    if len(audit_data) == 1:
        audit_data.append(['—', '—', '—', '—'])

    audit_table = Table(audit_data, colWidths=[3 * cm, 4 * cm, 4 * cm, 5 * cm])
    audit_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(audit_table)
    doc.build(story)
    return buffer.getvalue()


def render_pdf_fallback(template_name, context):
    if template_name == 'contract.docx':
        return _render_contract_pdf(context)
    if template_name == 'analytics_report.docx':
        return _render_analytics_pdf(context)
    raise DocumentGenerationError(f'Неизвестный шаблон: {template_name}')
