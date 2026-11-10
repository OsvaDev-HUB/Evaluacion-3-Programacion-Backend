from django.contrib import admin

from .forms import EstadoPedidoForm
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

    # Los productos solo se ven: cambiarlos descuadraría el stock y el total del pedido
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'total', 'estado', 'fecha')
    list_filter = ('estado',)
    search_fields = ('codigo', 'nombre', 'email')
    inlines = [DetallePedidoInline]
    # Se usa el mismo formulario del panel de gestión para validar los cambios de estado
    form = EstadoPedidoForm
    fields = ('codigo', 'usuario', 'token', 'nombre', 'email', 'telefono', 'total', 'estado')

    def has_change_permission(self, request, obj=None):
        # Un pedido cancelado o entregado solo se puede ver, no editar
        if obj is not None and obj.estado_final:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Solo se borran pedidos cancelados: los demás todavía tienen stock descontado.
        # Django revisa esto para cada pedido, también al borrar varios desde la lista
        if obj is not None and obj.estado != Pedido.CANCELADO:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Igual que en el panel: al cancelar, las unidades vuelven al inventario
        if change and 'estado' in form.changed_data and obj.estado == Pedido.CANCELADO:
            obj.devolver_stock()
        super().save_model(request, obj, form, change)


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
