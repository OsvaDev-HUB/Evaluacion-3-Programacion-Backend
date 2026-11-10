from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    precio = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    descripcion = models.TextField(blank=True)
    # Foto que sube el administrador desde /gestion/ (opcional)
    foto = models.FileField(upload_to="productos/", blank=True)
    # Dibujo que se muestra cuando el producto no tiene foto (opcional)
    ilustracion = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    """Pedido de retiro en tienda. Antes se guardaba en un JSON; ahora vive en la BD."""

    # Pasos del pedido, en el orden en que avanza
    RECIBIDO = "recibido"
    PREPARANDO = "preparando"
    LISTO = "listo"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"
    ESTADOS = [
        (RECIBIDO, "Recibido"),
        (PREPARANDO, "En preparación"),
        (LISTO, "Listo para retiro"),
        (ENTREGADO, "Entregado"),
        (CANCELADO, "Cancelado"),
    ]

    codigo = models.CharField(max_length=12, unique=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedidos")
    # Token de la confirmación: evita que un doble clic cree dos pedidos
    token = models.CharField(max_length=48, unique=True)
    nombre = models.CharField("nombre de quien retira", max_length=150)
    email = models.EmailField("correo electrónico")
    telefono = models.CharField("teléfono de contacto", max_length=20)
    total = models.PositiveIntegerField()
    estado = models.CharField(max_length=12, choices=ESTADOS, default=RECIBIDO)
    fecha = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Pedido #{self.codigo}"

    @property
    def puede_cancelarse(self):
        # El cliente solo cancela mientras la tienda no empieza a prepararlo
        return self.estado == self.RECIBIDO

    @property
    def estado_final(self):
        # Cancelado y entregado cierran el pedido: su estado ya no cambia
        return self.estado in (self.CANCELADO, self.ENTREGADO)

    def pasos(self):
        """Pasos del rastreo con su situación: hecho, actual o pendiente."""
        orden = [self.RECIBIDO, self.PREPARANDO, self.LISTO, self.ENTREGADO]
        posicion = orden.index(self.estado) if self.estado in orden else -1
        nombres = dict(self.ESTADOS)
        return [
            {"nombre": nombres[clave], "hecho": indice < posicion, "actual": indice == posicion}
            for indice, clave in enumerate(orden)
        ]

    def devolver_stock(self):
        """Devuelve al inventario las unidades del pedido (al cancelarlo)."""
        for detalle in self.detalles.filter(producto__isnull=False):
            Producto.objects.filter(pk=detalle.producto_id).update(stock=F("stock") + detalle.cantidad)


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    # Si el producto se elimina, el pedido conserva el nombre y el precio que tenía
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    precio = models.PositiveIntegerField()
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} × {self.nombre}"

    @property
    def subtotal(self):
        return self.precio * self.cantidad


class ConsultaCliente(models.Model):
    """Consulta que un cliente envía desde el formulario de contacto."""

    nombre = models.CharField(max_length=100, validators=[MinLengthValidator(3)])
    correo = models.EmailField()
    mensaje = models.TextField(validators=[MinLengthValidator(10)])
    # Producto por el que pregunta (opcional)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="producto de interés")
    fecha = models.DateTimeField(auto_now_add=True)
    # Si la envió un cliente con sesión iniciada, aparece en "Mi cuenta"
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="consultas")
    respuesta = models.TextField(blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "consulta de cliente"
        verbose_name_plural = "consultas de clientes"

    def __str__(self):
        return f"{self.nombre} ({self.fecha:%d-%m-%Y})"

    @property
    def respondida(self):
        return bool(self.respuesta)


class PerfilCliente(models.Model):
    """Datos extra del cliente que no están en el usuario de Django."""

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    comuna = models.CharField(max_length=60, blank=True)
    direccion = models.CharField("dirección", max_length=150, blank=True)

    class Meta:
        verbose_name = "perfil de cliente"
        verbose_name_plural = "perfiles de clientes"

    def __str__(self):
        return f"Perfil de {self.usuario}"


class Suscripcion(models.Model):
    """Correo inscrito para recibir ofertas de la tienda."""

    correo = models.EmailField(unique=True)
    activa = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "suscripción a ofertas"
        verbose_name_plural = "suscripciones a ofertas"

    def __str__(self):
        return self.correo
