# Diseño de la tienda El Tornillo

La portada `/` presenta la ferretería y orienta al cliente con ideas de proyectos, una sección Nuestra historia, una guía breve, una sección Contacto y el botón «Ver catálogo». Ese botón abre `/catalogo/`, una página independiente con productos, precios, búsqueda, filtros y orden. El hero usa el recorte sin fondo aportado en `Public/LandingPage/maestrohero.png`, servido como `catalogo/static/catalogo/img/landing/maestro-hero.webp`; reemplaza a la foto anterior `deposit-hero.webp`, que queda sin uso. El inventario y sus acciones se presentan en una sección exclusiva para administradores.

## Sistema visual

La dirección elegida por el usuario es «A medida»: un catálogo de taller con grafito, aluminio claro, blanco y naranja. El sistema normativo de colores, tipografía y componentes está en [DESIGN.md](../.impeccable/DESIGN.md), extraído del CSS implementado. [El sidecar de Impeccable](../.impeccable/design.json) contiene estados, cortes de pantalla y ejemplos de componentes; sus rampas de color sirven únicamente para previsualización.

- Grafito para cabecera, pie y texto principal; blanco para productos y formularios; aluminio para el fondo y los paneles.
- Naranja para acciones y selección. Verde para disponibilidad y confirmación; rojo para errores, agotados y acciones destructivas, siempre acompañado por texto.
- League Gothic Regular para marca y titulares expresivos; Barlow Condensed Medium/SemiBold para encabezados; Arial, Segoe UI y sans-serif para lectura. Las dos familias condensadas se sirven localmente con sus licencias OFL.
- Celdas de producto contiguas con bordes finos y esquinas rectas. Los controles tienen radio de 2px y altura mínima de 44px. La notificación flotante es la única superficie con sombra.
- Contenedor de hasta 1552px. El catálogo pasa de cuatro columnas a tres hasta 1100px, dos hasta 850px y una hasta 359px. A 640px, los filtros se convierten en un desplegable sobre los resultados y los márgenes laterales son de 16px.

La landing tiene una cabecera simple con Inicio, Cómo comprar, Nuestra historia, Contacto, Preguntas y Catálogo, en Barlow Condensed y mayúsculas como la barra del catálogo, además de cuenta y carrito. Desde 1100px hacia abajo, ese menú pasa a su propia fila bajo la marca para que los seis enlaces quepan. La portada usa las mismas piezas del catálogo: fondo de aluminio, titulares en League Gothic, celdas blancas contiguas con bordes finos y la regla de medición. La presentación sigue una referencia aportada por el usuario. A la izquierda van el titular, el texto, un botón «Ver catálogo» más grande y las cifras reales del inventario (productos, con stock y categorías), cada una con su ícono y separadas por líneas verticales. A la derecha, el maestro recortado aparece sobre hexágonos naranjos en SVG, tomados de la forma del logo: dos rellenos que se desvanecen y uno de contorno. Abajo, una regla detallada (marcas cortas cada 8px y largas cada 40px) cruza todo el ancho; el maestro pasa por delante de ella y llega al borde inferior del hero. El hero tiene fondo blanco y una línea inferior, para que el corte de la foto caiga justo sobre un borde. Bajo la regla se indican los precios en pesos chilenos y que la imagen es referencial. Hasta 850px el hero se apila: texto, maestro y regla; ahí el corte de las piernas coincide con la línea base de la regla y el borde superior de los hexágonos se desvanece. Después vienen las tres ideas de proyectos y luego «Recorre la tienda», que muestra una celda por categoría con foto, cantidad de productos y stock calculados desde el inventario, y abre el catálogo filtrado. Las ideas de proyectos y las categorías usan celdas contiguas. La guía explica la compra en tres pasos con números grandes, porque es una secuencia. Nuestra historia es una franja compacta de grafito con tres columnas: título, una frase destacada con un párrafo breve, y el equipo de maestros apoyado en el borde inferior. En tabletas la foto pasa a una columna lateral y en móvil se apila al final. Contacto es una grilla de celdas contiguas: la foto de asesoría a la izquierda (al lado contrario de la foto de Historia, para que no queden juntas) y cuatro celdas con ícono para teléfono, correo, dirección y horario. No tiene botones propios, para no repetir acciones que ya están en el hero y en la cabecera. Los datos son ficticios, creados para la evaluación; el correo usa el dominio reservado `.example` y el teléfono no es un enlace para marcar. La página termina con Preguntas frecuentes: la regla de medición arriba, el título fijo a la izquierda y un acordeón nativo (`<details>`) a la derecha que abre una pregunta a la vez, funciona sin JavaScript y con teclado, y gira el + a × al abrir. Las seis respuestas describen el funcionamiento real de la tienda (cuenta al confirmar, sin cobros, stock visible, retiro en tienda, cantidades limitadas por stock y pedidos en Mi cuenta) y enlazan al catálogo, al carrito o a la cuenta donde corresponde. Las celdas comparten el borde naranja interior del catálogo al pasar el puntero o enfocar con teclado. En móvil las categorías quedan en dos columnas y el resto se apila con lectura lineal.

