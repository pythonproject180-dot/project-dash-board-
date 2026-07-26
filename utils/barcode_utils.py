import barcode
from barcode.writer import ImageWriter
import io
from django.core.files.base import ContentFile

def generate_barcode(code_string, save_path_prefix='barcodes/'):
    """Generate a Code128 barcode image and return as ContentFile."""
    CODE128 = barcode.get_barcode_class('code128')
    writer = ImageWriter()
    bw = CODE128(code_string, writer=writer)
    buf = io.BytesIO()
    bw.write(buf, options={'module_width': 0.2, 'module_height': 5.0, 'font_size': 6, 'text_distance': 1.0})
    filename = f'{save_path_prefix}{code_string}.png'
    return ContentFile(buf.getvalue()), filename

def generate_barcode_for_object(obj, field_name='barcode'):
    """Generate and save barcode on a Django model object."""
    code_string = getattr(obj, 'bill_id', None) or getattr(obj, 'admission_id', None) or getattr(obj, 'request_id', None) or getattr(obj, 'sale_id', None) or getattr(obj, 'claim_id', None) or str(obj.pk)
    content, filename = generate_barcode(code_string)
    setattr(obj, field_name, filename)
    obj.save()
    return obj
