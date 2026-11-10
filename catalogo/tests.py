from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ConsultaCliente, DetallePedido, Pedido, PerfilCliente, Producto, Suscripcion
from .views import cargar_productos
from .usuarios import agregar_usuario, buscar_usuario, cargar_usuarios, editar_usuarios


class CatalogoAisladoMixin:
    """Carga la fixture de productos y aísla el archivo JSON de usuarios."""

    fixtures = ["productos"]

    def setUp(self):
        super().setUp()
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        usuarios = Path(temporal.name) / "usuarios.json"
        usuarios.write_text(
            (Path(__file__).parent.parent / "data/usuarios.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        configuracion = override_settings(
            USUARIOS_DATOS=usuarios,
        )
        configuracion.enable()
        self.addCleanup(configuracion.disable)
        with editar_usuarios() as datos:
            for usuario in get_user_model().objects.all():
                agregar_usuario(datos, usuario, "Clave-prueba-432!")


class DatosCatalogoTests(CatalogoAisladoMixin, TestCase):
    def test_base_de_datos_contiene_los_40_productos_de_ferreteria(self):
        productos = cargar_productos()

        self.assertEqual(len(productos), 40)
        self.assertEqual(len({producto["id"] for producto in productos}), 40)

        campos_requeridos = {"id", "nombre", "categoria", "precio", "stock"}
        for producto in productos:
            self.assertTrue(campos_requeridos.issubset(producto))


class InicioTests(CatalogoAisladoMixin, TestCase):
    def test_portada_presenta_la_tienda_y_enlaza_al_catalogo_separado(self):
        self.assertEqual(reverse("catalogo:inicio"), "/")
        self.assertEqual(reverse("catalogo:lista"), "/catalogo/")
        response = self.client.get(reverse("catalogo:inicio"))

        self.assertTemplateUsed(response, "catalogo/inicio.html")
        self.assertContains(response, 'id="titulo-inicio"')
        self.assertContains(response, 'href="/catalogo/"')
        self.assertContains(response, "Ver catálogo")
        self.assertContains(response, "catalogo/img/landing/maestro-hero.webp")
        self.assertContains(response, 'id="historia"')
        self.assertContains(response, 'id="contacto"')
        self.assertContains(response, "Nuestra historia")
        self.assertContains(response, "¿Tienes una pregunta?")
        self.assertContains(response, "Sabemos que cada visita nace de una necesidad distinta")
        self.assertContains(response, "contacto@eltornillo.example")
        self.assertContains(response, "Horario")
        self.assertNotContains(response, "data-producto")
        self.assertNotContains(response, 'id="filtros-catalogo"')
        self.assertNotContains(response, 'id="productos"')

    def test_catalogo_independiente_mantiene_productos_y_acceso_al_inicio(self):
        response = self.client.get(reverse("catalogo:lista"))

        self.assertTemplateUsed(response, "catalogo/lista.html")
        self.assertContains(response, "data-producto", count=40)
        self.assertContains(response, 'href="/" aria-label="El Tornillo, inicio"')
        self.assertNotContains(response, 'id="titulo-inicio"')
        self.assertNotContains(response, 'id="como-comprar"')


class ListaProductosTests(CatalogoAisladoMixin, TestCase):
    def test_lista_muestra_todos_los_productos_y_el_resumen(self):
        response = self.client.get(reverse("catalogo:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalogo/lista.html")
        self.assertEqual(response.context["total_productos"], 40)
        self.assertEqual(response.context["con_stock"], 32)
        self.assertEqual(response.context["sin_stock"], 8)
        self.assertEqual(response.context["total_categorias"], 8)
        self.assertEqual(len(response.context["categorias"]), 8)
        self.assertEqual(len(response.context["productos"]), 40)
        self.assertContains(response, "filtros-catalogo")
        self.assertContains(response, "data-producto", count=40)
        self.assertContains(response, "catalogo/js/catalogo.js")


class DetalleProductoTests(CatalogoAisladoMixin, TestCase):
    def test_detalle_muestra_un_producto_existente(self):
        response = self.client.get(
            reverse("catalogo:detalle", kwargs={"producto_id": 1})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalogo/detalle.html")
        self.assertContains(response, "Martillo carpintero 16 oz")

    def test_detalle_inexistente_responde_404(self):
        response = self.client.get(
            reverse("catalogo:detalle", kwargs={"producto_id": 999})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "catalogo/no_encontrado.html")
        self.assertContains(response, "Producto no encontrado", status_code=404)


class InicioSesionTests(CatalogoAisladoMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.usuario = get_user_model().objects.create_user(
            username="cliente_prueba",
            password="clave-segura-123",
        )
        with editar_usuarios() as datos:
            agregar_usuario(datos, self.usuario, "clave-segura-123")

    def test_pagina_de_inicio_de_sesion(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "Acceso de administración")

    def test_usuario_puede_iniciar_sesion(self):
        response = self.client.post(
            reverse("login"),
            {"username": "cliente_prueba", "password": "clave-segura-123"},
        )

        self.assertRedirects(response, reverse("catalogo:lista"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.usuario.id)

    def test_panel_administrador_solicita_credenciales(self):
        response = self.client.get(reverse("admin:index"))

        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('admin:index')}",
        )


class TiendaTests(CatalogoAisladoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = get_user_model().objects.create_user("comprador", email="cliente@example.test", password="Clave-prueba-432!")
        cls.otro = get_user_model().objects.create_user("otro", password="Clave-prueba-432!")
        cls.administrador = get_user_model().objects.create_user("encargado", is_staff=True, password="Clave-prueba-432!")

    def setUp(self):
        super().setUp()
        self.datos_producto = {"nombre": "Llave nueva", "categoria": "Herramientas manuales", "precio": 5000,
                               "stock": 5, "descripcion": "Llave para reparaciones.", "ilustracion": "llave"}

    def agregar(self, producto_id=1, cantidad=1, **extra):
        return self.client.post(reverse("catalogo:modificar_carrito", args=[producto_id]), {"cantidad": cantidad, **extra})

    def confirmar(self):
        response = self.client.get(reverse("catalogo:checkout"))
        return self.client.post(reverse("catalogo:checkout"), {"nombre": "Cliente de prueba", "email": "cliente@example.test",
                                "telefono": "+56 9 1234 5678", "token": response.context["token"]})

    def test_carrito_agrega_actualiza_elimina_y_calcula_desde_el_precio_real(self):
        self.agregar(cantidad=2, precio=1)
        response = self.client.get(reverse("catalogo:carrito"))
        self.assertEqual(response.context["total"], 25980)
        self.assertEqual(response.context["unidades"], 2)
        self.agregar(cantidad=3, accion="actualizar")
        self.assertEqual(self.client.session["carrito"], {"1": 3})
        self.agregar(accion="eliminar")
        self.assertEqual(self.client.session["carrito"], {})

    def test_carrito_rechaza_stock_insuficiente_y_cantidades_invalidas(self):
        for cantidad in (0, -1, "abc", "1.5", 19):
            with self.subTest(cantidad=cantidad):
                self.agregar(cantidad=cantidad)
                self.assertNotIn("1", self.client.session.get("carrito", {}))
        self.agregar(producto_id=4)
        self.assertNotIn("4", self.client.session.get("carrito", {}))
        self.agregar(cantidad=18)
        self.agregar(cantidad=1)
        self.assertEqual(self.client.session["carrito"]["1"], 18)

    def test_agregar_con_ajax_actualiza_contador_y_errores(self):
        url = reverse("catalogo:modificar_carrito", args=[1])
        response = self.client.post(url, {"cantidad": 2}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.json(), {"ok": True, "mensaje": "Producto agregado al carrito.", "cantidad": 2})
        response = self.client.post(url, {"cantidad": 99}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(response.json()["cantidad"], 2)

    def test_carrito_no_muta_por_get_y_exige_csrf(self):
        url = reverse("catalogo:modificar_carrito", args=[1])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(url, {"cantidad": 1}).status_code, 403)

    def test_carrito_se_ajusta_si_cambia_stock_o_se_elimina_producto(self):
        self.agregar(cantidad=8)
        self.agregar(producto_id=2)
        Producto.objects.filter(pk=1).update(stock=2)
        Producto.objects.filter(pk=2).delete()
        response = self.client.get(reverse("catalogo:carrito"))
        self.assertContains(response, "Ajustamos tu carrito")
        self.assertEqual(self.client.session["carrito"], {"1": 2})

    def test_login_conserva_carrito_y_redirige_por_rol(self):
        self.agregar(cantidad=2)
        self.client.post(reverse("login"), {"username": "comprador", "password": "Clave-prueba-432!"})
        self.assertEqual(self.client.session["carrito"], {"1": 2})
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "encargado", "password": "Clave-prueba-432!"})
        self.assertRedirects(response, reverse("catalogo:gestion"))

    def test_login_y_carrito_no_redirigen_a_sitios_externos(self):
        response = self.agregar(next="https://example.org/")
        self.assertRedirects(response, reverse("catalogo:carrito"))
        response = self.client.post(reverse("login"), {"username": "comprador", "password": "Clave-prueba-432!", "next": "https://example.org/"})
        self.assertRedirects(response, reverse("catalogo:lista"))

    def test_registro_crea_solo_cliente_y_conserva_carrito(self):
        self.agregar()
        response = self.client.post(reverse("catalogo:registro"), {
            "username": "nuevo_cliente", "first_name": "Cliente", "email": "nuevo@example.test",
            "password1": "Registro-fuerte-762!", "password2": "Registro-fuerte-762!",
            "is_staff": "true", "is_superuser": "true", "next": reverse("catalogo:checkout"),
        })
        self.assertRedirects(response, reverse("catalogo:checkout"))
        usuario = get_user_model().objects.get(username="nuevo_cliente")
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(buscar_usuario("nuevo_cliente")["rol"], "cliente")
        self.assertEqual(self.client.session["carrito"], {"1": 1})

    def test_cliente_no_puede_acceder_ni_escribir_en_administracion(self):
        rutas = [reverse("catalogo:gestion"), reverse("catalogo:crear_producto"),
                 reverse("catalogo:editar_producto", args=[1]), reverse("catalogo:eliminar_producto", args=[1]),
                 reverse("catalogo:ajustar_stock", args=[1]), reverse("catalogo:pedidos_gestion")]
        for ruta in rutas:
            self.assertEqual(self.client.get(ruta).status_code, 302)
        self.client.force_login(self.cliente)
        for ruta in rutas:
            self.assertEqual(self.client.get(ruta).status_code, 403)
            self.assertEqual(self.client.post(ruta, self.datos_producto).status_code, 403)
        self.assertEqual(cargar_productos()[0]["stock"], 18)

    def test_administrador_crea_edita_stock_elimina_y_no_reutiliza_id(self):
        self.client.force_login(self.administrador)
        response = self.client.post(reverse("catalogo:crear_producto"), self.datos_producto)
        self.assertRedirects(response, reverse("catalogo:gestion"))
        creado = cargar_productos()[-1]
        self.assertEqual(creado["nombre"], "Llave nueva")
        self.client.post(reverse("catalogo:editar_producto", args=[creado["id"]]), {**self.datos_producto, "stock": 0, "precio": 7000})
        self.assertEqual(cargar_productos()[-1]["stock"], 0)
        response = self.client.get(reverse("catalogo:detalle", args=[creado["id"]]))
        self.assertContains(response, "$7.000")
        self.assertContains(response, "Sin stock")
        self.client.get(reverse("catalogo:eliminar_producto", args=[creado["id"]]))
        self.assertEqual(len(cargar_productos()), 41)
        self.client.post(reverse("catalogo:eliminar_producto", args=[creado["id"]]))
        self.assertEqual(len(cargar_productos()), 40)
        self.client.post(reverse("catalogo:crear_producto"), self.datos_producto)
        self.assertGreater(cargar_productos()[-1]["id"], creado["id"])

    def test_admin_valida_precio_stock_y_nombre(self):
        self.client.force_login(self.administrador)
        for datos in ({"precio": -5}, {"stock": -1}, {"stock": "1.5"}, {"nombre": ""}, {"precio": "abc"}):
            response = self.client.post(reverse("catalogo:crear_producto"), {**self.datos_producto, **datos})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertEqual(len(cargar_productos()), 40)

    def test_admin_no_puede_crear_producto_con_precio_cero(self):
        self.client.force_login(self.administrador)
        response = self.client.post(reverse("catalogo:crear_producto"), {**self.datos_producto, "precio": 0})
        self.assertEqual(response.status_code, 200)
        self.assertIn("precio", response.context["form"].errors)
        self.assertEqual(Producto.objects.count(), 40)

    def test_editar_con_errores_no_cambia_el_producto(self):
        self.client.force_login(self.administrador)
        response = self.client.post(reverse("catalogo:editar_producto", args=[1]), {**self.datos_producto, "nombre": ""})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(Producto.objects.get(pk=1).nombre, "")

    def test_editar_o_eliminar_producto_inexistente_responde_404(self):
        self.client.force_login(self.administrador)
        self.assertEqual(self.client.get(reverse("catalogo:editar_producto", args=[999])).status_code, 404)
        self.assertEqual(self.client.post(reverse("catalogo:eliminar_producto", args=[999])).status_code, 404)

    def test_admin_ajusta_stock_desde_la_tabla_sin_quedar_negativo(self):
        self.client.force_login(self.administrador)
        ruta = reverse("catalogo:ajustar_stock", args=[1])
        stock_inicial = Producto.objects.get(pk=1).stock
        response = self.client.post(ruta, {"cambio": "sumar", "next": reverse("catalogo:gestion") + "?q=martillo"})
        self.assertRedirects(response, reverse("catalogo:gestion") + "?q=martillo")
        self.assertEqual(Producto.objects.get(pk=1).stock, stock_inicial + 1)
        self.client.post(ruta, {"cambio": "restar"})
        self.assertEqual(Producto.objects.get(pk=1).stock, stock_inicial)
        # No se puede bajar de 0 ni ajustar con GET
        Producto.objects.filter(pk=1).update(stock=0)
        self.client.post(ruta, {"cambio": "restar"})
        self.assertEqual(Producto.objects.get(pk=1).stock, 0)
        self.assertEqual(self.client.get(ruta).status_code, 405)

    def test_admin_sube_foto_del_producto_y_se_borra_al_eliminarlo(self):
        with TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta):
            self.client.force_login(self.administrador)
            # Basta con el encabezado de un PNG para la validación del formulario
            foto = SimpleUploadedFile("taladro.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32, content_type="image/png")
            response = self.client.post(reverse("catalogo:crear_producto"), {**self.datos_producto, "foto": foto})
            self.assertRedirects(response, reverse("catalogo:gestion"))
            creado = cargar_productos()[-1]
            self.assertTrue(creado["foto"].startswith("productos/"))
            self.assertTrue((Path(carpeta) / creado["foto"]).exists())
            self.assertContains(self.client.get(reverse("catalogo:detalle", args=[creado["id"]])), "/media/" + creado["foto"])
            self.client.post(reverse("catalogo:eliminar_producto", args=[creado["id"]]))
            self.assertFalse((Path(carpeta) / creado["foto"]).exists())

    def test_admin_no_puede_subir_archivos_que_no_son_imagenes(self):
        with TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta):
            self.client.force_login(self.administrador)
            for nombre, contenido in (("notas.txt", b"hola"), ("falsa.png", b"no es una imagen")):
                archivo = SimpleUploadedFile(nombre, contenido)
                response = self.client.post(reverse("catalogo:crear_producto"), {**self.datos_producto, "foto": archivo})
                self.assertEqual(response.status_code, 200)
                self.assertIn("foto", response.context["form"].errors)
            self.assertEqual(len(cargar_productos()), 40)

    def test_checkout_exige_login_y_carrito(self):
        response = self.client.get(reverse("catalogo:checkout"))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("catalogo:checkout"))
        self.client.force_login(self.cliente)
        self.assertRedirects(self.client.get(reverse("catalogo:checkout")), reverse("catalogo:carrito"))

    def test_pedido_registra_total_descuenta_stock_y_vacia_carrito(self):
        self.client.force_login(self.cliente)
        self.agregar(cantidad=2)
        response = self.confirmar()
        pedido = Pedido.objects.get()
        self.assertRedirects(response, reverse("catalogo:pedido", args=[pedido.codigo]))
        self.assertEqual(pedido.total, 25980)
        self.assertEqual(pedido.estado, Pedido.RECIBIDO)
        self.assertEqual(pedido.detalles.get().cantidad, 2)
        self.assertEqual(cargar_productos()[0]["stock"], 16)
        self.assertEqual(self.client.session["carrito"], {})
        response = self.client.get(reverse("catalogo:cuenta"))
        self.assertContains(response, pedido.codigo)
        # Una repetición del envío no duplica el pedido ni el descuento de stock.
        self.client.post(reverse("catalogo:checkout"), {"token": pedido.token})
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(cargar_productos()[0]["stock"], 16)

    def test_checkout_rechaza_token_incorrecto_y_contacto_invalido(self):
        self.client.force_login(self.cliente)
        self.agregar()
        response = self.client.post(reverse("catalogo:checkout"), {"nombre": "Cliente", "email": "cliente@example.test", "telefono": "12345678", "token": "falso"})
        self.assertContains(response, "Esta confirmación expiró")
        response = self.client.post(reverse("catalogo:checkout"), {"nombre": "Cliente", "email": "invalido", "telefono": "x"})
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(Pedido.objects.exists())
        self.assertEqual(cargar_productos()[0]["stock"], 18)

    def test_segundo_comprador_no_puede_comprar_stock_agotado(self):
        Producto.objects.filter(pk=1).update(stock=1)
        self.client.force_login(self.cliente)
        self.agregar()
        otro_client = Client()
        otro_client.force_login(self.otro)
        otro_client.post(reverse("catalogo:modificar_carrito", args=[1]), {"cantidad": 1})
        self.confirmar()
        response = otro_client.get(reverse("catalogo:checkout"))
        self.assertRedirects(response, reverse("catalogo:carrito"))
        self.assertEqual(cargar_productos()[0]["stock"], 0)
        self.assertEqual(Pedido.objects.count(), 1)

    def test_pedido_es_privado_para_su_cliente_y_administradores(self):
        self.client.force_login(self.cliente)
        self.agregar()
        self.confirmar()
        pedido = Pedido.objects.get()
        url = reverse("catalogo:pedido", args=[pedido.codigo])
        response = self.client.get(url)
        self.assertContains(response, "Tu pedido quedó registrado")
        self.assertContains(response, "Gracias, Cliente de prueba.")
        self.assertContains(response, "Seguir comprando")
        self.assertContains(response, "Mis pedidos")
        self.assertNotContains(response, "Datos del cliente")
        self.assertNotContains(response, "Volver a pedidos de la tienda")
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertNotContains(self.client.get(reverse("catalogo:cuenta")), pedido.codigo)
        self.client.force_login(self.administrador)
        response = self.client.get(url)
        self.assertContains(response, "Detalle del pedido")
        self.assertContains(response, "Datos del cliente")
        self.assertContains(response, pedido.nombre)
        self.assertContains(response, pedido.email)
        self.assertContains(response, pedido.telefono)
        self.assertContains(response, f"{pedido.fecha:%Y-%m-%d}")
        self.assertContains(response, "Productos del pedido")
        self.assertContains(response, "$12.990 por unidad")
        self.assertContains(response, "Volver a pedidos de la tienda")
        self.assertNotContains(response, "Tu pedido quedó registrado")
        self.assertNotContains(response, "Gracias,")
        self.assertNotContains(response, "Seguir comprando")
        self.assertNotContains(response, "Mis pedidos")
        self.assertContains(self.client.get(reverse("catalogo:pedidos_gestion")), pedido.codigo)

    def test_busqueda_categoria_stock_y_orden_funcionan_sin_javascript(self):
        response = self.client.get(reverse("catalogo:lista"), {"q": "latex"})
        self.assertEqual(len(response.context["productos"]), 1)
        response = self.client.get(reverse("catalogo:lista"), {"categoria": "Herramientas manuales", "stock": "disponible", "orden": "precio-asc"})
        productos = response.context["productos"]
        self.assertEqual(len(productos), 4)
        self.assertEqual([p["precio"] for p in productos], sorted(p["precio"] for p in productos))
        response = self.client.get(reverse("catalogo:lista"), {"q": "zzzinexistente"})
        self.assertContains(response, "No encontramos productos")


