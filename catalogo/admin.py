from django.contrib import admin
from .models import Producto

# Register your models here.
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # Columnas que se ven en el listado
    list_display = ('nombre', 'categoria', 'precio', 'stock')
    # Buscador por nombre y categoría
    search_fields = ('nombre', 'categoria')
    # Filtro lateral por categoría
    list_filter = ('categoria',)
