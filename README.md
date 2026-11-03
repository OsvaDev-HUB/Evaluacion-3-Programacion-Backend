<p align="center">
  <img src="catalogo/static/catalogo/img/marca/logo.webp" alt="Logo Ferretería El Tornillo" width="140">
</p>

<h1 align="center">Ferretería El Tornillo</h1>

<p align="center">
  Catálogo online con Django Admin y base de datos SQLite<br>
  Evaluación Sumativa 2 · Programación Back End (TI3041)
</p>

---

Proyecto desarrollado con Django para la Evaluación Sumativa 2 de Programación Back End. Corresponde a la variante A de la pauta: un catálogo online para una ferretería con 40 productos.

En esta etapa los productos dejan de estar en un archivo JSON. Ahora se guardan en una base de datos SQLite, se administran desde Django Admin y el catálogo los lee usando el ORM. El proyecto parte del código de la Evaluación Sumativa 1.

## Novedades de la ES2

- Modelo `Producto` con los campos `nombre`, `categoria`, `precio`, `stock` y `descripcion`, más `foto` e `ilustracion` opcionales, y método `__str__`.
- Conexión a SQLite configurada en `config/settings.py`.
- Modelo registrado en `/admin` con columnas (`list_display`), buscador (`search_fields`) y filtro por categoría (`list_filter`).
- Poblamiento inicial de 40 productos generado con IA en `catalogo/fixtures/productos.json`.
- El catálogo lee los productos desde la base de datos con `Producto.objects.order_by("id").values()`.
- La gestión de la tienda (`/gestion/`) y las compras también crean, editan y descuentan stock directamente en la base de datos.
- Registro del uso de IA en `uso_ia.md`.

## Funcionalidades del sitio

- Landing de presentación con ideas de proyectos, nuestra historia, contacto y guía de compra.
- Catálogo con nombre, categoría, precio y stock de cada producto.
- Búsqueda, filtros por categoría y disponibilidad, y orden por precio o nombre.
- Detalle de cada producto y página de error si el producto no existe.
- Resumen con el total de productos, productos con stock, agotados y categorías.
- Carrito de compras, registro e inicio de sesión de clientes, y pedidos de demostración.
- Diseño adaptable a celulares.

## Instalación

Se necesita Python 3 y `pip`.

En Linux o macOS:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata productos
python manage.py createsuperuser
python manage.py runserver
```

En Windows:

```bash
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata productos
python manage.py createsuperuser
python manage.py runserver
```

Luego se puede abrir la tienda en <http://127.0.0.1:8000/> y el administrador en <http://127.0.0.1:8000/admin/>.

El comando `loaddata productos` carga los 40 productos de la fixture en la base de datos. La base de datos (`db.sqlite3`) no se sube al repositorio, por eso hay que crear el superusuario con `createsuperuser` después de clonar.

## Credenciales de prueba

| Tipo de cuenta | Usuario | Contraseña | Dónde ingresa |
| --- | --- | --- | --- |
| Superusuario (Django Admin) | `superadmin` | `SuperAdminTornillo2026!` | <http://127.0.0.1:8000/admin/> |
| Administrador de la tienda | `admin` | `AdminTornillo2026!` | <http://127.0.0.1:8000/cuenta/ingresar/> |
| Cliente | `cliente` | `ClienteTornillo2026!` | <http://127.0.0.1:8000/cuenta/ingresar/> |

Las cuentas de la tienda (`admin` y `cliente`) vienen de la ES1 y están guardadas en `data/usuarios.json`.

## Rutas principales

- `/`: landing de presentación de la ferretería.
- `/catalogo/`: catálogo de productos leído desde la base de datos.
- `/producto/<id>/`: detalle de un producto.
- `/admin/`: Django Admin para crear, editar y eliminar productos.
- `/carrito/`: carrito de compras.
- `/cuenta/ingresar/`: ingreso de clientes y del administrador de la tienda.
- `/cuenta/registro/`: registro de clientes.
- `/gestion/`: gestión de productos y stock para el administrador de la tienda.
- `/gestion/pedidos/`: pedidos registrados.

## Archivos principales

- `catalogo/models.py`: modelo `Producto`.
- `catalogo/admin.py`: configuración del modelo en Django Admin.
- `catalogo/fixtures/productos.json`: poblamiento inicial de 40 productos.
- `catalogo/migrations/`: migraciones del modelo.
- `catalogo/views.py`: vistas y consultas de productos con el ORM.
- `catalogo/backends.py`: login de la tienda (`data/usuarios.json`) y login de superusuarios para `/admin`.
- `catalogo/tests.py`: pruebas automáticas del sitio.
- `data/usuarios.json`: cuentas de la tienda.
- `catalogo/templates/`: templates del sitio.
- `catalogo/static/catalogo/`: estilos, JavaScript e imágenes.
- `config/settings.py`: configuración del proyecto y de la base de datos.
- `uso_ia.md`: registro del uso de IA durante la evaluación.

## Comprobación

Con el entorno virtual activado:

```bash
python manage.py check
python manage.py test
```

Las compras son solo una demostración académica: no se realizan pagos ni envíos reales.
