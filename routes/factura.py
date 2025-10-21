# factura.py
from flask import Blueprint, render_template, abort, make_response, current_app
from flask_login import login_required, current_user
from io import BytesIO
from decimal import Decimal
from xhtml2pdf import pisa
from ..models import Factura, FacturaItem
from .utils import _dict_to_namespace, _static_file_to_datauri  # funciones auxiliares si las tienes

factura_bp = Blueprint('factura', __name__)

# ---------------------------------
# Ver factura en pantalla
# ---------------------------------
@factura_bp.route('/factura/<int:factura_id>')
@login_required
def invoice_detail(factura_id):
    factura = Factura.query.get_or_404(factura_id)

    try:
        usuario_id_session = current_user.id_usuario if hasattr(current_user, 'id_usuario') else current_user.get_id()
    except Exception:
        usuario_id_session = current_user.get_id()

    if str(factura.id_usuario) != str(usuario_id_session) and not getattr(current_user, 'is_admin', False):
        abort(403)

    items_db = FacturaItem.query.filter_by(id_factura=factura.id_factura).all()

    items_preparados = []
    total = Decimal('0.00')
    for it in items_db:
        precio = Decimal(str(getattr(it, 'precio_unitario', '0')))
        cantidad = int(getattr(it, 'cantidad', 1))
        subtotal = Decimal(str(getattr(it, 'subtotal', str(precio * cantidad))))
        items_preparados.append({
            'nombre_producto': getattr(it, 'nombre_producto', 'Producto'),
            'talla': getattr(it, 'talla', '-') or '-',
            'color': getattr(it, 'color', '-') or '-',
            'cantidad': cantidad,
            'precio_unitario': float(precio),
            'subtotal': float(subtotal)
        })
        total += subtotal

    creado = getattr(factura, 'creado_en', None)
    factura_ready = {
        'id_factura': factura.id_factura,
        'usuario': {'nombre': getattr(factura, 'nombre_cliente', getattr(current_user, 'nombre', factura.id_usuario))},
        'creado_en': creado,
        'items': items_preparados,
        'total': float(total),
        'direccion_envio': getattr(factura, 'direccion_envio', '') or 'No registrada'
    }

    factura_obj = _dict_to_namespace(factura_ready)
    return render_template('factura.html', factura=factura_obj)


# ---------------------------------
# Descargar factura en PDF
# ---------------------------------
@factura_bp.route('/factura/<int:factura_id>/pdf')
@login_required
def factura_pdf(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    usuario_session = getattr(current_user, 'id_usuario', None) or current_user.get_id()

    if str(factura.id_usuario) != str(usuario_session) and not getattr(current_user, 'is_admin', False):
        abort(403)

    items_db = FacturaItem.query.filter_by(id_factura=factura.id_factura).all()

    creado = getattr(factura, 'creado_en', None)
    creado_str = creado.strftime("%d/%m/%Y %H:%M") if creado else ''

    factura_ctx = {
        'id_factura': factura.id_factura,
        'usuario': {'nombre': getattr(factura, 'nombre_cliente', getattr(factura, 'id_usuario', 'Cliente'))},
        'creado_en_str': creado_str,
        'direccion_envio': getattr(factura, 'direccion_envio', '') or 'No registrada',
        'total': float(factura.total) if factura.total is not None else 0.0
    }

    items_ctx = []
    for it in items_db:
        items_ctx.append({
            'nombre_producto': getattr(it, 'nombre_producto', 'Producto'),
            'talla': getattr(it, 'talla', '-') or '-',
            'color': getattr(it, 'color', '-') or '-',
            'cantidad': int(getattr(it, 'cantidad', 1)),
            'precio_unitario': float(getattr(it, 'precio_unitario', 0)),
            'subtotal': float(getattr(it, 'subtotal', 0))
        })

    logo_datauri = _static_file_to_datauri('logo.png')

    html_out = render_template(
        'factura_pdf.html',
        factura=factura_ctx,
        items=items_ctx,
        logo_datauri=logo_datauri
    )

    pdf_io = BytesIO()
    pisa_status = pisa.CreatePDF(src=html_out, dest=pdf_io, encoding='utf-8')

    if pisa_status.err:
        current_app.logger.error("xhtml2pdf error: %s", pisa_status.err)
        return "Error generando PDF", 500

    pdf_bytes = pdf_io.getvalue()
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=factura_{factura.id_factura}.pdf'
    return response