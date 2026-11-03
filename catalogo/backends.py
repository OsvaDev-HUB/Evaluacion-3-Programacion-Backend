"""El JSON es la fuente de credenciales; Django conserva IDs y sesiones."""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.utils.crypto import constant_time_compare

from .usuarios import buscar_usuario


logger = logging.getLogger(__name__)


class UsuariosJSONBackend(ModelBackend):
    def obtener_registro(self, username):
        try:
            registro = buscar_usuario(username)
            if (registro and registro.get("activo") is True
                    and registro.get("rol") in ("admin", "cliente")
                    and isinstance(registro.get("password"), str)):
                return registro
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            logger.error("No se pudo leer el archivo de usuarios. El acceso fue rechazado.")
        return None

    @staticmethod
    def atributos(registro):
        return {
            "first_name": registro.get("nombre", ""),
            "email": registro.get("email", ""),
            "is_active": True,
            "is_staff": registro["rol"] == "admin",
            # El rol admin gestiona la tienda desde /gestion/.
            "is_superuser": False,
        }

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None
        registro = self.obtener_registro(username)
        if not registro or not constant_time_compare(password, registro["password"]):
            return None

        # El ID estable mantiene las relaciones con sesiones y pedidos existentes.
        with transaction.atomic():
            usuario, _ = get_user_model().objects.update_or_create(
                username=registro["username"], defaults=self.atributos(registro),
            )
            # Solo la copia interna de Django conserva el hash para sus sesiones.
            if not check_password(password, usuario.password):
                usuario.set_password(password)
                usuario.save(update_fields=["password"])
        return usuario

    def get_user(self, user_id):
        try:
            usuario = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return None
        registro = self.obtener_registro(usuario.username)
        if not registro:
            return None
        if not check_password(registro["password"], usuario.password):
            return None
        # Releer el JSON aplica los cambios de rol y desactiva cuentas al instante.
        # Una clave diferente en el JSON exige iniciar sesión nuevamente.
        for campo, valor in self.atributos(registro).items():
            setattr(usuario, campo, valor)
        return usuario


class SuperusuarioBackend(ModelBackend):
    """Login normal de Django, pero solo para superusuarios (los de createsuperuser)."""

    def user_can_authenticate(self, user):
        # Las cuentas de la tienda siguen entrando solo con usuarios.json
        return super().user_can_authenticate(user) and user.is_superuser
