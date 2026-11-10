from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import ConsultaCliente, Pedido, PerfilCliente, Producto
from .usuarios import actualizar_contacto, agregar_usuario, buscar_usuario, editar_usuarios

EXTENSIONES_FOTO = ("jpg", "jpeg", "png", "webp")
TAMANO_MAXIMO_FOTO = 5 * 1024 * 1024  # 5 MB


def es_imagen(inicio):
    """Revisa los primeros bytes del archivo para confirmar que es JPG, PNG o WebP."""
    es_png = inicio.startswith(b"\x89PNG\r\n\x1a\n")
    es_jpg = inicio.startswith(b"\xff\xd8\xff")
    es_webp = inicio[:4] == b"RIFF" and inicio[8:12] == b"WEBP"
    return es_png or es_jpg or es_webp


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    email = forms.EmailField(label="Correo electrónico")

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("first_name", "email", "username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Textos de ayuda breves para que el formulario no sea tan largo
        self.fields["username"].help_text = "Solo letras, números y los signos @ . + - _"
        self.fields["password1"].help_text = "Mínimo 8 caracteres, que no sea solo números ni una clave común."
        self.fields["password2"].help_text = ""

    def clean_username(self):
        username = super().clean_username()
        if username and buscar_usuario(username):
            raise forms.ValidationError("Ya existe una cuenta con ese nombre de usuario.")
        return username

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_staff = False
        usuario.is_superuser = False
        if commit:
            with transaction.atomic():
                with editar_usuarios() as datos:
                    agregar_usuario(datos, usuario, self.cleaned_data["password1"])
                    usuario.save()
        return usuario


# Dibujos disponibles para los productos que no tienen foto
OPCIONES_ILUSTRACION = [
    ("caja", "Producto / caja"), ("martillo", "Martillo"), ("destornillador", "Destornilladores"),
    ("alicate", "Alicate"), ("llave", "Llave ajustable"), ("huincha", "Huincha de medir"),
    ("taladro", "Taladro / atornillador"), ("sierra", "Sierra circular"),
    ("tornillos", "Fijaciones"), ("pintura", "Tarro de pintura"), ("rodillo", "Rodillo"),
    ("brocha", "Brocha"), ("cinta", "Cinta"), ("cable", "Cable eléctrico"),
    ("ampolleta", "Ampolleta"), ("tuberia", "Gasfitería"), ("saco", "Saco de construcción"),
    ("silicona", "Sellador"), ("guantes", "Guantes"), ("lentes", "Lentes de seguridad"),
    ("casco", "Casco"), ("protector", "Protección personal"),
]


class ProductoForm(forms.ModelForm):
    """Formulario del CRUD de productos, construido a partir del modelo Producto."""

    # Campos que no vienen tal cual del modelo
    ilustracion = forms.ChoiceField(label="Ilustración si no hay foto", choices=OPCIONES_ILUSTRACION)
    quitar_foto = forms.BooleanField(label="Quitar la foto actual", required=False)

    class Meta:
        model = Producto
        fields = ["nombre", "categoria", "precio", "stock", "descripcion", "foto", "ilustracion"]
        labels = {
            "nombre": "Nombre del producto",
            "categoria": "Categoría",
            "precio": "Precio en pesos chilenos",
            "stock": "Stock disponible",
            "descripcion": "Descripción",
            "foto": "Foto del producto",
        }
        widgets = {
            # "list" conecta el campo con las categorías que ya existen (datalist)
            "categoria": forms.TextInput(attrs={"list": "categorias"}),
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "foto": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En el modelo la descripción es opcional, pero en la tienda se pide siempre
        self.fields["descripcion"].required = True

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio < 1:
            raise forms.ValidationError("El precio debe ser mayor a $0.")
        return precio

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        # Solo se revisa si se subió una foto nueva; la que ya estaba guardada se deja igual
        if "foto" not in self.files:
            return foto
        extension = foto.name.rsplit(".", 1)[-1].lower() if "." in foto.name else ""
        if extension not in EXTENSIONES_FOTO:
            raise forms.ValidationError("Sube una imagen JPG, PNG o WebP.")
        if foto.size > TAMANO_MAXIMO_FOTO:
            raise forms.ValidationError("La foto pesa más de 5 MB. Elige una imagen más liviana.")
        inicio = foto.read(12)
        foto.seek(0)
        if not es_imagen(inicio):
            raise forms.ValidationError("El archivo no es una imagen válida.")
        return foto


class PedidoForm(forms.Form):
    nombre = forms.CharField(label="Nombre de quien retira", max_length=150)
    email = forms.EmailField(label="Correo electrónico")
    telefono = forms.RegexField(label="Teléfono de contacto", regex=r"^\+?[\d\s()-]{8,20}$", error_messages={"invalid": "Ingresa un teléfono válido de 8 a 20 caracteres."})


class EstadoPedidoForm(forms.ModelForm):
    """El administrador cambia el estado de un pedido."""

    class Meta:
        model = Pedido
        fields = ["estado"]
        labels = {"estado": "Estado del pedido"}

    def clean_estado(self):
        estado = self.cleaned_data["estado"]
        # self.instance.estado todavía tiene el estado guardado en la BD
        if self.instance.estado == Pedido.CANCELADO and estado != Pedido.CANCELADO:
            raise forms.ValidationError("Un pedido cancelado no se puede reactivar: su stock ya volvió a la tienda.")
        if self.instance.estado == Pedido.ENTREGADO and estado != Pedido.ENTREGADO:
            raise forms.ValidationError("Un pedido entregado no se puede cambiar: el cliente ya retiró los productos.")
        return estado


class ConsultaForm(forms.ModelForm):
    """Formulario de consultas de clientes (se guarda en ConsultaCliente)."""

    class Meta:
        model = ConsultaCliente
        fields = ["nombre", "correo", "producto", "mensaje"]
        labels = {
            "nombre": "Tu nombre",
            "correo": "Correo electrónico",
            "producto": "Producto por el que preguntas (opcional)",
            "mensaje": "Tu consulta",
        }
        help_texts = {"mensaje": "Mínimo 10 caracteres. Si preguntas por un pedido, incluye su número."}
        widgets = {
            "nombre": forms.TextInput(attrs={"autocomplete": "name"}),
            "correo": forms.EmailInput(attrs={"autocomplete": "email"}),
            "mensaje": forms.Textarea(attrs={"rows": 5}),
        }
        error_messages = {
            "nombre": {"required": "Escribe tu nombre para saber a quién responder."},
            "correo": {"required": "Escribe tu correo: ahí te enviaremos la respuesta.",
                       "invalid": "Revisa el correo: debe tener el formato nombre@dominio.cl."},
            "mensaje": {"required": "Escribe tu consulta."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.order_by("nombre")
        self.fields["producto"].empty_label = "Ninguno en particular"

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 letras.")
        return nombre

    def clean_mensaje(self):
        mensaje = self.cleaned_data["mensaje"].strip()
        if len(mensaje) < 10:
            raise forms.ValidationError(f"Cuéntanos un poco más: el mensaje tiene {len(mensaje)} caracteres y el mínimo es 10.")
        return mensaje


class RespuestaConsultaForm(forms.ModelForm):
    """El administrador responde una consulta."""

    class Meta:
        model = ConsultaCliente
        fields = ["respuesta"]
        labels = {"respuesta": "Respuesta para el cliente"}
        widgets = {"respuesta": forms.Textarea(attrs={"rows": 5})}

    def clean_respuesta(self):
        respuesta = self.cleaned_data["respuesta"].strip()
        if len(respuesta) < 5:
            raise forms.ValidationError("Escribe una respuesta de al menos 5 caracteres.")
        return respuesta


class PerfilForm(forms.ModelForm):
    """Datos del cliente: nombre y correo (usuario) más teléfono, comuna y dirección (perfil)."""

    nombre = forms.CharField(label="Nombre", max_length=150)
    apellido = forms.CharField(label="Apellido", max_length=150, required=False)
    email = forms.EmailField(label="Correo electrónico", help_text="Aquí te llegan las respuestas a tus consultas.")

    class Meta:
        model = PerfilCliente
        fields = ["telefono", "comuna", "direccion"]
        help_texts = {"telefono": "Lo usamos para avisarte cuando tu pedido esté listo.",
                      "direccion": "Calle y número. Queda como referencia: los pedidos se retiran en tienda."}
        widgets = {
            "telefono": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
            "comuna": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "direccion": forms.TextInput(attrs={"autocomplete": "street-address"}),
        }

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        # Los campos del usuario van primero en el formulario
        self.fields["nombre"].initial = usuario.first_name
        self.fields["apellido"].initial = usuario.last_name
        self.fields["email"].initial = usuario.email
        self.order_fields(["nombre", "apellido", "email", "telefono", "comuna", "direccion"])

    def bloquear(self):
        """Deja todos los campos bloqueados (solo lectura): Django ignora lo que llegue en ellos."""
        for campo in self.fields.values():
            campo.disabled = True

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 letras.")
        return nombre

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()
        if telefono and not PedidoForm.base_fields["telefono"].regex.match(telefono):
            raise forms.ValidationError("Ingresa un teléfono válido de 8 a 20 caracteres.")
        return telefono

    def save(self, commit=True):
        perfil = super().save(commit=False)
        perfil.usuario = self.usuario
        if commit:
            with transaction.atomic():
                perfil.save()
                self.usuario.first_name = self.cleaned_data["nombre"]
                self.usuario.last_name = self.cleaned_data["apellido"].strip()
                self.usuario.email = self.cleaned_data["email"]
                self.usuario.save(update_fields=["first_name", "last_name", "email"])
                # El login relee nombre y correo desde usuarios.json
                actualizar_contacto(self.usuario.username, self.usuario.first_name, self.usuario.email)
        return perfil


class SuscripcionForm(forms.Form):
    """Correo para recibir ofertas (formulario del pie de página)."""

    correo = forms.EmailField(
        label="Tu correo", error_messages={"invalid": "Revisa el correo: debe tener el formato nombre@dominio.cl."},
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "nombre@correo.cl"}),
    )
