def carrito(request):
    cantidades = request.session.get("carrito", {})
    return {"cantidad_carrito": sum(c for c in cantidades.values() if isinstance(c, int) and c > 0)}
