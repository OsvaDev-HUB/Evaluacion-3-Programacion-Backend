from django.contrib import admin

from .models import ConsultaCliente, DetallePedido, Pedido, PerfilCliente, Producto, Suscripcion


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # Columnas que se ven en el listado
    list_display = ('nombre', 'categoria', 'precio', 'stock')
    # Buscador por nombre y categoría
    search_fields = ('nombre', 'categoria')
    # Filtro lateral por categoría
    list_filter = ('categoria',)


class DetallePedidoInline(admin.TabularInline):
    # Los productos del pedido se ven dentro del mismo pedido
    model = DetallePedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'total', 'estado', 'fecha')
    list_filter = ('estado',)
    search_fields = ('codigo', 'nombre', 'email')
    inlines = [DetallePedidoInline]


@admin.register(ConsultaCliente)
class ConsultaClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'correo', 'producto', 'fecha', 'respondida')
    search_fields = ('nombre', 'correo', 'mensaje')
    list_filter = ('fecha',)

    @admin.display(boolean=True, description='Respondida')
    def respondida(self, consulta):
        return consulta.respondida


@admin.register(PerfilCliente)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'telefono', 'comuna')
    search_fields = ('usuario__username', 'telefono', 'comuna')


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('correo', 'activa', 'fecha')
    list_filter = ('activa',)
    search_fields = ('correo',)
