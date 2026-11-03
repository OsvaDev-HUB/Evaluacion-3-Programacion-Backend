"""Cuentas con contraseñas visibles en JSON para la demostración académica."""

import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

from .storage import editar_json


def cargar_usuarios():
    with Path(settings.USUARIOS_DATOS).open(encoding="utf-8") as archivo:
        return json.load(archivo)


def editar_usuarios():
    return editar_json(settings.USUARIOS_DATOS, cargar_usuarios)


def buscar_usuario(username):
    coincidencias = [
        usuario for usuario in cargar_usuarios()["usuarios"]
        if usuario["username"].casefold() == username.casefold()
    ]
    return coincidencias[0] if len(coincidencias) == 1 else None


def usuario_a_json(usuario, password):
    return {
        "username": usuario.username,
        "nombre": usuario.first_name,
        "email": usuario.email,
        "password": password,
        "rol": "admin" if usuario.is_staff else "cliente",
        "activo": usuario.is_active,
    }


def agregar_usuario(datos, usuario, password):
    if any(u["username"].casefold() == usuario.username.casefold() for u in datos["usuarios"]):
        raise ValidationError("Ya existe una cuenta con ese nombre de usuario.")
    datos["usuarios"].append(usuario_a_json(usuario, password))
