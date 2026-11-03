def carrito(request):
    cantidades = request.session.get("carrito", {})
    return {"cantidad_carrito": sum(c for c in cantidades.values() if isinstance(c, int) and c > 0)}


def gestion(request):
    """Consultas sin responder, para el aviso en el menú del administrador."""
    if request.user.is_authenticated and request.user.is_staff:
        from .models import ConsultaCliente
        return {"consultas_pendientes": ConsultaCliente.objects.filter(respuesta="").count()}
    return {}
