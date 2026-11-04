# Uso de IA

Proyecto: Catálogo online Ferretería El Tornillo - 40 productos
Evaluación: Sumativa 3 (ES3), Unidad 2 · ORM, reportes y formulario de clientes.

Herramienta: Claude Code (modelo Claude Sonnet 5.5), usado como copiloto (nivel N2) desde la terminal.

## Parte 1: Registro de consultas

### 1. Análisis de la pauta y preparación del entorno (etapa 0)

- **Prompt:** Analiza la pauta de la Evaluación Sumativa 3 ubicada en `docs/Evaluacion 3` y prepara el entorno de trabajo a partir del proyecto de la ES2, copia el código sin el entorno virtual ni la base de datos, instala las dependencias, aplica las migraciones, carga el poblamiento y verifica que el listado se muestre desde la base de datos. Los comandos de Git los ejecutaré yo.
- **Respuesta:** resumió las etapas y la escala de apreciación. Copió el proyecto de la ES2 sin `venv`, `.git` ni base de datos, creó el entorno virtual, instaló dependencias, migró, cargó los 40 productos con `loaddata` y verificó que el listado se mostrara desde la BD.
- **Qué usé o modifiqué:** usé el entorno preparado. Los comandos de Git y el primer push los hice yo, y después pedí revisar que el `.gitignore` no hubiera dejado pasar `venv/` ni `db.sqlite3`.

### 2. CRUD del catálogo con ModelForm (etapa 1)

- **Prompt:** Revisa qué funcionalidades del CRUD pedido en la etapa 1 ya existen en el proyecto de la ES2 y complétalas, crear, editar y eliminar productos desde el sitio, con confirmación al eliminar y redirección al listado después de cada operación.
- **Respuesta:** confirmó que crear, editar y eliminar ya funcionaban en `/gestion/`. Propuso pasar `ProductoForm` a `ModelForm` y usar `get_object_or_404` y `form.save()` para simplificar la vista.
- **Qué usé o modifiqué:** acepté el `ModelForm` y mantuve la redirección al listado de `/gestion/`. Se agregaron validaciones (precio mayor a $0 y descripción obligatoria), un ajuste rápido de stock sin valores negativos y pruebas automáticas.

### 3. Planificación de funcionalidades extra

- **Prompt:** Propón funcionalidades adicionales para el cliente y para el administrador, como editar sus datos, consultar sus pedidos y su estado, y suscribirse a ofertas, e indica en qué etapa de la pauta conviene implementar cada una.
- **Respuesta:** propuso pedidos con rastreo, consultas, perfil y suscripción para el cliente, y estado de pedidos, bandeja de consultas, reporte de ventas y suscriptores para el admin. Advirtió que cada extra tenía que poder explicarlo en la revisión.
- **Qué usé o modifiqué:** elegí todos los extras y los dejé para la etapa 3, para que cada commit coincidiera con su etapa.

### 4. Reportes con el ORM (etapa 2)

- **Prompt:** Implementa los dos reportes de la etapa 2 con consultas del ORM: un resumen por categoría con `annotate` o `aggregate`, y un listado de productos con stock crítico usando `filter` y `order_by`. Cada reporte debe tener su template y ser accesible desde la navegación de `base.html`.
- **Respuesta:** el reporte 1 agrupa por categoría con `values("categoria").annotate(...)` (`Count`, `Sum`, `Avg`, `Min`, `Max` y `Sum(F("precio") * F("stock"))`) y calcula los totales con `aggregate()`. El reporte 2 usa `filter(stock__lte=umbral).order_by("stock", "nombre")`. Agregó pruebas que comparan los totales con una suma hecha a mano.
- **Qué usé o modifiqué:** usé los reportes y revisé que los totales cuadraran con la BD (40 productos, 757 unidades y $6.341.430).

### 5. Navegación de gestión, exportación a Excel y estadísticas (etapa 2)

- **Prompt:** Mueve los enlaces de administración de la barra de categorías a un menú dentro de "Mi cuenta", para que no se sobrepongan. Agrega además la exportación a Excel de los reportes y más estadísticas, e indica qué corresponde a esta etapa y qué a la siguiente.
- **Respuesta:** creó un menú desplegable en "Mi cuenta", dentro de `base.html`, para seguir cumpliendo la navegación que pide la pauta. Agregó los agotados por categoría con `Count("id", filter=Q(stock=0))`, la distribución del stock, los productos con más valor en bodega y la descarga en Excel con `openpyxl`. Explicó que el estado de los pedidos correspondía a la etapa 3.
- **Qué usé o modifiqué:** usé el menú y las estadísticas. Agregué `openpyxl` a `requirements.txt` y dejé el estado de los pedidos para la etapa 3.

