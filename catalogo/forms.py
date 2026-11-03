from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db import transaction

from .usuarios import agregar_usuario, buscar_usuario, editar_usuarios

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


class ProductoForm(forms.Form):
    nombre = forms.CharField(label="Nombre del producto", max_length=120)
    categoria = forms.CharField(label="Categoría", max_length=60, widget=forms.TextInput(attrs={"list": "categorias"}))
    precio = forms.IntegerField(label="Precio en pesos chilenos", min_value=1, max_value=999999999)
    stock = forms.IntegerField(label="Stock disponible", min_value=0, max_value=999999)
    descripcion = forms.CharField(label="Descripción", max_length=1500, widget=forms.Textarea(attrs={"rows": 4}))
    foto = forms.FileField(
        label="Foto del producto", required=False,
        widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
    )
    quitar_foto = forms.BooleanField(label="Quitar la foto actual", required=False)
    ilustracion = forms.ChoiceField(label="Ilustración si no hay foto", choices=[
        ("caja", "Producto / caja"), ("martillo", "Martillo"), ("destornillador", "Destornilladores"),
        ("alicate", "Alicate"), ("llave", "Llave ajustable"), ("huincha", "Huincha de medir"),
        ("taladro", "Taladro / atornillador"), ("sierra", "Sierra circular"),
        ("tornillos", "Fijaciones"), ("pintura", "Tarro de pintura"), ("rodillo", "Rodillo"),
        ("brocha", "Brocha"), ("cinta", "Cinta"), ("cable", "Cable eléctrico"),
        ("ampolleta", "Ampolleta"), ("tuberia", "Gasfitería"), ("saco", "Saco de construcción"),
        ("silicona", "Sellador"), ("guantes", "Guantes"), ("lentes", "Lentes de seguridad"),
        ("casco", "Casco"), ("protector", "Protección personal"),
    ])

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if not foto:
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