Dentro del catálogo, la cabecera incorpora búsqueda y navegación de categorías. El índice lateral acompaña al titular «Nuestro catálogo.», el resumen, el orden y la retícula de productos. Su ancho real es 264px, con ajustes a 220px y 194px; los 240px de la referencia inicial no son una constante del código final.

Se conservan las fotografías referenciales existentes y sus originales en `Public/Products/`; el rediseño no generó nuevas fotografías de producto con IA. Las imágenes se contienen completas sobre blanco. El SVG existente actúa como respaldo cuando no hay foto y la ficha identifica el carácter referencial de la imagen. Los colores propios de esos recursos no definen la paleta de la interfaz.

## Logo y fotografías de personas

El logo aportado (`Public/LandingPage/logo.png`) aparece junto a la marca en la cabecera y el pie de todas las páginas, en el panel de inicio de sesión y como ícono de la pestaña. Conserva su naranja propio (#E04415); la interfaz sigue usando su acento #C54015.

Las seis fotos de maestros y clientes llegan sin fondo y se sirven en WebP desde `catalogo/static/catalogo/img/landing/`, cada una con su archivo `.json` de procedencia. Las fotos sin cortes se apoyan sobre una línea del sistema. Las que vienen cortadas a los lados o abajo van dentro de una celda blanca del mismo tamaño que la imagen, para que cada corte quede sobre un borde y no se note. Todas tienen un alto máximo para no agrandar las secciones:

| Lugar | Imagen | Función |
| --- | --- | --- |
| Hero de la portada | `maestro-hero.webp` | El maestro, sobre hexágonos naranjos, pasa por delante de la regla y llega al borde inferior del hero. |
| Nuestra historia | `equipo.webp` | El equipo, sin cortes, se apoya en el borde inferior de la banda de grafito; alto máximo 340px. |
| Contacto | `asesoria.webp` | Celda izquierda de la grilla de contacto; la foto llena la celda, así sus cortes quedan fuera de vista. |
| Inicio de sesión | `equipo-clientes.webp` | Asoma 210px al pie del panel oscuro; su corte derecho coincide con el borde del panel. |
| Registro | `revision-clientes.webp` | Al pie del panel oscuro, igual que en el inicio de sesión, rozando la lista de beneficios. |
| Carrito vacío y 404 | `maestra.webp` y `maestro-hero.webp` | Convierten el estado vacío en una invitación a seguir. |

Según la skill `marketing-psychology`, las personas con uniforme de la tienda aplican simpatía y unidad: muestran quién está detrás de «nosotros te ayudamos». Son imágenes referenciales; no se presentan como testimonios ni como clientes reales.

## Crear cuenta

La página de registro usa la misma estructura que el inicio de sesión: formulario a un lado y panel de grafito al otro, con foto al pie y, en celular, el formulario primero. El logo va a la derecha del título, en la misma fila, para que los textos suban y la foto, que llena el espacio libre del panel, se vea más grande. El formulario va en dos columnas (nombre y correo, usuario a todo el ancho, contraseña y confirmación) y las ayudas de Django se reemplazaron por textos breves en español; las reglas de validación no cambian. El panel muestra tres beneficios reales de tener cuenta, siguiendo la skill `marketing-psychology`: los pedidos quedan guardados, el nombre y el correo se completan solos al confirmar y el carrito se mantiene al registrarse.

Inicio de sesión y registro comparten una entrada coordinada: el contenido del panel oscuro y los campos del formulario aparecen en cascada, la línea divisoria del panel se dibuja de izquierda a derecha como la regla del hero y los maestros suben desde el borde inferior. El campo que ya tiene el foco no se anima. Al interactuar, la etiqueta del campo activo se vuelve naranja y el borde reacciona al puntero; al enviar, el botón cambia a «Ingresando…» o «Creando cuenta…», queda marcado como ocupado y no permite un segundo envío. Con movimiento reducido no hay animaciones.

## Crear y editar producto

El formulario de administración usa dos columnas en un panel de hasta 1040px. A la izquierda, una zona de foto con el mismo formato de la tarjeta del catálogo sirve de vista previa: se puede hacer clic o arrastrar una imagen, y se muestra al instante. A la derecha, los campos van en grilla (nombre a todo el ancho; categoría y precio; stock e ilustración; descripción a todo el ancho). Los botones Cancelar y Crear producto quedan en el encabezado. En celular la foto queda en una fila con su texto y los campos se apilan.

La foto es opcional. El servidor acepta JPG, PNG o WebP de hasta 5 MB y revisa los primeros bytes del archivo para confirmar que es una imagen; no se agregó ninguna dependencia nueva. Las fotos se guardan en `media/productos/` (carpeta ignorada por git) y su ruta queda en el campo `foto` del producto. Si un producto tiene foto, el catálogo, la ficha, el carrito y la administración la usan antes que la foto original o la ilustración. Al editar se puede reemplazar o quitar, y al eliminar el producto también se borra su archivo.

## Interacción y adaptación

La marca y los enlaces Inicio llevan a `/`; «Ver catálogo» lleva a `/catalogo/`. Nuestra historia, la guía y Contacto se encuentran en `/#historia`, `/#como-comprar` y `/#contacto`. Búsquedas, filtros, orden y enlaces «Seguir comprando» permanecen dentro de `/catalogo/`, con `#productos` cuando corresponde. Los enlaces nativos funcionan sin JavaScript y los saltos respetan la cabecera fija y el movimiento reducido.

Agregar al carrito conserva el formulario y añade confirmación mediante JavaScript: estado «Agregando…», resultado «Agregado» en verde durante 1600ms, contador actualizado y aviso accesible con enlace al carrito. Los errores muestran una explicación y restauran el botón. La interfaz mantiene foco visible, salto al contenido, etiquetas y navegación semántica. El movimiento es breve y se desactiva cuando el usuario pide reducirlo.

Compra se apila a 850px; ficha y acceso, a 640px. En acceso móvil aparece primero el formulario. Inventario mantiene tabla con desplazamiento horizontal local y un resumen de dos columnas en móvil. Estas adaptaciones comparten el mismo CSS que la tienda.

## Flujos

- La presentación invita a explorar; las tarjetas de producto y sus controles de compra se muestran exclusivamente en el catálogo y las páginas de compra.
- Un visitante puede explorar y armar su carrito; al confirmar un pedido inicia sesión o crea su cuenta.
- Un mismo acceso autentica clientes y administradores. Los permisos reales del usuario determinan el acceso a gestión.
- El administrador crea, edita y elimina productos, modifica stock y revisa pedidos.
- El pedido es una demostración sin cobros; comprueba stock, registra el pedido y descuenta existencias.
- ES1 conserva el JSON original con 40 productos. La administración solicitada utiliza un archivo local separado; las credenciales y roles se leen desde `data/usuarios.json`; Django conserva IDs de usuario y sesiones en SQLite, ampliación respecto del PDF.

## Psicología aplicada a la landing

La skill `marketing-psychology` guía tres decisiones. Jobs to Be Done orienta el texto y los accesos a reparar, renovar y construir. La ley de Hick reduce las opciones iniciales a una acción principal, «Ver catálogo», y reserva los filtros para el momento de explorar. La reducción de fricción explica que consultar precios, revisar stock y preparar el carrito no exige registrarse; la cuenta se solicita al confirmar.

La secuencia sigue AIDA: presentar el beneficio, mostrar proyectos posibles, explicar el siguiente paso y cerrar resolviendo las dudas que frenan una compra. Una revisión posterior con la misma skill ordenó las opciones de menor a mayor: primero tres proyectos y después las ocho categorías, como pide la ley de Hick. La historia pasó después de la guía para no cortar el recorrido entre elegir y comprar, y Contacto ahora entrega datos de contacto en vez de repetir los pasos de compra. Las preguntas frecuentes reemplazan al antiguo cierre con botón: responden objeciones antes de comprar (aversión al arrepentimiento) y dejan la acción dentro de cada respuesta, sin sumar otro botón. Solo se comunican capacidades existentes; el pedido se identifica como demostración. Estas son hipótesis de diseño, no resultados medidos de conversión ni de pruebas con clientes.
