from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Producto
from .storage import leer_tienda
from .views import cargar_productos
from .usuarios import agregar_usuario, buscar_usuario, cargar_usuarios, editar_usuarios


class CatalogoAisladoMixin:
    """Carga la fixture de productos y aísla los archivos JSON de usuarios y pedidos."""

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
            TIENDA_DATOS=Path(temporal.name) / "tienda.json",
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
                 reverse("catalogo:pedidos_gestion")]
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
        pedido = leer_tienda()["pedidos"][0]
        self.assertRedirects(response, reverse("catalogo:pedido", args=[pedido["id"]]))
        self.assertEqual(pedido["total"], 25980)
        self.assertEqual(cargar_productos()[0]["stock"], 16)
        self.assertEqual(self.client.session["carrito"], {})
        response = self.client.get(reverse("catalogo:cuenta"))
        self.assertContains(response, pedido["id"])
        # Una repetición del envío no duplica el pedido ni el descuento de stock.
        self.client.post(reverse("catalogo:checkout"), {"token": pedido["token"]})
        self.assertEqual(len(leer_tienda()["pedidos"]), 1)
        self.assertEqual(cargar_productos()[0]["stock"], 16)

    def test_checkout_rechaza_token_incorrecto_y_contacto_invalido(self):
        self.client.force_login(self.cliente)
        self.agregar()
        response = self.client.post(reverse("catalogo:checkout"), {"nombre": "Cliente", "email": "cliente@example.test", "telefono": "12345678", "token": "falso"})
        self.assertContains(response, "Esta confirmación expiró")
        response = self.client.post(reverse("catalogo:checkout"), {"nombre": "Cliente", "email": "invalido", "telefono": "x"})
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(leer_tienda()["pedidos"], [])
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
        self.assertEqual(len(leer_tienda()["pedidos"]), 1)

    def test_pedido_es_privado_para_su_cliente_y_administradores(self):
        self.client.force_login(self.cliente)
        self.agregar()
        self.confirmar()
        pedido = leer_tienda()["pedidos"][0]
        url = reverse("catalogo:pedido", args=[pedido["id"]])
        response = self.client.get(url)
        self.assertContains(response, "Tu pedido quedó registrado")
        self.assertContains(response, "Gracias, Cliente de prueba.")
        self.assertContains(response, "Seguir comprando")
        self.assertContains(response, "Mis pedidos")
        self.assertNotContains(response, "Datos del cliente")
        self.assertNotContains(response, "Volver a pedidos de la tienda")
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertNotContains(self.client.get(reverse("catalogo:cuenta")), pedido["id"])
        self.client.force_login(self.administrador)
        response = self.client.get(url)
        self.assertContains(response, "Detalle del pedido")
        self.assertContains(response, "Datos del cliente")
        self.assertContains(response, pedido["contacto"]["nombre"])
        self.assertContains(response, pedido["contacto"]["email"])
        self.assertContains(response, pedido["contacto"]["telefono"])
        self.assertContains(response, pedido["fecha"][:10])
        self.assertContains(response, "Productos del pedido")
        self.assertContains(response, "$12.990 por unidad")
        self.assertContains(response, "Volver a pedidos de la tienda")
        self.assertNotContains(response, "Tu pedido quedó registrado")
        self.assertNotContains(response, "Gracias,")
        self.assertNotContains(response, "Seguir comprando")
        self.assertNotContains(response, "Mis pedidos")
        self.assertContains(self.client.get(reverse("catalogo:pedidos_gestion")), pedido["id"])

    def test_busqueda_categoria_stock_y_orden_funcionan_sin_javascript(self):
        response = self.client.get(reverse("catalogo:lista"), {"q": "latex"})
        self.assertEqual(len(response.context["productos"]), 1)
        response = self.client.get(reverse("catalogo:lista"), {"categoria": "Herramientas manuales", "stock": "disponible", "orden": "precio-asc"})
        productos = response.context["productos"]
        self.assertEqual(len(productos), 4)
        self.assertEqual([p["precio"] for p in productos], sorted(p["precio"] for p in productos))
        response = self.client.get(reverse("catalogo:lista"), {"q": "zzzinexistente"})
        self.assertContains(response, "No encontramos productos")


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
