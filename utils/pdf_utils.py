"""PDF and Image generation utilities for Hamro Hospital."""
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
from PIL import Image


def render_to_pdf(template_src, context_dict=None):
    """Render a Django template to PDF."""
    if context_dict is None:
        context_dict = {}
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode('UTF-8')), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def download_as_pdf(template_src, context_dict, filename='document.pdf'):
    """Generate PDF and return as downloadable response."""
    pdf_response = render_to_pdf(template_src, context_dict)
    if pdf_response:
        pdf_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return pdf_response
    return HttpResponse('Error generating PDF', status=500)


def render_to_image(template_src, context_dict=None, width=800, format='JPEG'):
    """Render a Django template to an image (JPG/PNG) for download.
    Uses Pillow to convert the HTML-rendered content into an image.
    Note: For production-quality HTML-to-image, consider using html2image or wkhtmltoimage.
    This simplified version creates a placeholder image with text content.
    """
    if context_dict is None:
        context_dict = {}
    template = get_template(template_src)
    html = template.render(context_dict)

    # Create a simple image representation
    img = Image.new('RGB', (width, 1200), color=(255, 255, 255))
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    except (IOError, OSError):
        font = ImageFont.load_default()
        title_font = font

    # Draw header
    draw.text((20, 20), 'Hamro Hospital Management System', fill=(0, 0, 0), font=title_font)
    draw.text((20, 50), html[:2000], fill=(50, 50, 50), font=font)

    buf = io.BytesIO()
    img.save(buf, format=format, quality=95)
    buf.seek(0)
    content_type = 'image/jpeg' if format == 'JPEG' else 'image/png'
    return HttpResponse(buf.getvalue(), content_type=content_type)


def download_as_image(template_src, context_dict, filename='document.jpg', width=800, format='JPEG'):
    """Generate an image and return as downloadable response."""
    img_response = render_to_image(template_src, context_dict, width, format)
    if img_response:
        img_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return img_response
    return HttpResponse('Error generating image', status=500)
