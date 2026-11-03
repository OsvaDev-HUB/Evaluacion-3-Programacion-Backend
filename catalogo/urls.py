from django.urls import path
from . import views

app_name = "catalogo"
urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("catalogo/", views.lista_productos, name="lista"),
    path("producto/<int:producto_id>/", views.detalle_producto, name="detalle"),
    path("carrito/", views.carrito, name="carrito"),
    path("carrito/<int:producto_id>/", views.modificar_carrito, name="modificar_carrito"),
    path("compra/", views.checkout, name="checkout"),
    path("pedido/<str:pedido_id>/", views.pedido, name="pedido"),
    path("cuenta/", views.cuenta, name="cuenta"),
    path("cuenta/registro/", views.registro, name="registro"),
    path("gestion/", views.gestion, name="gestion"),
    path("gestion/productos/nuevo/", views.producto_formulario, name="crear_producto"),
    path("gestion/productos/<int:producto_id>/editar/", views.producto_formulario, name="editar_producto"),
    path("gestion/productos/<int:producto_id>/eliminar/", views.eliminar_producto, name="eliminar_producto"),
    path("gestion/productos/<int:producto_id>/stock/", views.ajustar_stock, name="ajustar_stock"),
    path("gestion/pedidos/", views.pedidos_gestion, name="pedidos_gestion"),
    path("gestion/reportes/categorias/", views.reporte_categorias, name="reporte_categorias"),
    path("gestion/reportes/categorias/excel/", views.exportar_reporte_categorias, name="exportar_categorias"),
    path("gestion/reportes/stock-critico/", views.reporte_stock_critico, name="reporte_stock"),
    path("gestion/reportes/stock-critico/excel/", views.exportar_stock_critico, name="exportar_stock"),
]