### 6. Formulario de clientes, sesiones y pedidos en la BD (etapa 3)

- **Prompt:** Implementa la etapa 3, el modelo `ConsultaCliente` registrado en `/admin`, el formulario con `ModelForm` y sus validaciones, la confirmación al guardar, los últimos productos visitados con sesiones y la verificación de CSRF. Incluye también las funcionalidades extra elegidas para el cliente y el administrador.
- **Respuesta:** creó los modelos `ConsultaCliente` (nombre, correo, mensaje, producto opcional y fecha automática), `Pedido`, `DetallePedido`, `PerfilCliente` y `Suscripcion`, registrados en `/admin`. Hizo `ConsultaForm` con `ModelForm` y validaciones (obligatorios, correo válido y largo mínimo), la página de confirmación, los últimos 3 productos vistos en `request.session` y pruebas de CSRF y de datos inválidos. Los pedidos pasaron del JSON a la BD, con estados, rastreo y devolución de stock al cancelar.
- **Qué usé o modifiqué:** usé la implementación y probé el formulario con datos inválidos y la cancelación de un pedido. Mi pedido de prueba anterior se pasó del JSON a la BD.

### 7. Adaptación de las vistas de detalle y animación del estado (etapa 3)

- **Prompt:** Adapta el detalle del pedido y el detalle de la consulta del administrador para aprovechar el ancho de pantalla en el computador, manteniendo la vista actual en el celular. Agrega también una animación al rastreo del estado del pedido.
- **Respuesta:** en el computador dejó dos columnas con `grid-template-areas`, y en el celular la vista anterior. Creó una base común (`.detalle-admin`) para el pedido y la consulta. En el rastreo, la línea se dibuja paso a paso y el paso actual queda marcado, respetando la opción de movimiento reducido.
- **Qué usé o modifiqué:** usé el diseño y la animación.

### 8. Formularios del cliente: consulta y mis datos (etapa 3)

- **Prompt:** Ensancha el formulario de consultas y muestra los datos del cliente bloqueados por defecto, con una opción para editarlos y una presentación más completa.
- **Respuesta:** el formulario de consulta ocupa todo el ancho, con nombre y correo lado a lado. En Mis datos, los campos salen deshabilitados desde el servidor (método `bloquear()` del formulario) y se habilitan con `?editar=1`. Se agregaron los grupos de campos, el apellido y un resumen de la cuenta.
- **Qué usé o modifiqué:** usé los cambios. Después pedí agregar las fotos de los maestros en esas pantallas, para que no se vieran vacías.



## Parte 2: Explicación del proceso

Partí con mi proyecto de la ES2 y le pedí a la IA que revisara la pauta y preparara el entorno para trabajar sobre lo que ya tenía.
Después le pedí revisar el CRUD, porque quería saber qué funcionaba y qué faltaba antes de seguir agregando cosas.
También le pedí los reportes con el ORM para cumplir la pauta y poder revisar el stock y el valor de los productos por categoría.
Para ampliar las opciones del sitio, elegí agregar consultas, edición de datos y seguimiento de pedidos para los clientes.
Me sirvieron tal cual la propuesta de usar ModelForm y los reportes por categoría y stock crítico, que mantuve después de revisarlos.
En los reportes comprobé que los totales coincidieran con la base de datos, y probé las consultas con datos inválidos y la cancelación de un pedido.
Otras cosas sí tuve que pedir que se corrigieran, como los enlaces de gestión que se sobreponían con las categorías y que movimos a Mi cuenta.
También pedí reorganizar los detalles de pedidos y consultas en dos columnas para aprovechar mejor la pantalla del computador.
En los formularios pedí más ancho, dejar los datos bloqueados hasta elegir editarlos y agregar fotos porque esas pantallas se veían vacías.
Aprendí que annotate permite calcular resultados por categoría, mientras que aggregate sirve para obtener un resumen general, como el total del inventario.
También entendí cómo se usa request.session para recordar los últimos productos visitados y la importancia de validar los datos de los formularios.
Durante el proceso fui revisando el resultado en el navegador y pidiendo ajustes; los commits y los push de cada etapa los hice yo.
