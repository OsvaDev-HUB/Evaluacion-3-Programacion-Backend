import secrets
import unicodedata
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import PedidoForm, ProductoForm, RegistroForm
from .models import Producto
from .storage import editar_tienda, leer_tienda
from .templatetags.tienda import ilustracion


def cargar_productos():
    # Los productos se leen desde la base de datos usando el ORM
    return list(Producto.objects.order_by("id").values())


def buscar_producto(productos, producto_id):
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto is None:
        raise Http404("Producto no encontrado")
    return producto


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.casefold()) if not unicodedata.combining(c))


def filtrar_productos(productos, request):
    busqueda = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "")
    stock = request.GET.get("stock", "")
    orden = request.GET.get("orden", "")
    resultado = [p for p in productos if normalizar(busqueda) in normalizar(p["nombre"] + " " + p["categoria"])]
    if categoria:
        resultado = [p for p in resultado if p["categoria"] == categoria]
    if stock == "disponible":
        resultado = [p for p in resultado if p["stock"] > 0]
    elif stock == "agotado":
        resultado = [p for p in resultado if p["stock"] == 0]
    if orden in ("precio-asc", "precio-desc"):
        resultado = sorted(resultado, key=lambda p: p["precio"], reverse=orden == "precio-desc")
    elif orden == "nombre":
        resultado = sorted(resultado, key=lambda p: normalizar(p["nombre"]))
    return resultado, {"busqueda": busqueda, "categoria_actual": categoria, "stock_actual": stock, "orden_actual": orden}


def resumen(productos):
    con_stock = sum(p["stock"] > 0 for p in productos)
    categorias = sorted({p["categoria"] for p in productos})
    return {"categorias": categorias, "total_productos": len(productos), "con_stock": con_stock,
            "sin_stock": len(productos) - con_stock, "total_categorias": len(categorias)}


# Producto cuya foto representa cada categoría en la portada.
FOTOS_CATEGORIAS = {
    "Herramientas manuales": 5,
    "Herramientas eléctricas": 8,
    "Fijaciones": 11,
    "Pinturas": 16,
    "Electricidad": 21,
    "Gasfitería": 26,
    "Construcción": 31,
    "Seguridad": 38,
}


def categorias_portada(productos):
    """Arma una celda por categoría con su foto, total de productos y stock."""
    categorias = []
    for nombre in sorted({p["categoria"] for p in productos}):
        grupo = [p for p in productos if p["categoria"] == nombre]
        id_foto = FOTOS_CATEGORIAS.get(nombre)
        producto_foto = next((p for p in grupo if p["id"] == id_foto), grupo[0])
        categorias.append({
            "nombre": nombre,
            "producto": producto_foto,
            "total": len(grupo),
            "con_stock": sum(p["stock"] > 0 for p in grupo),
        })
    return categorias


def inicio(request):
    productos = cargar_productos()
    return render(request, "catalogo/inicio.html", {
        **resumen(productos),
        "categorias_portada": categorias_portada(productos),
    })


def lista_productos(request):
    productos = cargar_productos()
    filtrados, filtros = filtrar_productos(productos, request)
    return render(request, "catalogo/lista.html", {"productos": filtrados, **resumen(productos), **filtros})


def detalle_producto(request, producto_id):
    productos = cargar_productos()
    try:
        producto = buscar_producto(productos, producto_id)
    except Http404:
        return render(request, "catalogo/no_encontrado.html", {"producto_id": producto_id}, status=404)
    relacionados = [p for p in productos if p["categoria"] == producto["categoria"] and p["id"] != producto_id][:4]
    return render(request, "catalogo/detalle.html", {"producto": producto, "relacionados": relacionados})


def destino_seguro(request, defecto="catalogo:lista"):
    destino = request.POST.get("next") or request.GET.get("next")
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return destino
    return reverse(defecto)


class AccesoView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return reverse("catalogo:gestion" if self.request.user.is_staff else "catalogo:lista")


