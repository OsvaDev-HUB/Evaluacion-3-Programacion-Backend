from django import template
from django.conf import settings

register = template.Library()

ILUSTRACIONES = (
    "martillo", "destornillador", "alicate", "llave", "huincha",
    "taladro", "sierra", "sierra", "taladro", "caja",
    "tornillos", "tornillos", "tornillos", "tornillos", "tornillos",
    "pintura", "pintura", "rodillo", "brocha", "cinta",
    "cable", "caja", "caja", "ampolleta", "cable",
    "tuberia", "tuberia", "cinta", "tuberia", "pintura",
    "saco", "saco", "silicona", "silicona", "caja",
    "guantes", "lentes", "casco", "protector", "protector",
)


@register.filter
def ilustracion(producto):
    if producto.get("ilustracion"):
        return producto["ilustracion"]
    indice = producto["id"] - 1
    return ILUSTRACIONES[indice] if 0 <= indice < len(ILUSTRACIONES) else "caja"


@register.filter
def imagen_producto(producto):
    """Devuelve la foto optimizada de los productos originales del catálogo."""
    producto_id = producto.get("id")
    if isinstance(producto_id, int) and 1 <= producto_id <= 40:
        return f"catalogo/img/productos/producto-{producto_id:02d}.webp"
    return ""


@register.filter
def foto_subida(producto):
    """URL de la foto que subió el administrador, o texto vacío si no tiene."""
    ruta = producto.get("foto")
    return settings.MEDIA_URL + ruta if ruta else ""


@register.filter
def pesos(valor):
    return "$" + f"{int(valor):,}".replace(",", ".")
