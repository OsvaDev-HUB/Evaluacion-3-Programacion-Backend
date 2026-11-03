# Uso de inteligencia artificial

**Proyecto:** catálogo online de una ferretería, variante A de la Evaluación Sumativa 1 de Programación Back End.

**Alcance:** Django, 40 productos en JSON, listado, detalle, resumen y mejoras de interfaz. Las propuestas mantienen el alcance de ES1: los productos se cargan desde JSON en la vista, sin incorporar persistencia en base de datos.

## Parte 1. Registro de consultas

### 1. Análisis de requisitos y planificación técnica

**Prompt 1**

```text
Revisa docs/Evaluacion_1 Backend.pdf y transforma los requisitos de la
variante A en un plan de implementación por etapas.

Utiliza la skill senior-architect para revisar la separación de
responsabilidades entre configuración, rutas, vistas, templates y archivos
estáticos. Lee sus instrucciones antes de aplicarla y ajusta sus
recomendaciones al tamaño de esta evaluación.

La solución debe usar Django y cargar 40 productos desde JSON en la vista.
Mantén el alcance de ES1: no añadas autenticación, administración, pagos
ni almacenamiento de productos en base de datos.
```

**Resumen de la respuesta:** el agente propone una estructura MVT de Django, distribuye las responsabilidades y vincula los requisitos con comprobaciones concretas. Identifica las etapas de entorno, aplicación, interfaz, mejoras y entrega.

### 2. Preparación del entorno y estructura de Django

**Prompt 2**

```text
Implementa las etapas de entorno y aplicación del plan aprobado.

Primero inspecciona la carpeta de trabajo y comprueba si existe un entorno
virtual. Utiliza ese entorno si es válido; de lo contrario, crea uno.
Instala Django dentro del entorno y registra las dependencias en
requirements.txt.

Crea config y catalogo, registra la aplicación en settings.py y conecta
sus rutas mediante include. Añade una vista mínima para verificar el
funcionamiento. Configura .gitignore para excluir el entorno virtual,
__pycache__ y los archivos temporales.

Explica los comandos necesarios para ejecutar el proyecto. Comprueba
manage.py check e informa el resultado real, incluidos los errores o
las comprobaciones que no puedas ejecutar.
```

**Resumen de la respuesta:** el agente prepara el entorno, registra la aplicación y conecta una ruta de prueba. Explica la activación del entorno virtual y la ejecución del servidor.

### 3. Generación y validación de los datos JSON

**Prompt 3**

```text
Genera data/catalogo.json con exactamente 40 productos de ferretería.
Cada producto debe tener id, nombre, categoria, precio y stock.

Usa identificadores enteros únicos, nombres descriptivos, categorías
consistentes y precios en pesos chilenos. Incluye productos con stock
cero para comprobar el destacado condicional.

Distribuye los productos entre herramientas manuales, herramientas
eléctricas, construcción, pinturas, electricidad, gasfitería, fijaciones
y seguridad. Los precios serán referenciales para la demostración.

Valida que el JSON pueda leerse, que existan exactamente 40 registros y
que todos cumplan el esquema. Informa los conteos obtenidos y cualquier
corrección aplicada antes de dar el archivo por terminado.
```

**Resumen de la respuesta:** el agente genera un catálogo de ejemplo y comprueba la cantidad de registros, los tipos de datos, la unicidad de los identificadores y la presencia de productos agotados.


### 4. Diseño de la interfaz mediante skills

**Prompt 4**

```text
Diseña e implementa el frontend del catálogo utilizando las skills 
impeccable, frontend-design y ui-ux-pro-max. Lee ambas instrucciones y explica
brevemente qué criterio aporta cada una a la solución.

El público son personas que necesitan encontrar herramientas y materiales,
comparar precios y comprobar disponibilidad. La interfaz debe facilitar
esas tareas y tener una identidad visual propia de una ferretería.

Antes de implementar, presenta una propuesta breve de paleta, tipografías,
jerarquía y distribución. Usa frontend-design para definir la dirección
visual y las búsquedas de ui-ux-pro-max para fundamentar las decisiones
de interacción, legibilidad y adaptación móvil.

Trabaja con templates de Django, HTML, CSS y JavaScript. No introduzcas
un framework de frontend. Construye base.html y lista.html con herencia,
cabecera, navegación, área de productos y pie de página.

Cada producto debe mostrar nombre, categoría, precio y stock. Conserva
foco visible, etiquetas accesibles y una distribución que funcione en
escritorio y móvil. Antes de finalizar, revisa la interfaz en el navegador
si hay uno disponible y distingue lo verificado de lo pendiente.
```

**Resumen de la respuesta:** el agente propone un sistema visual de ferretería, define los componentes compartidos y plantea una grilla adaptable. Relaciona las decisiones estéticas con `frontend-design` y las de usabilidad con `ui-ux-pro-max`.



**Prompt 5**

```text
Conecta la interfaz con data/catalogo.json desde catalogo/views.py.
La vista debe entregar los productos al contexto y lista.html debe
recorrerlos mediante un bucle de Django, sin copiar manualmente las tarjetas.

Añade una ruta de detalle con identificador entero y una vista que busque
el producto correspondiente. Si no existe, muestra una página comprensible
y devuelve el estado HTTP 404.

Calcula en Python el total de productos y cuántos tienen stock. Presenta
el resumen en el template y utiliza un condicional para distinguir los
agotados con texto y estilo, sin depender exclusivamente del color.

Reutiliza base.html y los componentes que correspondan. Explica el flujo
desde la URL hasta el template y verifica el listado completo, un detalle
válido, un identificador inexistente y los conteos del resumen.
```

**Resumen de la respuesta:** el agente conecta el JSON con las vistas, implementa el listado y el detalle, y calcula el resumen antes de renderizar. Propone un estado visual para los productos sin stock.


**Prompt 6**

```text
Mejora la sensación de interacción del catálogo utilizando impeccable, 
conservando el sistema visual aprobado.

Propón una entrada breve y coordinada para el encabezado y una aparición
en cascada de los productos al entrar en pantalla. Añade respuestas suaves
en enlaces, botones e imágenes cuando ayuden a entender la interacción.
```

**Resumen de la respuesta:** el agente propone una cascada mediante `IntersectionObserver` y animaciones nativas, junto con transiciones CSS para los estados de interacción. Incluye una alternativa sin movimiento.


## Parte 2. Explicación personal del proceso


Usé la IA como apoyo para organizar el proyecto y avanzar por partes.<br>
Primero le pedí ayuda con la estructura de Django para ordenar los archivos.<br>
Después solicité los 40 productos en JSON para construir el catálogo de ferretería.<br>
Para el diseño pedí las skills frontend-design y ui-ux-pro-max.<br>
Buscaba una página clara, con una identidad propia y que se pudiera usar en el celular.<br>
Me sirvió tal cual la propuesta de compartir la cabecera y el pie con un template base.<br>
Comprobé esa estructura revisando las páginas del listado y del detalle.<br>
En la parte visual pedí ajustar los espacios y suavizar los efectos que distraían.<br>
También solicité distinguir los productos agotados para que su estado fuera fácil de entender.<br>
Durante el proceso entendí mejor cómo la vista lee el JSON y lo envía al template.<br>
Aprendí cómo el bucle muestra los productos y el condicional permite destacar los que no tienen stock.<br>
La IA me ayudó a avanzar, pero también entendí que debo probar y comprender lo que propone.
