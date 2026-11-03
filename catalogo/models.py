from django.db import models


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