class ReportesTests(CatalogoAisladoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = get_user_model().objects.create_user("comprador", password="Clave-prueba-432!")
        cls.administrador = get_user_model().objects.create_user("encargado", is_staff=True, password="Clave-prueba-432!")

    def test_reportes_solo_para_administradores(self):
        for ruta in (reverse("catalogo:reporte_categorias"), reverse("catalogo:reporte_stock")):
            self.assertEqual(self.client.get(ruta).status_code, 302)
            self.client.force_login(self.cliente)
            self.assertEqual(self.client.get(ruta).status_code, 403)
            self.client.logout()

    def test_reporte_categorias_cuadra_con_los_productos(self):
        self.client.force_login(self.administrador)
        response = self.client.get(reverse("catalogo:reporte_categorias"))
        productos = list(Producto.objects.all())
        totales = response.context["totales"]
        # Se compara con un cálculo hecho a mano en Python, sin usar el ORM
        self.assertEqual(totales["cantidad"], len(productos))
        self.assertEqual(totales["total_stock"], sum(p.stock for p in productos))
        self.assertEqual(totales["valor_inventario"], sum(p.precio * p.stock for p in productos))
        categorias = response.context["categorias"]
        self.assertEqual(len(categorias), 8)
        electricas = next(f for f in categorias if f["categoria"] == "Herramientas eléctricas")
        de_la_categoria = [p for p in productos if p.categoria == "Herramientas eléctricas"]
        self.assertEqual(electricas["cantidad"], len(de_la_categoria))
        self.assertEqual(electricas["total_stock"], sum(p.stock for p in de_la_categoria))
        self.assertEqual(electricas["precio_promedio"], round(sum(p.precio for p in de_la_categoria) / len(de_la_categoria)))
        self.assertEqual(sum(f["cantidad"] for f in categorias), len(productos))
        self.assertEqual(response.context["mayor_valor"]["categoria"], "Herramientas eléctricas")

    def test_reporte_stock_filtra_y_ordena_por_stock(self):
        self.client.force_login(self.administrador)
        response = self.client.get(reverse("catalogo:reporte_stock"))
        productos = list(response.context["productos"])
        self.assertEqual(response.context["umbral"], 10)
        self.assertEqual(len(productos), Producto.objects.filter(stock__lte=10).count())
        self.assertTrue(all(p.stock <= 10 for p in productos))
        self.assertEqual([p.stock for p in productos], sorted(p.stock for p in productos))
        self.assertEqual(response.context["agotados"], Producto.objects.filter(stock=0).count())

    def test_reporte_stock_con_umbral_y_categoria(self):
        self.client.force_login(self.administrador)
        response = self.client.get(reverse("catalogo:reporte_stock"), {"umbral": 0, "categoria": "Seguridad"})
        self.assertTrue(all(p.stock == 0 and p.categoria == "Seguridad" for p in response.context["productos"]))
        # Un umbral que no es número vuelve al valor por defecto
        response = self.client.get(reverse("catalogo:reporte_stock"), {"umbral": "abc"})
        self.assertEqual(response.context["umbral"], 10)

    def test_estadisticas_de_estado_y_mayor_valor(self):
        self.client.force_login(self.administrador)
        response = self.client.get(reverse("catalogo:reporte_categorias"))
        productos = list(Producto.objects.all())
        estados = {e["clave"]: e["cantidad"] for e in response.context["estados_stock"]}
        # Los cuatro niveles suman todos los productos y cuadran con un conteo a mano
        self.assertEqual(sum(estados.values()), len(productos))
        self.assertEqual(estados["agotado"], sum(p.stock == 0 for p in productos))
        self.assertEqual(estados["critico"], sum(0 < p.stock <= 10 for p in productos))
        self.assertEqual(estados["alto"], sum(p.stock > 30 for p in productos))
        self.assertEqual(response.context["totales"]["agotados"], estados["agotado"])
        ranking = response.context["productos_mayor_valor"]
        esperado = sorted((p.precio * p.stock for p in productos), reverse=True)[:5]
        self.assertEqual([p.valor_inventario for p in ranking], esperado)

    def test_reporte_stock_calcula_unidades_para_llegar_al_umbral(self):
        self.client.force_login(self.administrador)
        response = self.client.get(reverse("catalogo:reporte_stock"), {"umbral": 10})
        faltan = sum(10 - p.stock for p in Producto.objects.filter(stock__lte=10))
        self.assertEqual(response.context["unidades_faltantes"], faltan)

    def test_exportar_reportes_a_excel(self):
        from io import BytesIO
        from openpyxl import load_workbook

        # Solo el administrador puede descargar
        ruta = reverse("catalogo:exportar_categorias")
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(ruta).status_code, 403)

        self.client.force_login(self.administrador)
        response = self.client.get(ruta)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertIn("attachment;", response["Content-Disposition"])
        libro = load_workbook(BytesIO(response.content))
        self.assertEqual(libro.sheetnames, ["Por categoría", "Estado del stock", "Mayor valor en bodega"])
        hoja = libro["Por categoría"]
        total = [celda.value for celda in hoja[hoja.max_row]]
        self.assertEqual(total[0], "Total")
        self.assertEqual(total[1], Producto.objects.count())
        self.assertEqual(total[7], sum(p.precio * p.stock for p in Producto.objects.all()))
        self.assertEqual(hoja["H2"].number_format, '"$"#,##0')

        # El Excel de stock crítico respeta el umbral y la categoría
        response = self.client.get(reverse("catalogo:exportar_stock"), {"umbral": 0, "categoria": "Seguridad"})
        hoja = load_workbook(BytesIO(response.content)).active
        filas = list(hoja.iter_rows(min_row=2, max_row=hoja.max_row - 1, values_only=True))
        self.assertEqual(len(filas), Producto.objects.filter(stock=0, categoria="Seguridad").count())
        self.assertTrue(all(fila[4] == 0 and fila[2] == "Seguridad" for fila in filas))

    def test_todos_los_excel_tienen_total_y_existe_el_global(self):
        from io import BytesIO
        from openpyxl import load_workbook

        # Solo el administrador puede descargar el Excel global
        ruta_global = reverse("catalogo:exportar_global")
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(ruta_global).status_code, 403)
        self.client.force_login(self.administrador)

        # Cada hoja de cada Excel termina en una fila de total
        for nombre in ["exportar_categorias", "exportar_stock", "exportar_ventas", "exportar_suscriptores", "exportar_global"]:
            libro = load_workbook(BytesIO(self.client.get(reverse(f"catalogo:{nombre}")).content))
            for hoja in libro.worksheets:
                with self.subTest(excel=nombre, hoja=hoja.title):
                    self.assertEqual(hoja.cell(hoja.max_row, 1).value, "Total")

        # El global junta toda la información en un solo archivo
        response = self.client.get(ruta_global)
        self.assertIn("reporte-global", response["Content-Disposition"])
        libro = load_workbook(BytesIO(response.content))
        self.assertEqual(libro.sheetnames, [
            "Productos", "Por categoría", "Estado del stock", "Mayor valor en bodega", "Stock crítico",
            "Pedidos", "Más vendidos", "Ingresos por categoría", "Pedidos por estado", "Consultas", "Suscriptores",
        ])
        hoja = libro["Productos"]
        productos = Producto.objects.all()
        self.assertEqual(hoja.max_row, productos.count() + 2)
        total = [celda.value for celda in hoja[hoja.max_row]]
        self.assertEqual(total[4], sum(p.stock for p in productos))
        self.assertEqual(total[5], sum(p.precio * p.stock for p in productos))

    def test_reportes_aparecen_en_la_navegacion_de_base(self):
        self.client.force_login(self.administrador)
        response = self.client.get(reverse("catalogo:lista"))
        self.assertContains(response, reverse("catalogo:reporte_categorias"))
        self.assertContains(response, reverse("catalogo:reporte_stock"))
        self.client.force_login(self.cliente)
        self.assertNotContains(self.client.get(reverse("catalogo:lista")), reverse("catalogo:reporte_stock"))