def registro(request):
    if request.user.is_authenticated:
        return redirect("catalogo:lista")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            usuario = form.save()
        except (ValidationError, IntegrityError):
            form.add_error("username", "Ya existe una cuenta con ese nombre de usuario.")
        else:
            # El cliente nuevo queda guardado en usuarios.json, por eso inicia sesión con ese backend
            login(request, usuario, backend="catalogo.backends.UsuariosJSONBackend")
            messages.success(request, "Tu cuenta está lista. Ya puedes confirmar tu pedido.")
            return redirect(destino_seguro(request))
    return render(request, "registration/registro.html", {"form": form, "next": destino_seguro(request)})


def detalle_carrito(request, productos=None):
    """Precios y disponibilidad siempre se resuelven en el servidor."""
    productos = productos if productos is not None else cargar_productos()
    mapa = {str(p["id"]): p for p in productos}
    cantidades = request.session.get("carrito", {})
    items = []
    ajustado = False
    valido = {}
    for clave, cantidad in cantidades.items():
        producto = mapa.get(clave)
        if not producto or not isinstance(cantidad, int) or cantidad <= 0:
            ajustado = True
            continue
        unidades = min(cantidad, producto["stock"])
        ajustado = ajustado or unidades != cantidad
        if unidades:
            valido[clave] = unidades
            items.append({"producto": producto, "cantidad": unidades, "subtotal": unidades * producto["precio"]})
    if ajustado:
        request.session["carrito"] = valido
    return {"items": items, "total": sum(i["subtotal"] for i in items),
            "unidades": sum(i["cantidad"] for i in items), "ajustado": ajustado}


def carrito(request):
    contexto = detalle_carrito(request)
    if contexto["ajustado"]:
        messages.warning(request, "Ajustamos tu carrito a las existencias actuales. Revisa las cantidades antes de continuar.")
    return render(request, "catalogo/carrito.html", contexto)


@require_POST
def modificar_carrito(request, producto_id):
    producto = buscar_producto(cargar_productos(), producto_id)
    carrito_actual = request.session.get("carrito", {}).copy()
    clave = str(producto_id)
    accion = request.POST.get("accion", "agregar")
    error = None
    try:
        cantidad = int(request.POST.get("cantidad", "1"))
        if cantidad < 1:
            raise ValueError
    except (ValueError, TypeError):
        cantidad = 0
        error = "Ingresa una cantidad entera mayor que cero."
    if accion == "eliminar":
        carrito_actual.pop(clave, None)
        error = None
        mensaje = "Producto eliminado del carrito."
    elif accion not in ("agregar", "actualizar"):
        error = "La acción solicitada no es válida."
    elif not error:
        cantidad_final = cantidad + carrito_actual.get(clave, 0) if accion == "agregar" else cantidad
        if cantidad_final > producto["stock"]:
            error = f'Solo hay {producto["stock"]} unidades disponibles de {producto["nombre"]}.'
        else:
            carrito_actual[clave] = cantidad_final
            mensaje = "Producto agregado al carrito." if accion == "agregar" else "Cantidad actualizada."
    if not error:
        request.session["carrito"] = carrito_actual
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"ok": not error, "mensaje": error or mensaje, "cantidad": sum(carrito_actual.values())}, status=400 if error else 200)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, mensaje)
    return redirect(destino_seguro(request, "catalogo:carrito"))


@login_required
def checkout(request):
    contexto = detalle_carrito(request)
    if contexto["ajustado"]:
        messages.warning(request, "El stock cambió. Revisa las cantidades disponibles en tu carrito.")
        return redirect("catalogo:carrito")
    if not contexto["items"]:
        messages.info(request, "Agrega productos a tu carrito para continuar.")
        return redirect("catalogo:carrito")
    token = request.session.get("pedido_token")
    if not token:
        token = secrets.token_hex(24)
        request.session["pedido_token"] = token
    form = PedidoForm(request.POST or None, initial={"nombre": request.user.first_name or request.user.username, "email": request.user.email})
    if request.method == "POST" and form.is_valid():
        if request.POST.get("token") != token:
            form.add_error(None, "Esta confirmación expiró. Revisa los datos e inténtalo nuevamente.")
        else:
            with transaction.atomic(), editar_tienda() as datos:
                existente = next((p for p in datos["pedidos"] if p["token"] == token and p["usuario_id"] == request.user.pk), None)
                if existente:
                    pedido = existente
                else:
                    actual = detalle_carrito(request)
                    if actual["ajustado"] or not actual["items"]:
                        messages.warning(request, "El stock cambió durante la confirmación. Revisa tu carrito.")
                        return redirect("catalogo:carrito")
                    pedido = {"id": secrets.token_hex(6).upper(), "token": token, "usuario_id": request.user.pk,
                              "fecha": timezone.localtime().isoformat(), "contacto": form.cleaned_data,
                              "items": [{"nombre": i["producto"]["nombre"], "precio": i["producto"]["precio"],
                                         "cantidad": i["cantidad"], "subtotal": i["subtotal"]} for i in actual["items"]],
                              "total": actual["total"]}
                    # Se descuenta el stock de cada producto en la base de datos
                    for item in actual["items"]:
                        Producto.objects.filter(pk=item["producto"]["id"]).update(stock=F("stock") - item["cantidad"])
                    datos["pedidos"].append(pedido)
            request.session["carrito"] = {}
            request.session.pop("pedido_token", None)
            return redirect("catalogo:pedido", pedido_id=pedido["id"])
    return render(request, "catalogo/checkout.html", {**contexto, "form": form, "token": token})


@login_required
def pedido(request, pedido_id):
    encontrado = next((p for p in leer_tienda()["pedidos"] if p["id"] == pedido_id and
                       (p["usuario_id"] == request.user.pk or request.user.is_staff)), None)
    if not encontrado:
        raise Http404("Pedido no encontrado")
    return render(request, "catalogo/pedido.html", {"pedido": encontrado})


@login_required
def cuenta(request):
    pedidos = [p for p in reversed(leer_tienda()["pedidos"]) if p["usuario_id"] == request.user.pk]
    return render(request, "catalogo/cuenta.html", {"pedidos": pedidos})


def administrador_requerido(vista):
    @login_required
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied("Solo los administradores pueden gestionar la tienda.")
        return vista(request, *args, **kwargs)
    return protegida


@administrador_requerido
def gestion(request):
    productos = cargar_productos()
    filtrados, filtros = filtrar_productos(productos, request)
    return render(request, "catalogo/gestion.html", {"productos": filtrados, **resumen(productos), **filtros})


@administrador_requerido
def producto_formulario(request, producto_id=None):
    productos = cargar_productos()
    producto = buscar_producto(productos, producto_id) if producto_id is not None else None
    inicial = {**producto, "ilustracion": ilustracion(producto)} if producto else {"stock": 0, "ilustracion": "caja"}
    form = ProductoForm(request.POST or None, request.FILES or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        campos = dict(form.cleaned_data)
        foto = campos.pop("foto")
        quitar_foto = campos.pop("quitar_foto")
        if producto:
            actual = Producto.objects.get(pk=producto_id)
            for campo, valor in campos.items():
                setattr(actual, campo, valor)
        else:
            actual = Producto(**campos)
        # Una foto nueva reemplaza a la anterior; también se puede quitar
        if foto or quitar_foto:
            actual.foto.delete(save=False)
        if foto:
            actual.foto = foto
        actual.save()
        messages.success(request, "Producto actualizado." if producto else "Producto creado.")
        return redirect("catalogo:gestion")
    return render(request, "catalogo/producto_formulario.html", {"form": form, "producto": producto, **resumen(productos)})


@administrador_requerido
def eliminar_producto(request, producto_id):
    producto = buscar_producto(cargar_productos(), producto_id)
    if request.method == "POST":
        actual = Producto.objects.get(pk=producto_id)
        actual.foto.delete(save=False)
        actual.delete()
        messages.success(request, "Producto eliminado de la tienda.")
        return redirect("catalogo:gestion")
    return render(request, "catalogo/eliminar_producto.html", {"producto": producto})


@administrador_requerido
def pedidos_gestion(request):
    return render(request, "catalogo/pedidos_gestion.html", {"pedidos": list(reversed(leer_tienda()["pedidos"]))})