class CredencialesJSONTests(CatalogoAisladoMixin, TestCase):
    def ingresar(self, username="admin", password="AdminTornillo2026!"):
        return self.client.post(reverse("login"), {"username": username, "password": password})

    def test_cuentas_precreadas_ingresan_y_aplican_sus_roles(self):
        self.assertEqual(get_user_model().objects.count(), 0)
        response = self.ingresar()
        self.assertRedirects(response, reverse("catalogo:gestion"))
        self.assertContains(self.client.get(reverse("catalogo:gestion")), "Crear producto")
        self.client.post(reverse("logout"))
        response = self.ingresar("cliente", "ClienteTornillo2026!")
        self.assertRedirects(response, reverse("catalogo:lista"))
        self.assertEqual(self.client.get(reverse("catalogo:gestion")).status_code, 403)
        self.assertEqual(len(cargar_usuarios()["usuarios"]), 2)

    def test_claves_del_json_son_visibles_en_archivo_y_no_se_publican_por_http(self):
        for username, password in (("admin", "AdminTornillo2026!"), ("cliente", "ClienteTornillo2026!")):
            registro = buscar_usuario(username)
            self.assertEqual(registro["password"], password)
            self.assertNotContains(self.client.get(reverse("login")), registro["password"])
        self.assertEqual(self.client.get("/data/usuarios.json").status_code, 404)

    def test_clave_erronea_o_cuenta_comun_solo_en_sqlite_no_permiten_ingresar(self):
        response = self.ingresar(password="incorrecta")
        self.assertTrue(response.context["form"].errors)
        get_user_model().objects.create_user("solo_sqlite", password="Clave-sqlite-123!", is_staff=True)
        response = self.ingresar("solo_sqlite", "Clave-sqlite-123!")
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_superusuario_de_sqlite_entra_al_admin_y_ve_productos(self):
        get_user_model().objects.create_superuser("superadmin", password="Clave-super-123!")
        response = self.client.post(reverse("admin:login"), {"username": "superadmin", "password": "Clave-super-123!",
                                                             "next": reverse("admin:index")})
        self.assertRedirects(response, reverse("admin:index"))
        response = self.client.get(reverse("admin:catalogo_producto_changelist"))
        self.assertContains(response, "Martillo carpintero 16 oz")

    def test_json_controla_rol_activo_y_revocacion_de_sesion(self):
        self.ingresar()
        with editar_usuarios() as datos:
            datos["usuarios"][0]["rol"] = "cliente"
        self.assertEqual(self.client.get(reverse("catalogo:gestion")).status_code, 403)
        with editar_usuarios() as datos:
            datos["usuarios"][0]["activo"] = False
        response = self.client.get(reverse("catalogo:cuenta"))
        self.assertEqual(response.status_code, 302)
        response = self.ingresar()
        self.assertTrue(response.context["form"].errors)

    def test_cambiar_clave_en_json_invalida_clave_y_sesion_anteriores(self):
        self.ingresar()
        with editar_usuarios() as datos:
            datos["usuarios"][0]["password"] = "Nueva-clave-567!"
        self.assertEqual(self.client.get(reverse("catalogo:gestion")).status_code, 302)
        self.assertTrue(self.ingresar().context["form"].errors)
        self.assertRedirects(self.ingresar(password="Nueva-clave-567!"), reverse("catalogo:gestion"))

    def test_cliente_registrado_se_guarda_en_json_y_puede_reingresar(self):
        response = self.client.post(reverse("catalogo:registro"), {
            "username": "cliente_nuevo", "first_name": "Cliente nuevo", "email": "nuevo@example.test",
            "password1": "Registro-cliente-678!", "password2": "Registro-cliente-678!", "rol": "admin",
        })
        self.assertRedirects(response, reverse("catalogo:lista"))
        self.assertEqual(buscar_usuario("cliente_nuevo")["rol"], "cliente")
        self.assertEqual(buscar_usuario("cliente_nuevo")["password"], "Registro-cliente-678!")
        usuario = get_user_model().objects.get(username="cliente_nuevo")
        self.assertNotEqual(usuario.password, "Registro-cliente-678!")
        self.assertTrue(usuario.check_password("Registro-cliente-678!"))
        self.client.post(reverse("logout"))
        self.assertRedirects(self.ingresar("cliente_nuevo", "Registro-cliente-678!"), reverse("catalogo:lista"))
        self.assertEqual(self.client.get(reverse("catalogo:gestion")).status_code, 403)

    def test_registro_no_puede_ocupar_nombre_precreado_aun_sin_fila_sqlite(self):
        response = self.client.post(reverse("catalogo:registro"), {
            "username": "ADMIN", "first_name": "Intruso", "email": "nuevo@example.test",
            "password1": "Registro-cliente-678!", "password2": "Registro-cliente-678!",
        })
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(buscar_usuario("admin")["rol"], "admin")

    def test_json_invalido_rechaza_acceso_sin_usar_clave_de_sqlite(self):
        from django.conf import settings
        self.ingresar()
        self.client.post(reverse("logout"))
        Path(settings.USUARIOS_DATOS).write_text("{json incompleto", encoding="utf-8")
        with self.assertLogs("catalogo.backends", level="ERROR"):
            response = self.ingresar()
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)


class ClientesTests(CatalogoAisladoMixin, TestCase):
    """Etapa 3: consultas, sesiones, pedidos con estado, perfil, ofertas y ventas."""

    @classmethod
    def setUpTestData(cls):
        cls.cliente = get_user_model().objects.create_user("comprador", first_name="Ana", email="ana@example.test", password="Clave-prueba-432!")
        cls.otro = get_user_model().objects.create_user("otro", password="Clave-prueba-432!")
        cls.administrador = get_user_model().objects.create_user("encargado", is_staff=True, password="Clave-prueba-432!")

    def comprar(self, producto_id=1, cantidad=1):
        """Agrega un producto al carrito y confirma el pedido; devuelve el Pedido creado."""
        self.client.post(reverse("catalogo:modificar_carrito", args=[producto_id]), {"cantidad": cantidad})
        token = self.client.get(reverse("catalogo:checkout")).context["token"]
        self.client.post(reverse("catalogo:checkout"), {"nombre": "Ana", "email": "ana@example.test",
                                                        "telefono": "+56 9 1234 5678", "token": token})
        return Pedido.objects.latest("fecha")

    # --- Consultas (ModelForm) ---

    def test_consulta_rechaza_datos_invalidos_con_mensajes_claros(self):
        casos = [
            ({"nombre": "", "correo": "", "mensaje": ""}, ["nombre", "correo", "mensaje"]),
            ({"nombre": "Ana", "correo": "correo-malo", "mensaje": "Mensaje suficientemente largo"}, ["correo"]),
            ({"nombre": "A", "correo": "ana@example.test", "mensaje": "corto"}, ["nombre", "mensaje"]),
            ({"nombre": "Ana", "correo": "ana@example.test", "mensaje": "          "}, ["mensaje"]),
        ]
        for datos, campos in casos:
            response = self.client.post(reverse("catalogo:consulta"), datos)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(sorted(response.context["form"].errors), sorted(campos))
        self.assertContains(response, "Revisa los datos del formulario.")
        self.assertFalse(ConsultaCliente.objects.exists())

    def test_consulta_valida_se_guarda_y_muestra_confirmacion(self):
        response = self.client.post(reverse("catalogo:consulta"), {
            "nombre": "Ana", "correo": "ana@example.test", "producto": 8, "mensaje": "¿La sierra trae disco incluido?"})
        consulta = ConsultaCliente.objects.get()
        self.assertRedirects(response, reverse("catalogo:consulta_enviada"))
        self.assertEqual(consulta.producto_id, 8)
        self.assertIsNone(consulta.usuario)
        self.assertIsNotNone(consulta.fecha)
        response = self.client.get(reverse("catalogo:consulta_enviada"))
        self.assertContains(response, "Recibimos tu consulta")
        self.assertContains(response, "ana@example.test")
        # Otra sesión no puede ver la confirmación
        self.assertRedirects(Client().get(reverse("catalogo:consulta_enviada")), reverse("catalogo:consulta"))

    def test_consulta_desde_la_ficha_y_con_sesion_queda_en_mi_cuenta(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("catalogo:consulta"), {"producto": 21})
        self.assertEqual(response.context["form"].initial["producto"], 21)
        self.assertEqual(response.context["form"].initial["correo"], "ana@example.test")
        self.client.post(reverse("catalogo:consulta"), {
            "nombre": "Ana", "correo": "ana@example.test", "producto": 21, "mensaje": "¿Sirve para exterior?"})
        self.assertEqual(ConsultaCliente.objects.get().usuario, self.cliente)
        self.assertContains(self.client.get(reverse("catalogo:cuenta")), "¿Sirve para exterior?")

    def test_formularios_exigen_token_csrf(self):
        cliente_csrf = Client(enforce_csrf_checks=True)
        datos = {"nombre": "Ana", "correo": "ana@example.test", "mensaje": "Mensaje de prueba válido"}
        self.assertEqual(cliente_csrf.post(reverse("catalogo:consulta"), datos).status_code, 403)
        self.assertEqual(cliente_csrf.post(reverse("catalogo:suscribirse"), {"correo": "a@b.cl"}).status_code, 403)
        # Con el token del formulario sí se acepta
        response = cliente_csrf.get(reverse("catalogo:consulta"))
        self.assertContains(response, "csrfmiddlewaretoken")
        token = response.cookies["csrftoken"].value
        response = cliente_csrf.post(reverse("catalogo:consulta"), {**datos, "csrfmiddlewaretoken": token})
        self.assertRedirects(response, reverse("catalogo:consulta_enviada"))

    def test_admin_responde_consultas_y_el_cliente_ve_la_respuesta(self):
        consulta = ConsultaCliente.objects.create(nombre="Ana", correo="ana@example.test", mensaje="¿Tienen despacho?", usuario=self.cliente)
        ruta = reverse("catalogo:responder_consulta", args=[consulta.pk])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("catalogo:consultas_gestion")).status_code, 403)
        self.assertEqual(self.client.post(ruta, {"respuesta": "Hola"}).status_code, 403)
        self.client.force_login(self.administrador)
        self.assertEqual(self.client.get(reverse("catalogo:consultas_gestion")).context["conteo"]["pendientes"], 1)
        response = self.client.post(ruta, {"respuesta": "no"})
        self.assertIn("respuesta", response.context["form"].errors)
        self.client.post(ruta, {"respuesta": "Solo retiro en tienda por ahora."})
        consulta.refresh_from_db()
        self.assertTrue(consulta.respondida)
        self.assertIsNotNone(consulta.fecha_respuesta)
        self.assertEqual(self.client.get(reverse("catalogo:consultas_gestion")).context["conteo"]["pendientes"], 0)
        self.client.force_login(self.cliente)
        self.assertContains(self.client.get(reverse("catalogo:cuenta")), "Solo retiro en tienda por ahora.")

    # --- Sesión: últimos 3 productos vistos ---

    def test_sesion_guarda_los_ultimos_tres_productos_vistos(self):
        for producto_id in (5, 12, 21, 8):
            self.client.get(reverse("catalogo:detalle", args=[producto_id]))
        # El más reciente primero y solo 3
        self.assertEqual(self.client.session["vistos"], [8, 21, 12])
        # Volver a uno visto lo sube al primer lugar sin repetirlo
        response = self.client.get(reverse("catalogo:detalle", args=[12]))
        self.assertEqual(self.client.session["vistos"], [12, 8, 21])
        # La ficha muestra los anteriores, sin el producto actual
        self.assertEqual([p.id for p in response.context["vistos"]], [8, 21])
        # Al iniciar sesión se conservan los vistos (como el carrito) y Mi cuenta los muestra
        self.client.force_login(self.cliente)
        self.client.get(reverse("catalogo:detalle", args=[3]))
        self.assertEqual([p.id for p in self.client.get(reverse("catalogo:cuenta")).context["vistos"]], [3, 12, 8])

    # --- Pedidos con estado y rastreo ---

    def test_cliente_cancela_pedido_recibido_y_vuelve_el_stock(self):
        self.client.force_login(self.cliente)
        pedido = self.comprar(cantidad=2)
        self.assertEqual(Producto.objects.get(pk=1).stock, 16)
        self.assertContains(self.client.get(reverse("catalogo:pedido", args=[pedido.codigo])), "Cancelar pedido")
        # Otro cliente no puede cancelarlo
        self.client.force_login(self.otro)
        self.assertEqual(self.client.post(reverse("catalogo:cancelar_pedido", args=[pedido.codigo])).status_code, 404)
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("catalogo:cancelar_pedido", args=[pedido.codigo])).status_code, 405)
        self.client.post(reverse("catalogo:cancelar_pedido", args=[pedido.codigo]))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.CANCELADO)
        self.assertEqual(Producto.objects.get(pk=1).stock, 18)
        # Cancelar dos veces no devuelve el stock dos veces
        self.client.post(reverse("catalogo:cancelar_pedido", args=[pedido.codigo]))
        self.assertEqual(Producto.objects.get(pk=1).stock, 18)

    def test_admin_avanza_el_estado_y_el_cliente_ve_el_rastreo(self):
        self.client.force_login(self.cliente)
        pedido = self.comprar()
        ruta = reverse("catalogo:cambiar_estado_pedido", args=[pedido.codigo])
        self.assertEqual(self.client.post(ruta, {"estado": "entregado"}).status_code, 403)
        self.client.force_login(self.administrador)
        self.client.post(ruta, {"estado": "preparando"})
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.PREPARANDO)
        self.assertEqual([p["hecho"] for p in pedido.pasos()], [True, False, False, False])
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("catalogo:pedido", args=[pedido.codigo]))
        self.assertContains(response, 'aria-current="step"')
        self.assertNotContains(response, "Cancelar pedido")
        # Ya en preparación, el cliente no puede cancelarlo
        self.client.post(reverse("catalogo:cancelar_pedido", args=[pedido.codigo]))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.PREPARANDO)

    def test_admin_cancela_devuelve_stock_y_no_reactiva_ni_cancela_entregados(self):
        self.client.force_login(self.cliente)
        cancelado = self.comprar(cantidad=3)
        entregado = self.comprar(producto_id=2)
        self.client.force_login(self.administrador)
        self.client.post(reverse("catalogo:cambiar_estado_pedido", args=[cancelado.codigo]), {"estado": "cancelado"})
        self.assertEqual(Producto.objects.get(pk=1).stock, 18)
        self.client.post(reverse("catalogo:cambiar_estado_pedido", args=[cancelado.codigo]), {"estado": "recibido"})
        cancelado.refresh_from_db()
        self.assertEqual(cancelado.estado, Pedido.CANCELADO)
        self.client.post(reverse("catalogo:cambiar_estado_pedido", args=[entregado.codigo]), {"estado": "entregado"})
        stock = Producto.objects.get(pk=2).stock
        self.client.post(reverse("catalogo:cambiar_estado_pedido", args=[entregado.codigo]), {"estado": "cancelado"})
        entregado.refresh_from_db()
        self.assertEqual(entregado.estado, Pedido.ENTREGADO)
        self.assertEqual(Producto.objects.get(pk=2).stock, stock)
        # Tampoco se puede devolver a "recibido" para cancelarlo después
        self.client.post(reverse("catalogo:cambiar_estado_pedido", args=[entregado.codigo]), {"estado": "recibido"})
        entregado.refresh_from_db()
        self.assertEqual(entregado.estado, Pedido.ENTREGADO)
        # En el detalle de un pedido cerrado no aparece el formulario de estado
        response = self.client.get(reverse("catalogo:pedido", args=[cancelado.codigo]))
        self.assertNotContains(response, "Guardar estado")
        self.assertContains(response, "Pedido cerrado")
        # Filtro por estado en la lista de pedidos
        response = self.client.get(reverse("catalogo:pedidos_gestion"), {"estado": "cancelado"})
        self.assertEqual(list(response.context["pedidos"]), [cancelado])

    def datos_admin_pedido(self, pedido, estado):
        """Datos que envía el formulario del admin de Django al guardar un pedido."""
        detalles = list(pedido.detalles.all())
        datos = {
            "codigo": pedido.codigo, "usuario": pedido.usuario_id, "token": pedido.token,
            "nombre": pedido.nombre, "email": pedido.email, "telefono": pedido.telefono,
            "total": pedido.total, "estado": estado,
            "detalles-TOTAL_FORMS": len(detalles), "detalles-INITIAL_FORMS": len(detalles),
            "detalles-MIN_NUM_FORMS": 0, "detalles-MAX_NUM_FORMS": 1000,
        }
        for i, detalle in enumerate(detalles):
            datos.update({
                f"detalles-{i}-id": detalle.id, f"detalles-{i}-pedido": pedido.id,
                f"detalles-{i}-producto": detalle.producto_id, f"detalles-{i}-nombre": detalle.nombre,
                f"detalles-{i}-precio": detalle.precio, f"detalles-{i}-cantidad": detalle.cantidad,
            })
        return datos

    def test_admin_de_django_respeta_los_estados_del_pedido(self):
        jefe = get_user_model().objects.create_superuser("jefe", password="Clave-prueba-432!")
        self.client.force_login(self.cliente)
        pedido = self.comprar(cantidad=3)
        entregado = self.comprar(producto_id=2)
        stock = Producto.objects.get(pk=1).stock
        self.client.force_login(jefe, backend="catalogo.backends.SuperusuarioBackend")
        ruta = reverse("admin:catalogo_pedido_change", args=[pedido.pk])
        # Cancelar desde el admin también devuelve el stock
        response = self.client.post(ruta, self.datos_admin_pedido(pedido, "cancelado"))
        self.assertRedirects(response, reverse("admin:catalogo_pedido_changelist"))
        self.assertEqual(Producto.objects.get(pk=1).stock, stock + 3)
        # Ya cancelado, el admin solo lo muestra y no deja guardar cambios
        self.assertNotContains(self.client.get(ruta), 'name="_save"')
        self.assertEqual(self.client.post(ruta, self.datos_admin_pedido(pedido, "recibido")).status_code, 403)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.CANCELADO)
        self.assertEqual(Producto.objects.get(pk=1).stock, stock + 3)
        # Un pedido entregado tampoco se puede editar
        ruta = reverse("admin:catalogo_pedido_change", args=[entregado.pk])
        self.client.post(ruta, self.datos_admin_pedido(entregado, "entregado"))
        self.assertEqual(self.client.post(ruta, self.datos_admin_pedido(entregado, "cancelado")).status_code, 403)
        entregado.refresh_from_db()
        self.assertEqual(entregado.estado, Pedido.ENTREGADO)

    def test_admin_de_django_no_cambia_productos_ni_borra_pedidos_activos(self):
        jefe = get_user_model().objects.create_superuser("jefe", password="Clave-prueba-432!")
        self.client.force_login(self.cliente)
        activo = self.comprar(cantidad=3)
        cancelado = self.comprar(producto_id=2)
        self.client.post(reverse("catalogo:cancelar_pedido", args=[cancelado.codigo]))
        stock = Producto.objects.get(pk=1).stock
        self.client.force_login(jefe, backend="catalogo.backends.SuperusuarioBackend")
        # Los productos del pedido se ven, pero no se pueden editar
        ruta = reverse("admin:catalogo_pedido_change", args=[activo.pk])
        self.assertNotContains(self.client.get(ruta), 'name="detalles-0-cantidad"')
        datos = self.datos_admin_pedido(activo, "preparando")
        datos["detalles-0-cantidad"] = 1
        self.client.post(ruta, datos)
        activo.refresh_from_db()
        self.assertEqual(activo.estado, Pedido.PREPARANDO)
        self.assertEqual(activo.detalles.get().cantidad, 3)
        # Un pedido activo no se borra, ni solo ni desde la lista
        borrar = reverse("admin:catalogo_pedido_delete", args=[activo.pk])
        self.assertEqual(self.client.post(borrar, {"post": "yes"}).status_code, 403)
        self.client.post(reverse("admin:catalogo_pedido_changelist"),
                         {"action": "delete_selected", "_selected_action": [activo.pk], "post": "yes"})
        self.assertTrue(Pedido.objects.filter(pk=activo.pk).exists())
        self.assertEqual(Producto.objects.get(pk=1).stock, stock)
        # Un pedido cancelado sí se puede borrar
        self.client.post(reverse("admin:catalogo_pedido_delete", args=[cancelado.pk]), {"post": "yes"})
        self.assertFalse(Pedido.objects.filter(pk=cancelado.pk).exists())

    # --- Perfil y ofertas ---

    def test_perfil_guarda_datos_y_los_usa_en_el_checkout(self):
        self.client.force_login(self.cliente)
        response = self.client.post(reverse("catalogo:editar_perfil"), {
            "nombre": "Ana", "email": "ana@example.test", "telefono": "abc", "comuna": "", "direccion": ""})
        self.assertIn("telefono", response.context["form"].errors)
        response = self.client.post(reverse("catalogo:editar_perfil"), {
            "nombre": "Ana María", "email": "ana.maria@example.test", "telefono": "+56 9 5555 4444",
            "comuna": "Ñuñoa", "direccion": "Los Aromos 345", "apellido": "Rojas"})
        self.assertRedirects(response, reverse("catalogo:editar_perfil"))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.last_name, "Rojas")
        # Después de guardar, los campos se muestran bloqueados hasta apretar "Editar"
        response = self.client.get(reverse("catalogo:editar_perfil"))
        self.assertFalse(response.context["editando"])
        self.assertTrue(all(campo.disabled for campo in response.context["form"].fields.values()))
        self.assertTrue(self.client.get(reverse("catalogo:editar_perfil"), {"editar": 1}).context["editando"])
        self.assertEqual(PerfilCliente.objects.get(usuario=self.cliente).comuna, "Ñuñoa")
        # El nombre y el correo también quedan en usuarios.json (el login los relee de ahí)
        registro = buscar_usuario("comprador")
        self.assertEqual((registro["nombre"], registro["email"]), ("Ana María", "ana.maria@example.test"))
        self.client.post(reverse("catalogo:modificar_carrito", args=[1]), {"cantidad": 1})
        self.assertEqual(self.client.get(reverse("catalogo:checkout")).context["form"].initial["telefono"], "+56 9 5555 4444")

    def test_suscripcion_desde_el_pie_y_desde_la_cuenta(self):
        response = self.client.post(reverse("catalogo:suscribirse"), {"correo": "Vecina@Correo.cl", "next": "/catalogo/"})
        self.assertRedirects(response, "/catalogo/#ofertas", fetch_redirect_response=False)
        self.assertTrue(Suscripcion.objects.get(correo="vecina@correo.cl").activa)
        self.client.post(reverse("catalogo:suscribirse"), {"correo": "vecina@correo.cl"})
        self.assertEqual(Suscripcion.objects.count(), 1)
        response = self.client.post(reverse("catalogo:suscribirse"), {"correo": "no-es-correo"}, follow=True)
        self.assertContains(response, "Revisa el correo")
        self.assertEqual(Suscripcion.objects.count(), 1)
        # Desde la cuenta se activa y se desactiva
        self.client.force_login(self.cliente)
        self.client.post(reverse("catalogo:cambiar_suscripcion"), {"activa": "1"})
        self.assertTrue(Suscripcion.objects.get(correo="ana@example.test").activa)
        self.client.post(reverse("catalogo:cambiar_suscripcion"), {"activa": "0"})
        self.assertFalse(Suscripcion.objects.get(correo="ana@example.test").activa)
        self.assertFalse(self.client.get(reverse("catalogo:cuenta")).context["suscrito"])

    def test_suscriptores_solo_para_admin_y_con_excel(self):
        from io import BytesIO
        from openpyxl import load_workbook

        Suscripcion.objects.create(correo="a@example.test")
        Suscripcion.objects.create(correo="b@example.test", activa=False)
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("catalogo:suscriptores_gestion")).status_code, 403)
        self.client.force_login(self.administrador)
        response = self.client.get(reverse("catalogo:suscriptores_gestion"))
        self.assertEqual((response.context["activas"], response.context["inactivas"]), (1, 1))
        hoja = load_workbook(BytesIO(self.client.get(reverse("catalogo:exportar_suscriptores")).content)).active
        # Encabezado, 2 suscriptores y la fila de total
        self.assertEqual(hoja.max_row, 4)

    # --- Reporte de ventas ---

    def test_reporte_de_ventas_no_cuenta_pedidos_cancelados(self):
        from io import BytesIO
        from openpyxl import load_workbook

        self.client.force_login(self.cliente)
        self.comprar(producto_id=1, cantidad=2)  # 2 × $12.990
        self.comprar(producto_id=2, cantidad=1)  # 1 × $8.990
        cancelado = self.comprar(producto_id=3, cantidad=4)
        self.client.post(reverse("catalogo:cancelar_pedido", args=[cancelado.codigo]))
        self.client.force_login(self.administrador)
        datos = self.client.get(reverse("catalogo:reporte_ventas")).context
        self.assertEqual(datos["resumen"]["pedidos"], 2)
        self.assertEqual(datos["resumen"]["ingresos"], 2 * 12990 + 8990)
        self.assertEqual(datos["resumen"]["unidades"], 3)
        self.assertEqual(datos["mas_vendidos"][0]["nombre"], Producto.objects.get(pk=1).nombre)
        self.assertEqual(datos["mas_vendidos"][0]["unidades"], 2)
        self.assertEqual({e["clave"]: e["cantidad"] for e in datos["por_estado"]}["cancelado"], 1)
        libro = load_workbook(BytesIO(self.client.get(reverse("catalogo:exportar_ventas")).content))
        self.assertEqual(libro.sheetnames, ["Más vendidos", "Ingresos por categoría", "Pedidos por estado"])

    def test_modelos_nuevos_registrados_en_admin(self):
        from django.contrib import admin

        for modelo in (Pedido, ConsultaCliente, PerfilCliente, Suscripcion):
            self.assertIn(modelo, admin.site._registry)
